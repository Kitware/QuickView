#import paraview.web.venv  # Available in PV 5.10

from trame.app import get_server

from trame.widgets import vuetify, html
from trame.widgets import paraview as pvWidgets
from trame.widgets import client, grid

from trame.ui.vuetify import SinglePageWithDrawerLayout

from vissource.vissource  import  EAMVisSource
from vissource.viewmanager import ViewManager
from appui import properties3Dm, properties2D

import numpy as np
import traceback

import argparse

parser = argparse.ArgumentParser(prog='eamapp.py',
                                 description='Trame based app for visualizing EAM data')
parser.add_argument('-cf', '--conn', nargs="?", help='the nc file with connnectivity information')
parser.add_argument('-df', '--data', help='the nc file with data/variables')
parser.add_argument('-sf', '--state', nargs='+', help='state file to be loaded')
parser.add_argument('-wd', '--workdir', help='working directory (to store session data)')
args, xargs = parser.parse_known_args()


# -----------------------------------------------------------------------------
# trame setup
# -----------------------------------------------------------------------------

server = get_server()
server.client_type = "vue2" # instead of 'vue2'
state, ctrl = server.state, server.controller
pvWidgets.initialize(server)
import os
ConnFile = args.conn 
if args.conn is None:
    ConnFile = os.path.join(os.path.dirname(__file__), "data", "connectivity.nc")
DataFile = args.data
StateFile = args.state
WorkDir = args.workdir
from utilities import ValidateArguments
ValidateArguments(ConnFile, DataFile, StateFile, WorkDir)

state.connfile = ConnFile
state.datafile = DataFile

# -----------------------------------------------------------------------------
# ParaView code
# -----------------------------------------------------------------------------
state.vlev = 0
# create a new 'EAM Data Reader'
try:
    source = EAMVisSource()
    GlobeFile = os.path.join(os.path.dirname(__file__), "data", "globe.vtk")
    source.Update(datafile=DataFile, connfile=ConnFile, globefile=GlobeFile, lev=0)
    print(source.extents)
except Exception as e:
    print("Problem : ", e)
    traceback.print_exc()

viewmanager = ViewManager(source, server, state)

state.timesteps     = source.timestamps
state.lev           = source.lev
state.ilev          = source.ilev
state.extents       = list(source.extents)
state.vars2D        = source.vars2D
state.vars3Di       = source.vars3Di
state.vars3Dm       = source.vars3Dm
state.vars2Dstate   = [False] * len(source.vars2D)
state.vars3Distate  = [False] * len(source.vars3Di)
state.vars3Dmstate  = [False] * len(source.vars3Dm)

state.views         = []
state.cmaps         = ["0"]
state.layout        = []

state.ccardsentry   = []
state.ccardscolor   = [None] * len(source.vars2D + source.vars3Di + source.vars3Dm)
state.varcolor      = []
state.uselogscale   = []

ctrl.view_update = viewmanager.UpdateCamera
ctrl.view_reset_camera = viewmanager.ResetCamera
ctrl.on_server_ready.add(ctrl.view_update)
server.trigger_name(ctrl.view_reset_camera)

noncvd = [
    {"text" : 'Rainbow Desat.',    "value"  : 'Rainbow Desaturated',   },
    {"text" : 'Cool to Warm',      "value"  : 'Cool to Warm',}, 
    {"text" : 'Viridis',           "value"  : 'Viridis (matplotlib)', },
    {"text" : 'Inferno',           "value"  : 'Inferno (matplotlib)', }, 
]

cvd = [
    {"text" : 'Batlow',    "value"  : 'batlow',},
    {"text" : 'Oslo',      "value"  : 'oslo',}, 
    {"text" : 'Tokyo',     "value"  : 'tokyo', },
]

state.colormaps = noncvd

# -----------------------------------------------------------------------------
# GUI
# -----------------------------------------------------------------------------
state.trame__title = "ParaView eamdata"
layout = SinglePageWithDrawerLayout(server)

def update2DVars(index, visibility):
    state.vars2Dstate[index] = visibility
    state.dirty("vars2Dstate")

def update3DmVars(index, visibility):
    state.vars3Dmstate[index] = visibility
    state.dirty("vars3Dmstate")

@state.change('vcols')
def Columns(vcols, **kwargs):
    viewmanager.SetCols(vcols)

def Apply():
    s2d     = []
    s3dm    = []
    s3di    = []
    if len(state.vars2D) > 0 :
        v2d     = np.array(state.vars2D)
        f2d     = np.array(state.vars2Dstate)
        s2d     = v2d[f2d].tolist()
    if len(state.vars3Dm) > 0 :
        v3dm    = np.array(state.vars3Dm)
        f3dm    = np.array(state.vars3Dmstate)
        s3dm    = v3dm[f3dm].tolist()
    if len(state.vars3Di) > 0 :
        v3di    = np.array(state.vars3Di)
        f3di    = np.array(state.vars3Distate)
        s3di    = v3di[f3di].tolist()
    source.LoadVariables(s2d, s3dm, s3di)

    state.color2D = s2d
    state.color3D = s3dm
    vars = s2d + s3dm

    state.ccardsentry = vars
    state.ccardsvars  = [{"text" : var, "value" : var} for var in vars] 
    
    with state:  
        viewmanager.UpdateView()

def ApplyColor(index, type, value):
    viewmanager.UpdateColor(index, type, value)

def updatecolors(event):
    if len(event) == 0:
        state.colormaps = cvd
    elif len(event) == 2:
        state.colormaps = cvd + noncvd
    elif '0' in event:
        state.colormaps = noncvd
    elif '1' in event:
        state.colormaps = noncvd

def ui_card(title, varname):
    with vuetify.VCard(v_show=f"{varname} == true"):
        vuetify.VCardTitle(
            title,
            classes="grey lighten-1 py-1 grey--text text--darken-3",
            style="user-select: none; cursor: pointer",
            hide_details=True,
            dense=True,
        )
        content = vuetify.VCardText(classes="py-2")
    return content

with layout:
    # uncomment following line to disable scrolling on views
    # client.Style("html { overflow: hidden; }")
    layout.icon.click = ctrl.view_reset_camera
    layout.title.set_text("EAM QuickView")
    with layout.toolbar:
        vuetify.VSpacer()
        vuetify.VDivider(vertical=True, classes="mx-2")
        #with vuetify.VContainer(fluid=True, style="max-height; 50px;", hide_details=True, classes="ma-0 pa-0"):
        with vuetify.VListItemGroup(dense=True):
                vuetify.VCheckbox(label="Use CVD friendly colormaps", value=0, v_model = ("cmaps",), dense=True, style="min-height : unset", hide_details=True , change=(updatecolors, "[$event]")),
                vuetify.VCheckbox(label="Use non-CVD friendly colormaps", value=1, v_model = ("cmaps",), dense=True, style="min-height : unset", hide_details=True, change=(updatecolors, "[$event]"))
        vuetify.VDivider(vertical=True, classes="mx-2")
        html.Div(
            f"Connectivity File :  \"{ConnFile}\" <br> Data File :  \"{DataFile}\"",
            style="padding: 10px;",
        )
        vuetify.VDivider(vertical=True, classes="mx-2")
        with vuetify.VBtn(icon=True, click=ctrl.view_reset_camera):
            vuetify.VIcon("mdi-restore")

    items = []
    with layout.drawer as drawer:
        drawer.width = 400
        vuetify.VDivider(classes="mb-2")
        with vuetify.VContainer(fluid=True, classes="d-flex justify-center align-center"):
                vuetify.VBtn("Update Views", click=Apply, style="background-color: gray; color: white; width: 200px; height: 50px;")
        vuetify.VDivider(classes="mx-2") 
        with vuetify.VContainer(fluid=True):
            with ui_card(title="Select Data Slice", varname="true"):
                with vuetify.VRow():
                    with vuetify.VCol(cols=6):
                        vuetify.VSlider(
                            label='Lev',
                            v_model=("vlev", 0),
                            min=0,
                            max=("lev.length - 1", )
                        )
                    with vuetify.VCol(cols=2):
                        html.Div("{{'(' + String(vlev) + ')'}}")
                    with vuetify.VCol(cols=3):
                        html.Div("{{parseFloat(lev[vlev]).toFixed(2)}}")
                with vuetify.VRow():
                    with vuetify.VCol(cols=6):
                        vuetify.VSlider(
                            label='Time',
                            v_model=("tstamp", 0),
                            min=0,
                            max=("timesteps.length - 1", )
                        )
                    with vuetify.VCol(cols=2):
                        html.Div("{{'(' + String(tstamp) + ')'}}")
                    with vuetify.VCol(cols=3):
                        html.Div("{{parseFloat(timesteps[tstamp]).toFixed(2)}}")
                #with ui_card(title="Clipping", varname="true"):
                vuetify.VCheckbox(
                    label="Lat/Long Clipping",
                    v_model=("clipping", False),
                    dense=True
                )
                with vuetify.VContainer(fluid=True):
                    with ui_card(title=None, varname="clipping"):
                        with vuetify.VRow():
                            with vuetify.VCol(cols=3):
                                vuetify.VTextField(
                                    v_model=("cliplong[0]",)
                                )
                            with vuetify.VCol(cols=6):
                               html.Div("Longitude", classes="text-center align-center justify-center text-subtitle-1", style="color: blue") 
                            with vuetify.VCol(cols=3):
                                vuetify.VTextField(
                                    v_model=("cliplong[1]",)
                                ) 
                        with vuetify.VRow():
                            vuetify.VRangeSlider(
                                #label='Longitude',
                                v_model=("cliplong", [source.extents[0], source.extents[1]]),
                                min=("extents[0]", ),
                                max=("extents[1]", ),
                            )
                        vuetify.VDivider(classes="mx-2")
                        with vuetify.VRow():
                            with vuetify.VCol(cols=3):
                                vuetify.VTextField(
                                    v_model=("cliplat[0]",)
                                )
                            with vuetify.VCol(cols=6):
                               html.Div("Latitude", classes="text-center align-center justify-center text-subtitle-1", style="color: blue") 
                            with vuetify.VCol(cols=3):
                                vuetify.VTextField(
                                    v_model=("cliplat[1]",)
                                )
                        with vuetify.VRow():
                            vuetify.VRangeSlider(
                                #label='Latitude',
                                v_model=("cliplat", [source.extents[2], source.extents[3]]),
                                min=("extents[2]", ),
                                max=("extents[3]", ),
                            )
        vuetify.VDivider(classes="mx-2")
        with vuetify.VContainer(fluid=True):
            with ui_card(title="Map Projection Selection", varname="true"):
                html.A(
                    "Projection",
                    style="padding: 10px;",
                )
                vuetify.VSelect(
                    items=("options", ["Cyl. Equidistant","Robinson", "Mollweide"]),
                    v_model=("projection", "Cyl. Equidistant")
                )
        vuetify.VDivider(classes="mx-2")
        with vuetify.VContainer(fluid=True):
            with ui_card(title="Variable Selection", varname="true"):
                html.A(
                    "2D Variables",
                    style="padding: 10px;",
                )
                with vuetify.VContainer(fluid=True, style="max-height: 200px", classes="overflow-y-auto"):
                    with vuetify.VListItemGroup(dense=True, label="2D Variables"):
                        vuetify.VCheckbox(
                            v_for="v, i in vars2D",
                            key="i",
                            label=("vars2D[i]",),
                            v_model=("vars2Dstate[i]",),
                            change=(update2DVars, "[i, $event]"),
                            style="max-height: 20px",
                            dense=True
                        )
                vuetify.VDivider(classes="mx-2")
                html.A(
                    "3D Middle Layer Variables",
                    style="padding: 10px;",
                )
                with vuetify.VContainer(fluid=True, style="max-height: 200px", classes="overflow-y-auto"):
                    with vuetify.VListItemGroup(dense=True, label="3D Variables"):
                        vuetify.VCheckbox(
                            v_for="v, i in vars3Dm",
                            key="i",
                            label=("vars3Dm[i]",),
                            v_model=("vars3Dmstate[i]",),
                            change=(update3DmVars, "[i, $event]"),
                            style="max-height: 20px",
                            dense=True
                        )
        vuetify.VDivider(classes="mx-2") 
        temp = server.trigger_name(ctrl.view_reset_camera)
        with layout.content:
            """
            with vuetify.VRow(
            ):
                vuetify.VCol(
                    #<vtk-remote-view ref="trame__remote_view_1" :viewId="trame__remote_view_1Id" class="pa-0 drag_ignore" style="width: 100%; height: 100%;" />
                    '<vtk-remote-view :ref="(el) => ($refs[vref] = el)" :viewId="get(`${vref}Id`)" class="pa-0 drag_ignore" style="width: 100%; height: 100%;" interactiveRatio="1" ></vtk-remote-view>',
                    v_for="vref, idx in views",
                    key="vref",
                    cols=("12 / vcols",),
                    style="height: 400px",
                )
            """
            with grid.GridLayout(
                layout=("layout", []),
                #row_height=20,
            ):
                with grid.GridItem(
                    v_for="vref, idx in views",
                    #v_for="item in layout",
                    key="idx",
                    v_bind=("layout[idx]", ),
                    #classes="pa-4",
                    #style="border: solid 1px #333; background: rgba(0, 69, 96, 0.5);",
                ):
                    html.Div(
                        '<vtk-remote-view :ref="(el) => ($refs[vref] = el)" :viewId="get(`${vref}Id`)" class="pa-0 drag_ignore" style="width: 100%; height: 100%;" interactiveRatio="1" ></vtk-remote-view>',
                        style="height: 200px, width: 400px"
                    )
                    with vuetify.VRow(classes="pt-2", dense=True):
                            with vuetify.VCol(cols=3):
                                vuetify.VSelect(
                                    v_model=("varcolor[idx]", state.colormaps[0]),
                                    items=("colormaps",),
                                    dense=True,
                                    hide_details=True,
                                    change=(ApplyColor, "[idx, 'color', $event]")
                                )
                            with vuetify.VCol(cols=3):
                                vuetify.VCheckbox(
                                    label="use log scale",
                                    v_model=("uselogscale[idx]", False),
                                    change=(ApplyColor, "[idx, 'log', $event]")
                                )
                            with vuetify.VCol(cols=2):
                                html.Div("Color<br>Range")
                            with vuetify.VCol(cols=1):
                                html.Div("min")
                                vuetify.VTextField(
                                )
                            with vuetify.VCol(cols=1):
                                html.Div("max")
                                vuetify.VTextField(
                                )
                            with vuetify.VCol(cols=1):
                                with vuetify.VBtn(icon=True):
                                    vuetify.VIcon("mdi-plus")
                            with vuetify.VCol(cols=1):
                                with vuetify.VBtn(icon=True):
                                    vuetify.VIcon("mdi-minus")
                            

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    server.start()
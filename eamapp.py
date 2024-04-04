#import paraview.web.venv  # Available in PV 5.10

from trame.app import get_server

from trame.widgets import vuetify
from trame.widgets import paraview as pvWidgets
from trame.widgets import client

from trame.ui.vuetify import SinglePageWithDrawerLayout

from vissource.vissource  import  EAMVisSource
from vissource.viewmanager import ViewManager
from appui import properties3Dm, properties2D

import numpy as np
import traceback
import asyncio

# -----------------------------------------------------------------------------
# trame setup
# -----------------------------------------------------------------------------

server = get_server()
server.client_type = "vue2" # instead of 'vue2'
state, ctrl = server.state, server.controller
pvWidgets.initialize(server)


# -----------------------------------------------------------------------------
# ParaView code
# -----------------------------------------------------------------------------
state.vlev = 0
# create a new 'EAM Data Reader'
try:
    source = EAMVisSource()
    ConnFile='/Users/ayenpure/repositories/eam/eamapp/data/TEMPEST_ne30pg2.scrip.renamed.nc'
    DataFile='/Users/ayenpure/repositories/eam/eamapp/data/aerosol_F2010.eam.h0.2014-12.nc'
    GlobeFile='/Users/ayenpure/repositories/eam/eamapp/data/cstar0.vtr'
    source.Update(datafile=DataFile, connfile=ConnFile, globefile=GlobeFile, lev=0)
except Exception as e:
    print("Problem : ", e)
    traceback.print_exc()

viewmanager = ViewManager(source, server, state)

state.colors        = viewmanager.colors

state.vars2D        = source.vars2D
state.vars3Di       = source.vars3Di
state.vars3Dm       = source.vars3Dm
state.vars2Dstate   = [False] * len(source.vars2D)
state.vars3Distate  = [False] * len(source.vars3Di)
state.vars3Dmstate  = [False] * len(source.vars3Dm)

state.views         = []
state.colors        = []
state.view_layout   = []

state.ccardsentry   = []
state.ccardscolor   = [None] * len(source.vars2D + source.vars3Di + source.vars3Dm)

ctrl.view_update = viewmanager.UpdateCamera
ctrl.view_reset_camera = viewmanager.ResetCamera
ctrl.on_server_ready.add(ctrl.view_update)
server.trigger_name(ctrl.view_reset_camera)

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

'''
@state.change("time_stamp")
def FetchTimeStamp(time_stamp, **kwargs):
    source.UpdateTimeStep(time_stamp)


@state.change('vlev')
def Lev(vlev, **kwargs):
    source.UpdateLev(vlev)

@state.change('projection')
def Projection(projection, **kwargs):
    source.SetProjection(projection)
'''

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
    #state.ccardscolor = ["Varidis"] * len(vars)
    state.ccardsvars  = [{"text" : var, "value" : var} for var in vars] 
    with state:  
        viewmanager.UpdateView()

def ApplyColor(color, index):
    viewmanager.UpdateColor(color, index)

with layout:
    # uncomment following line to disable scrolling on views
    # client.Style("html { overflow: hidden; }")
    layout.icon.click = ctrl.view_reset_camera
    layout.title.set_text("EAM/E3SM Viz")
    with layout.toolbar:
        vuetify.VSpacer()
        vuetify.VFileInput(
            label='Data File'
        )
        vuetify.VFileInput(
            label='Connectivity File'
        )
        vuetify.VDivider(vertical=True, classes="mx-2")
        with vuetify.VBtn(icon=True, click=ctrl.view_reset_camera):
            vuetify.VIcon("mdi-restore")

    items = []
    with layout.drawer as drawer:
        drawer.width = 325
        vuetify.VDivider(classes="mb-2")
        vuetify.VSlider(
            label='Lev',
            v_model=("vlev", 0),
            min=0,
            max=72
        )
        vuetify.VSlider(
            label='Time',
            v_model=("time_stamp", 0),
        )
        with vuetify.VContainer(fluid=True, style="max-height: 400px", classes="overflow-y-auto"):
            with vuetify.VListItemGroup(dense=True):
                vuetify.VCheckbox(
                    v_for="v, i in vars2D",
                    key="i",
                    label=("vars2D[i]",),
                    v_model=("vars2Dstate[i]",),
                    change=(update2DVars, "[i, $event]"),
                    style="max-height: 20px",
                    dense=True
                )
        with vuetify.VContainer(fluid=True, style="max-height: 400px", classes="overflow-y-auto"):
            with vuetify.VListItemGroup(dense=True):
                vuetify.VCheckbox(
                    v_for="v, i in vars3Dm",
                    key="i",
                    label=("vars3Dm[i]",),
                    v_model=("vars3Dmstate[i]",),
                    change=(update3DmVars, "[i, $event]"),
                    style="max-height: 20px",
                    dense=True
                )
        vuetify.VSelect(
            label="Projection",
            items=("options", ["Robinson", "Mollweide"]),
            v_model=("projection", 'Robinson')
        )
        vuetify.VBtn(
            "Apply",
            click=Apply
        )
        vuetify.VSlider(
            label='Columns',
            v_model=("vcols", 1),
            min=1,
            max=3
        ) 
        vuetify.VSelect(
            v_model=("ccardselect", None),
            items=("ccardsvars", []),
            dense=True,
            hide_details=True,
        )
        colors = [
            {"text" : 'Viridis',    "value"  : 'Viridis (matplotlib)', },
            {"text" : 'Inferno',    "value"  : 'Inferno (matplotlib)', }, 
            {"text" : 'Cool to Warm',   "value"  : 'Cool to Warm',}, 
            {"text" : 'Turbo',      "value"  : 'Turbo',   }
        ]
        with vuetify.VCard(
            v_for="v, i in ccardsentry",
            key="i",
            v_show="ccardsentry[i] == ccardselect"
        ):
            vuetify.VCardTitle(
                title=("ccardsentry[i]",), 
                classes="grey lighten-1 py-1 grey--text text--darken-3",
                dense=True,
                style="max-height: 20px",
            )
            with vuetify.VCardText(classes="py-2"):
                with vuetify.VRow(classes="pt-2", dense=True):
                    with vuetify.VCol(cols=6):
                        vuetify.VSelect(
                            v_model=("varcolor", "Viridis"),
                            items=("colormaps", colors),
                            dense=True,
                            hide_details=True,
                        )
                        vuetify.VBtn(
                            "Update",
                            click=(ApplyColor,"[varcolor, i]")                           
                        )
        temp = server.trigger_name(ctrl.view_reset_camera)
        with layout.content:
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

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    server.start()
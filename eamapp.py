import paraview.web.venv  # Available in PV 5.10

from trame.app import get_server
from trame.widgets import vuetify, paraview
from trame.ui.vuetify import SinglePageWithDrawerLayout

from vissource.vissource import EAMVisSource
from appui import properties3Dm, properties2D

import numpy as np

# -----------------------------------------------------------------------------
# trame setup
# -----------------------------------------------------------------------------

server = get_server()
server.client_type = "vue2" # instead of 'vue2'
state, ctrl = server.state, server.controller

# -----------------------------------------------------------------------------
# ParaView code
# -----------------------------------------------------------------------------

# create a new 'EAM Data Reader'
try:
    source = EAMVisSource()
    ConnFile='/home/local/KHQ/abhi.yenpure/repositories/eam/EAMApp/data/TEMPEST_ne30pg2.scrip.renamed.nc'
    DataFile='/data/eam/202311/v2_F2010_nc00_inst_macmic01.eam.h0.2010-12-25-00000.nc'
    source.Update(datafile=DataFile, connfile=ConnFile)
except Exception as e:
    print("Problem : ", e)

state.vars2D        = source.vars2D
state.vars2Dstate   = [False] * len(source.vars2D)
state.vars3Di       = source.vars3Di
state.vars3Distate  = [False] * len(source.vars3Di)
state.vars3Dm       = source.vars3Dm
state.vars3Dmstate  = [False] * len(source.vars3Dm)

# State use to track active UI card
state.setdefault("active_ui", None) # prevent resetting value if already present

pviews   = source.views
hviews   = []

def update_views(**kwargs):
    try:
        for v in hviews:
            v.update()
    except Exception as e:
        print("Error occured : ", e)

def reset_camera(**kwargs):
    try:
        for v in hviews:
            v.reset_camera()
    except Exception as e:
        print("Error occured : ", e)

ctrl.view_update = update_views
ctrl.view_reset_camera = reset_camera
ctrl.on_server_ready.add(ctrl.view_update)

# -----------------------------------------------------------------------------
# GUI
# -----------------------------------------------------------------------------
state.trame__title = "ParaView eamdata"

@state.change("colorby2D")
def update2Dview(colorby2D, **kwargs):
    print("Coloring by : ", colorby2D)
    colorvar = state.colorby2D
    colormap = state.colormap2D
    source.UpdateViews2D(colorvar, colormap)
    ctrl.view_update()

@state.change("colorby3D")
def update3Dview(colorby3D, **kwargs):
    print("Coloring by : ", colorby3D)
    colorvar = state.colorby3D
    colormap = state.colormap3D
    source.UpdateViews3D(colorvar, colormap)
    ctrl.view_update()

def update2DVars(index, visibility):
    state.vars2Dstate[index] = visibility

def update3DmVars(index, visibility):
    state.vars3Dmstate[index] = visibility

@state.change("time_stamp")
def FetchTimeStamp(time_stamp, **kwargs):
    source.UpdateTimeStep(time_stamp)
    pass

@state.change('linkviews')
def Spherical(linkviews, **kwargs):
    print(linkviews)
    source.AddCameraLink(linkviews)

@state.change('manageview')
def ManageView(manageview, **kwargs):
    print(manageview)
    if manageview == '2D':
        state.active_ui = "prop2D"
    elif manageview == '3D':
        state.active_ui = "prop3D"
    pass

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

layout = SinglePageWithDrawerLayout(server)
with layout:
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
        with vuetify.VContainer(fluid=True, style="max-height: 400px", classes="overflow-y-auto"):
            with vuetify.VListItemGroup(dense=True):
                vuetify.VCheckbox(
                    v_for="v, i in vars2D",
                    key="i",
                    label=("vars2D[i]",),
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
                    change=(update3DmVars, "[i, $event]"),
                    style="max-height: 20px",
                    dense=True
                )
        vuetify.VSelect(

        )
        vuetify.VSlider(
            label='Time',
            v_model=("time_stamp", 0),
        )
        vuetify.VBtn(
            "Apply",
            click=Apply
        )
        vuetify.VCheckbox(
            label='Link Views',
            v_model=('linkviews', False)
        )
        vuetify.VSelect(
            style="max-height: 400px",
            label="Manage Views",
            v_model=("manageview", None),
            items=("view_list", ['2D', '3D']),
            hide_details=True,
            dense=True,
            outlined=True,
            classes="pt-1",
        )
        properties2D()
        properties3Dm()

    with layout.content:
        with vuetify.VContainer(
            fluid=True,
            classes="pa-0 fill-height",
        ):
            #html_view = paraview.VtkLocalView(pviews[1])
            #ctrl.view_update = html_view.update
            #ctrl.view_reset_camera = html_view.reset_camera
            with vuetify.VRow(dense=True, style="height: 50%;"):
                with vuetify.VCol():
                    hviews.append(paraview.VtkLocalView(pviews[0].GetView()))
                with vuetify.VCol():
                    hviews.append(paraview.VtkLocalView(pviews[1].GetView()))
            '''
            with vuetify.VRow(dense=True, style="height: 50%;"):
                with vuetify.VCol():
                    hviews.append(paraview.VtkLocalView(pviews[0]))
                with vuetify.VCol():
                    hviews.append(paraview.VtkLocalView(pviews[0]))
            '''
# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    server.start()

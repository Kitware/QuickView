import paraview.web.venv  # Available in PV 5.10

from trame.app import get_server
from trame.widgets import vuetify, paraview
from trame.ui.vuetify import SinglePageWithDrawerLayout

from vissource.vissource import EAMVisSource

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
source = EAMVisSource()
ConnFile='/home/local/KHQ/abhi.yenpure/repositories/eam/EAMApp/data/TEMPEST_ne30pg2.scrip.renamed.nc'
DataFile='/data/eam/202311/v2_F2010_nc00_inst_macmic01.eam.h0.2010-12-25-00000.nc'
source.Update(datafile=DataFile, connfile=ConnFile)
vars2D   = source.vars2D
vars3Di  = source.vars3Di
vars3Dm  = source.vars3Dm
pviews   = source.views
hviews   = []

def update_views(**kwargs):
    try:
        for v in hviews:
            v.update()
    except Exception as e:
        print("Error occured : ", e)

ctrl.on_server_ready.add(ctrl.view_update)
ctrl.view_update = update_views

# -----------------------------------------------------------------------------
# GUI
# -----------------------------------------------------------------------------
state.trame__title = "ParaView eamdata"

DEFAULT_RESOLUTION = 6
def update_reset_resolution():
    state.resolution = DEFAULT_RESOLUTION

@state.change("mesh_color_array_idx")                         
def update_mesh_color_by_name(mesh_color_array_idx, **kwargs):
    print(mesh_color_array_idx)
    #ColorBy(representation, ("CELLS", mesh_color_array_idx))
    ctrl.view_update()                                        

@state.change("variable3Dm")                         
def FetchVaribles(variable3Dm, **kwargs):
    print(variable3Dm)

@state.change("time_stamp")                         
def FetchTimeStamp(time_stamp, **kwargs):
    print(time_stamp)

with SinglePageWithDrawerLayout(server) as layout:
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
        with vuetify.VBtn(icon=True, click=update_reset_resolution):
            vuetify.VIcon("mdi-undo-variant")

    items = []
    with layout.drawer:                                    
        with vuetify.VContainer(
            fluid=True,
            style="max-height: 400px",
            classes="overflow-y-auto",
        ):
            with vuetify.VItemGroup(
                label='3D Variables',
                v_model=('variable3Dm', False),
                dense=True
            ):
                for item in vars3Dm:
                    vuetify.VCheckbox(
                        style="max-height: 20px",
                        label=item, 
                        dense=True,
                    )
        vuetify.VSelect(                         
            # Color By                           
            style="max-height: 400px",
            label="Color by",                    
            v_model=("mesh_color_array_idx", 'XXX'), 
            items=("array_list", vars3Dm),
            hide_details=True,                   
            dense=True,                          
            outlined=True,                       
            classes="pt-1",                      
        )
        vuetify.VSlider(
            label='Time',   
            v_model=("time_stamp", -1), 
        ) 
    with layout.content:
        with vuetify.VContainer(
            fluid=True,
            classes="pa-0 fill-height",
        ):
            with vuetify.VRow(dense=True, style="height: 50%;"):
                with vuetify.VCol():
                    hviews.append(paraview.VtkRemoteView(pviews[0], ref="view1"))
                with vuetify.VCol():
                    hviews.append(paraview.VtkRemoteView(pviews[1], ref="view2"))
            with vuetify.VRow(dense=True, style="height: 50%;"):
                with vuetify.VCol():
                    hviews.append(paraview.VtkRemoteView(pviews[2], ref="view3"))
                with vuetify.VCol():
                    hviews.append(paraview.VtkRemoteView(pviews[3], ref="view4"))

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    server.start()
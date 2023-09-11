import paraview.web.venv  # Available in PV 5.10

from trame.app import get_server
from trame.widgets import vuetify, paraview
from trame.ui.vuetify import SinglePageWithDrawerLayout

from paraview import simple
from paraview.simple import OutputPort
from paraview.simple import Show
from paraview.simple import Render 
from paraview.simple import LoadPlugin 
from paraview.simple import ColorBy 
from paraview.simple import GetColorTransferFunction 

from paraview import servermanager

import numpy as np
# -----------------------------------------------------------------------------
# trame setup
# -----------------------------------------------------------------------------

server = get_server()
state, ctrl = server.state, server.controller

# -----------------------------------------------------------------------------
# ParaView code
# -----------------------------------------------------------------------------

DEFAULT_RESOLUTION = 6

LoadPlugin("/home/local/KHQ/abhi.yenpure/repositories/eam/EAMApp/eam_reader.py", ns=globals())
LoadPlugin("/home/local/KHQ/abhi.yenpure/repositories/eam/EAMApp/eam_filters.py", ns=globals())

# create a new 'EAM Data Reader'
eamdata = EAMDataReader(registrationName='eamdata', 
        ConnectivityFile='/home/local/KHQ/abhi.yenpure/repositories/eam/scripts/TEMPEST_ne30pg2.scrip.renamed.nc',
        DataFile='/home/local/KHQ/abhi.yenpure/repositories/eam/scripts/aerosol_F2010.eam.h0.2014-12.nc')
vars2D  = list(np.asarray(eamdata.GetProperty('a2DVariablesInfo'))[::2])
vars3Dm = list(np.asarray(eamdata.GetProperty('a3DMiddleLayerVariablesInfo'))[::2])
vars3Di = list(np.asarray(eamdata.GetProperty('a3DInterfaceLayerVariablesInfo'))[::2])
eamdata.a3DMiddleLayerVariables = vars3Dm

print(dir(eamdata))
print(dir(eamdata.SMProxy))

timestamps = eamdata.GetProperty('TimestepValues')
print('Timesteps : ', timestamps)

representation  = Show(OutputPort(eamdata, 1))
ColorBy(representation, ("CELLS", "AREL"))

# get color transfer function/color map for 'AREI'
aREILUT = GetColorTransferFunction('AREI')
# Apply a preset using its name. Note this may not work as expected when presets have duplicate names.
aREILUT.ApplyPreset('Viridis (matplotlib)', True)

view            = Render()
eamdata.UpdatePipeline()

def update_reset_resolution():
    state.resolution = DEFAULT_RESOLUTION

# -----------------------------------------------------------------------------
# GUI
# -----------------------------------------------------------------------------
state.trame__title = "ParaView eamdata"

@state.change("mesh_color_array_idx")                         
def update_mesh_color_by_name(mesh_color_array_idx, **kwargs):
    print(mesh_color_array_idx)
    ColorBy(representation, ("CELLS", mesh_color_array_idx))
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
            v_model=("mesh_color_array_idx", vars3Dm[0]), 
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
            html_view = paraview.VtkRemoteView(view)
            ctrl.view_update = html_view.update
            ctrl.view_reset_camera = html_view.reset_camera

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    server.start()

import os

import numpy as np

from paraview import simple
from paraview.simple import LoadPlugin 
from paraview.simple import LoadState 
from paraview.simple import FindSource
from paraview.simple import FindViewOrCreate

# -----------------------------------------------------------------------------
# ParaView code
# -----------------------------------------------------------------------------

class EAMVisSource:
    def __init__(self):
        self.DataFile = None
        self.ConnFile = None
        self.views    = []
        self.vars2D   = []
        self.vars3Di  = []
        self.vars3Dm  = []

        file       = os.path.abspath(__file__)
        currdir    = os.path.dirname(file)
        root       = os.path.dirname(currdir)
        print(root)
        try:
            plugdir    = os.path.join(root, 'plugins')
            plugins         = os.listdir(path=plugdir)
            for plugin in plugins:
                plugpath = os.path.abspath(os.path.join(plugdir, plugin))
                LoadPlugin(plugpath, ns=globals())
        except Exception as e:
            print("Error loading plugin :", e)
        try:
            statedir   = os.path.join(root, 'state')
            states     = os.listdir(path=statedir)
            for state in states:
                statepath = os.path.abspath(os.path.join(statedir, state))
                LoadState(statepath)
        except Exception as e:
            print("Error loading state :", e)

    def Update(self, datafile, connfile):
        data = FindSource('Data')
        data.DataFile = datafile
        data.ConnectivityFile = connfile
        data.a2DVariables = ['CLDLOW', 'CLDTOT']
        data.a3DMiddleLayerVariables = ['cnd01_ALST_ACTDIAG01', 'cnd01_AST_ACTDIAG01', 'cnd01_CDMC_ACTDIAG01', 'cnd01_CDNC_ACTDIAG01', 'cnd01_RAL_ACTDIAG01', 'cnd01_REL_ACTDIAG01']
        data.UpdatePipeline()
        
        self.vars2D  = list(np.asarray(data.GetProperty('a2DVariablesInfo'))[::2])
        self.vars3Dm = list(np.asarray(data.GetProperty('a3DMiddleLayerVariablesInfo'))[::2])
        self.vars3Di = list(np.asarray(data.GetProperty('a3DInterfaceLayerVariablesInfo'))[::2])

        renderView1 = FindViewOrCreate('RenderView1', viewtype='RenderView')
        renderView2 = FindViewOrCreate('RenderView2', viewtype='RenderView')
        renderView3 = FindViewOrCreate('RenderView3', viewtype='RenderView')
        renderView4 = FindViewOrCreate('RenderView4', viewtype='RenderView')
        renderView5 = FindViewOrCreate('RenderView5', viewtype='RenderView')

        self.views  = [] 
        self.views.append(renderView1)
        self.views.append(renderView2)
        self.views.append(renderView3)
        self.views.append(renderView4)
        self.views.append(renderView5)

if __name__ == "__main__":
    e = EAMVisSource()

'''
LoadPlugin("/home/local/KHQ/abhi.yenpure/repositories/eam/EAMApp/eam_reader.py", ns=globals())
LoadPlugin("/home/local/KHQ/abhi.yenpure/repositories/eam/EAMApp/eam_filters.py", ns=globals())
LoadPlugin("/home/local/KHQ/abhi.yenpure/repositories/eam/EAMApp/eam_projection.py", ns=globals())
LoadPlugin("/home/local/KHQ/abhi.yenpure/repositories/eam/EAMApp/eam_linesrc.py", ns=globals())

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

view = Render()
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
'''

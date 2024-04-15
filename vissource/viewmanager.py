from trame.widgets import (
    vuetify, 
    paraview as pvWidgets
)

import math
import os

from paraview.simple import (
    Text,
    Show,
    ImportPresets,
    CreateRenderView,
    GetScalarBar,
    ColorBy,
    GetColorTransferFunction,
    SetActiveView
)

def GetRenderView(geom, var, num, colormap, globe):
    #rview = FindViewOrCreate(f'rv{num}', 'RenderView')
    rview  = CreateRenderView()#f"rv{num}")#, 'RenderView')
    rep    = Show(geom, rview)
    ColorBy(rep, ("CELLS", var))
    coltrfunc = GetColorTransferFunction(var)
    coltrfunc.ApplyPreset('oslo', True)
    rep.SetScalarBarVisibility(rview, True)
    rview.CameraParallelProjection = 1
    rview.ResetCamera(True)
    LUTColorBar = GetScalarBar(coltrfunc, rview)
    LUTColorBar.AutoOrient = 0
    LUTColorBar.Orientation = 'Horizontal'
    LUTColorBar.WindowLocation = 'Lower Right Corner'
    LUTColorBar.Title = ''

    #repG = Show(globe, rview)
    #repG.SetRepresentationType('Wireframe')
    #repG.RenderLinesAsTubes = 1
    #repG.LineWidth = 2.0
    #ColorBy(repG, None)

    text = Text(registrationName=f'Text{num}')
    text.Text = var
    textrep = Show(text, rview, 'TextSourceRepresentation')
    textrep.Bold = 1      
    textrep.FontSize = 22 
    textrep.Italic = 1    
    textrep.Shadow = 1 

    return rview

class ViewManager():
    def __init__(self, source, server, state):
        self.rows       = 1
        self.columns    = 1
        self.server     = server
        self.source     = source
        self.state      = state
        self.widgets    = []
        self.colors     = []
        file       = os.path.abspath(__file__)
        currdir    = os.path.dirname(file)
        root       = os.path.dirname(currdir)
        try:
            presdir    = os.path.join(root, 'presets')
            presets    = os.listdir(path=presdir)
            for preset in presets:
                prespath = os.path.abspath(os.path.join(presdir, preset))
                if os.path.isfile(prespath):
                    name = preset.split('_')[0]
                    ImportPresets(prespath)
                    self.colors.append(name)
        except Exception as e:
            print("Error loading presets :", e)

    def SetCols(self, cols):
        if cols == self.columns:
             return
        self.columns = cols
            
    def ResetCamera(self, **kwargs):
         for widget in self.widgets:
              widget.reset_camera()
         pass

    def UpdateCamera(self, **kwargs):
         for widget in self.widgets:
              widget.update()

    def UpdateView(self):
        self.widgets.clear()

        self.source.UpdateLev(self.state.vlev)
        self.source.UpdateProjection(self.state.projection)

        view2D   = self.source.views['2DProj']
        viewG    = self.source.views['GProj']
        vars2D   = self.source.vars.get('2D', None)
        vars3Dm  = self.source.vars.get('3Dm', None)

        numViews = len(vars2D) + len(vars3Dm)
        if numViews == 0:
            return
        self.rows = math.ceil(numViews / self.columns)

        counter = 0
        self.rViews = []
        colormap = "Rainbow"
        for var in vars2D:
                rview = GetRenderView(view2D, var, counter, colormap, viewG) 
                self.rViews.append(rview)
                counter += 1
        for var in vars3Dm:
                rview = GetRenderView(view2D, var, counter, colormap, viewG) 
                self.rViews.append(rview)
                counter += 1

        sWidgets = []
        for view in self.rViews:
            widget = pvWidgets.VtkRemoteView(view,
                                interactive_ratio=1,
                                classes="pa-0 drag_ignore",
                                style="width: 100%; height: 100%;",
                                trame_server=self.server,
                                )
            self.widgets.append(widget)
            sWidgets.append(widget.ref_name)
        self.state.views = sWidgets

    def UpdateColor(self, color, logclut, index):
        var     = self.state.ccardsentry[index]
        rview   = self.rViews[index]
        #SetActiveView(rview)
        coltrfunc = GetColorTransferFunction(var)
        coltrfunc.ApplyPreset(color, True)
        if logclut:
            coltrfunc.MapControlPointsToLogSpace()
        else:
            coltrfunc.MapControlPointsToLinearSpace()
        self.ResetCamera()
from trame.widgets import (
    grid,
    vuetify, 
    paraview as pvWidgets
)

import math

from paraview.simple import (
    Show,
    CreateRenderView,
    FindViewOrCreate,
    ColorBy,
    GetColorTransferFunction
)

def GetRenderView(geom, var, num, colormap, globe):
    rview = CreateRenderView(f'rv{num}')
    rep   = Show(geom, rview)
    rview.ResetCamera(True)
    ColorBy(rep, ("CELLS", var))
    coltrfunc = GetColorTransferFunction(var)
    coltrfunc.ApplyPreset(colormap, True)

    repG = Show(globe, rview)
    repG.SetRepresentationType('Wireframe')
    repG.RenderLinesAsTubes = 1
    repG.LineWidth = 2.0
    ColorBy(repG, None)
    '''
    text = Text(registrationName=f'Text{num}')
    text.Text = var
    textrep = Show(text, rview, 'TextSourceRepresentation')
    '''
    return rview

class ViewManager():
    def __init__(self, source, server, state):
        self.rows       = 1
        self.columns    = 1
        self.server     = server
        self.source     = source
        self.state      = state
        self.widgets    = []

    def SetCols(self, cols):
        if cols == self.columns:
             return
        self.columns = cols
            
    def ResetCamera(self, **kwargs):
         #for widget in self.widgets:
         #     widget.reset_camera()
         pass

    def UpdateCamera(self, **kwargs):
         for widget in self.widgets:
              widget.update()

    def UpdateView(self):
        self.widgets.clear()

        self.source.UpdateLev(self.state.vlev)
        self.source.UpdateProjection(self.state.projection)

        view2D   = self.source.views['2DProj']
        view3Dm  = self.source.views['3DmProj']
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
                rview = GetRenderView(view3Dm, var, counter, colormap, viewG) 
                self.rViews.append(rview)
                counter += 1

        sWidgets = []
        for view in self.rViews:
            widget = pvWidgets.VtkLocalView(view,
                                interactive_quality=100,
                                classes="pa-0 drag_ignore",
                                style="width: 100%; height: 100%;",
                                trame_server=self.server,
                                )
            self.widgets.append(widget)
            sWidgets.append(widget.ref_name)
        self.state.views = sWidgets

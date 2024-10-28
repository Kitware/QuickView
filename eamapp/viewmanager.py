from trame.widgets import (
    vuetify, 
    paraview as pvWidgets
)

import math
import os
import numpy as np
from pyproj import Proj, Transformer

from vtkmodules.numpy_interface import dataset_adapter as dsa
from paraview.simple import (
    Delete,
    Text,
    Show,
    CreateRenderView,
    FindViewOrCreate,
    GetScalarBar,
    ColorBy,
    GetColorTransferFunction,
)

def ApplyProj(projection, point):
    if projection is None:
        return point
    else:
        new = projection.transform(point[0] - 180, point[1])
        return [new[0], new[1], 1.]

def GenerateAnnotations(long, lat, projection, center):
    texts = []
    interval = 30
    llon     = long[0]
    hlon     = long[1]
    llat     = lat[0]
    hlat     = lat[1]

    llon = math.floor(llon  / interval) * interval
    hlon = math.ceil(hlon / interval) * interval

    llat = math.floor(llat  / interval) * interval
    hlat = math.ceil(hlat / interval) * interval
   
    lonx = np.arange(llon, hlon + interval, interval)
    laty = np.arange(llat, hlat + interval, interval)

    print(lonx)
    from functools import partial

    proj = partial(ApplyProj, None)
    if projection != 'Cyl. Equidistant':
        latlon  = Proj(init="epsg:4326")
        if projection == 'Robinson':
            proj = Proj(proj="robin")
        elif projection == 'Mollweide':
            proj = Proj(proj="moll")
        xformer = Transformer.from_proj(latlon, proj)
        proj = partial(ApplyProj, xformer)

    for x in lonx:
        lon = x - center
        pos = lon 
        if lon > 180:
            pos = -180 + (lon % 180)
        elif lon < -180:
            pos = 180 - (abs(lon) % 180)
        txt = str(x)
        print(f" x : {x}, lon : {lon}, pos : {pos}, {lon % 180}")
        if pos == 180:
            continue
        text       = Text(registrationName=f"text{x}")
        text.Text = txt
        pos = proj([pos, hlat, 1.])
        texts.append((text, pos))
    for y in laty:
        text       = Text(registrationName=f"text{y}")
        text.Text  = str(y)
        pos = proj([hlon, y, 1.])
        pos[0] += pos[0] * 0.075
        texts.append((text, pos))

    return texts

def AddAnnotations(rview, annotations):
    for (text, pos) in annotations:
        display = Show(text, rview, 'TextSourceRepresentation')
        display.TextPropMode = 'Billboard 3D Text'
        display.BillboardPosition = pos
        display.Bold = 1
        display.FontSize = 12
        display.Italic = 1
        display.Shadow = 1
    pass

class ViewData():
    def __init__(self, color, uselog = False, rep = None, min = None, max = None):
        self.color  = color
        self.uselog = uselog
        self.rep    = rep
        self.min    = min
        self.max    = max 

def BuildColorInformationCache(state: map):
    vars    = state["ccardsentry"]
    colors  = state["varcolor"]
    logscl  = state["uselogscale"]
    varmin  = state["varmin"]
    varmax  = state["varmax"]    
    cache = {}
    for index, var in enumerate(vars):
        cache[var] = ViewData(colors[index], rep=None, uselog=logscl[index], min=varmin[index], max=varmax[index])
    return cache

def GetRenderView(index, views, var, average, num, colordata : ViewData):

    from timeit import default_timer as timer

    #rview = CreateRenderView(f'rv{index}')
    rview = CreateRenderView()

    rview.UseColorPaletteForBackground = 0
    rview.BackgroundColorMode = 'Gradient'

    data = views['2DProj']
    rep    = Show(data, rview)
    ColorBy(rep, ("CELLS", var))
    coltrfunc = GetColorTransferFunction(var)
    coltrfunc.ApplyPreset(colordata.color, True)
    rep.SetScalarBarVisibility(rview, True)
    rview.CameraParallelProjection = 1
    rview.ResetCamera(True)
    LUTColorBar = GetScalarBar(coltrfunc, rview)
    LUTColorBar.AutoOrient = 1
    #LUTColorBar.Orientation = 'Horizontal'
    LUTColorBar.WindowLocation = 'Lower Right Corner'
    LUTColorBar.Title = ''
    LUTColorBar.ScalarBarLength = 0.75
    coltrfunc.RescaleTransferFunction(float(colordata.min), float(colordata.max))
    colordata.rep = rep
    
    globe = views['GProj']
    #print("Globe : ", globe)
    repG = Show(globe, rview)
    #print("Representation : ", repG)
    ColorBy(repG, None)
    repG.SetRepresentationType('Wireframe')
    repG.RenderLinesAsTubes = 1
    repG.LineWidth = 1.0
    repG.AmbientColor = [0.67, 0.67, 0.67]
    repG.DiffuseColor = [0.67, 0.67, 0.67]
    
    annot = views['GLines']
    repAn = Show(annot, rview)
    repAn.SetRepresentationType('Wireframe')
    repAn.AmbientColor = [0.67, 0.67, 0.67]
    repAn.DiffuseColor = [0.67, 0.67, 0.67]
    repAn.Opacity = 0.4
    
    text = Text(registrationName=f'Text{num}')
    text.Text = var + "  Avg: %.2f" % average
    textrep = Show(text, rview, 'TextSourceRepresentation')
    textrep.Bold = 1    
    textrep.FontSize = 22 
    textrep.Italic = 1 
    textrep.Shadow = 1
    textrep.WindowLocation = 'Upper Center'
    
    return rview

from eamapp.pipeline import EAMVisSource

class ViewManager():
    def __init__(self, source : EAMVisSource, server, state):
        self.rows       = 1
        self.columns    = 1
        self.server     = server
        self.source     = source
        self.state      = state
        self.widgets    = []
        self.colors     = []
        self.cache      = {}
        self.rViews = []

    def SetCols(self, cols):
        if cols == self.columns:
            return
        self.columns = cols
            
    def ResetCamera(self, **kwargs):
        for widget in self.widgets:
            widget.reset_camera()

    def UpdateCamera(self, **kwargs):
        for widget in self.widgets:
            widget.update()

    def UpdateView(self, rep_change=False):
        self.widgets.clear()

        long = self.state.cliplong 
        lat  = self.state.cliplat
        print("Updating clip extents : ", long, lat)

        self.source.UpdateLev(self.state.vlev, self.state.vilev)
        
        self.source.ApplyClipping(long, lat)
        self.source.UpdateCenter(self.state.center)
        self.source.UpdateProjection(self.state.projection)
        self.source.UpdatePipeline()

        vars2D   = self.source.vars.get('2D', None)
        vars3Dm  = self.source.vars.get('3Dm', None)
        vars3Di  = self.source.vars.get('3Di', None)

        numViews = len(vars2D) + len(vars3Dm) + len(vars3Di)
        if numViews == 0:
            return
        self.rows = math.ceil(numViews / self.columns)

        counter = 0
        #for rview in self.rViews:
        #    Delete(rview)
        del self.rViews[:]
        annotations = GenerateAnnotations(self.state.cliplong, self.state.cliplat, self.state.projection, self.source.center)

        data = self.source.views['2DProj']
        import paraview.servermanager as sm
        vtkdata     = sm.Fetch(data)
        area        = np.array(vtkdata.GetCellData().GetArray("area"))

        for index, var in enumerate(vars2D + vars3Dm + vars3Di):
                vtkvar   = vtkdata.GetCellData().GetArray(var)
                range    = vtkvar.GetRange()
                vardata  = np.array(vtkvar)
                average  = np.sum(area * vardata) / np.sum(area)

                colordata : ViewData = self.cache.get(var, ViewData(self.state.varcolor[index]))
                colordata.min = range[0]
                colordata.max = range[1]
                rview = GetRenderView(index, self.source.views, var, average, counter, colordata) 
                
                AddAnnotations(rview, annotations)
                self.rViews.append(rview)
                self.cache[var] = colordata
                self.state.varmin[index] = colordata.min
                self.state.varmax[index] = colordata.max
                counter += 1

        wdt = 4
        hgt = 3

        del self.state.views[:]
        del self.state.layout[:]
        del self.widgets[:]

        sWidgets = []
        layout   = []
        for idx, view in enumerate(self.rViews):
            x = int(idx % 3) * wdt
            y = int(idx / 3) * hgt
            widget = pvWidgets.VtkRemoteView(view,
                                interactive_ratio=1,
                                classes="pa-0 drag_ignore",
                                style="width: 100%; height: 100%;",
                                trame_server=self.server,
                                )
            self.widgets.append(widget)
            sWidgets.append(widget.ref_name)
            layout.append({"x" : x, "y" : y, "w" : wdt, "h" : hgt, "i" : idx})
        self.state.views = sWidgets
        self.state.layout = layout

    def UpdateColor(self, index, type, value):
        var     = self.state.ccardsentry[index]
        coltrfunc   = GetColorTransferFunction(var)

        colordata : ViewData = self.cache[var]
        if type.lower() == 'color':
            colordata.color = value
            coltrfunc.ApplyPreset(colordata.color, True)
        elif type.lower() == 'log':
            colordata.uselog = value
            if colordata.uselog:
                coltrfunc.MapControlPointsToLogSpace()
                coltrfunc.UseLogScale = 1
            else:
                coltrfunc.MapControlPointsToLinearSpace()
                coltrfunc.UseLogScale = 0
        elif type.lower() == 'inv':
            coltrfunc.InvertTransferFunction()
        self.UpdateCamera()
    
    def UpdateColorProps(self, index, min, max):
        var     = self.state.ccardsentry[index]
        coltrfunc   = GetColorTransferFunction(var)
        coltrfunc.RescaleTransferFunction(float(min), float(max))
        self.UpdateCamera()

    def ResetColorProps(self, index):
        var     = self.state.ccardsentry[index]
        colordata : ViewData = self.cache[var]
        self.state.varmin[index] = colordata.min
        self.state.dirty("varmin")
        self.state.varmax[index] = colordata.max
        self.state.dirty("varmax")
        colordata.rep.RescaleTransferFunctionToDataRange(False, True)
        self.UpdateCamera() 

    def ZoomIn(self, index):
        rview   = self.rViews[index]
        rview.CameraParallelScale *= 0.95
        self.UpdateCamera()

    def ZoomOut(self, index):
        rview   = self.rViews[index]
        rview.CameraParallelScale *= 1.05 
        self.UpdateCamera()

    def Move(self, vindex, dir, factor):
        extents = self.source.moveextents
        move = (
            (extents[1] - extents[0]) * 0.05,
            (extents[3] - extents[2]) * 0.05,
            (extents[5] - extents[4]) * 0.05
        )

        rview   = self.rViews[vindex]
        pos = rview.CameraPosition
        foc = rview.CameraFocalPoint
        pos[dir] += move[dir] if factor > 0 else -move[dir]
        foc[dir] += move[dir] if factor > 0 else -move[dir]
        rview.CameraPosition = pos
        rview.CameraFocalPoint = foc
        self.UpdateCamera()

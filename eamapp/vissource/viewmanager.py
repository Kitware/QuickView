from trame.widgets import (
    vuetify, 
    paraview as pvWidgets
)

import math
import os
import numpy as np
from pyproj import Proj, Transformer

from paraview.simple import (
    Text,
    Show,
    ImportPresets,
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

def GenerateAnnotations(long, lat, projection):
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
        text       = Text(registrationName=f"text{x}")
        text.Text  = str(x)
        pos = proj([x, hlat, 1.])
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
    def __init__(self, color, uselog = False):
        self.color  = color
        self.uselog = uselog
        self.rep    = None
        self.min    = None
        self.max    = None 

def GetRenderView(index, views, var, num, colordata : ViewData):
    data = views['2DProj']

    from timeit import default_timer as timer
    
    from paraview.simple import servermanager as sm
    start = timer()
    vtkdata = sm.Fetch(data)
    range = vtkdata.GetCellData().GetArray(var).GetRange() 
    end = timer()
    print("Time to get range: ", end - start)

    start = timer()
    rview = FindViewOrCreate(f'rv{index}', 'RenderView')
    end = timer()

    print("Time to find/create render views : ", end - start)

    rview.UseColorPaletteForBackground = 0
    rview.BackgroundColorMode = 'Gradient'

    start = timer()
    #rview  = CreateRenderView()#f"rv{num}")#, 'RenderView')
    rep    = Show(data, rview)
    ColorBy(rep, ("CELLS", var))
    coltrfunc = GetColorTransferFunction(var)
    coltrfunc.ApplyPreset(colordata.color, True)
    rep.SetScalarBarVisibility(rview, True)
    rview.CameraParallelProjection = 1
    rview.CameraParallelScale = 125
    rview.ResetCamera(True)
    LUTColorBar = GetScalarBar(coltrfunc, rview)
    LUTColorBar.AutoOrient = 0
    LUTColorBar.Orientation = 'Horizontal'
    LUTColorBar.WindowLocation = 'Lower Right Corner'
    LUTColorBar.Title = ''
    rep.RescaleTransferFunctionToDataRange(False, True)

    colordata.rep = rep
    colordata.min = range[0]
    colordata.max = range[1]

    globe = views['GProj']
    repG = Show(globe, rview)
    ColorBy(repG, None)
    repG.SetRepresentationType('Wireframe')
    repG.RenderLinesAsTubes = 1
    repG.LineWidth = 1.0
    repG.AmbientColor = [0.67, 0.67, 0.67]
    repG.DiffuseColor = [0.67, 0.67, 0.67]

    annot = views['GLines']
    repAn = Show(annot, rview)
    repAn.SetRepresentationType('Wireframe')
    #repAn.RenderLinesAsTubes = 1
    #repG.LineWidth = 0.5
    repAn.AmbientColor = [0.67, 0.67, 0.67]
    repAn.DiffuseColor = [0.67, 0.67, 0.67]

    text = Text(registrationName=f'Text{num}')
    text.Text = var
    textrep = Show(text, rview, 'TextSourceRepresentation')
    textrep.Bold = 1      
    textrep.FontSize = 22 
    textrep.Italic = 1    
    textrep.Shadow = 1 
    end = timer()
    print("Time to setup views : ", end - start)

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
        self.cache      = {}
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

        long = [self.state.extents[0], self.state.extents[1]]
        lat  = [self.state.extents[2], self.state.extents[3]]
        self.source.UpdateLev(self.state.vlev, self.state.vilev)
        if self.state.clipping:
            long = self.state.cliplong 
            lat  = self.state.cliplat
        self.source.ApplyClipping(long, lat)

        self.source.UpdateProjection(self.state.projection)

        vars2D   = self.source.vars.get('2D', None)
        vars3Dm  = self.source.vars.get('3Dm', None)
        vars3Di  = self.source.vars.get('3Di', None)

        numViews = len(vars2D) + len(vars3Dm) + len(vars3Di)
        if numViews == 0:
            return
        self.rows = math.ceil(numViews / self.columns)

        counter = 0
        self.rViews = []
        annotations = GenerateAnnotations(self.state.cliplong, self.state.cliplat, self.state.projection)

        data = self.source.views['2DProj']

        for index, var in enumerate(vars2D + vars3Dm + vars3Di):
                colordata : ViewData = self.cache.get(var, ViewData(self.state.varcolor[index]))
                rview = GetRenderView(index, self.source.views, var, counter, colordata) 
                AddAnnotations(rview, annotations)
                self.rViews.append(rview)
                self.cache[var] = colordata
                self.state.varmin[index] = colordata.min
                self.state.varmax[index] = colordata.max
                counter += 1

        wdt = 4
        hgt = 3

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
        self.state.varmax[index] = colordata.max
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
        rview   = self.rViews[vindex]
        pos = rview.CameraPosition
        foc = rview.CameraFocalPoint
        pos[dir] += 10 if factor > 0 else -10
        foc[dir] += 10 if factor > 0 else -10
        rview.CameraPosition = pos
        rview.CameraFocalPoint = foc
        self.UpdateCamera()
from trame.widgets import vuetify, paraview as pvWidgets

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
    GetScalarBar,
    ColorBy,
    GetColorTransferFunction,
)

import paraview.servermanager as sm


def ApplyProj(projection, point):
    if projection is None:
        return point
    else:
        new = projection.transform(point[0] - 180, point[1])
        return [new[0], new[1], 1.0]


def GenerateAnnotations(long, lat, projection, center):
    texts = []
    interval = 30
    llon = long[0]
    hlon = long[1]
    llat = lat[0]
    hlat = lat[1]

    llon = math.floor(llon / interval) * interval
    hlon = math.ceil(hlon / interval) * interval

    llat = math.floor(llat / interval) * interval
    hlat = math.ceil(hlat / interval) * interval

    lonx = np.arange(llon, hlon + interval, interval)
    laty = np.arange(llat, hlat + interval, interval)

    from functools import partial

    proj = partial(ApplyProj, None)
    if projection != "Cyl. Equidistant":
        latlon = Proj(init="epsg:4326")
        if projection == "Robinson":
            proj = Proj(proj="robin")
        elif projection == "Mollweide":
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
        if pos == 180:
            continue
        text = Text(registrationName=f"text{x}")
        text.Text = txt
        pos = proj([pos, hlat, 1.0])
        texts.append((text, pos))
    for y in laty:
        text = Text(registrationName=f"text{y}")
        text.Text = str(y)
        pos = proj([hlon, y, 1.0])
        pos[0] += pos[0] * 0.075
        texts.append((text, pos))

    return texts


def AddAnnotations(rview, annotations):
    for text, pos in annotations:
        display = Show(text, rview, "TextSourceRepresentation")
        display.TextPropMode = "Billboard 3D Text"
        display.BillboardPosition = pos
        display.Bold = 1
        display.FontSize = 12
        display.Italic = 1
        display.Shadow = 1
    pass


class ViewData:
    def __init__(
        self,
        view=None,
        rep=None,
        avg=None,
        color=None,
        uselog=False,
        min=None,
        max=None,
    ):
        self.view = view
        self.rep = rep
        self.avg = avg
        self.color = color
        self.uselog = uselog
        self.min = min
        self.max = max


def BuildColorInformationCache(state: map):
    vars = state["ccardsentry"]
    colors = state["varcolor"]
    logscl = state["uselogscale"]
    varmin = state["varmin"]
    varmax = state["varmax"]
    cache = {}
    for index, var in enumerate(vars):
        cache[var] = ViewData(
            colors[index],
            rep=None,
            uselog=logscl[index],
            min=varmin[index],
            max=varmax[index],
        )
    return cache


def UpdateRenderView(index, var, viewdata: ViewData, sources, annotations):

    from timeit import default_timer as timer

    # rview = CreateRenderView(f'rv{index}')

    rview = viewdata.view
    print("Updating View with data : ", viewdata)

    data = sources["2DProj"]
    rep = Show(data, rview)
    viewdata.rep = rep
    ColorBy(rep, ("CELLS", var))
    coltrfunc = GetColorTransferFunction(var)
    coltrfunc.ApplyPreset(viewdata.color, True)
    rep.SetScalarBarVisibility(rview, True)
    LUTColorBar = GetScalarBar(coltrfunc, rview)
    LUTColorBar.AutoOrient = 1
    # LUTColorBar.Orientation = 'Horizontal'
    LUTColorBar.WindowLocation = "Lower Right Corner"
    LUTColorBar.Title = ""
    LUTColorBar.ScalarBarLength = 0.75
    # coltrfunc.RescaleTransferFunction(float(viewdata.min), float(viewdata.max))

    globe = sources["GProj"]
    repG = Show(globe, rview)
    ColorBy(repG, None)
    repG.SetRepresentationType("Wireframe")
    repG.RenderLinesAsTubes = 1
    repG.LineWidth = 1.0
    repG.AmbientColor = [0.67, 0.67, 0.67]
    repG.DiffuseColor = [0.67, 0.67, 0.67]

    annot = sources["GLines"]
    repAn = Show(annot, rview)
    repAn.SetRepresentationType("Wireframe")
    repAn.AmbientColor = [0.67, 0.67, 0.67]
    repAn.DiffuseColor = [0.67, 0.67, 0.67]
    repAn.Opacity = 0.4

    text = Text(registrationName=f"Text{index}")
    text.Text = var + "  Avg: %.2f" % viewdata.avg
    textrep = Show(text, rview, "TextSourceRepresentation")
    textrep.Bold = 1
    textrep.FontSize = 22
    textrep.Italic = 1
    textrep.Shadow = 1
    textrep.WindowLocation = "Upper Center"

    AddAnnotations(rview, annotations)

    rview.CameraParallelProjection = 1
    rview.ResetCamera(True)


from eamapp.pipeline import EAMVisSource
from trame.decorators import TrameApp, trigger, change


@TrameApp()
class ViewManager:
    def __init__(self, source: EAMVisSource, server, state):
        self.server = server
        self.source = source
        self.state = state
        self.widgets = []
        self.colors = []
        self.annotations = []
        self.cache = {}
        self.to_delete = []
        self.rep_change = False

    def ResetCamera(self, **kwargs):
        for widget in self.widgets:
            widget.reset_camera()

    def UpdateCamera(self, **kwargs):
        for widget in self.widgets:
            widget.update()

    @trigger("view_gc")
    def DeleteRenderView(self, ref_name):
        view_to_delete = None
        view_id = self.state[f"{ref_name}Id"]
        for view in self.to_delete:
            if view.GetGlobalIDAsString() == view_id:
                view_to_delete = view
        if view_to_delete is not None:
            self.to_delete = [v for v in self.to_delete if v != view_to_delete]
            Delete(view_to_delete)

    # All the variables that deem previous renders outdated need to be updated
    @change("cliplon", "cliplat", "vlev", "vilev", "conter", "projection")
    def repchange(self, **kwargs):
        self.rep_change = True

    @change("tstamp")
    def timechange(self, **kwargs):
        self.rep_change = True

    def UpdateView(self):
        self.widgets.clear()
        state = self.state
        source = self.source

        long = state.cliplong
        lat = state.cliplat

        source.UpdateLev(self.state.vlev, self.state.vilev)
        source.ApplyClipping(long, lat)
        source.UpdateCenter(self.state.center)
        source.UpdateProjection(self.state.projection)
        source.UpdatePipeline()

        vars2D = source.vars.get("2D", None)
        vars3Dm = source.vars.get("3Dm", None)
        vars3Di = source.vars.get("3Di", None)

        numViews = len(vars2D) + len(vars3Dm) + len(vars3Di)
        if numViews == 0:
            return

        to_render = vars2D + vars3Dm + vars3Di
        rendered = self.cache.keys()
        to_delete = set(rendered) - set(to_render)
        print("View to delete : ", to_delete)
        # Move old variables so they their proxies can be deleted
        self.to_delete.extend([self.cache[x].view for x in to_delete])

        # Get area variable to calculate weighted average
        data = self.source.views["2DProj"]
        vtkdata = sm.Fetch(data)
        area = np.array(vtkdata.GetCellData().GetArray("area"))

        self.annotations = GenerateAnnotations(
            state.cliplong,
            state.cliplat,
            state.projection,
            source.center,
        )

        del self.state.views[:]
        del self.state.layout[:]
        del self.widgets[:]
        sWidgets = []
        layout = []
        wdt = 4
        hgt = 3

        for index, var in enumerate(to_render):
            x = int(index % 3) * wdt
            y = int(index / 3) * hgt
            view = None

            viewdata: ViewData = self.cache.get(var, None)
            if viewdata is not None:
                view = viewdata.view
                UpdateRenderView(
                    index, var, viewdata, self.source.views, self.annotations
                )
                state.varmin[index] = viewdata.min
                state.varmax[index] = viewdata.max
            else:
                viewdata = ViewData()

                view = CreateRenderView()
                view.UseColorPaletteForBackground = 0
                view.BackgroundColorMode = "Gradient"
                viewdata.view = view

                vtkvar = vtkdata.GetCellData().GetArray(var)
                range = vtkvar.GetRange()
                vardata = np.array(vtkvar)
                average = np.sum(area * vardata) / np.sum(area)
                print(f"Average for {var} : {average}")

                viewdata.avg = average
                viewdata.color = self.state.varcolor[index]
                viewdata.min = range[0]
                viewdata.max = range[1]

                UpdateRenderView(
                    index, var, viewdata, self.source.views, self.annotations
                )

                state.varmin[index] = viewdata.min
                state.varmax[index] = viewdata.max

                self.cache[var] = viewdata

            print(var, view)
            widget = pvWidgets.VtkRemoteView(
                view,
                interactive_ratio=1,
                classes="pa-0 drag_ignore",
                style="width: 100%; height: 100%;",
                trame_server=self.server,
            )
            print(widget)
            self.widgets.append(widget)
            sWidgets.append(widget.ref_name)
            layout.append({"x": x, "y": y, "w": wdt, "h": hgt, "i": index})

        for var in to_delete:
            self.cache.pop(var)

        self.state.views = sWidgets
        self.state.layout = layout

    def UpdateColor(self, index, type, value):
        var = self.state.ccardsentry[index]
        coltrfunc = GetColorTransferFunction(var)

        viewdata: ViewData = self.cache[var]
        if type.lower() == "color":
            viewdata.color = value
            coltrfunc.ApplyPreset(viewdata.color, True)
        elif type.lower() == "log":
            viewdata.uselog = value
            if viewdata.uselog:
                coltrfunc.MapControlPointsToLogSpace()
                coltrfunc.UseLogScale = 1
            else:
                coltrfunc.MapControlPointsToLinearSpace()
                coltrfunc.UseLogScale = 0
        elif type.lower() == "inv":
            coltrfunc.InvertTransferFunction()
        self.UpdateCamera()

    def UpdateColorProps(self, index, min, max):
        var = self.state.ccardsentry[index]
        coltrfunc = GetColorTransferFunction(var)
        coltrfunc.RescaleTransferFunction(float(min), float(max))
        self.UpdateCamera()

    def ResetColorProps(self, index):
        var = self.state.ccardsentry[index]
        colordata: ViewData = self.cache[var]
        self.state.varmin[index] = colordata.min
        self.state.dirty("varmin")
        self.state.varmax[index] = colordata.max
        self.state.dirty("varmax")
        colordata.rep.RescaleTransferFunctionToDataRange(False, True)
        self.UpdateCamera()

    def ZoomIn(self, index):
        rview = self.rViews[index]
        rview.CameraParallelScale *= 0.95
        self.UpdateCamera()

    def ZoomOut(self, index):
        rview = self.rViews[index]
        rview.CameraParallelScale *= 1.05
        self.UpdateCamera()

    def Move(self, vindex, dir, factor):
        extents = self.source.moveextents
        move = (
            (extents[1] - extents[0]) * 0.05,
            (extents[3] - extents[2]) * 0.05,
            (extents[5] - extents[4]) * 0.05,
        )

        rview = self.rViews[vindex]
        pos = rview.CameraPosition
        foc = rview.CameraFocalPoint
        pos[dir] += move[dir] if factor > 0 else -move[dir]
        foc[dir] += move[dir] if factor > 0 else -move[dir]
        rview.CameraPosition = pos
        rview.CameraFocalPoint = foc
        self.UpdateCamera()

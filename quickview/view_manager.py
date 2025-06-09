import math
import numpy as np
import paraview.servermanager as sm

from trame.widgets import paraview as pvWidgets
from trame.decorators import TrameApp, trigger, change
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
    AddCameraLink,
    Render,
    ResetCamera,
)

from quickview.pipeline import EAMVisSource
from quickview.utilities import EventType


def apply_projection(projection, point):
    if projection is None:
        return point
    else:
        new = projection.transform(point[0] - 180, point[1])
        return [new[0], new[1], 1.0]


def generate_annotations(long, lat, projection, center):
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

    proj = partial(apply_projection, None)
    if projection != "Cyl. Equidistant":
        latlon = Proj(init="epsg:4326")
        if projection == "Robinson":
            proj = Proj(proj="robin")
        elif projection == "Mollweide":
            proj = Proj(proj="moll")
        xformer = Transformer.from_proj(latlon, proj)
        proj = partial(apply_projection, xformer)

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


class ViewData:
    def __init__(
        self,
        view=None,
        index=None,
        data_rep=None,
        var_text=None,
        var_info=None,
        avg=None,
        color=None,
        uselog=False,
        inv=False,
        min=None,
        max=None,
    ):
        self.view = view
        self.data_rep = data_rep
        self.var_text = var_text
        self.var_info = var_info
        self.avg = avg
        self.color = color
        self.uselog = uselog
        self.inv = inv
        self.min = min
        self.max = max
        self.index = index


def build_color_information(state: map):
    vars = state["variables"]
    colors = state["varcolor"]
    logscl = state["uselogscale"]
    # invert = state["invert"]
    varmin = state["varmin"]
    varmax = state["varmax"]
    cache = {}
    for index, var in enumerate(vars):
        cache[var] = ViewData(
            view=None,
            color=colors[index],
            uselog=logscl[index],
            min=varmin[index],
            max=varmax[index],
        )
    return cache


@TrameApp()
class ViewManager:
    def __init__(self, source: EAMVisSource, server, state):
        self.server = server
        self.source = source
        self.state = state
        self.widgets = []
        self.colors = []
        self.cache = {}
        self.to_delete = []
        self.rep_change = False

    def step_update_existing_views(self):
        if len(self.cache) == 0:
            return

        data = sm.Fetch(self.source.views["2DProj"])
        area = np.array(data.GetCellData().GetArray("area"))

        for var, viewdata in self.cache.items():
            vardata = data.GetCellData().GetArray(var)
            varrange = vardata.GetRange()
            varavg = self.compute_average(vardata, area)
            viewdata.min = varrange[0]
            viewdata.max = varrange[1]
            viewdata.avg = varavg

            viewdata.data_rep.RescaleTransferFunctionToDataRange(False, True)
            (v_text, V_info) = self.get_var_info(var, viewdata.avg)
            if viewdata.var_text is not None:
                viewdata.var_text.Text = v_text
            if viewdata.var_info is not None:
                viewdata.var_info.Text = V_info
            self.update_state_color_properties(viewdata.index, viewdata)

    def update_existing_view(self, var, viewdata: ViewData):
        viewdata.data_rep.RescaleTransferFunctionToDataRange(False, True)
        (v_text, V_info) = self.get_var_info(var, viewdata.avg)
        if viewdata.var_text is not None:
            viewdata.var_text.Text = v_text
        if viewdata.var_info is not None:
            viewdata.var_info.Text = V_info
        rview = viewdata.view

        Render(rview)
        # ResetCamera(rview)

    def get_var_info(self, var, average):
        var_text = var + "\n(avg: " + "{:.2E}".format(average) + ")"
        info_text = None
        vars = self.source.vars.get("2D", None)
        t = self.state.tstamp
        if var in vars:
            info_text = f"t = {t}"
        vars = self.source.vars.get("3Dm", None)
        if var in vars:
            k = self.state.vlev
            info_text = f"k = {k}\nt = {t}"
        vars = self.source.vars.get("3Di", None)
        if var in vars:
            k = self.state.vilev
            info_text = f"k = {k}\nt = {t}"

        return (var_text, info_text)

    def update_new_view(self, var, viewdata: ViewData, sources):
        rview = viewdata.view

        # Update unique sources to all render views
        data = sources["2DProj"]
        rep = Show(data, rview)
        viewdata.data_rep = rep
        ColorBy(rep, ("CELLS", var))
        coltrfunc = GetColorTransferFunction(var)
        coltrfunc.ApplyPreset(viewdata.color, True)
        coltrfunc.NanOpacity = 0.0
        LUTColorBar = GetScalarBar(coltrfunc, rview)
        LUTColorBar.AutoOrient = 1
        LUTColorBar.WindowLocation = "Lower Right Corner"
        LUTColorBar.Title = ""
        LUTColorBar.ComponentTitle = ""
        LUTColorBar.ScalarBarLength = 0.75
        #LUTColorBar.NanOpacity = 0.0

        (v_text, V_info) = self.get_var_info(var, viewdata.avg)
        text = Text(registrationName=f"Text{var}")
        text.Text = v_text
        viewdata.var_text = text
        textrep = Show(text, rview, "TextSourceRepresentation")
        textrep.WindowLocation = "Upper Right Corner"
        textrep.FontFamily = "Times"

        info = Text(registrationName=f"Info{var}")
        info.Text = V_info
        viewdata.var_info = info
        textrep = Show(info, rview, "TextSourceRepresentation")
        textrep.WindowLocation = "Upper Left Corner"
        textrep.FontFamily = "Times"

        # Update common sources to all render views

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

        rep.SetScalarBarVisibility(rview, self.state.scalarbar)
        rview.CameraParallelProjection = 1

        Render(rview)
        # ResetCamera(rview)

    def update_state_color_properties(self, index, viewdata: ViewData):
        state = self.state
        state.varcolor[index] = viewdata.color
        state.varmin[index] = viewdata.min
        state.varmax[index] = viewdata.max
        state.uselogscale[index] = viewdata.uselog

    def reset_camera(self, **kwargs):
        for widget in self.widgets:
            widget.reset_camera()

    def reset_views(self, **kwargs):
        for widget in self.widgets:
            widget.update()

    def reset_specific_view(self, index):
        self.widgets[index].update()

    @trigger("resetview")
    async def reset_resize_specific_view(self, index, sizeinfo=None):
        if sizeinfo is not None:
            var = self.state.variables[index]
            viewdata: ViewData = self.cache[var]
            height = int(sizeinfo["height"])
            width = int(sizeinfo["width"])
            viewdata.view.ViewSize = (width, height)
            Render(viewdata.view)
        import asyncio

        await asyncio.sleep(0.01)
        self.widgets[index].update()

    @trigger("view_gc")
    def delete_render_view(self, ref_name):
        view_to_delete = None
        view_id = self.state[f"{ref_name}Id"]
        for view in self.to_delete:
            if view.GetGlobalIDAsString() == view_id:
                view_to_delete = view
        if view_to_delete is not None:
            self.to_delete = [v for v in self.to_delete if v != view_to_delete]
            Delete(view_to_delete)

    def compute_average(self, vardata, area):
        if np.isnan(vardata).any():
            mask = ~np.isnan(vardata)
            if not np.any(mask):
                return np.nan  # all values are NaN
            vardata = np.array(vardata)[mask]
            area = np.array(area)[mask]
        return np.average(vardata, weights=area)

    def create_or_update_views(self):
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
        to_render = vars2D + vars3Dm + vars3Di
        rendered = self.cache.keys()
        to_delete = set(rendered) - set(to_render)
        # Move old variables so they their proxies can be deleted
        self.to_delete.extend([self.cache[x].view for x in to_delete])

        # Get area variable to calculate weighted average
        data = self.source.views["2DProj"]
        vtkdata = sm.Fetch(data)
        area = np.array(vtkdata.GetCellData().GetArray("area"))

        del self.state.views[:]
        del self.state.layout[:]
        del self.widgets[:]
        sWidgets = []
        layout = []
        wdt = 4
        hgt = 3

        view0 = None
        for index, var in enumerate(to_render):
            x = int(index % 3) * wdt
            y = int(index / 3) * hgt

            vardata = vtkdata.GetCellData().GetArray(var)
            varrange = vardata.GetRange()
            varavg = self.compute_average(vardata, area)

            view = None
            viewdata: ViewData = self.cache.get(var, None)
            if viewdata is not None:
                view = viewdata.view
                viewdata.avg = varavg
                viewdata.min = varrange[0]
                viewdata.max = varrange[1]
                if view is None:
                    view = CreateRenderView()
                    view.GetRenderWindow().SetOffScreenRendering(True)
                    viewdata.view = view
                    view.UseColorPaletteForBackground = 0
                    view.BackgroundColorMode = "Gradient"
                    self.update_new_view(var, viewdata, self.source.views)
                else:
                    self.update_existing_view(var, viewdata)
            else:
                view = CreateRenderView()
                viewdata = ViewData(
                    view=view,
                    color=state.varcolor[0],
                    avg=varavg,
                    min=varrange[0],
                    max=varrange[1],
                )
                view.UseColorPaletteForBackground = 0
                view.BackgroundColorMode = "Gradient"
                self.cache[var] = viewdata
                self.update_new_view(var, viewdata, self.source.views)
            viewdata.index = index
            self.update_state_color_properties(index, viewdata)

            if index == 0:
                view0 = view
            else:
                AddCameraLink(view, view0, f"viewlink{index}")
            widget = pvWidgets.VtkRemoteView(
                view,
                interactive_ratio=1,
                classes="pa-0 drag_ignore",
                style="width: 100%; height: 100%;",
                trame_server=self.server,
            )
            self.widgets.append(widget)
            sWidgets.append(widget.ref_name)
            layout.append({"x": x, "y": y, "w": wdt, "h": hgt, "i": index})

        for var in to_delete:
            self.cache.pop(var)

        self.state.views = sWidgets
        self.state.layout = layout
        self.state.dirty("views")
        # from trame.app import asynchronous
        # asynchronous.create_task(self.flushViews())

    """
    async def flushViews(self):
        await self.server.network_completion
        print("Flushing views")
        self.reset_views()
        import asyncio
        await asyncio.sleep(1)
        print("Resetting views after sleep")
        self.reset_views()
    """

    def apply_colormap(self, index, type, value):
        var = self.state.variables[index]
        coltrfunc = GetColorTransferFunction(var)

        viewdata: ViewData = self.cache[var]
        if type == EventType.COL.value:
            viewdata.color = value
            coltrfunc.ApplyPreset(viewdata.color, True)
        elif type == EventType.LOG.value:
            viewdata.uselog = value
            if viewdata.uselog:
                coltrfunc.MapControlPointsToLogSpace()
                coltrfunc.UseLogScale = 1
            else:
                coltrfunc.MapControlPointsToLinearSpace()
                coltrfunc.UseLogScale = 0
        elif type == EventType.INV.value:
            viewdata.inv = value
            coltrfunc.InvertTransferFunction()
        self.reset_specific_view(index)

    def update_scalar_bars(self, event):
        print("Updating Scalar bar")
        for var, viewdata in self.cache.items():
            view = viewdata.view
            viewdata.data_rep.SetScalarBarVisibility(view, event)
            coltrfunc = GetColorTransferFunction(var)
            coltrfunc.ApplyPreset(viewdata.color, True)
            LUTColorBar = GetScalarBar(coltrfunc, view)
            LUTColorBar.Title = ""
            LUTColorBar.ComponentTitle = ""
        self.reset_views()

    def update_view_color_properties(self, index, min, max):
        var = self.state.variables[index]
        coltrfunc = GetColorTransferFunction(var)
        coltrfunc.RescaleTransferFunction(float(min), float(max))
        self.reset_specific_view(index)

    def reset_view_color_properties(self, index):
        var = self.state.variables[index]
        viewdata: ViewData = self.cache[var]
        self.state.varmin[index] = viewdata.min
        self.state.dirty("varmin")
        self.state.varmax[index] = viewdata.max
        self.state.dirty("varmax")
        viewdata.data_rep.RescaleTransferFunctionToDataRange(False, True)
        self.reset_views()

    def zoom_in(self, index=0):
        var = self.state.variables[index]
        viewdata: ViewData = self.cache[var]
        rview = viewdata.view
        rview.CameraParallelScale *= 0.95
        self.reset_views()

    def zoom_out(self, index=0):
        var = self.state.variables[index]
        viewdata: ViewData = self.cache[var]
        rview = viewdata.view
        rview.CameraParallelScale *= 1.05
        self.reset_views()

    def move(self, dir, factor, index=0):
        var = self.state.variables[index]
        viewdata: ViewData = self.cache[var]
        rview = viewdata.view
        extents = self.source.moveextents
        move = (
            (extents[1] - extents[0]) * 0.05,
            (extents[3] - extents[2]) * 0.05,
            (extents[5] - extents[4]) * 0.05,
        )

        pos = rview.CameraPosition
        foc = rview.CameraFocalPoint
        pos[dir] += move[dir] if factor > 0 else -move[dir]
        foc[dir] += move[dir] if factor > 0 else -move[dir]
        rview.CameraPosition = pos
        rview.CameraFocalPoint = foc
        self.reset_views()

import math
import numpy as np
import paraview.servermanager as sm

from trame.widgets import paraview as pvWidgets
from trame.decorators import TrameApp, trigger
from pyproj import Proj, Transformer

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
)

from quickview.pipeline import EAMVisSource
from quickview.utilities import EventType
from typing import Dict, List, Optional


class ViewRegistry:
    """Central registry for managing views"""

    def __init__(self):
        self._contexts: Dict[str, "ViewContext"] = {}
        self._view_order: List[str] = []

    def register_view(self, variable: str, context: "ViewContext"):
        """Register a new view or update existing one"""
        self._contexts[variable] = context
        if variable not in self._view_order:
            self._view_order.append(variable)

    def get_view(self, variable: str) -> Optional["ViewContext"]:
        """Get view context for a variable"""
        return self._contexts.get(variable)

    def remove_view(self, variable: str):
        """Remove a view from the registry"""
        if variable in self._contexts:
            del self._contexts[variable]
            self._view_order.remove(variable)

    def get_ordered_views(self) -> List["ViewContext"]:
        """Get all views in order they were added"""
        return [
            self._contexts[var] for var in self._view_order if var in self._contexts
        ]

    def get_all_variables(self) -> List[str]:
        """Get all registered variable names"""
        return list(self._contexts.keys())

    def items(self):
        """Iterate over variable-context pairs"""
        return self._contexts.items()

    def clear(self):
        """Clear all registered views"""
        self._contexts.clear()
        self._view_order.clear()

    def __len__(self):
        """Get number of registered views"""
        return len(self._contexts)

    def __contains__(self, variable: str):
        """Check if a variable is registered"""
        return variable in self._contexts


class ViewConfiguration:
    """Mutable configuration for a view - what the user can control"""

    def __init__(
        self,
        variable: str,
        colormap: str,
        use_log_scale: bool = False,
        invert_colors: bool = False,
        min_value: float = None,
        max_value: float = None,
        override_range: bool = False,
    ):
        self.variable = variable
        self.colormap = colormap
        self.use_log_scale = use_log_scale
        self.invert_colors = invert_colors
        self.min_value = min_value
        self.max_value = max_value
        self.override_range = override_range  # True when user manually sets min/max


class ViewState:
    """Runtime state for a view - ParaView objects and computed values"""

    def __init__(
        self,
        view_proxy=None,
        data_representation=None,
        var_text_proxy=None,
        var_info_proxy=None,
        computed_average: float = None,
    ):
        self.view_proxy = view_proxy
        self.data_representation = data_representation
        self.var_text_proxy = var_text_proxy
        self.var_info_proxy = var_info_proxy
        self.computed_average = computed_average


class ViewContext:
    """Complete context for a rendered view combining configuration and state"""

    def __init__(self, config: ViewConfiguration, state: ViewState, index: int):
        self.config = config
        self.state = state
        self.index = index


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


def build_color_information(state: map):
    vars = state["variables"]
    colors = state["varcolor"]
    logscl = state["uselogscale"]
    invert = state["invert"]
    varmin = state["varmin"]
    varmax = state["varmax"]
    # Get override_range from state if available
    override_range = state.get("override_range", None)
    # Store layout from state if available for backward compatibility
    layout = state.get("layout", None)

    registry = ViewRegistry()
    for index, var in enumerate(vars):
        # Use provided override_range if available
        if override_range is not None and index < len(override_range):
            override = override_range[index]
        else:
            # Legacy behavior for older saved states without override_range
            override = True

        config = ViewConfiguration(
            variable=var,
            colormap=colors[index],
            use_log_scale=logscl[index],
            invert_colors=invert[index],
            min_value=varmin[index],
            max_value=varmax[index],
            override_range=override,
        )
        view_state = ViewState()
        context = ViewContext(config, view_state, index)
        registry.register_view(var, context)

    # Store layout info in registry for later use
    if layout:
        registry._saved_layout = [item.copy() for item in layout]

    return registry


@TrameApp()
class ViewManager:
    def __init__(self, source: EAMVisSource, server, state):
        self.server = server
        self.source = source
        self.state = state
        self.widgets = []
        self.colors = []
        self.registry = ViewRegistry()  # Central registry for view management
        self.to_delete = []
        self.rep_change = False

    def update_views_for_timestep(self):
        if len(self.registry) == 0:
            return
        data = sm.Fetch(self.source.views["atmosphere_data"])

        for var, context in self.registry.items():
            varavg = self.compute_average(var, vtkdata=data)
            context.state.computed_average = varavg
            if not context.config.override_range:
                context.state.data_representation.RescaleTransferFunctionToDataRange(
                    False, True
                )
                range = self.compute_range(var=var)
                context.config.min_value = range[0]
                context.config.max_value = range[1]
            (v_text, V_info) = self.get_var_info(var, context.state.computed_average)
            if context.state.var_text_proxy is not None:
                context.state.var_text_proxy.Text = v_text
            if context.state.var_info_proxy is not None:
                context.state.var_info_proxy.Text = V_info
            self.sync_color_config_to_state(context.index, context)

    def refresh_view_display(self, var, context: ViewContext):
        if not context.config.override_range:
            context.state.data_representation.RescaleTransferFunctionToDataRange(
                False, True
            )
        (v_text, V_info) = self.get_var_info(var, context.state.computed_average)
        if context.state.var_text_proxy is not None:
            context.state.var_text_proxy.Text = v_text
        if context.state.var_info_proxy is not None:
            context.state.var_info_proxy.Text = V_info
        rview = context.state.view_proxy

        Render(rview)
        # ResetCamera(rview)

    def get_var_info(self, var, average):
        var_text = var + "\n(avg: " + "{:.2E}".format(average) + ")"
        info_text = None
        surface_vars = self.source.vars.get("surface", [])
        t = self.state.tstamp
        if surface_vars and var in surface_vars:
            info_text = f"t = {t}"
        midpoint_vars = self.source.vars.get("midpoint", [])
        if midpoint_vars and var in midpoint_vars:
            k = self.state.midpoint
            info_text = f"k = {k}\nt = {t}"
        interface_vars = self.source.vars.get("interface", [])
        if interface_vars and var in interface_vars:
            k = self.state.interface
            info_text = f"k = {k}\nt = {t}"

        return (var_text, info_text)

    def configure_new_view(self, var, context: ViewContext, sources):
        rview = context.state.view_proxy

        # Update unique sources to all render views
        data = sources["atmosphere_data"]
        rep = Show(data, rview)
        context.state.data_representation = rep
        ColorBy(rep, ("CELLS", var))
        coltrfunc = GetColorTransferFunction(var)
        coltrfunc.ApplyPreset(context.config.colormap, True)
        coltrfunc.NanOpacity = 0.0
        LUTColorBar = GetScalarBar(coltrfunc, rview)
        LUTColorBar.AutoOrient = 1
        LUTColorBar.WindowLocation = "Lower Right Corner"
        LUTColorBar.Title = ""
        LUTColorBar.ComponentTitle = ""
        LUTColorBar.ScalarBarLength = 0.75
        # LUTColorBar.NanOpacity = 0.0

        (v_text, V_info) = self.get_var_info(var, context.state.computed_average)
        text = Text(registrationName=f"Text{var}")
        text.Text = v_text
        context.state.var_text_proxy = text
        textrep = Show(text, rview, "TextSourceRepresentation")
        textrep.WindowLocation = "Upper Right Corner"
        textrep.FontFamily = "Times"

        info = Text(registrationName=f"Info{var}")
        info.Text = V_info
        context.state.var_info_proxy = info
        textrep = Show(info, rview, "TextSourceRepresentation")
        textrep.WindowLocation = "Upper Left Corner"
        textrep.FontFamily = "Times"

        # Update common sources to all render views

        globe = sources["continents"]
        repG = Show(globe, rview)
        ColorBy(repG, None)
        repG.SetRepresentationType("Wireframe")
        repG.RenderLinesAsTubes = 1
        repG.LineWidth = 1.0
        repG.AmbientColor = [0.67, 0.67, 0.67]
        repG.DiffuseColor = [0.67, 0.67, 0.67]

        annot = sources["grid_lines"]
        repAn = Show(annot, rview)
        repAn.SetRepresentationType("Wireframe")
        repAn.AmbientColor = [0.67, 0.67, 0.67]
        repAn.DiffuseColor = [0.67, 0.67, 0.67]
        repAn.Opacity = 0.4

        rep.SetScalarBarVisibility(rview, self.state.show_color_bar)
        rview.CameraParallelProjection = 1

        Render(rview)
        # ResetCamera(rview)

    def sync_color_config_to_state(self, index, context: ViewContext):
        with self.state as state:
            state.varcolor[index] = context.config.colormap
            state.varmin[index] = context.config.min_value
            state.varmax[index] = context.config.max_value
            state.uselogscale[index] = context.config.use_log_scale
            state.override_range[index] = context.config.override_range

    def reset_camera(self, **kwargs):
        for widget in self.widgets:
            widget.reset_camera()

    def render_all_views(self, **kwargs):
        for widget in self.widgets:
            widget.update()

    def render_view_by_index(self, index):
        self.widgets[index].update()

    @trigger("resetview")
    async def resize_and_refresh_view(self, index, sizeinfo=None):
        if sizeinfo is not None:
            var = self.state.variables[index]
            context: ViewContext = self.registry.get_view(var)
            height = int(sizeinfo["height"])
            width = int(sizeinfo["width"])
            context.state.view_proxy.ViewSize = (width, height)
            Render(context.state.view_proxy)
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

    def compute_average(self, var, vtkdata=None):
        if vtkdata is None:
            data = self.source.views["atmosphere_data"]
            vtkdata = sm.Fetch(data)
        vardata = vtkdata.GetCellData().GetArray(var)
        area = np.array(vtkdata.GetCellData().GetArray("area"))
        if np.isnan(vardata).any():
            mask = ~np.isnan(vardata)
            if not np.any(mask):
                return np.nan  # all values are NaN
            vardata = np.array(vardata)[mask]
            area = np.array(area)[mask]
        return np.average(vardata, weights=area)

    def compute_range(self, var, vtkdata=None):
        if vtkdata is None:
            data = self.source.views["atmosphere_data"]
            vtkdata = sm.Fetch(data)
        vardata = vtkdata.GetCellData().GetArray(var)
        return vardata.GetRange()

    def rebuild_visualization_layout(self, cached_layout=None):
        self.widgets.clear()
        state = self.state
        source = self.source
        long = state.cliplong
        lat = state.cliplat
        source.UpdateLev(self.state.midpoint, self.state.interface)
        source.ApplyClipping(long, lat)
        source.UpdateCenter(self.state.center)
        source.UpdateProjection(self.state.projection)
        source.UpdatePipeline()
        surface_vars = source.vars.get("surface", [])
        midpoint_vars = source.vars.get("midpoint", [])
        interface_vars = source.vars.get("interface", [])
        to_render = surface_vars + midpoint_vars + interface_vars
        rendered = self.registry.get_all_variables()
        to_delete = set(rendered) - set(to_render)
        # Move old variables so they their proxies can be deleted
        self.to_delete.extend(
            [self.registry.get_view(x).state.view_proxy for x in to_delete]
        )

        # Get area variable to calculate weighted average
        data = self.source.views["atmosphere_data"]
        vtkdata = sm.Fetch(data)

        # Use cached layout if provided, or fall back to saved layout in registry
        layout_map = cached_layout if cached_layout else {}

        # If no cached layout, check if we have saved layout in registry
        if not layout_map and hasattr(self.registry, "_saved_layout"):
            # Convert saved layout array to variable-name-based map
            temp_map = {}
            for item in self.registry._saved_layout:
                if isinstance(item, dict) and "i" in item:
                    idx = item["i"]
                    if hasattr(state, "variables") and idx < len(state.variables):
                        var_name = state.variables[idx]
                        temp_map[var_name] = {
                            "x": item.get("x", 0),
                            "y": item.get("y", 0),
                            "w": item.get("w", 4),
                            "h": item.get("h", 3),
                        }
            layout_map = temp_map

        del self.state.views[:]
        del self.state.layout[:]
        del self.widgets[:]
        sWidgets = []
        layout = []
        wdt = 4
        hgt = 3

        view0 = None
        for index, var in enumerate(to_render):
            # Check if we have saved position for this variable
            if var in layout_map:
                # Use saved position
                pos = layout_map[var]
                x = pos["x"]
                y = pos["y"]
                wdt = pos["w"]
                hgt = pos["h"]
            else:
                # Default grid position (3 columns)
                x = int(index % 3) * 4
                y = int(index / 3) * 3
                wdt = 4
                hgt = 3

            varrange = self.compute_range(var, vtkdata=vtkdata)
            varavg = self.compute_average(var, vtkdata=vtkdata)

            view = None
            context: ViewContext = self.registry.get_view(var)
            if context is not None:
                view = context.state.view_proxy
                context.state.computed_average = varavg
                if view is None:
                    view = CreateRenderView()
                    view.UseColorPaletteForBackground = 0
                    view.BackgroundColorMode = "Gradient"
                    view.GetRenderWindow().SetOffScreenRendering(True)
                    context.state.view_proxy = view
                    context.config.min_value = varrange[0]
                    context.config.max_value = varrange[1]
                    self.configure_new_view(var, context, self.source.views)
                else:
                    self.refresh_view_display(var, context)
            else:
                view = CreateRenderView()
                # Preserve override flag if context already exists
                existing_context = self.registry.get_view(var)
                override = (
                    existing_context.config.override_range
                    if existing_context
                    else False
                )

                config = ViewConfiguration(
                    variable=var,
                    colormap=state.varcolor[0],
                    use_log_scale=False,
                    invert_colors=False,
                    min_value=varrange[0],
                    max_value=varrange[1],
                    override_range=override,
                )
                view_state = ViewState(
                    view_proxy=view,
                    computed_average=varavg,
                )
                context = ViewContext(config, view_state, index)
                view.UseColorPaletteForBackground = 0
                view.BackgroundColorMode = "Gradient"
                self.registry.register_view(var, context)
                self.configure_new_view(var, context, self.source.views)
            context.index = index
            self.sync_color_config_to_state(index, context)

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
            # Use index as identifier to maintain compatibility with grid expectations
            layout.append({"x": x, "y": y, "w": wdt, "h": hgt, "i": index})

        for var in to_delete:
            self.registry.remove_view(var)

        self.state.views = sWidgets
        self.state.layout = layout
        self.state.dirty("views")
        self.state.dirty("layout")
        # from trame.app import asynchronous
        # asynchronous.create_task(self.flushViews())

    """
    async def flushViews(self):
        await self.server.network_completion
        print("Flushing views")
        self.render_all_views()
        import asyncio
        await asyncio.sleep(1)
        print("Resetting views after sleep")
        self.render_all_views()
    """

    def update_view_color_settings(self, index, type, value):
        var = self.state.variables[index]
        coltrfunc = GetColorTransferFunction(var)

        context: ViewContext = self.registry.get_view(var)
        if type == EventType.COL.value:
            context.config.colormap = value
            coltrfunc.ApplyPreset(context.config.colormap, True)
        elif type == EventType.LOG.value:
            context.config.use_log_scale = value
            if context.config.use_log_scale:
                coltrfunc.MapControlPointsToLogSpace()
                coltrfunc.UseLogScale = 1
            else:
                coltrfunc.MapControlPointsToLinearSpace()
                coltrfunc.UseLogScale = 0
        elif type == EventType.INV.value:
            context.config.invert_colors = value
            coltrfunc.InvertTransferFunction()
        self.render_view_by_index(index)

    def update_scalar_bars(self, event):
        for var, context in self.registry.items():
            view = context.state.view_proxy
            context.state.data_representation.SetScalarBarVisibility(view, event)
            coltrfunc = GetColorTransferFunction(var)
            coltrfunc.ApplyPreset(context.config.colormap, True)
            LUTColorBar = GetScalarBar(coltrfunc, view)
            LUTColorBar.Title = ""
            LUTColorBar.ComponentTitle = ""
        self.render_all_views()

    def set_manual_color_range(self, index, min, max):
        var = self.state.variables[index]
        context: ViewContext = self.registry.get_view(var)
        context.config.override_range = True
        context.config.min_value = float(min)
        context.config.max_value = float(max)
        # Update state to reflect manual override
        self.state.override_range[index] = True
        self.state.dirty("override_range")
        coltrfunc = GetColorTransferFunction(var)
        coltrfunc.RescaleTransferFunction(float(min), float(max))
        self.render_view_by_index(index)

    def revert_to_auto_color_range(self, index):
        var = self.state.variables[index]
        # Get colors from main file
        varrange = self.compute_range(var)
        context: ViewContext = self.registry.get_view(var)
        context.config.override_range = False
        context.config.min_value = varrange[0]
        context.config.max_value = varrange[1]
        self.state.varmin[index] = context.config.min_value
        self.state.dirty("varmin")
        self.state.varmax[index] = context.config.max_value
        self.state.dirty("varmax")
        self.state.override_range[index] = context.config.override_range
        self.state.dirty("override_range")
        context.state.data_representation.RescaleTransferFunctionToDataRange(
            False, True
        )
        self.render_all_views()

    def zoom_in(self, index=0):
        var = self.state.variables[index]
        context: ViewContext = self.registry.get_view(var)
        rview = context.state.view_proxy
        rview.CameraParallelScale *= 0.95
        self.render_all_views()

    def zoom_out(self, index=0):
        var = self.state.variables[index]
        context: ViewContext = self.registry.get_view(var)
        rview = context.state.view_proxy
        rview.CameraParallelScale *= 1.05
        self.render_all_views()

    def pan_camera(self, dir, factor, index=0):
        var = self.state.variables[index]
        context: ViewContext = self.registry.get_view(var)
        rview = context.state.view_proxy
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
        self.render_all_views()

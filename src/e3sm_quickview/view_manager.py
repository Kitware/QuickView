import paraview.servermanager as sm

from trame.widgets import paraview as pvWidgets
from trame.decorators import TrameApp, trigger, change

from paraview.simple import (
    Delete,
    Show,
    CreateRenderView,
    ColorBy,
    GetColorTransferFunction,
    AddCameraLink,
    Render,
)

from e3sm_quickview.pipeline import EAMVisSource
from typing import Dict, List, Optional

from e3sm_quickview.utils.math import calculate_weighted_average
from e3sm_quickview.utils.color import get_cached_colorbar_image
from e3sm_quickview.utils.geometry import (
    generate_annotations as generate_map_annotations,
)

# Constants for camera and display
LABEL_OFFSET_FACTOR = 0.075  # Factor for offsetting labels from map edge
ZOOM_IN_FACTOR = 0.95  # Scale factor for zooming in
ZOOM_OUT_FACTOR = 1.05  # Scale factor for zooming out
DEFAULT_MARGIN = 1.05  # Default margin for viewport fitting (5% margin)
GRATICULE_INTERVAL = 30  # Default interval for map graticule in degrees
PAN_OFFSET_RATIO = 0.05  # Ratio of extent to use for pan offset (5%)

# Grid layout constants
DEFAULT_GRID_COLUMNS = 3  # Number of columns in default grid layout
DEFAULT_GRID_WIDTH = 4  # Default width of grid items
DEFAULT_GRID_HEIGHT = 3  # Default height of grid items


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
    """Runtime state for a view - ParaView objects"""

    def __init__(
        self,
        view_proxy=None,
        data_representation=None,
    ):
        self.view_proxy = view_proxy
        self.data_representation = data_representation


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
    return generate_map_annotations(
        long,
        lat,
        projection,
        center,
        interval=GRATICULE_INTERVAL,
        label_offset_factor=LABEL_OFFSET_FACTOR,
    )


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
        self.registry = ViewRegistry()  # Central registry for view management
        self.to_delete = []

    def get_default_colormap(self):
        """Get default colormap from interface or fallback"""
        # Try to get from the server's interface instance
        if self.state.use_cvd_colors:
            return "batlow"
        # Fallback to a reasonable default
        return "Cool to Warm (Extended)"

    @change("pipeline_valid")
    def _on_change_pipeline_valid(self, pipeline_valid, **kwargs):
        """Clear view registry when pipeline becomes invalid."""
        if not pipeline_valid:
            print("Clearing registry")
            # Clear all views and variables from registry
            self.registry.clear()
            # Clear widgets and colors tracking
            del self.state.views[:]
            del self.state.layout[:]
            self.state.dirty("views")
            self.state.dirty("layout")

    def close_view(self, var, index, layout_cache: map):
        # Clear cache and remove layout and widget entry
        with self.state as state:
            self.registry.remove_view(var)
            state.varcolor.pop(index)
            state.varmin.pop(index)
            state.varmax.pop(index)
            state.uselogscale.pop(index)
            state.override_range.pop(index)
            state.invert.pop(index)
            state.colorbar_images.pop(index)
            self.widgets.pop(index)

        self.state.dirty("varcolor")
        self.state.dirty("varmin")
        self.state.dirty("varmax")
        self.state.dirty("uselogscale")
        self.state.dirty("override_range")
        self.state.dirty("invert")
        self.state.dirty("colorbar_images")
        self.rebuild_after_close(layout_cache)

    def update_views_for_timestep(self):
        if len(self.registry) == 0:
            return
        data = sm.Fetch(self.source.views["atmosphere_data"])

        first_view = None
        for var, context in self.registry.items():
            index = self.state.variables.index(var)
            varavg = self.compute_average(var, vtkdata=data)
            # Directly set average in trame state
            self.state.varaverage[index] = varavg
            self.state.dirty("varaverage")
            if not context.config.override_range:
                context.state.data_representation.RescaleTransferFunctionToDataRange(
                    False, True
                )
                range = self.compute_range(var=var)
                context.config.min_value = range[0]
                context.config.max_value = range[1]
            self.sync_color_config_to_state(index, context)
            self.generate_colorbar_image(index)

            # Track the first view for camera fitting
            if first_view is None and context.state.view_proxy:
                first_view = context.state.view_proxy

        if first_view is not None:
            first_view.ResetCamera(True, 0.9)

    def refresh_view_display(self, context: ViewContext):
        if not context.config.override_range:
            context.state.data_representation.RescaleTransferFunctionToDataRange(
                False, True
            )
        rview = context.state.view_proxy

        Render(rview)
        # ResetCamera(rview)

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

        # Apply log scale if configured
        if context.config.use_log_scale:
            coltrfunc.MapControlPointsToLogSpace()
            coltrfunc.UseLogScale = 1

        # Apply inversion if configured
        if context.config.invert_colors:
            coltrfunc.InvertTransferFunction()

        # Ensure the color transfer function is scaled to the data range
        if not context.config.override_range:
            rep.RescaleTransferFunctionToDataRange(False, True)
        else:
            coltrfunc.RescaleTransferFunction(
                context.config.min_value, context.config.max_value
            )

        # ParaView scalar bar is always hidden - using custom HTML colorbar instead

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

        # Always hide ParaView scalar bar - using custom HTML colorbar
        rep.SetScalarBarVisibility(rview, False)
        rview.CameraParallelProjection = 1

        Render(rview)
        # ResetCamera(rview)

    def sync_color_config_to_state(self, index, context: ViewContext):
        # Update state arrays directly without context manager to avoid recursive flush
        self.state.varcolor[index] = context.config.colormap
        self.state.varmin[index] = context.config.min_value
        self.state.varmax[index] = context.config.max_value
        self.state.uselogscale[index] = context.config.use_log_scale
        self.state.override_range[index] = context.config.override_range
        self.state.invert[index] = context.config.invert_colors
        # Mark arrays as dirty to ensure UI updates
        self.state.dirty("varcolor")
        self.state.dirty("varmin")
        self.state.dirty("varmax")
        self.state.dirty("uselogscale")
        self.state.dirty("override_range")
        self.state.dirty("invert")

    def generate_colorbar_image(self, index):
        """Generate colorbar image for a variable at given index.

        This uses the cached colorbar images based on the colormap name
        and invert status.
        """
        if index >= len(self.state.variables):
            return

        var = self.state.variables[index]
        context = self.registry.get_view(var)
        if context is None:
            return

        # Get cached colorbar image based on colormap and invert status
        try:
            image_data = get_cached_colorbar_image(
                context.config.colormap, context.config.invert_colors
            )
            # Update state with the cached image
            self.state.colorbar_images[index] = image_data
            self.state.dirty("colorbar_images")
        except Exception as e:
            print(f"Error getting cached colorbar image for {var}: {e}")

    def reset_camera(self, **kwargs):
        if len(self.widgets) > 0 and len(self.state.variables) > 0:
            var = self.state.variables[0]
            context = self.registry.get_view(var)
            if context and context.state.view_proxy:
                context.state.view_proxy.ResetCamera(True, 0.9)
        self.render_all_views()

    def render_all_views(self, **kwargs):
        for widget in self.widgets:
            widget.update()

    def render_view_by_index(self, index):
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

        # Check if area variable exists
        area_array = vtkdata.GetCellData().GetArray("area")
        return calculate_weighted_average(vardata, area_array)

    def compute_range(self, var, vtkdata=None):
        if vtkdata is None:
            data = self.source.views["atmosphere_data"]
            vtkdata = sm.Fetch(data)
        vardata = vtkdata.GetCellData().GetArray(var)
        return vardata.GetRange()

    def rebuild_after_close(self, cached_layout=None):
        to_render = self.state.variables
        rendered = self.registry.get_all_variables()
        to_delete = set(rendered) - set(to_render)
        # Move old variables so they their proxies can be deleted
        self.to_delete.extend(
            [self.registry.get_view(x).state.view_proxy for x in to_delete]
        )

        layout_map = cached_layout if cached_layout else {}

        del self.state.views[:]
        del self.state.layout[:]
        del self.widgets[:]
        sWidgets = []
        layout = []
        wdt = 4
        hgt = 3

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

            context: ViewContext = self.registry.get_view(var)
            view = context.state.view_proxy
            context.index = index
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

    def rebuild_visualization_layout(self, cached_layout=None, update_pipeline=True):
        self.widgets.clear()
        state = self.state
        source = self.source
        long = state.cliplong
        lat = state.cliplat
        tstamp = state.tstamp
        time = 0.0 if len(self.state.timesteps) == 0 else self.state.timesteps[tstamp]

        if update_pipeline:
            source.UpdateLev(self.state.midpoint, self.state.interface)
            source.ApplyClipping(long, lat)
            source.UpdateCenter(self.state.center)
            source.UpdateProjection(self.state.projection)
            source.UpdatePipeline(time)

        to_render = self.state.variables
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
                if view is None:
                    view = CreateRenderView()
                    view.OrientationAxesVisibility = 0
                    view.UseColorPaletteForBackground = 0
                    view.BackgroundColorMode = "Gradient"
                    view.GetRenderWindow().SetOffScreenRendering(True)
                    context.state.view_proxy = view
                    # First time creating view for this context
                    # Context already has its configuration from previous sessions
                    # Just update range if not overridden (critical requirement)
                    if not context.config.override_range:
                        context.config.min_value = varrange[0]
                        context.config.max_value = varrange[1]
                    self.configure_new_view(var, context, self.source.views)
                else:
                    # Trust the ViewContext - it's already configured
                    # Only update the color range if not overridden (critical requirement)
                    if not context.config.override_range:
                        context.config.min_value = varrange[0]
                        context.config.max_value = varrange[1]

                    # Only refresh the display, don't change configuration
                    self.refresh_view_display(context)
            else:
                # Creating a completely new ViewContext
                view = CreateRenderView()

                # Use defaults for new variables
                default_colormap = self.get_default_colormap()

                config = ViewConfiguration(
                    variable=var,
                    colormap=default_colormap,
                    use_log_scale=False,  # Default
                    invert_colors=False,  # Default
                    min_value=varrange[0],  # Always use current data range
                    max_value=varrange[1],
                    override_range=False,  # Default to auto-range
                )
                view_state = ViewState(
                    view_proxy=view,
                )
                context = ViewContext(config, view_state, index)
                view.UseColorPaletteForBackground = 0
                view.BackgroundColorMode = "Gradient"
                self.registry.register_view(var, context)
                self.configure_new_view(var, context, self.source.views)

            # Apply manual color range if override is enabled
            if context.config.override_range:
                coltrfunc = GetColorTransferFunction(var)
                coltrfunc.RescaleTransferFunction(
                    context.config.min_value, context.config.max_value
                )

            context.index = index
            # Set the computed average directly in trame state
            self.state.varaverage[index] = varavg
            self.state.dirty("varaverage")
            self.sync_color_config_to_state(index, context)
            self.generate_colorbar_image(index)

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

    def update_colormap(self, index, value):
        """Update the colormap for a variable."""
        var = self.state.variables[index]
        coltrfunc = GetColorTransferFunction(var)
        context: ViewContext = self.registry.get_view(var)

        context.config.colormap = value
        # Apply the preset
        coltrfunc.ApplyPreset(context.config.colormap, True)
        # Reapply inversion if it was enabled
        if context.config.invert_colors:
            coltrfunc.InvertTransferFunction()

        # Generate new colorbar image with updated colormap
        self.generate_colorbar_image(index)
        # Sync all color configuration changes back to state
        self.sync_color_config_to_state(index, context)
        self.render_view_by_index(index)

    def update_log_scale(self, index, value):
        """Update the log scale setting for a variable."""
        var = self.state.variables[index]
        coltrfunc = GetColorTransferFunction(var)
        context: ViewContext = self.registry.get_view(var)

        context.config.use_log_scale = value
        if context.config.use_log_scale:
            coltrfunc.MapControlPointsToLogSpace()
            coltrfunc.UseLogScale = 1
        else:
            coltrfunc.MapControlPointsToLinearSpace()
            coltrfunc.UseLogScale = 0
        # Note: We don't regenerate the colorbar image here because the color gradient
        # itself doesn't change with log scale - only the data mapping changes.
        # The colorbar always shows a linear color progression.

        # Sync all color configuration changes back to state
        self.sync_color_config_to_state(index, context)
        self.render_view_by_index(index)

    def update_invert_colors(self, index, value):
        """Update the color inversion setting for a variable."""
        var = self.state.variables[index]
        coltrfunc = GetColorTransferFunction(var)
        context: ViewContext = self.registry.get_view(var)

        context.config.invert_colors = value
        coltrfunc.InvertTransferFunction()
        # Generate new colorbar image when colors are inverted
        self.generate_colorbar_image(index)

        # Sync all color configuration changes back to state
        self.sync_color_config_to_state(index, context)
        self.render_view_by_index(index)

    def update_scalar_bars(self, event=None):
        # Always hide ParaView scalar bars - using custom HTML colorbar
        # The HTML colorbar is always visible, no toggle needed
        for _, context in self.registry.items():
            view = context.state.view_proxy
            context.state.data_representation.SetScalarBarVisibility(view, False)
        self.render_all_views()

    def set_manual_color_range(self, index, min, max):
        var = self.state.variables[index]
        context: ViewContext = self.registry.get_view(var)
        context.config.override_range = True
        context.config.min_value = float(min)
        context.config.max_value = float(max)
        # Sync all changes back to state
        self.sync_color_config_to_state(index, context)
        # Update color transfer function
        coltrfunc = GetColorTransferFunction(var)
        coltrfunc.RescaleTransferFunction(float(min), float(max))
        # Note: colorbar image doesn't change with range, only data mapping changes
        self.render_view_by_index(index)

    def revert_to_auto_color_range(self, index):
        var = self.state.variables[index]
        # Get colors from main file
        varrange = self.compute_range(var)
        context: ViewContext = self.registry.get_view(var)
        context.config.override_range = False
        context.config.min_value = varrange[0]
        context.config.max_value = varrange[1]
        # Sync all changes back to state
        self.sync_color_config_to_state(index, context)
        # Rescale transfer function to data range
        context.state.data_representation.RescaleTransferFunctionToDataRange(
            False, True
        )
        # Note: colorbar image doesn't change with range, only data mapping changes
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

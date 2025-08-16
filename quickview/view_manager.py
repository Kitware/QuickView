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
    ColorBy,
    GetColorTransferFunction,
    AddCameraLink,
    Render,
)

from quickview.pipeline import EAMVisSource
from quickview.utilities import get_cached_colorbar_image
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
            # Directly set average in trame state
            self.state.varaverage[context.index] = varavg
            self.state.dirty("varaverage")
            if not context.config.override_range:
                context.state.data_representation.RescaleTransferFunctionToDataRange(
                    False, True
                )
                range = self.compute_range(var=var)
                context.config.min_value = range[0]
                context.config.max_value = range[1]
            self.sync_color_config_to_state(context.index, context)
            self.generate_colorbar_image(context.index)
            # Fit objects optimally after geometry changes
            if context.state.view_proxy:
                self.fit_to_viewport(context.state.view_proxy)

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

    def calculate_parallel_scale(self, view, margin=1.05):
        """
        Calculate optimal ParallelScale for a view based on GridProj bounds.
        
        Args:
            view: The render view to calculate scale for
            margin: Margin factor (1.05 = 5% margin around objects)
            
        Returns:
            Optimal parallel scale value, or None if calculation fails
        """
        from paraview.simple import UpdatePipeline, FindSource
        
        try:
            # Ensure pipeline is up to date
            UpdatePipeline()
            
            # Get GridProj bounds - it encompasses the full map extent
            grid_source = FindSource("GridProj")
            if not grid_source:
                return None
            
            bounds = grid_source.GetDataInformation().GetBounds()
            if not bounds or bounds[0] > bounds[1]:
                return None
            
            # Calculate data dimensions
            width = bounds[1] - bounds[0]
            height = bounds[3] - bounds[2]
            
            if width <= 0 or height <= 0:
                return None
            
            # Get viewport dimensions
            view_size = view.ViewSize
            if view_size[0] <= 0 or view_size[1] <= 0:
                return None
                
            viewport_aspect = view_size[0] / view_size[1]
            data_aspect = width / height
            
            # Calculate optimal parallel scale
            if data_aspect > viewport_aspect:
                # Data is wider than viewport - fit to width
                parallel_scale = (width / (2.0 * viewport_aspect)) * margin
            else:
                # Data is taller than viewport - fit to height
                parallel_scale = (height / 2.0) * margin
                
            return parallel_scale
            
        except Exception as e:
            print(f"Error calculating parallel scale: {e}")
            return None
    
    def fit_to_viewport(self, view, margin=1.05):
        """
        Dynamically calculate and set optimal ParallelScale to fit objects in viewport.
        
        Args:
            view: The render view to fit
            margin: Margin factor (1.05 = 5% margin around objects)
        """
        from paraview.simple import SetActiveView, FindSource
        
        try:
            # Set this as the active view to ensure camera operations work correctly
            SetActiveView(view)
            
            # Calculate the optimal parallel scale
            parallel_scale = self.calculate_parallel_scale(view, margin)
            if parallel_scale is None:
                return
            
            # Get GridProj bounds for centering the camera
            grid_source = FindSource("GridProj")
            if not grid_source:
                return
                
            combined_bounds = grid_source.GetDataInformation().GetBounds()
            if not combined_bounds:
                return
            
            # Get the view's camera directly
            camera = view.GetActiveCamera()
            camera.SetParallelProjection(True)
            camera.SetParallelScale(parallel_scale)
            
            # Center camera on data
            center = [
                (combined_bounds[0] + combined_bounds[1]) / 2,
                (combined_bounds[2] + combined_bounds[3]) / 2,
                (combined_bounds[4] + combined_bounds[5]) / 2
            ]
            camera.SetFocalPoint(*center)
            
            # For 2D projections, position camera perpendicular to XY plane
            camera_pos = [center[0], center[1], center[2] + 1000]
            camera.SetPosition(*camera_pos)
            camera.SetViewUp(0, 1, 0)
            
            # Apply the camera settings to the view
            view.CameraParallelScale = parallel_scale
            
        except Exception as e:
            print(f"Error in fit_to_viewport: {e}")
            # Fallback to simple reset if our calculation fails
            try:
                from paraview.simple import ResetCamera
                ResetCamera(view)
            except:
                pass
    def reset_camera(self, **kwargs):
        """Reset camera for all views to optimally fit objects."""
        for i, widget in enumerate(self.widgets):
            if i < len(self.state.variables):
                var = self.state.variables[i]
                context = self.registry.get_view(var)
                if context and context.state.view_proxy:
                    self.fit_to_viewport(context.state.view_proxy)
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

        if area_array is not None:
            # Area-weighted averaging
            area = np.array(area_array)
            if np.isnan(vardata).any():
                mask = ~np.isnan(vardata)
                if not np.any(mask):
                    return np.nan  # all values are NaN
                vardata = np.array(vardata)[mask]
                area = np.array(area)[mask]
            return np.average(vardata, weights=area)
        else:
            # Simple arithmetic averaging
            vardata = np.array(vardata)
            if np.isnan(vardata).any():
                mask = ~np.isnan(vardata)
                if not np.any(mask):
                    return np.nan  # all values are NaN
                vardata = vardata[mask]
            return np.mean(vardata)

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
                    self.refresh_view_display(context)
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
                    colormap=state.varcolor[index]
                    if index < len(state.varcolor)
                    else state.varcolor[0],
                    use_log_scale=state.uselogscale[index]
                    if index < len(state.uselogscale)
                    else False,
                    invert_colors=state.invert[index]
                    if index < len(state.invert)
                    else False,
                    min_value=varrange[0],
                    max_value=varrange[1],
                    override_range=override,
                )
                view_state = ViewState(
                    view_proxy=view,
                )
                context = ViewContext(config, view_state, index)
                view.UseColorPaletteForBackground = 0
                view.BackgroundColorMode = "Gradient"
                self.registry.register_view(var, context)
                self.configure_new_view(var, context, self.source.views)
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

        view0.CameraParallelScale = 100

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

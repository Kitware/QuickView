import paraview.servermanager as sm

from trame.widgets import paraview as pvWidgets
from trame.decorators import TrameApp, trigger

from paraview.simple import (
    Delete,
    Show,
    CreateRenderView,
    ColorBy,
    GetColorTransferFunction,
    AddCameraLink,
    Render,
)

from quickview.pipeline import EAMVisSource
from quickview.utils.color import get_cached_colorbar_image
from quickview.utils.geometry import generate_annotations as generate_map_annotations
from quickview.utils.math import calculate_weighted_average
from quickview.utils.state import ViewContext, ViewRegistry

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


# ViewRegistry and ViewContext classes have been moved to view_state.py


def generate_annotations(long, lat, projection, center):
    """Generate map annotations using geo_utils."""
    return generate_map_annotations(
        long,
        lat,
        projection,
        center,
        interval=GRATICULE_INTERVAL,
        label_offset_factor=LABEL_OFFSET_FACTOR,
    )


# build_color_information has been moved to view_state.py


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

    def get_color_config(self, index):
        """Get all color configuration for a variable from state arrays"""
        state = self.state
        return {
            "colormap": state.varcolor[index]
            if index < len(state.varcolor)
            else "Cool to Warm",
            "use_log_scale": state.uselogscale[index]
            if index < len(state.uselogscale)
            else False,
            "invert_colors": state.invert[index]
            if index < len(state.invert)
            else False,
            "min_value": state.varmin[index] if index < len(state.varmin) else None,
            "max_value": state.varmax[index] if index < len(state.varmax) else None,
            "override_range": state.override_range[index]
            if index < len(state.override_range)
            else False,
        }

    def should_use_manual_range(self, index):
        """Check if manual range should be used for a variable"""
        return (
            hasattr(self.state, "override_range")
            and index < len(self.state.override_range)
            and self.state.override_range[index]
        )

    def get_color_range(self, var, index):
        """Get the appropriate color range (manual or computed) for a variable"""
        if self.should_use_manual_range(index):
            return (self.state.varmin[index], self.state.varmax[index])
        else:
            return self.compute_range(var)

    def update_views_for_timestep(self, fit_viewport=True):
        """Update views for timestep changes.

        Args:
            fit_viewport: Whether to fit viewport after update (default True).
                         Set to False to avoid redundant fits when caller will do it.
        """
        if len(self.registry) == 0:
            return
        data = sm.Fetch(self.source.views["atmosphere_data"])

        first_view = None

        for var, context in self.registry.items():
            varavg = self.compute_average(var, vtkdata=data)
            # Directly set average in trame state
            self.state.varaverage[context.index] = varavg
            self.state.dirty("varaverage")

            if not context.override_range:
                context.data_representation.RescaleTransferFunctionToDataRange(
                    False, True
                )
                range = self.compute_range(var=var)
                # Update both context and state
                context.min_value = range[0]
                context.max_value = range[1]
                self.state.varmin[context.index] = range[0]
                self.state.varmax[context.index] = range[1]
                self.state.dirty("varmin")
                self.state.dirty("varmax")

            self.generate_colorbar_image(context.index)

            # Track the first view for camera fitting
            if first_view is None and context.view_proxy:
                first_view = context.view_proxy

        # Only fit the first view since cameras are linked
        if fit_viewport and first_view:
            self.fit_to_viewport(first_view)

    def refresh_view_display(self, context: ViewContext):
        if not self.should_use_manual_range(context.index):
            context.data_representation.RescaleTransferFunctionToDataRange(False, True)

        if context.view_proxy:
            Render(context.view_proxy)
            # ResetCamera(rview)

    def configure_new_view(self, var, context: ViewContext, sources):
        rview = context.view_proxy

        # Update unique sources to all render views
        data = sources["atmosphere_data"]
        rep = Show(data, rview)
        context.data_representation = rep
        ColorBy(rep, ("CELLS", var))

        # Use context configuration if available, fallback to state
        colormap = (
            context.colormap
            if context.colormap
            else (
                self.state.varcolor[context.index]
                if context.index < len(self.state.varcolor)
                else "Cool to Warm"
            )
        )

        coltrfunc = GetColorTransferFunction(var)
        coltrfunc.ApplyPreset(colormap, True)
        coltrfunc.NanOpacity = 0.0

        # Apply log scale if configured
        if context.use_log_scale:
            coltrfunc.MapControlPointsToLogSpace()
            coltrfunc.UseLogScale = 1

        # Apply inversion if configured
        if context.invert_colors:
            coltrfunc.InvertTransferFunction()

        # Ensure the color transfer function is scaled to the data range
        if not context.override_range:
            rep.RescaleTransferFunctionToDataRange(False, True)
        else:
            if context.min_value is not None and context.max_value is not None:
                coltrfunc.RescaleTransferFunction(context.min_value, context.max_value)

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

        # Skip individual fit - will be handled by view0 after all views are created
        Render(rview)

    # This function is no longer needed - we work directly with state arrays

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

        # Use context configuration
        colormap = (
            context.colormap
            if context.colormap
            else (
                self.state.varcolor[index]
                if index < len(self.state.varcolor)
                else "Cool to Warm"
            )
        )
        invert = context.invert_colors

        # Get cached colorbar image based on colormap and invert status
        try:
            image_data = get_cached_colorbar_image(colormap, invert)
            # Update state with the cached image
            self.state.colorbar_images[index] = image_data
            self.state.dirty("colorbar_images")
        except Exception as e:
            print(f"Error getting cached colorbar image for {var}: {e}")

    def fit_to_viewport(self, view, margin=DEFAULT_MARGIN, use_largest_viewport=False):
        """
        Reset camera to fit objects in viewport.

        Args:
            view: The render view to fit
            margin: Not used (kept for compatibility)
            use_largest_viewport: Not used (kept for compatibility)
        """
        from paraview.simple import SetActiveView

        try:
            # Set this view as active and reset camera
            SetActiveView(view)
            view.ResetCamera(True, 0.9)

        except Exception as e:
            print(f"Error in fit_to_viewport: {e}")

    def reset_camera(self, **kwargs):
        """Reset camera for all views to optimally fit objects."""
        # Only reset the first view since cameras are linked
        if len(self.widgets) > 0 and len(self.state.variables) > 0:
            var = self.state.variables[0]
            context = self.registry.get_view(var)
            if context and context.view_proxy:
                self.fit_to_viewport(context.view_proxy)
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

        # Check if area variable exists for weighted averaging
        area_array = vtkdata.GetCellData().GetArray("area")

        # Use utility function for calculation
        return calculate_weighted_average(vardata, area_array)

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
        self.to_delete.extend([self.registry.get_view(x).view_proxy for x in to_delete])

        # Remove deselected variables from registry to free memory
        for var in to_delete:
            self.registry.remove_view(var)

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
                # Default grid position
                x = int(index % DEFAULT_GRID_COLUMNS) * DEFAULT_GRID_WIDTH
                y = int(index / DEFAULT_GRID_COLUMNS) * DEFAULT_GRID_HEIGHT
                wdt = DEFAULT_GRID_WIDTH
                hgt = DEFAULT_GRID_HEIGHT

            varrange = self.compute_range(var, vtkdata=vtkdata)
            varavg = self.compute_average(var, vtkdata=vtkdata)

            view = None
            context: ViewContext = self.registry.get_view(var)
            if context is not None:
                view = context.view_proxy
                if view is None:
                    view = CreateRenderView()
                    view.UseColorPaletteForBackground = 0
                    view.BackgroundColorMode = "Gradient"
                    view.GetRenderWindow().SetOffScreenRendering(True)
                    context.view_proxy = view

                    # Update context's index to current position
                    context.index = index

                    # Sync min/max values
                    if context.override_range:
                        # Use context's saved values
                        self.state.varmin[index] = (
                            context.min_value
                            if context.min_value is not None
                            else varrange[0]
                        )
                        self.state.varmax[index] = (
                            context.max_value
                            if context.max_value is not None
                            else varrange[1]
                        )
                    else:
                        # Use computed range and update context
                        context.min_value = varrange[0]
                        context.max_value = varrange[1]
                        self.state.varmin[index] = varrange[0]
                        self.state.varmax[index] = varrange[1]

                    self.configure_new_view(var, context, self.source.views)
                else:
                    self.refresh_view_display(context)
                    # Skip individual viewport fitting - will be done once for view0
            else:
                view = CreateRenderView()
                view.UseColorPaletteForBackground = 0
                view.BackgroundColorMode = "Gradient"
                view.GetRenderWindow().SetOffScreenRendering(True)

                # Create new context
                context = ViewContext(var, index)
                context.view_proxy = view

                # Copy configuration from state arrays (already restored)
                context.colormap = (
                    state.varcolor[index] if index < len(state.varcolor) else None
                )
                context.use_log_scale = (
                    state.uselogscale[index]
                    if index < len(state.uselogscale)
                    else False
                )
                context.invert_colors = (
                    state.invert[index] if index < len(state.invert) else False
                )
                context.override_range = (
                    state.override_range[index]
                    if index < len(state.override_range)
                    else False
                )

                # Set min/max based on override flag
                if context.override_range:
                    # Use saved min/max from state
                    context.min_value = (
                        state.varmin[index]
                        if index < len(state.varmin)
                        else varrange[0]
                    )
                    context.max_value = (
                        state.varmax[index]
                        if index < len(state.varmax)
                        else varrange[1]
                    )
                    self.state.varmin[index] = context.min_value
                    self.state.varmax[index] = context.max_value
                else:
                    # Use computed range
                    context.min_value = varrange[0]
                    context.max_value = varrange[1]
                    self.state.varmin[index] = varrange[0]
                    self.state.varmax[index] = varrange[1]

                # Mark as configured if it has non-default values
                if (
                    context.colormap
                    or context.use_log_scale
                    or context.invert_colors
                    or context.override_range
                ):
                    context.has_been_configured = True

                # Register the view
                self.registry.register_view(var, context)

                self.configure_new_view(var, context, self.source.views)
            context.index = index
            # Set the computed average directly in trame state
            self.state.varaverage[index] = varavg
            self.state.dirty("varaverage")
            # No need to sync - we're already working with state arrays
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

        # Only fit view0 since all cameras are linked
        if view0 is not None:
            self.fit_to_viewport(view0)

        self.state.views = sWidgets
        self.state.layout = layout
        self.state.dirty("views")
        self.state.dirty("layout")

        # Single render after all updates
        self.render_all_views()

    """
    async def flushViews(self):
        await self.server.network_completion
        self.render_all_views()
        import asyncio
        await asyncio.sleep(1)
        self.render_all_views()
    """

    def update_colormap(self, index, value):
        """Update the colormap for a variable."""
        var = self.state.variables[index]
        context = self.registry.get_view(var)
        if not context:
            return

        coltrfunc = GetColorTransferFunction(var)

        # Persist to context
        context.colormap = value
        context.has_been_configured = True

        # Update state for UI
        self.state.varcolor[index] = value
        self.state.dirty("varcolor")

        # Apply the preset
        coltrfunc.ApplyPreset(value, True)
        # Reapply inversion if it was enabled
        if context.invert_colors:
            coltrfunc.InvertTransferFunction()

        # Generate new colorbar image with updated colormap
        self.generate_colorbar_image(index)
        self.render_view_by_index(index)

    def update_log_scale(self, index, value):
        """Update the log scale setting for a variable."""
        var = self.state.variables[index]
        context = self.registry.get_view(var)
        if not context:
            return

        coltrfunc = GetColorTransferFunction(var)

        # Persist to context
        context.use_log_scale = value
        context.has_been_configured = True

        # Update state for UI
        self.state.uselogscale[index] = value
        self.state.dirty("uselogscale")

        if value:
            coltrfunc.MapControlPointsToLogSpace()
            coltrfunc.UseLogScale = 1
        else:
            coltrfunc.MapControlPointsToLinearSpace()
            coltrfunc.UseLogScale = 0
        # Note: We don't regenerate the colorbar image here because the color gradient
        # itself doesn't change with log scale - only the data mapping changes.
        # The colorbar always shows a linear color progression.

        self.render_view_by_index(index)

    def update_invert_colors(self, index, value):
        """Update the color inversion setting for a variable."""
        var = self.state.variables[index]
        context = self.registry.get_view(var)
        if not context:
            return

        coltrfunc = GetColorTransferFunction(var)

        # Persist to context
        context.invert_colors = value
        context.has_been_configured = True

        # Update state for UI
        self.state.invert[index] = value
        self.state.dirty("invert")

        coltrfunc.InvertTransferFunction()
        # Generate new colorbar image when colors are inverted
        self.generate_colorbar_image(index)

        self.render_view_by_index(index)

    def update_scalar_bars(self, event=None):
        # Always hide ParaView scalar bars - using custom HTML colorbar
        # The HTML colorbar is always visible, no toggle needed
        for _, context in self.registry.items():
            view = context.view_proxy
            if context.data_representation:
                context.data_representation.SetScalarBarVisibility(view, False)
        self.render_all_views()

    def set_manual_color_range(self, index, min, max):
        var = self.state.variables[index]
        context = self.registry.get_view(var)
        if not context:
            return

        # Persist to context
        context.override_range = True
        context.min_value = float(min)
        context.max_value = float(max)
        context.has_been_configured = True

        # Update state for UI
        self.state.override_range[index] = True
        self.state.varmin[index] = float(min)
        self.state.varmax[index] = float(max)
        self.state.dirty("override_range")
        self.state.dirty("varmin")
        self.state.dirty("varmax")

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
        if not context:
            return

        # Persist to context
        context.override_range = False
        context.min_value = varrange[0]
        context.max_value = varrange[1]
        context.has_been_configured = True

        # Update state for UI
        self.state.override_range[index] = False
        self.state.varmin[index] = varrange[0]
        self.state.varmax[index] = varrange[1]
        self.state.dirty("override_range")
        self.state.dirty("varmin")
        self.state.dirty("varmax")

        # Rescale transfer function to data range
        if context.data_representation:
            context.data_representation.RescaleTransferFunctionToDataRange(False, True)
        # Note: colorbar image doesn't change with range, only data mapping changes
        self.render_all_views()

    def zoom_in(self, index=0):
        var = self.state.variables[index]
        context: ViewContext = self.registry.get_view(var)
        if context and context.view_proxy:
            context.view_proxy.CameraParallelScale *= ZOOM_IN_FACTOR
        self.render_all_views()

    def zoom_out(self, index=0):
        var = self.state.variables[index]
        context: ViewContext = self.registry.get_view(var)
        if context and context.view_proxy:
            context.view_proxy.CameraParallelScale *= ZOOM_OUT_FACTOR
        self.render_all_views()

    def pan_camera(self, dir, factor, index=0):
        var = self.state.variables[index]
        context: ViewContext = self.registry.get_view(var)
        if not context or not context.view_proxy:
            return

        rview = context.view_proxy
        extents = self.source.moveextents
        move = (
            (extents[1] - extents[0]) * PAN_OFFSET_RATIO,
            (extents[3] - extents[2]) * PAN_OFFSET_RATIO,
            (extents[5] - extents[4]) * PAN_OFFSET_RATIO,
        )

        pos = rview.CameraPosition
        foc = rview.CameraFocalPoint
        pos[dir] += move[dir] if factor > 0 else -move[dir]
        foc[dir] += move[dir] if factor > 0 else -move[dir]
        rview.CameraPosition = pos
        rview.CameraFocalPoint = foc
        self.render_all_views()

from trame.widgets import grid
from trame.widgets import vuetify as v2, html, client
from e3sm_quickview.ui.view_settings import ViewProperties
from datetime import datetime
from paraview.simple import SaveScreenshot
from paraview.simple import GetColorTransferFunction
from e3sm_quickview.utils.color import (
    create_vertical_scalar_bar,
    get_lut_from_color_transfer_function,
)
from PIL import Image
import tempfile
import os
import io

from trame.decorators import trigger, TrameApp, task


@TrameApp()
class Grid:
    @property
    def state(self):
        return self.server.state

    @property
    def ctrl(self):
        return self.server.controller

    @trigger("save_screenshot")
    def save_screenshot(self, index):
        """Generate and return screenshot data for browser download."""
        # Get the variable name and view
        var = self.state.variables[index]
        context = self.viewmanager.registry.get_view(var)
        if context is None or context.state.view_proxy is None:
            print(f"No view found for variable {var}")
            return None

        view = context.state.view_proxy

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"quickview_{var}_{timestamp}.png"

        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            tmp_path = tmp_file.name
        try:
            # Save main screenshot to temp file
            SaveScreenshot(tmp_path, view)  # , ImageResolution=[800, 600])
            # Read the original screenshot from ParaView
            main_image = Image.open(tmp_path)
            # Get log scale setting for label formatting
            use_log = self.state.uselogscale[index]

            # Create vertical scalar bar configuration
            class ScalarBarConfig:
                def __init__(self):
                    self.scalar_bar_num_labels = 7
                    self.scalar_bar_title = None  # Could set to var name if desired
                    self.scalar_bar_title_font_size = 14
                    self.scalar_bar_label_font_size = 12
                    if use_log:
                        self.scalar_bar_label_format = "%.1e"
                    else:
                        self.scalar_bar_label_format = "%.2f"

            # Get the actual ParaView color transfer function being used for this variable
            # This ensures we get the exact colormap that's displayed in the view
            paraview_lut = GetColorTransferFunction(var)

            # The color transfer function is already configured with the correct
            # colormap, inversion, log scale, and range from the view, so we don't
            # need to modify it - just use it as is

            # Convert to VTK lookup table
            vtk_lut = get_lut_from_color_transfer_function(paraview_lut, num_colors=256)

            # Create config
            config = ScalarBarConfig()
            config.scalar_bar_title = var
            # Calculate colorbar width as 10% of main image width
            colorbar_width = int(main_image.width * 0.15)

            # Create vertical scalar bar with same height as main image
            colorbar_image = create_vertical_scalar_bar(
                vtk_lut, colorbar_width, main_image.height, config
            )

            # Create extended image by combining original screenshot with scalar bar
            # No artificial backgrounds - just extend the original image
            composite_width = main_image.width + colorbar_image.width
            composite = Image.new(
                main_image.mode,  # Use same mode as original image
                (composite_width, main_image.height),
                color=(255, 255, 255)
                if main_image.mode == "RGB"
                else (255, 255, 255, 255),
            )

            # Paste original screenshot and vertical colorbar
            composite.paste(main_image, (0, 0))
            # Paste the colorbar with gradient background (no alpha mask needed)
            composite.paste(colorbar_image, (main_image.width, 0))

            # Save composite to bytes
            output = io.BytesIO()
            composite.save(output, format="PNG")
            composite_bytes = output.getvalue()

            # Store filename in state for the download button to use
            self.state.screenshot_filename = filename

            # Return the binary data as an attachment
            return self.server.protocol.addAttachment(composite_bytes)
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    @trigger("save_screenshot_tauri")
    @task
    async def save_screenshot_tauri(self, index):
        os.write(1, "Executing Tauri!!!!".encode())
        """Generate screenshot and save to file using Tauri file dialog."""
        # Get the variable name and view
        var = self.state.variables[index]
        context = self.viewmanager.registry.get_view(var)
        if context is None or context.state.view_proxy is None:
            print(f"No view found for variable {var}")
            return None

        view = context.state.view_proxy

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"quickview_{var}_{timestamp}.png"

        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            # Save main screenshot to temp file
            SaveScreenshot(tmp_path, view)

            # Read the original screenshot from ParaView
            main_image = Image.open(tmp_path)

            # Get log scale setting for label formatting
            use_log = self.state.uselogscale[index]

            # Create vertical scalar bar configuration
            class ScalarBarConfig:
                def __init__(self):
                    self.scalar_bar_num_labels = 7
                    self.scalar_bar_title = None
                    self.scalar_bar_title_font_size = 14
                    self.scalar_bar_label_font_size = 12
                    if use_log:
                        self.scalar_bar_label_format = "%.1e"
                    else:
                        self.scalar_bar_label_format = "%.2f"

            # Get the actual ParaView color transfer function being used for this variable
            paraview_lut = GetColorTransferFunction(var)

            # Convert to VTK lookup table
            vtk_lut = get_lut_from_color_transfer_function(paraview_lut, num_colors=256)

            # Create config
            config = ScalarBarConfig()
            config.scalar_bar_title = var

            # Calculate colorbar width as 15% of main image width
            colorbar_width = int(main_image.width * 0.15)

            # Create vertical scalar bar with same height as main image
            colorbar_image = create_vertical_scalar_bar(
                vtk_lut, colorbar_width, main_image.height, config
            )

            # Create extended image by combining original screenshot with scalar bar
            composite_width = main_image.width + colorbar_image.width
            composite = Image.new(
                main_image.mode,
                (composite_width, main_image.height),
                color=(255, 255, 255)
                if main_image.mode == "RGB"
                else (255, 255, 255, 255),
            )

            # Paste original screenshot and vertical colorbar
            composite.paste(main_image, (0, 0))
            composite.paste(colorbar_image, (main_image.width, 0))

            # Use Tauri's save dialog to get the save location
            with self.state as state:
                if state.tauri_avail:
                    # Open save dialog with suggested filename
                    response = await self.ctrl.save(f"Save Screenshot - {filename}")
                    if response:
                        # Save the composite image to the selected location
                        composite.save(response, format="PNG")
                        print(f"Screenshot saved to: {response}")
                        return {"success": True, "path": response}
                else:
                    print("Tauri is not available")
                    return {"success": False, "error": "Tauri not available"}

        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def update_colormap(self, index, value):
        """Update the colormap for a variable."""
        self.viewmanager.update_colormap(index, value)

    def update_log_scale(self, index, value):
        """Update the log scale setting for a variable."""
        self.viewmanager.update_log_scale(index, value)

    def update_invert_colors(self, index, value):
        """Update the color inversion setting for a variable."""
        self.viewmanager.update_invert_colors(index, value)

    def set_manual_color_range(self, index, type, value):
        # Get current values from state to handle min/max independently
        min_val = self.state.varmin[index] if type.lower() == "max" else value
        max_val = self.state.varmax[index] if type.lower() == "min" else value
        # Delegate to view manager which will update both the view and sync state
        self.viewmanager.set_manual_color_range(index, min_val, max_val)

    def revert_to_auto_color_range(self, index):
        self.viewmanager.revert_to_auto_color_range(index)

    def __init__(
        self,
        server,
        view_manager=None,
        close_view=None,
    ):
        self.server = server
        self.viewmanager = view_manager

        with grid.GridLayout(
            layout=("layout",),
            col_num=12,
            row_height=100,
            is_draggable=True,
            is_resizable=True,
            vertical_compact=True,
            layout_updated="layout = $event; trigger('layout_changed', [$event])",
        ) as self.grid:
            with grid.GridItem(
                v_for="vref, idx in views",
                key="vref",
                v_bind=("layout[idx]",),
                style="transition-property: none;",
            ):
                with v2.VCard(classes="fill-height", style="overflow: hidden;"):
                    with v2.VCardText(
                        style="height: calc(100% - 0.66rem); position: relative;",
                        classes="pa-0",
                    ) as cardcontent:
                        # VTK View fills entire space
                        cardcontent.add_child(
                            """
                            <vtk-remote-view :ref="(el) => ($refs[vref] = el)" :viewId="get(`${vref}Id`)" class="pa-0 drag-ignore" style="width: 100%; height: 100%;" interactiveRatio="1" >
                            </vtk-remote-view>
                            """,
                        )
                        client.ClientTriggers(
                            beforeDestroy="trigger('view_gc', [vref])",
                            # mounted=(self.viewmanager.reset_specific_view, '''[idx,
                            #         {width: $refs[vref].vtkContainer.getBoundingClientRect().width,
                            #         height: $refs[vref].vtkContainer.getBoundingClientRect().height}]
                            #         ''')
                        )
                        # Mask to prevent VTK view from getting scroll/mouse events
                        html.Div(
                            style="position:absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 1;"
                        )
                        # Top-left info: time, level, variable name and average
                        with html.Div(
                            style="position: absolute; top: 8px; left: 8px; padding: 4px 8px; background-color: rgba(255, 255, 255, 0.1); color: white; font-size: 0.875rem; border-radius: 4px; z-index: 2;",
                            classes="drag-ignore font-monospace",
                        ):
                            # Variable name
                            html.Div(
                                "{{ variables[idx] }}",
                                style="color: white;",
                                classes="font-weight-medium",
                            )
                            # Average value
                            html.Div(
                                (
                                    "(avg: {{ "
                                    "varaverage[idx] !== null && varaverage[idx] !== undefined && !isNaN(varaverage[idx]) && typeof varaverage[idx] === 'number' ? "
                                    "varaverage[idx].toExponential(2) : "
                                    "'N/A' "
                                    "}})"
                                ),
                                style="color: white;",
                                classes="font-weight-medium",
                            )
                            # Show time
                            html.Div(
                                "t = {{ tstamp }}",
                                style="color: white;",
                                classes="font-weight-medium",
                            )
                            # Show level for midpoint variables
                            html.Div(
                                v_if="midpoint_vars.includes(variables[idx])",
                                children="k = {{ midpoint }}",
                                style="color: white;",
                                classes="font-weight-medium",
                            )
                            # Show level for interface variables
                            html.Div(
                                v_if="interface_vars.includes(variables[idx])",
                                children="k = {{ interface }}",
                                style="color: white;",
                                classes="font-weight-medium",
                            )
                        # Colorbar container (horizontal layout at bottom)
                        with html.Div(
                            style="position: absolute; bottom: 8px; left: 8px; right: 8px; display: flex; align-items: center; justify-content: center; padding: 4px 8px 4px 8px; background-color: rgba(255, 255, 255, 0.1); height: 28px; z-index: 3; overflow: visible; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);",
                            classes="drag-ignore",
                        ):
                            # View Properties button (small icon)
                            ViewProperties(
                                update_colormap=self.update_colormap,
                                update_log_scale=self.update_log_scale,
                                update_invert=self.update_invert_colors,
                                update_range=self.set_manual_color_range,
                                reset=self.revert_to_auto_color_range,
                                style="margin-right: 8px; display: flex; align-items: center;",
                            )
                            # Color min value
                            html.Span(
                                (
                                    "{{ "
                                    "varmin[idx] !== null && varmin[idx] !== undefined && !isNaN(varmin[idx]) && typeof varmin[idx] === 'number' ? ("
                                    "uselogscale[idx] && varmin[idx] > 0 ? "
                                    "'10^(' + Math.log10(varmin[idx]).toFixed(1) + ')' : "
                                    "varmin[idx].toExponential(1)"
                                    ") : 'Auto' "
                                    "}}"
                                ),
                                style="color: white;",
                                classes="font-weight-medium",
                            )
                            # Colorbar
                            with html.Div(
                                style="flex: 1; display: flex; align-items: center; margin: 0 8px; height: 0.6rem; position: relative;",
                                classes="drag-ignore",
                            ):
                                # Colorbar image
                                html.Img(
                                    src=(
                                        "colorbar_images[idx] || 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='",
                                        None,
                                    ),
                                    style="height: 100%; width: 100%; object-fit: fill;",
                                    classes="rounded-lg border-thin",
                                    v_on=(
                                        "{"
                                        "mousemove: (e) => { "
                                        "const rect = e.target.getBoundingClientRect(); "
                                        "const x = e.clientX - rect.left; "
                                        "const width = rect.width; "
                                        "const fraction = Math.max(0, Math.min(1, x / width)); "
                                        "probe_location = [x, width, fraction, idx]; "
                                        "}, "
                                        "mouseenter: () => { probe_enabled = true; }, "
                                        "mouseleave: () => { probe_enabled = false; probe_location = null; } "
                                        "}"
                                    ),
                                )
                                # Probe tooltip (pan3d style - as sibling to colorbar)
                                html.Div(
                                    v_if="probe_enabled && probe_location && probe_location[3] === idx",
                                    v_bind_style="{position: 'absolute', bottom: '100%', left: probe_location[0] + 'px', transform: 'translateX(-50%)', marginBottom: '0.25rem', backgroundColor: '#000000', color: '#ffffff', padding: '0.25rem 0.5rem', borderRadius: '0.25rem', fontSize: '0.875rem', whiteSpace: 'nowrap', pointerEvents: 'none', zIndex: 1000, fontFamily: 'monospace', boxShadow: '0 2px 4px rgba(0,0,0,0.3)'}",
                                    children=(
                                        "{{ "
                                        "probe_location && varmin[idx] !== null && varmax[idx] !== null ? ("
                                        "uselogscale[idx] && varmin[idx] > 0 && varmax[idx] > 0 ? "
                                        "'10^(' + ("
                                        "Math.log10(varmin[idx]) + "
                                        "(Math.log10(varmax[idx]) - Math.log10(varmin[idx])) * probe_location[2]"
                                        ").toFixed(2) + ')' : "
                                        "((varmin[idx] || 0) + ((varmax[idx] || 1) - (varmin[idx] || 0)) * probe_location[2]).toExponential(3)"
                                        ") : '' "
                                        "}}"
                                    ),
                                )
                            # Color max value
                            html.Span(
                                (
                                    "{{ "
                                    "varmax[idx] !== null && varmax[idx] !== undefined && !isNaN(varmax[idx]) && typeof varmax[idx] === 'number' ? ("
                                    "uselogscale[idx] && varmax[idx] > 0 ? "
                                    "'10^(' + Math.log10(varmax[idx]).toFixed(1) + ')' : "
                                    "varmax[idx].toExponential(1)"
                                    ") : 'Auto' "
                                    "}}"
                                ),
                                style="color: white;",
                                classes="font-weight-medium",
                            )
                    # Action buttons container (download and close)
                    with html.Div(
                        style="position: absolute; top: 8px; right: 8px; display: flex; gap: 4px; z-index: 2;",
                        classes="drag-ignore",
                    ):
                        # Download screenshot button with tooltip
                        with v2.VTooltip(bottom=True):
                            with html.Template(v_slot_activator="{ on, attrs }"):
                                with v2.VBtn(
                                    icon=True,
                                    style="color: white; background-color: rgba(255, 255, 255, 0.1);",
                                    click="tauri_avail ? trigger('save_screenshot_tauri', [idx]) : utils.download(`quickview_${variables[idx]}_${Date.now()}.png`, trigger('save_screenshot', [idx]), 'image/png')",
                                    classes="ma-0",
                                    v_bind="attrs",
                                    v_on="on",
                                ):
                                    v2.VIcon("mdi-file-download", small=True)
                            html.Span("Save Screenshot")

                        # Close view button with tooltip
                        with v2.VTooltip(bottom=True):
                            with html.Template(v_slot_activator="{ on, attrs }"):
                                with v2.VBtn(
                                    icon=True,
                                    style="color: white; background-color: rgba(255, 255, 255, 0.1);",
                                    click=(close_view, "[idx]"),
                                    classes="ma-0",
                                    v_bind="attrs",
                                    v_on="on",
                                ):
                                    v2.VIcon("mdi-close", small=True)
                            html.Span("Close View")

        pass

from trame.decorators import TrameApp, task
from trame.widgets import html, vuetify2 as v2
from e3sm_quickview.ui.view_settings import ViewControls

import json


@TrameApp()
class Toolbar:
    @task
    async def select_data_file(self):
        with self.state as state:
            if state.tauri_avail:
                response = await self.ctrl.open("Open Data File")
                self.state.data_file = response
                self.state.pipeline_valid = False
            else:
                print("Tauri unavailable")

    def update_colormap(self, index, value):
        """Update the colormap for a variable."""
        self.viewmanager.update_colormap(index, value)

    def update_log_scale(self, index, value):
        """Update the log scale setting for a variable."""
        self.viewmanager.update_log_scale(index, value)

    def update_invert_colors(self, index, value):
        """Update the color inversion setting for a variable."""
        self.viewmanager.update_invert_colors(index, value)

    @task
    async def select_connectivity_file(self):
        with self.state as state:
            if state.tauri_avail:
                response = await self.ctrl.open("Open Connectivity File")
                self.state.conn_file = response
                self.state.pipeline_valid = False
            else:
                print("Tauri unavailable")

    @task
    async def export_state(self):
        # Small delay to ensure client state is synchronized
        import asyncio

        await asyncio.sleep(0.1)

        if self._generate_state is not None:
            config = self._generate_state()
        with self.state as state:
            if state.tauri_avail:
                response = await self.ctrl.save("Export State")
                export_path = response
                with open(export_path, "w") as file:
                    json.dump(config, file, indent=4)
            else:
                print("Tauri unavailable")

    @task
    async def import_state(self):
        with self.state as state:
            if state.tauri_avail:
                response = await self.ctrl.open("Import State", filter=["json"])
                import_path = response
                if self._load_state is not None:
                    self._load_state(import_path)
            else:
                print("Tauri unavailable")

    @property
    def state(self):
        return self.server.state

    @property
    def ctrl(self):
        return self.server.controller

    def _handle_cvd_toggle(self):
        """Handle CVD-friendly colors toggle button click"""
        with self.state:
            # Toggle CVD colors, but ensure at least one option is selected
            if not self.state.use_cvd_colors or self.state.use_standard_colors:
                self.state.use_cvd_colors = not self.state.use_cvd_colors
            self._update_color_maps()

    def _handle_standard_toggle(self):
        """Handle standard colors toggle button click"""
        with self.state:
            # Toggle standard colors, but ensure at least one option is selected
            if not self.state.use_standard_colors or self.state.use_cvd_colors:
                self.state.use_standard_colors = not self.state.use_standard_colors
            self._update_color_maps()

    def _update_color_maps(self):
        """Update the available color maps based on toggle states"""
        if self._update_available_color_maps is not None:
            # Directly call update_available_color_maps without parameters
            self._update_available_color_maps()

    def __init__(
        self,
        layout_toolbar,
        server,
        load_data=None,
        load_state=None,
        load_variables=None,
        update_available_color_maps=None,
        generate_state=None,
        zoom=None,
        move=None,
        **kwargs,
    ):
        self.server = server

        self._generate_state = generate_state
        self._load_state = load_state
        self._update_available_color_maps = update_available_color_maps

        # Set initial color maps based on default toggle states
        self._update_color_maps()

        with layout_toolbar as toolbar:
            toolbar.density = "compact"
            toolbar.style = "overflow-x: auto; overflow-y: hidden;"
            with html.Div(
                style="min-width: 32px; flex-shrink: 0; display: flex; align-items: center; justify-content: center;"
            ):
                v2.VProgressCircular(
                    bg_color="rgba(0,0,0,0)",
                    indeterminate=("trame__busy",),
                    color="primary",
                    size=24,
                )
            v2.VDivider(vertical=True, classes="mx-2")
            v2.VBtn(
                "Load Variables",
                classes="ma-2",
                color="primary",
                dense=True,
                # flat=True,
                tonal=True,
                small=True,
                click=load_variables,
                style="background-color: lightgray;",  # width: 200px; height: 50px;",
            )
            v2.VSpacer()
            v2.VDivider(vertical=True, classes="mx-2")
            # Color options toggle buttons group
            with v2.VCard(
                flat=True,
                classes="d-flex align-center px-2 py-1 mx-1",
                style="background-color: #f5f5f5; border-radius: 4px; flex-shrink: 0;",
            ):
                with v2.VTooltip(bottom=True):
                    with html.Template(v_slot_activator="{ on, attrs }"):
                        with v2.VBtn(
                            icon=True,
                            dense=True,
                            small=True,
                            v_bind="attrs",
                            v_on="on",
                            click=self._handle_cvd_toggle,
                            color=("use_cvd_colors ? 'primary' : ''",),
                            classes="mx-1",
                        ):
                            v2.VIcon("mdi-eye-check-outline")
                    html.Span("CVD-friendly colors")
                with v2.VTooltip(bottom=True):
                    with html.Template(v_slot_activator="{ on, attrs }"):
                        with v2.VBtn(
                            icon=True,
                            dense=True,
                            small=True,
                            v_bind="attrs",
                            v_on="on",
                            click=self._handle_standard_toggle,
                            color=("use_standard_colors ? 'primary' : ''",),
                            classes="mx-1",
                        ):
                            v2.VIcon("mdi-palette")
                    html.Span("Standard colors")
            v2.VDivider(vertical=True, classes="mx-2")
            with v2.VCard(
                flat=True,
                classes="d-flex align-center px-2 py-1 mx-1",
                style="background-color: #f5f5f5; border-radius: 4px; min-width: 35%; flex-shrink: 1;",
            ):
                with v2.VTooltip(bottom=True):
                    with html.Template(v_slot_activator="{ on, attrs }"):
                        v2.VTextField(
                            prepend_icon="mdi-vector-rectangle",
                            placeholder="Connectivity",
                            v_model=("conn_file", ""),
                            hide_details=True,
                            dense=True,
                            append_icon="mdi-folder-upload",
                            click_append=self.select_connectivity_file,
                            filled=True,
                            background_color="white",
                            classes="mr-2",
                            style="max-width: 48%;",
                            v_bind="attrs",
                            v_on="on",
                        )
                    html.Span("Connectivity file (SCRIP format .nc file)")
                with v2.VTooltip(bottom=True):
                    with html.Template(v_slot_activator="{ on, attrs }"):
                        v2.VTextField(
                            prepend_icon="mdi-database",
                            placeholder="Data File",
                            v_model=("data_file", ""),
                            hide_details=True,
                            dense=True,
                            append_icon="mdi-folder-upload",
                            click_append=self.select_data_file,
                            filled=True,
                            background_color="white",
                            style="max-width: 48%;",
                            v_bind="attrs",
                            v_on="on",
                        )
                    html.Span("EAM simulation output (.nc file)")
                with v2.VTooltip(bottom=True):
                    with html.Template(v_slot_activator="{ on, attrs }"):
                        with v2.VBtn(
                            icon=True,
                            dense=True,
                            flat=True,
                            small=True,
                            click=load_data,
                            color=("!pipeline_valid ? 'primary' : 'secondary'",),
                            v_bind="attrs",
                            v_on="on",
                        ):
                            v2.VIcon("mdi-file-check")
                    html.Span("Load Files")
                with v2.VTooltip(bottom=True):
                    with html.Template(v_slot_activator="{ on, attrs }"):
                        with v2.VBtn(
                            icon=True,
                            dense=True,
                            flat=True,
                            small=True,
                            click=self.export_state,
                            v_bind="attrs",
                            v_on="on",
                            classes="mx-1",
                        ):
                            v2.VIcon("mdi-download")
                    html.Span("Save State")
                with v2.VTooltip(bottom=True):
                    with html.Template(v_slot_activator="{ on, attrs }"):
                        with v2.VBtn(
                            icon=True,
                            dense=True,
                            flat=True,
                            small=True,
                            click=self.import_state,
                            v_bind="attrs",
                            v_on="on",
                            classes="mx-1",
                        ):
                            v2.VIcon("mdi-upload")
                    html.Span("Load State")
                with v2.VTooltip(bottom=True):
                    with html.Template(v_slot_activator="{ on, attrs }"):
                        with v2.VBtn(
                            icon=True,
                            dense=True,
                            flat=True,
                            small=True,
                            v_bind="attrs",
                            v_on="on",
                        ):
                            v2.VIcon(
                                v_if="pipeline_valid",
                                children=["mdi-check-circle-outline"],
                                color="green",
                            )
                            v2.VIcon(
                                v_if="!pipeline_valid",
                                children=["mdi-alert-circle-outline"],
                                color="red",
                            )
                    with html.Div(v_if="pipeline_valid"):
                        html.Span("Pipeline Valid")
                    with html.Div(v_if="!pipeline_valid"):
                        html.Span("Pipeline Invalid")
            v2.VDivider(vertical=True, classes="mx-2")
            ViewControls(
                zoom=zoom,
                move=move,
                style="flex-shrink: 0;",
            )
            with v2.VTooltip(bottom=True):
                with html.Template(v_slot_activator="{ on, attrs }"):
                    with v2.VBtn(
                        icon=True,
                        v_bind="attrs",
                        v_on="on",
                        click=self.ctrl.view_reset_camera,
                    ):
                        v2.VIcon("mdi-restore")
                html.Span("Reset View Cameras")

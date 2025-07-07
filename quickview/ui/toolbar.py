from trame.decorators import TrameApp, task
from trame.widgets import html, vuetify2 as v2, tauri

import json


@TrameApp()
class Toolbar:
    @task
    async def select_data_file(self):
        print("Selecting data file : ", self.ctrl.open)
        with self.state:
            response = await self.ctrl.open("Open Data File")
            self.state.data_file = response

    @task
    async def select_connectivity_file(self):
        print("Selecting connectivity file : ", self.ctrl.open)
        with self.state:
            response = await self.ctrl.open("Open Connectivity File")
            self.state.conn_file = response

    @task
    async def export_state(self):
        print("Exporting state!!!!")
        if self._generate_state is not None:
            config = self._generate_state()
        with self.state:
            response = await self.ctrl.save("Export State")
            export_path = response
            with open(export_path, "w") as file:
                json.dump(config, file, indent=4)

    @task
    async def import_state(self):
        print("Importing state")
        with self.state:
            response = await self.ctrl.open("Import State", filter=["json"])
            import_path = response
            if self._load_state is not None:
                self._load_state(import_path)

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

    def _handle_color_bar_toggle(self):
        """Toggle the color bar visibility"""
        with self.state:
            self.state.show_color_bar = not self.state.show_color_bar
            if self._update_scalar_bars is not None:
                self._update_scalar_bars(self.state.show_color_bar)

    def __init__(
        self,
        layout_toolbar,
        server,
        load_data=None,
        load_state=None,
        load_variables=None,
        update_available_color_maps=None,
        update_scalar_bars=None,
        generate_state=None,
        **kwargs,
    ):
        self.server = server
        with tauri.Dialog() as dialog:
            self.ctrl.open = dialog.open
            self.ctrl.save = dialog.save
        self._generate_state = generate_state
        self._load_state = load_state
        self._update_available_color_maps = update_available_color_maps
        self._update_scalar_bars = update_scalar_bars

        # Initialize toggle states
        with self.state:
            self.state.use_cvd_colors = False
            self.state.use_standard_colors = True
            self.state.show_color_bar = True

        # Set initial color maps based on default toggle states
        self._update_color_maps()
        
        # Apply initial scalar bar visibility
        if self._update_scalar_bars is not None:
            self._update_scalar_bars(True)

        with layout_toolbar as toolbar:
            toolbar.density = "compact"
            v2.VDivider(vertical=True, classes="mx-2")
            v2.VBtn(
                "Load Variables",
                classes="ma-2",
                dense=True,
                # flat=True,
                tonal=True,
                small=True,
                click=load_variables,
                style="background-color: lightgray;",  # width: 200px; height: 50px;",
            )
            v2.VSpacer()
            v2.VDivider(vertical=True, classes="mx-2")
            # Color options toggle buttons
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
                    ):
                        v2.VIcon("mdi-palette")
                html.Span("Standard colors")
            with v2.VTooltip(bottom=True):
                with html.Template(v_slot_activator="{ on, attrs }"):
                    with v2.VBtn(
                        icon=True,
                        dense=True,
                        small=True,
                        v_bind="attrs",
                        v_on="on",
                        click=self._handle_color_bar_toggle,
                        color=("show_color_bar ? 'primary' : ''",),
                    ):
                        v2.VIcon("mdi-format-color-fill")
                html.Span("Show color bar")
            v2.VDivider(vertical=True, classes="mx-2")
            with v2.VCol(style="width: 25%;", classes="justify-center pa-0"):
                with v2.VRow(
                    no_gutters=True,
                    classes="align-center",
                    style="max-height: 2rem;",
                ):
                    with v2.VCol():
                        v2.VTextField(
                            prepend_icon="mdi-vector-rectangle",
                            placeholder="Connectivity File",
                            v_model=("conn_file", ""),
                            hide_details=True,
                            dense=True,
                            append_icon="mdi-folder-upload",
                            click_append=self.select_connectivity_file,
                        )
                with v2.VRow(
                    no_gutters=True,
                    classes="overflow-x-hidden align-center mr-0",
                    style="max-height: 2rem;",
                ):
                    with v2.VCol():
                        v2.VTextField(
                            prepend_icon="mdi-database",
                            placeholder="Data File",
                            v_model=("data_file", ""),
                            hide_details=True,
                            dense=True,
                            append_icon="mdi-folder-upload",
                            click_append=self.select_data_file,
                        )
            with v2.VTooltip(bottom=True):
                with html.Template(v_slot_activator="{ on, attrs }"):
                    with v2.VBtn(
                        icon=True,
                        dense=True,
                        flat=True,
                        small=True,
                        click=load_data,
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
                        click=load_data,
                        v_bind="attrs",
                        v_on="on",
                    ):
                        v2.VIcon("mdi-swap-horizontal")
                html.Span("Replace Files")
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
                html.Span(
                    f"Pipeline {'Valid' if self.state.pipeline_valid else 'Invalid'}"
                )

            v2.VDivider(vertical=True, classes="mx-2")
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
                    ):
                        v2.VIcon("mdi-upload")
                html.Span("Load State")
            v2.VDivider(vertical=True, classes="mx-2")
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

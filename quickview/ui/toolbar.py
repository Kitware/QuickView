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
            with v2.VMenu(offset_y=True):
                with html.Template(v_slot_activator="{ on: menu, attrs }"):
                    with v2.VTooltip(bottom=True):
                        with html.Template(v_slot_activator="{ on: tooltip, attrs }"):
                            with v2.VBtn(
                                icon=True,
                                dense=True,
                                flat=True,
                                small=True,
                                v_bind="attrs",
                                v_on="{ ...tooltip, ...menu }",
                            ):
                                v2.VIcon("mdi-palette")
                        html.Span("Color Options")
                with v2.VList():
                    with v2.VListItem():
                        v2.VCheckbox(
                            classes="ma-0",
                            label="Use CVD colors",
                            value=0,
                            v_model=("cmaps",),
                            dense=True,
                            hide_details=True,
                            change=(update_available_color_maps, "[$event]"),
                            style="height: 20px;",
                        )
                    with v2.VListItem():
                        v2.VCheckbox(
                            classes="ma-0",
                            label="Use non-CVD colors",
                            value=1,
                            v_model=("cmaps",),
                            dense=True,
                            hide_details=True,
                            change=(update_available_color_maps, "[$event]"),
                            style="height: 20px;",
                        )
                    with v2.VListItem():
                        v2.VCheckbox(
                            classes="ma-0",
                            label="Show Color Bar",
                            value=1,
                            v_model=("scalarbar", False),
                            dense=True,
                            hide_details=True,
                            change=(update_scalar_bars, "[$event]"),
                            style="height: 20px;",
                        )
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

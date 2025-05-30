import os

from trame.decorators import TrameApp, task
from trame.widgets import html, vuetify2 as v2, tauri

from quickview.ui.view_settings import ViewControls
from quickview.ui.file_selection import FileSelect
import json


@TrameApp()
class Toolbar:
    @task
    async def select_data_file(self):
        print("Selecting data file : ", self.ctrl.open)
        with self.state:
            response = await self.ctrl.open("Open Data File")
            print(f"Selected data file: {response}")
            self.state.data_file = response

    @task
    async def select_connectivity_file(self):
        print("Selecting connectivity file : ", self.ctrl.open)
        with self.state:
            response = await self.ctrl.open("Open Connectivity File")
            print(f"Selected connectivity file: {response}")
            self.state.conn_file = response

    @task
    async def export_state(self):
        print("Exporting state!!!!")
        if self.generate_state is not None:
            state = self.generate_state()
            print(state)
        with self.state:
            response = await self.ctrl.save("Export State")
            print(f"Selected export location: {response}")
            export_path = response
            with open(export_path, "w") as file:
                json.dump(state, file, indent=4)

    @task
    async def import_state(self):
        print("Importing state")
        with self.state:
            response = await self.ctrl.open("Import State", filter=["json"])
            print(f"Selected import location: {response}")
            import_path = response

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
        self.generate_state = generate_state

        with layout_toolbar as toolbar:
            toolbar.density = "compact"
            v2.VDivider(vertical=True, classes="mx-2")
            v2.VBtn(
                "Load Variables",
                classes="ma-2",
                click=load_variables,
                style="background-color: lightgray;",  # width: 200px; height: 50px;",
            )
            v2.VSpacer()
            v2.VDivider(vertical=True, classes="mx-2")
            with v2.VListItemGroup(classes="text-truncate", dense=True):
                v2.VCheckbox(
                    classes="ma-0",
                    label="Use CVD colors",
                    value=0,
                    v_model=("cmaps",),
                    dense=True,
                    hide_details=True,
                    change=(update_available_color_maps, "[$event]"),
                    style="height: 20px;",
                ),
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
                    classes="align-center mt-n4",
                    style="max-height: 2rem;",
                ):
                    # with v2.VCol():
                    #    html.Div("Connectivity File")
                    with v2.VCol():
                        v2.VTextField(
                            prepend_icon="mdi-vector-rectangle",
                            placeholder="Connectivity File",
                            v_model=("conn_file", ""),
                            hide_details=True,
                            dense=True,
                            flat=True,
                            variant="solo",
                            reverse=True,
                        )
                    with html.Div(classes="flex-0"):
                        with v2.VBtn(
                            icon=True,
                            size="sm",
                            dense=True,
                            flat=True,
                            variant="outlined",
                            classes="mx-2",
                            click=self.select_connectivity_file,
                        ):
                            v2.VIcon("mdi-folder-upload")
                with v2.VRow(
                    no_gutters=True,
                    classes="align-center mr-0",
                    style="max-height: 2rem;",
                ):
                    # with v2.VCol():
                    #    html.Div("Data File")
                    with v2.VCol():
                        v2.VTextField(
                            prepend_icon="mdi-database",
                            placeholder="Data File",
                            v_model=("data_file", ""),
                            hide_details=True,
                            dense=True,
                            flat=True,
                            variant="solo",
                            reverse=True,
                        )
                    with html.Div(classes="flex-0"):
                        with v2.VBtn(
                            icon=True,
                            size="sm",
                            dense=True,
                            flat=True,
                            variant="outlined",
                            classes="mx-2",
                            click=self.select_data_file,
                        ):
                            v2.VIcon("mdi-folder-upload")

            with html.Div(classes="flex-0"):
                with v2.VTooltip(bottom=True):
                    with html.Template(v_slot_activator="{ on, attrs }"):
                        with v2.VBtn(
                            icon=True,
                            dense=True,
                            flat=True,
                            large=True,
                            classes="mx-2",
                            click=load_data,
                            v_bind="attrs",
                            v_on="on",
                        ):
                            v2.VIcon("mdi-file-check")
                    html.Span(f"Load Files")
                with v2.VTooltip(bottom=True):
                    with html.Template(v_slot_activator="{ on, attrs }"):
                        with v2.VBtn(
                            icon=True,
                            dense=True,
                            flat=True,
                            large=True,
                            classes="mx-2",
                            click=load_data,
                            v_bind="attrs",
                            v_on="on",
                        ):
                            v2.VIcon("mdi-swap-horizontal")
                    html.Span(f"Replace Files")

            v2.VDivider(vertical=True, classes="mx-2")
            with v2.VTooltip(bottom=True):
                with html.Template(v_slot_activator="{ on, attrs }"):
                    with v2.VBtn(
                        icon=True,
                        tile=True,
                        click=self.export_state,
                        v_bind="attrs",
                        v_on="on",
                    ):
                        v2.VIcon("mdi-download")
                html.Span(f"Save State")
            with v2.VTooltip(bottom=True):
                with html.Template(v_slot_activator="{ on, attrs }"):
                    with v2.VBtn(
                        icon=True,
                        tile=True,
                        click=self.import_state,
                        v_bind="attrs",
                        v_on="on",
                    ):
                        v2.VIcon("mdi-upload")
                html.Span(f"Load State")
            with v2.VDialog(v_model=("export_config",), max_width=800):
                with v2.VContainer(
                    fluid=True, classes="d-flex justify-center align-center"
                ):
                    FileSelect()
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
                html.Span(f"Reset View Cameras")

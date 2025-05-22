import os

from trame.decorators import TrameApp, task
from trame.widgets import html, vuetify2 as v2, tauri

from quickview.ui.view_settings import ViewControls
from quickview.ui.file_selection import FileSelect

@TrameApp()
class Toolbar:

    @task
    async def select_data_file(self):
        with self.state:
            response = await self.ctrl.select_file("Open Data File")
            self.state.DataFile = response

    @task
    async def select_connectivity_file(self):
        with self.state:
            response = await self.ctrl.select_file("Open Connectivity File")
            self.state.ConnFile = response

    def __init__(
        self,
        layout_toolbar,
        server,
        load_data=None,
        load_variables=None,
        update_available_color_maps=None,
        update_scalar_bars=None,
        **kwargs,
    ):
        self.server = server
        self.state = server.state
        self.ctrl = server.controller
        with tauri.Dialog() as dialog:
            self.ctrl.select_file = dialog.open

        with layout_toolbar as toolbar:
            toolbar.density = "compact"
            v2.VSpacer()
            v2.VDivider(vertical=True, classes="mx-2")
            v2.VBtn(
                "Load Variables",
                classes="ma-2",
                click=load_variables,
                style="background-color: lightgray;",  # width: 200px; height: 50px;",
            )
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
                with v2.VRow(no_gutters=True, classes="align-center mt-n4", style="max-height: 2rem;"):
                    #with v2.VCol():
                    #    html.Div("Connectivity File")
                    with v2.VCol():
                        v2.VTextField(
                            prepend_inner_icon="mdi-vector-rectangle",
                            label="Connectivity File",
                            v_model=("ConnFile", ""),
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
                            v2.VIcon("mdi-upload")
            
                with v2.VRow(no_gutters=True, classes="align-center mr-0" , style="max-height: 2rem;"):
                    #with v2.VCol():
                    #    html.Div("Data File")
                    with v2.VCol():
                        v2.VTextField(
                            prepend_inner_icon="mdi-database",
                            label="Data File",
                            v_model=("DataFile", ""),
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
                            v2.VIcon("mdi-upload")

                """
                with v2.VRow(classes="ma-0"):
                    with v2.VCol(cols=4, classes="text-truncate py-0 text-right"):
                        html.Span("Connectivity File")
                    with v2.VCol(classes="text-truncate py-0 text-left"):
                        with v2.VTooltip(bottom=True):
                            with html.Template(v_slot_activator="{ on, attrs }"):
                                v2.VTextField(
                                    v_model=("ConnFile", ""),
                                    label="Connectivity File",
                                    classes="text-truncate py-0 text-left",
                                    hide_details=True,
                                    style="width: 100%;",
                                    v_bind="attrs",
                                    v_on="on",
                                )
                            html.Span(f"{self.state.ConnFile}")
                    with v2.VCol(cols=1):
                        with v2.VBtn(
                            icon=True,
                            dense=True,
                            size="sm",
                            flat=True,
                            variant="outlined",
                            classes="mx-2",
                        ):
                            v2.VIcon("mdi-upload")

                with v2.VRow(classes="ma-0"):
                    with v2.VCol(cols=4, classes="text-truncate py-0 text-right"):
                        html.Span("Data File")
                    with v2.VCol(classes="text-truncate py-0 text-left"):
                        with v2.VTooltip(bottom=True):
                            with html.Template(v_slot_activator="{ on, attrs }"):
                                v2.VTextField(
                                    v_model=("DataFile", ""),
                                    label="Data File",
                                    classes="text-truncate py-0 text-left",
                                    hide_details=True,
                                    style="width: 100%;",
                                    v_bind="attrs",
                                    v_on="on",
                                )
                            html.Span(f"{self.state.DataFile}")
                """                
            with v2.VCol(classes="justify-center"):
                v2.VBtn(
                    "Load Files",
                    classes="ma-2",
                    click=load_data,
                    style="background-color: lightgray;",  # width: 200px; height: 50px;",
                )

            v2.VDivider(vertical=True, classes="mx-2")
            with v2.VTooltip(bottom=True):
                with html.Template(v_slot_activator="{ on, attrs }"):
                    with v2.VBtn(
                        icon=True,
                        tile=True,
                        click="export_config = true",
                        v_bind="attrs",
                        v_on="on",
                    ):
                        v2.VIcon("mdi-content-save")
                html.Span(f"Save Application State")
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

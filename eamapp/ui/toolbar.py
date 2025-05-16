import os

from trame.decorators import TrameApp
from trame.widgets import html, vuetify2 as v2

from eamapp.ui.view_settings import ViewControls
from eamapp.ui.file_selection import FileSelect


@TrameApp()
class Toolbar:
    def __init__(
        self,
        layout_toolbar,
        server,
        load_data=None,
        load_variables=None,
        zoom=None,
        move=None,
        update_available_color_maps=None,
        update_scalar_bars=None,
        **kwargs,
    ):
        self.server = server
        self.state = server.state
        self.ctrl = server.controller
        with layout_toolbar as toolbar:
            toolbar.density = "compact"
            v2.VSpacer()
            ViewControls(zoom=zoom, move=move)
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
                    label="Show Scalar Bar",
                    value=1,
                    v_model=("scalarbar", False),
                    dense=True,
                    hide_details=True,
                    change=(update_scalar_bars, "[$event]"),
                    style="height: 20px;",
                )
            v2.VDivider(vertical=True, classes="mx-2")
            with v2.VCol(style="width: 25%;", classes="justify-center"):
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
            with v2.VCol(classes="justify-center"):
                v2.VBtn(
                    "Load Data",
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

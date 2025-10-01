import asyncio
import json
import time

from pathlib import Path

from trame.app import TrameApp
from trame.ui.vuetify3 import VAppLayout
from trame.widgets import vuetify3 as v3, paraview as pvw, client, html
from trame.decorators import controller

from quickview.pipeline import EAMVisSource
from quickview.assets import ASSETS
from quickview.components.file_browser import ParaViewFileBrowser

from paraview import simple

# -----------------------------------------------------------------------------
# Externalize
# -----------------------------------------------------------------------------
VAR_HEADERS = [
    {"title": "Name", "align": "start", "key": "name", "sortable": True},
    {"title": "Type", "align": "start", "key": "type", "sortable": True},
]
# -----------------------------------------------------------------------------


class EAMApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(server)

        # CLI
        cli = self.server.cli
        cli.add_argument(
            "-cf",
            "--conn",
            nargs="?",
            help="the nc file with connnectivity information",
        )
        cli.add_argument(
            "-df",
            "--data",
            help="the nc file with data/variables",
        )
        cli.add_argument(
            "-sf",
            "--state",
            nargs="?",
            help="state file to be loaded",
        )
        cli.add_argument(
            "-wd",
            "--workdir",
            default=str(Path.cwd().resolve()),
            help="working directory (to store session data)",
        )
        args, _ = cli.parse_known_args()

        # Development setup
        if self.server.hot_reload:
            self.ctrl.on_server_reload.add(self._build_ui)

        # Helpers
        self.file_browser = ParaViewFileBrowser(
            self.server,
            prefix="pv_files",
            home=args.workdir,  # can use current=
            group="",
        )

        # Data input
        self.state.variables_listing = []
        self.source = EAMVisSource()
        self.app_state = {}
        if args.state is not None:
            self.app_state = json.loads(Path(args.state).read_text())
            self.source.Update(
                **{k: self.app_state[k] for k in ("data_file", "conn_file")}
            )
        elif args.data and args.conn:
            self.file_browser.set_data_simulation(args.data)
            self.file_browser.set_data_connectivity(args.conn)
            self.ctrl.on_server_ready.add(self.file_browser.load_data_files)

        # GUI
        self._build_ui()

    def _build_ui(self, **_):
        with VAppLayout(self.server, fill_height=True) as self.ui:
            with v3.VLayout():
                with v3.VNavigationDrawer(
                    permanent=True, rail=("compact_drawer", True), width=220
                ):
                    with v3.VList(
                        density="compact",
                        nav=True,
                        select_strategy="independent",
                        v_model_selected=("active_tools", ["load-data"]),
                    ):
                        with v3.VListItem(
                            title=("compact_drawer ? null : 'QuickView'",),
                            classes="text-h6",
                        ):
                            with v3.Template(raw_attrs=["#prepend"]):
                                v3.VAvatar(image=ASSETS.icon, size=24, classes="me-4")
                            v3.VProgressCircular(
                                color="primary",
                                indeterminate=True,
                                v_show="trame__busy",
                                v_if="compact_drawer",
                                style="position: absolute !important;left: 50%;top: 50%; transform: translate(-50%, -50%);",
                            )
                            v3.VProgressLinear(
                                v_else=True,
                                color="primary",
                                indeterminate=True,
                                v_show="trame__busy",
                                absolute=True,
                                style="top:90%;width:100%;",
                            )
                        v3.VListItem(
                            prepend_icon="mdi-file-document-outline",
                            value="load-data",
                            title=("compact_drawer ? null : 'File loading'",),
                        )
                        v3.VListItem(
                            prepend_icon="mdi-list-status",
                            value="select-fields",
                            disabled=("variables_listing.length === 0",),
                            title=("compact_drawer ? null : 'Fields selection'",),
                        )
                        v3.VListItem(
                            prepend_icon="mdi-collage",
                            value="adjust-layout",
                            title=("compact_drawer ? null : 'Layout management'",),
                        )
                        v3.VListItem(
                            prepend_icon="mdi-crop",
                            value="adjust-databounds",
                            title=("compact_drawer ? null : 'Lat/Long cropping'",),
                        )
                        v3.VListItem(
                            prepend_icon="mdi-earth",
                            value="projection-sphere",
                            title=("compact_drawer ? null : 'Map Projection'",),
                        )
                        v3.VListItem(
                            prepend_icon="mdi-movie-open-cog-outline",
                            value="animation-controls",
                            title=("compact_drawer ? null : 'Animation controls'",),
                        )

                        v3.VListItem(
                            prepend_icon="mdi-folder-arrow-left-right-outline",
                            value="import-export",
                            title=("compact_drawer ? null : 'State Import/Export'",),
                        )

                        # v3.VListItem(
                        #     prepend_icon="mdi-compass-rose",
                        #     value="reset-camera",
                        #     disabled=True,
                        # )
                        # v3.VListItem(
                        #     prepend_icon="mdi-cog",
                        #     value="settings",
                        #     disabled=True,
                        # )

                        # v3.VListItem(
                        #     prepend_icon="mdi-earth-box",
                        #     value="projection-box",
                        #     disabled=True,
                        # )

                    with v3.Template(raw_attrs=["#append"]):
                        with v3.VList(density="compact", nav=True):
                            v3.VListItem(
                                prepend_icon="mdi-lifebuoy",
                                click="compact_drawer = !compact_drawer",
                                title=("compact_drawer ? null : 'Toggle Help'",),
                            )
                            if self.server.hot_reload:
                                v3.VListItem(
                                    prepend_icon="mdi-timer-sand-complete",
                                    click=self.fake_busy,
                                    title=("compact_drawer ? null : 'Trigger busy'",),
                                )
                                v3.VListItem(
                                    prepend_icon="mdi-database-refresh-outline",
                                    click=self.ctrl.on_server_reload,
                                    title=("compact_drawer ? null : 'Refresh UI'",),
                                )

                with v3.VMain(classes="bg-red"):
                    # Field selection container
                    with v3.VNavigationDrawer(
                        model_value=("active_tools.includes('select-fields')",),
                        width=500,
                    ):
                        v3.VTextField(
                            v_model=("variables_filter", ""),
                            hide_details=True,
                            color="primary",
                            placeholder="Filter",
                            density="compact",
                            variant="outlined",
                            classes="mx-2 mt-2",
                            prepend_inner_icon="mdi-magnify",
                            clearable=True,
                        )
                        v3.VDataTable(
                            v_model=("variables_selected", []),
                            show_select=True,
                            item_value="id",
                            density="compact",
                            fixed_header=True,
                            headers=("variables_headers", VAR_HEADERS),
                            items=("variables_listing", []),
                            height="calc(100vh - 6.5rem)",
                            style="user-select: none; cursor: pointer;",
                            hover=True,
                            search=("variables_filter", ""),
                            items_per_page=-1,
                            hide_default_footer=True,
                        )

                        with v3.VCardActions(key="variables_selected.length"):
                            v3.VChip(
                                "{{ variables_selected.filter((v) => v.at(-1) === 's').length }} Surfaces",
                                color="success",
                                v_show="variables_selected.filter((v) => v.at(-1) === 's').length",
                                size="small",
                                closable=True,
                                click_close="variables_selected = variables_selected.filter((v) => v.at(-1) !== 's')",
                            )
                            v3.VChip(
                                "{{ variables_selected.filter((v) => v.at(-1) === 'i').length }} Interfaces",
                                color="info",
                                v_show="variables_selected.filter((v) => v.at(-1) === 'i').length",
                                size="small",
                                closable=True,
                                click_close="variables_selected = variables_selected.filter((v) => v.at(-1) !== 'i')",
                            )
                            v3.VChip(
                                "{{ variables_selected.filter((v) => v.at(-1) === 'm').length }} Midpoints",
                                color="warning",
                                v_show="variables_selected.filter((v) => v.at(-1) === 'm').length",
                                size="small",
                                closable=True,
                                click_close="variables_selected = variables_selected.filter((v) => v.at(-1) !== 'm')",
                            )
                            v3.VSpacer()
                            v3.VBtn(
                                classes="text-none",
                                color="primary",
                                prepend_icon="mdi-database",
                                text="Load variables",
                                variant="flat",
                                disabled=("variables_selected.length === 0",),
                            )

                    with v3.VContainer(classes="h-100", fluid=True):
                        # load-data
                        with v3.VDialog(
                            model_value=("active_tools.includes('load-data')",),
                            contained=True,
                            max_width="80vw",
                            persistent=True,
                        ):
                            self.file_browser.ui()

                        # layout content
                        with html.Div(classes="bg-green h-100"):
                            v3.VLabel("Hello {{ active_tools }}")

    def fake_busy(self):
        time.sleep(3)

    @controller.add_task("file_selection_load")
    async def data_loading_open(self, simulation, connectivity):
        await asyncio.sleep(0.1)
        self.source.Update(
            data_file=simulation,
            conn_file=connectivity,
        )

        self.file_browser.loading_completed(self.source.valid)

        if self.source.valid:
            with self.state as s:
                s.active_tools = list(
                    set(
                        (
                            "select-fields",
                            *(tool for tool in s.active_tools if tool != "load-data"),
                        )
                    )
                )

                self.state.variables_filter = ""
                self.state.variables_listing = [
                    *(
                        {"name": name, "type": "surface", "id": f"{name}s"}
                        for name in self.source.surface_vars
                    ),
                    *(
                        {"name": name, "type": "interface", "id": f"{name}i"}
                        for name in self.source.interface_vars
                    ),
                    *(
                        {"name": name, "type": "midpoint", "id": f"{name}m"}
                        for name in self.source.midpoint_vars
                    ),
                ]

            # for name in ["timestamps", "midpoints", "interfaces", "surface_vars", "interface_vars", "midpoint_vars", ]:
            #     print(name, getattr(self.source, name))

    @controller.set("file_selection_cancel")
    def data_loading_hide(self):
        self.state.active_tools = [
            tool for tool in self.state.active_tools if tool != "load-data"
        ]


def main():
    app = EAMApp()
    app.server.start()


if __name__ == "__main__":
    main()

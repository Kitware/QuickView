import asyncio
import json
import time

from pathlib import Path

from trame.app import TrameApp
from trame.ui.vuetify3 import VAppLayout
from trame.widgets import vuetify3 as v3, client, html
from trame.decorators import controller, change

from quickview.pipeline import EAMVisSource
from quickview.assets import ASSETS
from quickview.view_manager2 import ViewManager
from quickview.components.file_browser import ParaViewFileBrowser

v3.enable_lab()

# -----------------------------------------------------------------------------
# Externalize
# -----------------------------------------------------------------------------
VAR_HEADERS = [
    {"title": "Name", "align": "start", "key": "name", "sortable": True},
    {"title": "Type", "align": "start", "key": "type", "sortable": True},
]


def js_var_count(name):
    return f"variables_selected.filter((v) => v[0] === '{name[0]}').length"


def js_var_remove(name):
    return (
        f"variables_selected = variables_selected.filter((v) => v[0] !== '{name[0]}')"
    )


def js_var_title(name):
    return " ".join(["{{", js_var_count(name), "}}", name.capitalize()])


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

        # Data input
        self.state.variables_listing = []
        self.state.toolbar_slider_visibility = []
        self.source = EAMVisSource()
        self.app_state = {}

        # Helpers
        self.view_manager = ViewManager(self.server, self.source)
        self.file_browser = ParaViewFileBrowser(
            self.server,
            prefix="pv_files",
            home=args.workdir,  # can use current=
            group="",
        )

        # Process CLI to pre-load data
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

    # -------------------------------------------------------------------------
    # UI definition
    # -------------------------------------------------------------------------

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
                        with v3.VTooltip(
                            text="Reset camera", disabled=("!compact_drawer",)
                        ):
                            with v3.Template(v_slot_activator="{ props }"):
                                with v3.VListItem(
                                    v_bind="props",
                                    title=("compact_drawer ? null : 'QuickView'",),
                                    classes="text-h6",
                                    click=self.view_manager.reset_camera,
                                ):
                                    with v3.Template(raw_attrs=["#prepend"]):
                                        v3.VAvatar(
                                            image=ASSETS.icon, size=24, classes="me-4"
                                        )
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
                        with v3.VTooltip(
                            text="File loading", disabled=("!compact_drawer",)
                        ):
                            with v3.Template(v_slot_activator="{ props }"):
                                v3.VListItem(
                                    v_bind="props",
                                    prepend_icon="mdi-file-document-outline",
                                    value="load-data",
                                    title=("compact_drawer ? null : 'File loading'",),
                                )
                        with v3.VTooltip(
                            text="Fields selection", disabled=("!compact_drawer",)
                        ):
                            with v3.Template(v_slot_activator="{ props }"):
                                v3.VListItem(
                                    v_bind="props",
                                    prepend_icon="mdi-list-status",
                                    value="select-fields",
                                    disabled=("variables_listing.length === 0",),
                                    title=(
                                        "compact_drawer ? null : 'Fields selection'",
                                    ),
                                )

                        with v3.VTooltip(
                            text="State Import/Export", disabled=("!compact_drawer",)
                        ):
                            with v3.Template(v_slot_activator="{ props }"):
                                v3.VListItem(
                                    v_bind="props",
                                    prepend_icon="mdi-folder-arrow-left-right-outline",
                                    value="import-export",
                                    title=(
                                        "compact_drawer ? null : 'State Import/Export'",
                                    ),
                                )

                        with v3.VTooltip(
                            text="Toggle Help", disabled=("!compact_drawer",)
                        ):
                            with v3.Template(v_slot_activator="{ props }"):
                                v3.VListItem(
                                    v_bind="props",
                                    prepend_icon="mdi-lifebuoy",
                                    click="compact_drawer = !compact_drawer",
                                    title=("compact_drawer ? null : 'Toggle Help'",),
                                )

                        v3.VDivider(classes="my-1")

                        with v3.VTooltip(
                            text="Map Projection", disabled=("!compact_drawer",)
                        ):
                            with v3.Template(v_slot_activator="{ props }"):
                                with v3.VListItem(
                                    v_bind="props",
                                    prepend_icon="mdi-earth",
                                    title=("compact_drawer ? null : 'Map Projection'",),
                                ):
                                    with v3.VMenu(
                                        activator="parent", location="end", offset=10
                                    ):
                                        v3.VList(
                                            mandatory=True,
                                            v_model_selected=(
                                                "projection",
                                                ["Cyl. Equidistant"],
                                            ),
                                            density="compact",
                                            items=(
                                                "projections",
                                                [
                                                    {
                                                        "title": "Cylindrical Equidistant",
                                                        "value": "Cyl. Equidistant",
                                                    },
                                                    {
                                                        "title": "Robinson",
                                                        "value": "Robinson",
                                                    },
                                                    {
                                                        "title": "Mollweide",
                                                        "value": "Mollweide",
                                                    },
                                                ],
                                            ),
                                        )

                        with v3.VTooltip(
                            text="Layout management", disabled=("!compact_drawer",)
                        ):
                            with v3.Template(v_slot_activator="{ props }"):
                                v3.VListItem(
                                    v_bind="props",
                                    prepend_icon="mdi-collage",
                                    value="adjust-layout",
                                    title=(
                                        "compact_drawer ? null : 'Layout management'",
                                    ),
                                )

                        v3.VDivider(classes="my-1")

                        with v3.VTooltip(
                            text="Lat/Long cropping", disabled=("!compact_drawer",)
                        ):
                            with v3.Template(v_slot_activator="{ props }"):
                                v3.VListItem(
                                    v_bind="props",
                                    prepend_icon="mdi-crop",
                                    value="adjust-databounds",
                                    title=(
                                        "compact_drawer ? null : 'Lat/Long cropping'",
                                    ),
                                )

                        with v3.VTooltip(
                            text="Slice selection", disabled=("!compact_drawer",)
                        ):
                            with v3.Template(v_slot_activator="{ props }"):
                                v3.VListItem(
                                    v_bind="props",
                                    prepend_icon="mdi-tune-variant",
                                    value="select-slice-time",
                                    title=(
                                        "compact_drawer ? null : 'Slice selection'",
                                    ),
                                )

                        with v3.VTooltip(
                            text="Animation controls", disabled=("!compact_drawer",)
                        ):
                            with v3.Template(v_slot_activator="{ props }"):
                                v3.VListItem(
                                    v_bind="props",
                                    prepend_icon="mdi-movie-open-cog-outline",
                                    value="animation-controls",
                                    title=(
                                        "compact_drawer ? null : 'Animation controls'",
                                    ),
                                )

                        if self.server.hot_reload:
                            v3.VDivider(classes="mt-8 mb-1", color="red")
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

                    # with v3.Template(raw_attrs=["#append"]):
                    #     with v3.VList(density="compact", nav=True):
                    #         v3.VListItem(
                    #             prepend_icon="mdi-lifebuoy",
                    #             click="compact_drawer = !compact_drawer",
                    #             title=("compact_drawer ? null : 'Toggle Help'",),
                    #         )

                with v3.VMain():
                    # load-data
                    with html.Div(
                        style="position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:1000;"
                    ):
                        with v3.VDialog(
                            model_value=("active_tools.includes('load-data')",),
                            contained=True,
                            max_width="80vw",
                            persistent=True,
                        ):
                            self.file_browser.ui()

                    # Field selection container
                    with v3.VNavigationDrawer(
                        model_value=("active_tools.includes('select-fields')",),
                        width=500,
                        permanent=True,
                    ):
                        with v3.VCardActions(key="variables_selected.length"):
                            for name, color in [
                                ("surfaces", "success"),
                                ("interfaces", "info"),
                                ("midpoints", "warning"),
                            ]:
                                v3.VChip(
                                    js_var_title(name),
                                    color=color,
                                    v_show=js_var_count(name),
                                    size="small",
                                    closable=True,
                                    click_close=js_var_remove(name),
                                )

                            v3.VSpacer()
                            v3.VBtn(
                                classes="text-none",
                                color="primary",
                                prepend_icon="mdi-database",
                                text=(
                                    "`Load ${variables_selected.length} variable${variables_selected.length > 1 ? 's' :''}`",
                                ),
                                variant="flat",
                                disabled=(
                                    "variables_selected.length === 0 || variables_loaded",
                                ),
                                click=self.data_load_variables,
                            )

                        v3.VTextField(
                            v_model=("variables_filter", ""),
                            hide_details=True,
                            color="primary",
                            placeholder="Filter",
                            density="compact",
                            variant="outlined",
                            classes="mx-2",
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
                            height=(
                                "`calc(max(100vh, ${Math.floor(main_size?.size?.height || 0)}px) - 6rem)`",
                            ),
                            style="user-select: none; cursor: pointer;",
                            hover=True,
                            search=("variables_filter", ""),
                            items_per_page=-1,
                            hide_default_footer=True,
                        )

                    with v3.VContainer(classes="h-100 pa-0", fluid=True):
                        with client.SizeObserver("main_size"):
                            # Layout control toolbar
                            with v3.VToolbar(
                                v_show="active_tools.includes('adjust-layout')",
                                color="white",
                                classes="border-b-thin",
                                density="compact",
                            ):
                                v3.VIcon("mdi-collage", classes="px-6 opacity-50")
                                v3.VLabel("Layout Controls", classes="text-subtitle-2")
                                v3.VSpacer()

                                with v3.VRadioGroup(
                                    classes="d-inline-block",
                                    hide_details=True,
                                    inline=True,
                                    v_model=("col_mode", "auto"),
                                ):
                                    v3.VRadio(label="Auto", value="auto")
                                    v3.VRadio(label="Full width", value="1")
                                    v3.VRadio(label="2 cols", value="2")
                                    v3.VRadio(label="3 cols", value="3")
                                    v3.VRadio(label="4 cols", value="4")
                                    v3.VRadio(label="6 cols", value="6")
                                    v3.VRadio(label="12 cols", value="12")

                                v3.VSpacer()
                                v3.VSlider(
                                    v_model=("aspect_ratio", 2),
                                    prepend_icon="mdi-aspect-ratio",
                                    min=1,
                                    max=2,
                                    step=0.1,
                                    density="compact",
                                    hide_details=True,
                                    style="max-width: 400px;",
                                    classes="mx-4",
                                )

                            # Crop selection
                            with v3.VToolbar(
                                v_show="active_tools.includes('adjust-databounds')",
                                color="white",
                                classes="border-b-thin",
                            ):
                                v3.VIcon("mdi-crop", classes="pl-6 opacity-50")
                                with v3.VRow(classes="ma-0 px-2 align-center"):
                                    with v3.VCol(cols=6):
                                        with v3.VRow(classes="mx-2 my-0"):
                                            v3.VLabel(
                                                "Longitude", classes="text-subtitle-2"
                                            )
                                            v3.VSpacer()
                                            v3.VLabel(
                                                "{{ crop_longitude }}",
                                                classes="text-body-2",
                                            )
                                        v3.VRangeSlider(
                                            v_model=("crop_longitude", [-180, 180]),
                                            min=-180,
                                            max=180,
                                            step=1,
                                            density="compact",
                                            hide_details=True,
                                        )
                                    with v3.VCol(cols=6):
                                        with v3.VRow(classes="mx-2 my-0"):
                                            v3.VLabel(
                                                "Latitude", classes="text-subtitle-2"
                                            )
                                            v3.VSpacer()
                                            v3.VLabel(
                                                "{{ crop_latitude }}",
                                                classes="text-body-2",
                                            )
                                        v3.VRangeSlider(
                                            v_model=("crop_latitude", [-90, 90]),
                                            min=-90,
                                            max=90,
                                            step=1,
                                            density="compact",
                                            hide_details=True,
                                        )

                            # Layer/Time selection
                            with v3.VToolbar(
                                v_show="active_tools.includes('select-slice-time')",
                                color="white",
                                classes="border-b-thin",
                            ):
                                v3.VIcon("mdi-tune-variant", classes="ml-3 opacity-50")
                                with v3.VRow(
                                    classes="ma-0 pr-2 align-center", dense=True
                                ):
                                    # midpoint layer
                                    with v3.VCol(
                                        cols=("toolbar_slider_cols", 4),
                                        v_show="toolbar_slider_visibility.includes('m')",
                                    ):
                                        self.state.setdefault(
                                            "layer_midpoints_value", 80.50
                                        )
                                        with v3.VRow(classes="mx-2 my-0"):
                                            v3.VLabel(
                                                "Layer Midpoints",
                                                classes="text-subtitle-2",
                                            )
                                            v3.VSpacer()
                                            v3.VLabel(
                                                "{{ layer_midpoints_value }} hPa (k={{layer_midpoints}})",
                                                classes="text-body-2",
                                            )
                                        v3.VSlider(
                                            v_model=("layer_midpoints", 0),
                                            min=0,
                                            max=("layer_midpoints_max", 10),
                                            step=1,
                                            density="compact",
                                            hide_details=True,
                                        )

                                    # interface layer
                                    with v3.VCol(
                                        cols=("toolbar_slider_cols", 4),
                                        v_show="toolbar_slider_visibility.includes('i')",
                                    ):
                                        self.state.setdefault(
                                            "layer_interfaces_value", 80.50
                                        )
                                        with v3.VRow(classes="mx-2 my-0"):
                                            v3.VLabel(
                                                "Layer Interfaces",
                                                classes="text-subtitle-2",
                                            )
                                            v3.VSpacer()
                                            v3.VLabel(
                                                "{{ layer_interfaces_value }} hPa (k={{layer_interfaces}})",
                                                classes="text-body-2",
                                            )
                                        v3.VSlider(
                                            v_model=("layer_interfaces", 0),
                                            min=0,
                                            max=("layer_interfaces_max", 10),
                                            step=1,
                                            density="compact",
                                            hide_details=True,
                                        )

                                    # time
                                    with v3.VCol(cols=("toolbar_slider_cols", 4)):
                                        self.state.setdefault("time_value", 80.50)
                                        with v3.VRow(classes="mx-2 my-0"):
                                            v3.VLabel("Time", classes="text-subtitle-2")
                                            v3.VSpacer()
                                            v3.VLabel(
                                                "{{ time_value }} hPa (t={{time}})",
                                                classes="text-body-2",
                                            )
                                        v3.VSlider(
                                            v_model=("time", 0),
                                            min=0,
                                            max=("time_max", 10),
                                            step=1,
                                            density="compact",
                                            hide_details=True,
                                        )

                            # Animation
                            with v3.VToolbar(
                                v_show="active_tools.includes('animation-controls')",
                                color="white",
                                classes="border-b-thin",
                                density="compact",
                            ):
                                v3.VIcon(
                                    "mdi-movie-open-cog-outline",
                                    classes="px-6 opacity-50",
                                )
                                with v3.VRow(classes="ma-0 px-2 align-center"):
                                    v3.VSelect(
                                        v_model=("animation_track", "Time"),
                                        items=(
                                            "animation_tracks",
                                            [
                                                "Time",
                                                "Layer Midpoints",
                                                "Layer Interfaces",
                                            ],
                                        ),
                                        flat=True,
                                        variant="plain",
                                        hide_details=True,
                                        density="compact",
                                        style="max-width: 200px;",
                                    )
                                    v3.VSlider(
                                        v_model=("animation_step", 1),
                                        min=0,
                                        max=("amimation_step_max", 100),
                                        step=1,
                                        hide_details=True,
                                        density="compact",
                                    )
                                    v3.VIconBtn(
                                        icon="mdi-page-first",
                                        flat=True,
                                    )
                                    v3.VIconBtn(
                                        icon="mdi-chevron-left",
                                        flat=True,
                                    )
                                    v3.VIconBtn(
                                        icon="mdi-chevron-right",
                                        flat=True,
                                    )
                                    v3.VIconBtn(
                                        icon="mdi-page-last",
                                        flat=True,
                                    )
                                    v3.VIconBtn(
                                        icon="mdi-play",
                                        flat=True,
                                    )
                                    v3.VIconBtn(
                                        icon="mdi-stop",
                                        flat=True,
                                    )

                            client.ServerTemplate(name=("active_layout", "auto_layout"))

    # -------------------------------------------------------------------------
    # Methods connected to UI
    # -------------------------------------------------------------------------

    def fake_busy(self):
        time.sleep(3)

    @controller.add_task("file_selection_load")
    async def data_loading_open(self, simulation, connectivity):
        # Reset state
        self.state.variables_selected = []
        self.state.variables_loaded = False

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
                        {"name": name, "type": "surface", "id": f"s{name}"}
                        for name in self.source.surface_vars
                    ),
                    *(
                        {"name": name, "type": "interface", "id": f"i{name}"}
                        for name in self.source.interface_vars
                    ),
                    *(
                        {"name": name, "type": "midpoint", "id": f"m{name}"}
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

    @property
    def selected_variables(self):
        vars_per_type = {n: [] for n in "smi"}
        for var in self.state.variables_selected:
            type = var[0]
            name = var[1:]
            vars_per_type[type].append(name)

        print("=> selected_variables", vars_per_type)

        return vars_per_type

    def data_load_variables(self):
        vars_to_show = self.selected_variables

        self.source.LoadVariables(
            vars_to_show["s"],  # surfaces
            vars_to_show["m"],  # midpoints
            vars_to_show["i"],  # interfaces
        )
        self.view_manager.build_auto_layout(vars_to_show)

        # Compute Layer/Time column spread
        n_cols = 1  # time
        toolbar_slider_visibility = []
        for var_type in "mi":
            if vars_to_show[var_type]:
                toolbar_slider_visibility.append(var_type)
                n_cols += 1

        with self.state:
            self.state.variables_loaded = True
            self.state.toolbar_slider_cols = 12 / n_cols if n_cols else 12
            self.state.toolbar_slider_visibility = toolbar_slider_visibility
            self.state.dirty("toolbar_slider_visibility")

    @change("variables_selected")
    def _on_dirty_variable_selection(self, **_):
        self.state.variables_loaded = False

    @change("col_mode")
    def _on_layout_refresh(self, **_):
        vars_to_show = self.selected_variables
        print("col_mode", vars_to_show)
        if any(vars_to_show.values()):
            print("build layout")
            self.view_manager.build_auto_layout(vars_to_show)

    @change("projection")
    async def _on_projection(self, projection, **_):
        proj_str = projection[0]
        self.source.UpdateProjection(proj_str)
        self.source.UpdatePipeline()
        self.view_manager.reset_camera()

        # Hack to force reset_camera for "cyl mode"
        # => may not be needed if we switch to rca
        if " " in proj_str:
            for _ in range(2):
                await asyncio.sleep(0.1)
                self.view_manager.reset_camera()


# -------------------------------------------------------------------------
# Standalone execution
# -------------------------------------------------------------------------
def main():
    app = EAMApp()
    app.server.start()


if __name__ == "__main__":
    main()

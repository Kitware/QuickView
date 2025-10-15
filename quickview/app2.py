import asyncio
import json
import time

from pathlib import Path

from trame.app import TrameApp, asynchronous, file_upload
from trame.ui.vuetify3 import VAppLayout
from trame.widgets import vuetify3 as v3, client, html, dataclass
from trame.decorators import controller, change, trigger

from quickview import __version__ as quickview_version
from quickview.pipeline import EAMVisSource
from quickview.assets import ASSETS
from quickview.view_manager2 import ViewManager
from quickview.components.file_browser import ParaViewFileBrowser
from quickview.utils import compute
from quickview import module as qv_module

v3.enable_lab()

# -----------------------------------------------------------------------------
# Externalize
# -----------------------------------------------------------------------------
VAR_HEADERS = [
    {"title": "Name", "align": "start", "key": "name", "sortable": True},
    {"title": "Type", "align": "start", "key": "type", "sortable": True},
]

TRACK_STEPS = {
    "timestamps": "time_idx",
    "interfaces": "interface_idx",
    "midpoints": "midpoint_idx",
}

TRACK_ENTRIES = {
    "timestamps": {"title": "Time", "value": "timestamps"},
    "midpoints": {"title": "Layer Midpoints", "value": "midpoints"},
    "interfaces": {"title": "Layer Interfaces", "value": "interfaces"},
}


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

        # Pre-load deferred widgets
        dataclass.initialize(self.server)
        self.server.enable_module(qv_module)

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

        # Initial UI state
        self.state.update(
            {
                "trame__title": "QuickView",
                "trame__favicon": ASSETS.icon,
                "animation_play": False,
                # All available variables
                "variables_listing": [],
                # Selected variables to load
                "variables_selected": [],
                # Control 'Load Variables' button availability
                "variables_loaded": False,
                # Level controls
                "midpoint_idx": 0,
                "midpoints": [],
                "interface_idx": 0,
                "interfaces": [],
                # Time controls
                "time_idx": 0,
                "timestamps": [],
                # Fields summaries
                "fields_avgs": {},
            }
        )

        # Data input
        self.source = EAMVisSource()

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
            state_content = json.loads(Path(args.state).read_text())

            async def wait_for_import(**_):
                await self.import_state(state_content)

            self.ctrl.on_server_ready.add_task(wait_for_import)
        elif args.data and args.conn:
            self.file_browser.set_data_simulation(args.data)
            self.file_browser.set_data_connectivity(args.conn)
            self.ctrl.on_server_ready.add(self.file_browser.load_data_files)

        # Development setup
        if self.server.hot_reload:
            self.ctrl.on_server_reload.add(self._build_ui)
            self.ctrl.on_server_reload.add(self.view_manager.refresh_ui)

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
                            text=f"QuickView {quickview_version}",
                            disabled=("!compact_drawer",),
                        ):
                            with v3.Template(v_slot_activator="{ props }"):
                                with v3.VListItem(
                                    v_bind="props",
                                    title=(
                                        f"compact_drawer ? null : 'QuickView {quickview_version}'",
                                    ),
                                    classes="text-h6",
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
                            text="Reset camera", disabled=("!compact_drawer",)
                        ):
                            with v3.Template(v_slot_activator="{ props }"):
                                v3.VListItem(
                                    v_bind="props",
                                    prepend_icon="mdi-crop-free",
                                    title=("compact_drawer ? null : 'Reset camera'",),
                                    click=self.view_manager.reset_camera,
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
                            v3.VListItem(
                                prepend_icon="mdi-database-refresh-outline",
                                click=self.ctrl.on_server_reload,
                                title=("compact_drawer ? null : 'Refresh UI'",),
                            )

                    # Show version at the bottom
                    with v3.Template(raw_attrs=["#append"]):
                        v3.VDivider()
                        v3.VLabel(
                            f"{quickview_version}",
                            classes="text-center text-caption d-block text-wrap",
                        )

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
                            # Import/Export toolbar
                            with v3.VToolbar(
                                v_show="active_tools.includes('import-export')",
                                color="white",
                                classes="border-b-thin",
                            ):
                                v3.VIcon(
                                    "mdi-folder-arrow-left-right-outline",
                                    classes="px-6 opacity-50",
                                )
                                v3.VLabel(
                                    "Import/Export Controls", classes="text-subtitle-2"
                                )
                                v3.VSpacer()

                                v3.VTextField(
                                    v_model=("download_name", "quickview-state.json"),
                                    hide_details=True,
                                    density="compact",
                                    label="Download state file",
                                    prepend_inner_icon="mdi-file-download-outline",
                                    variant="outlined",
                                    flat=True,
                                    style="max-width: 250px",
                                    classes="mx-2",
                                    click_prependInner="utils.download(download_name, trigger('download_state'), 'application/json')",
                                )

                                v3.VFileInput(
                                    v_model=("upload_state_file", None),
                                    hide_details=True,
                                    chips=True,
                                    density="compact",
                                    label="Import state file",
                                    prepend_icon=False,
                                    prepend_inner_icon="mdi-file-upload-outline",
                                    variant="outlined",
                                    style="max-width: 250px",
                                    classes="mx-2",
                                )

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

                                v3.VSlider(
                                    v_model=("aspect_ratio", 2),
                                    prepend_icon="mdi-aspect-ratio",
                                    min=1,
                                    max=2,
                                    step=0.1,
                                    density="compact",
                                    hide_details=True,
                                    style="max-width: 400px;",
                                )
                                v3.VSpacer()
                                v3.VCheckbox(
                                    v_model=("layout_grouped", True),
                                    label=("layout_grouped ? 'Grouped' : 'Uniform'",),
                                    hide_details=True,
                                    inset=True,
                                    false_icon="mdi-apps",
                                    true_icon="mdi-focus-field",
                                    density="compact",
                                )

                                with v3.VBtn(
                                    "Size",
                                    classes="text-none mx-4",
                                    prepend_icon="mdi-view-module",
                                    append_icon="mdi-menu-down",
                                ):
                                    with v3.VMenu(activator="parent"):
                                        with v3.VList(density="compact"):
                                            v3.VListItem(
                                                title="Auto",
                                                click=(
                                                    self.view_manager.apply_size,
                                                    "[0]",
                                                ),
                                            )
                                            v3.VListItem(
                                                title="Full Width",
                                                click=(
                                                    self.view_manager.apply_size,
                                                    "[1]",
                                                ),
                                            )
                                            v3.VListItem(
                                                title="2 Columns",
                                                click=(
                                                    self.view_manager.apply_size,
                                                    "[2]",
                                                ),
                                            )
                                            v3.VListItem(
                                                title="3 Columns",
                                                click=(
                                                    self.view_manager.apply_size,
                                                    "[3]",
                                                ),
                                            )
                                            v3.VListItem(
                                                title="4 Columns",
                                                click=(
                                                    self.view_manager.apply_size,
                                                    "[4]",
                                                ),
                                            )
                                            v3.VListItem(
                                                title="6 Columns",
                                                click=(
                                                    self.view_manager.apply_size,
                                                    "[6]",
                                                ),
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
                                        v_show="midpoints.length > 1",
                                    ):
                                        with v3.VRow(classes="mx-2 my-0"):
                                            v3.VLabel(
                                                "Layer Midpoints",
                                                classes="text-subtitle-2",
                                            )
                                            v3.VSpacer()
                                            v3.VLabel(
                                                "{{ parseFloat(midpoints[midpoint_idx] || 0).toFixed(2) }} hPa (k={{ midpoint_idx }})",
                                                classes="text-body-2",
                                            )
                                        v3.VSlider(
                                            v_model=("midpoint_idx", 0),
                                            min=0,
                                            max=("Math.max(0, midpoints.length - 1)",),
                                            step=1,
                                            density="compact",
                                            hide_details=True,
                                        )

                                    # interface layer
                                    with v3.VCol(
                                        cols=("toolbar_slider_cols", 4),
                                        v_show="interfaces.length > 1",
                                    ):
                                        with v3.VRow(classes="mx-2 my-0"):
                                            v3.VLabel(
                                                "Layer Interfaces",
                                                classes="text-subtitle-2",
                                            )
                                            v3.VSpacer()
                                            v3.VLabel(
                                                "{{ parseFloat(interfaces[interface_idx] || 0).toFixed(2) }} hPa (k={{interface_idx}})",
                                                classes="text-body-2",
                                            )
                                        v3.VSlider(
                                            v_model=("interface_idx", 0),
                                            min=0,
                                            max=("Math.max(0, interfaces.length - 1)",),
                                            step=1,
                                            density="compact",
                                            hide_details=True,
                                        )

                                    # time
                                    with v3.VCol(
                                        cols=("toolbar_slider_cols", 4),
                                        v_show="timestamps.length > 1",
                                    ):
                                        self.state.setdefault("time_value", 80.50)
                                        with v3.VRow(classes="mx-2 my-0"):
                                            v3.VLabel("Time", classes="text-subtitle-2")
                                            v3.VSpacer()
                                            v3.VLabel(
                                                "{{ parseFloat(timestamps[time_idx]).toFixed(2) }} (t={{time_idx}})",
                                                classes="text-body-2",
                                            )
                                        v3.VSlider(
                                            v_model=("time_idx", 0),
                                            min=0,
                                            max=("Math.max(0, timestamps.length - 1)",),
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
                                        v_model=("animation_track", "timestamps"),
                                        items=("animation_tracks", []),
                                        flat=True,
                                        variant="plain",
                                        hide_details=True,
                                        density="compact",
                                        style="max-width: 10rem;",
                                    )
                                    v3.VDivider(vertical=True, classes="mx-2")
                                    v3.VSlider(
                                        v_model=("animation_step", 1),
                                        min=0,
                                        max=("amimation_step_max", 0),
                                        step=1,
                                        hide_details=True,
                                        density="compact",
                                        classes="mx-4",
                                    )
                                    v3.VDivider(vertical=True, classes="mx-2")
                                    v3.VIconBtn(
                                        icon="mdi-page-first",
                                        flat=True,
                                        disabled=("animation_step === 0",),
                                        click="animation_step = 0",
                                    )
                                    v3.VIconBtn(
                                        icon="mdi-chevron-left",
                                        flat=True,
                                        disabled=("animation_step === 0",),
                                        click="animation_step = Math.max(0, animation_step - 1)",
                                    )
                                    v3.VIconBtn(
                                        icon="mdi-chevron-right",
                                        flat=True,
                                        disabled=(
                                            "animation_step === amimation_step_max",
                                        ),
                                        click="animation_step = Math.min(amimation_step_max, animation_step + 1)",
                                    )
                                    v3.VIconBtn(
                                        icon="mdi-page-last",
                                        disabled=(
                                            "animation_step === amimation_step_max",
                                        ),
                                        flat=True,
                                        click="animation_step = amimation_step_max",
                                    )
                                    v3.VDivider(vertical=True, classes="mx-2")
                                    v3.VIconBtn(
                                        icon=(
                                            "animation_play ? 'mdi-stop' : 'mdi-play'",
                                        ),
                                        flat=True,
                                        click="animation_play = !animation_play",
                                    )

                            client.ServerTemplate(name=("active_layout", "auto_layout"))

    # -------------------------------------------------------------------------
    # Derived properties
    # -------------------------------------------------------------------------

    @property
    def selected_variables(self):
        vars_per_type = {n: [] for n in "smi"}
        for var in self.state.variables_selected:
            type = var[0]
            name = var[1:]
            vars_per_type[type].append(name)

        return vars_per_type

    @property
    def selected_variable_names(self):
        # Remove var type (first char)
        return [var[1:] for var in self.state.variables_selected]

    # -------------------------------------------------------------------------
    # Methods connected to UI
    # -------------------------------------------------------------------------

    @trigger("download_state")
    def download_state(self):
        active_variables = self.selected_variables
        state_content = {}
        state_content["files"] = {
            "simulation": self.file_browser.get("data_simulation"),
            "connectivity": self.file_browser.get("data_connectivity"),
        }
        state_content["variables-selection"] = self.state.variables_selected
        state_content["layout"] = {
            "aspect-ratio": self.state.aspect_ratio,
            "grouped": self.state.layout_grouped,
            "active": self.state.active_layout,
            "tools": self.state.active_tools,
            "help": not self.state.compact_drawer,
        }
        state_content["data-selection"] = {
            k: self.state[k]
            for k in [
                "time_idx",
                "midpoint_idx",
                "interface_idx",
                "crop_longitude",
                "crop_latitude",
                "projection",
            ]
        }
        views_to_export = state_content["views"] = []
        for view_type, var_names in active_variables.items():
            for var_name in var_names:
                config = self.view_manager.get_view(var_name, view_type).config
                views_to_export.append(
                    {
                        "type": view_type,
                        "name": var_name,
                        "config": {
                            "preset": config.preset,
                            "invert": config.invert,
                            "use_log_scale": config.use_log_scale,
                            "color_range": config.color_range,
                            "override_range": config.override_range,
                            "order": config.order,
                            "size": config.size,
                        },
                    }
                )

        return json.dumps(state_content, indent=2)

    @change("upload_state_file")
    def _on_import_state(self, upload_state_file, **_):
        if upload_state_file is None:
            return

        file_proxy = file_upload.ClientFile(upload_state_file)
        state_content = json.loads(file_proxy.content)
        asynchronous.create_task(self.import_state(state_content))

    @controller.set("import_state")
    async def import_state(self, state_content):
        # Files
        self.file_browser.set_data_simulation(state_content["files"]["simulation"])
        self.file_browser.set_data_connectivity(state_content["files"]["connectivity"])
        await self.data_loading_open(
            self.file_browser.get("data_simulation"),
            self.file_browser.get("data_connectivity"),
        )

        # Load variables
        self.state.variables_selected = state_content["variables-selection"]
        self.state.update(state_content["data-selection"])
        await self._data_load_variables()

        # Update view states
        for view_state in state_content["views"]:
            view_type = view_state["type"]
            var_name = view_state["name"]
            config = self.view_manager.get_view(var_name, view_type).config
            config.update(**view_state["config"])

        # Update layout
        self.state.aspect_ratio = state_content["layout"]["aspect-ratio"]
        self.state.layout_grouped = state_content["layout"]["grouped"]
        self.state.active_layout = state_content["layout"]["active"]
        self.state.active_tools = state_content["layout"]["tools"]
        self.state.compact_drawer = not state_content["layout"]["help"]

    @controller.add_task("file_selection_load")
    async def data_loading_open(self, simulation, connectivity):
        # Reset state
        self.state.variables_selected = []
        self.state.variables_loaded = False
        self.state.midpoint_idx = 0
        self.state.midpoints = []
        self.state.interface_idx = 0
        self.state.interfaces = []
        self.state.time_idx = 0
        self.state.timestamps = []

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

                # Update Layer/Time values and ui layout
                n_cols = 0
                available_tracks = []
                for name in ["midpoints", "interfaces", "timestamps"]:
                    values = getattr(self.source, name)
                    self.state[name] = values

                    if len(values) > 1:
                        n_cols += 1
                        available_tracks.append(TRACK_ENTRIES[name])

                self.state.toolbar_slider_cols = 12 / n_cols if n_cols else 12
                self.state.animation_tracks = available_tracks
                self.state.animation_track = (
                    self.state.animation_tracks[0]["value"]
                    if available_tracks
                    else None
                )

    @controller.set("file_selection_cancel")
    def data_loading_hide(self):
        self.state.active_tools = [
            tool for tool in self.state.active_tools if tool != "load-data"
        ]

    def data_load_variables(self):
        asynchronous.create_task(self._data_load_variables())

    async def _data_load_variables(self):
        """Called at 'Load Variables' button click"""
        vars_to_show = self.selected_variables

        self.source.LoadVariables(
            vars_to_show["s"],  # surfaces
            vars_to_show["m"],  # midpoints
            vars_to_show["i"],  # interfaces
        )

        # Trigger source update + compute avg
        with self.state:
            self.state.variables_loaded = True
        await self.server.network_completion

        # Update views in layout
        with self.state:
            self.view_manager.build_auto_layout(vars_to_show)
        await self.server.network_completion

        # Reset camera after yield
        await asyncio.sleep(0.1)
        self.view_manager.reset_camera()

    @change("variables_selected")
    def _on_dirty_variable_selection(self, **_):
        self.state.variables_loaded = False

    @change("layout_grouped")
    def _on_layout_change(self, **_):
        vars_to_show = self.selected_variables

        if any(vars_to_show.values()):
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

    @change(
        "variables_loaded",
        "time_idx",
        "midpoint_idx",
        "interface_idx",
        "crop_longitude",
        "crop_latitude",
        "projection",
    )
    def _on_time_change(
        self,
        variables_loaded,
        time_idx,
        timestamps,
        midpoint_idx,
        interface_idx,
        crop_longitude,
        crop_latitude,
        projection,
        **_,
    ):
        if not variables_loaded:
            return

        time_value = timestamps[time_idx] if len(timestamps) else 0.0
        self.source.UpdateLev(midpoint_idx, interface_idx)
        self.source.ApplyClipping(crop_longitude, crop_latitude)
        self.source.UpdateProjection(projection[0])
        self.source.UpdateTimeStep(time_idx)
        self.source.UpdatePipeline(time_value)

        self.view_manager.update_color_range()
        self.view_manager.render()

        # Update avg computation
        # Get area variable to calculate weighted average
        data = self.source.views["atmosphere_data"]
        self.state.fields_avgs = compute.extract_avgs(
            data, self.selected_variable_names
        )

    @change("animation_track")
    def _on_animation_track_change(self, animation_track, **_):
        self.state.animation_step = 0
        self.state.amimation_step_max = 0

        if animation_track:
            self.state.amimation_step_max = len(self.state[animation_track]) - 1

    @change("animation_step")
    def _on_animation_step(self, animation_track, animation_step, **_):
        if animation_track:
            self.state[TRACK_STEPS[animation_track]] = animation_step

    @change("animation_play")
    def _on_animation_play(self, animation_play, **_):
        if animation_play:
            asynchronous.create_task(self._run_animation())

    async def _run_animation(self):
        with self.state as s:
            while s.animation_play:
                await asyncio.sleep(0.1)
                if s.animation_step < s.amimation_step_max:
                    with s:
                        s.animation_step += 1
                    await self.server.network_completion
                else:
                    s.animation_play = False


# -------------------------------------------------------------------------
# Standalone execution
# -------------------------------------------------------------------------
def main():
    app = EAMApp()
    app.server.start()


if __name__ == "__main__":
    main()

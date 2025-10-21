import asyncio
import json
import datetime
import os

from pathlib import Path

from trame.app import TrameApp, asynchronous, file_upload
from trame.ui.vuetify3 import VAppLayout
from trame.widgets import vuetify3 as v3, client, html, dataclass, trame as tw
from trame.decorators import controller, change, trigger, life_cycle

from e3sm_quickview import module as qv_module
from e3sm_quickview.assets import ASSETS
from e3sm_quickview.components import doc, file_browser, css, toolbars, dialogs, drawers
from e3sm_quickview.pipeline import EAMVisSource
from e3sm_quickview.utils import compute, js, constants, cli
from e3sm_quickview.view_manager2 import ViewManager


v3.enable_lab()


class EAMApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(server)

        # Pre-load deferred widgets
        dataclass.initialize(self.server)
        self.server.enable_module(qv_module)

        # CLI
        args = cli.configure_and_parse(self.server.cli)

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
        self.file_browser = file_browser.ParaViewFileBrowser(
            self.server,
            prefix="pv_files",
            home=None if args.user_home else args.workdir,  # can use current=
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
    # Tauri adapter
    # -------------------------------------------------------------------------

    @life_cycle.server_ready
    def _tauri_ready(self, **_):
        os.write(1, f"tauri-server-port={self.server.port}\n".encode())

    @life_cycle.client_connected
    def _tauri_show(self, **_):
        os.write(1, "tauri-client-ready\n".encode())

    # -------------------------------------------------------------------------
    # UI definition
    # -------------------------------------------------------------------------

    def _build_ui(self, **_):
        with VAppLayout(self.server, fill_height=True) as self.ui:
            # Keyboard shortcut
            with tw.MouseTrap(
                ResetCamera=self.view_manager.reset_camera,
                SizeAuto=(self.view_manager.apply_size, "[0]"),
                Size1=(self.view_manager.apply_size, "[1]"),
                Size2=(self.view_manager.apply_size, "[2]"),
                Size3=(self.view_manager.apply_size, "[3]"),
                Size4=(self.view_manager.apply_size, "[4]"),
                Size6=(self.view_manager.apply_size, "[6]"),
                ToolbarLayout=(self.toggle_toolbar, "['adjust-layout']"),
                ToolbarCrop=(self.toggle_toolbar, "['adjust-databounds']"),
                ToolbarSelect=(self.toggle_toolbar, "['select-slice-time']"),
                ToolbarAnimation=(self.toggle_toolbar, "['animation-controls']"),
                ToggleVariableSelection=(self.toggle_toolbar, "['select-fields']"),
                RemoveAllToolbars=(self.toggle_toolbar),
                ToggleGroups="layout_grouped = !layout_grouped",
                ProjectionEquidistant="projection = ['Cyl. Equidistant']",
                ProjectionRobinson="projection = ['Robinson']",
                ProjectionMollweide="projection = ['Mollweide']",
                ToggleViewLock="lock_views = !lock_views",
            ) as mt:
                mt.bind(["r"], "ResetCamera")
                mt.bind(["alt+0", "0"], "SizeAuto")
                mt.bind(["alt+1", "1"], "Size1")
                mt.bind(["alt+2", "2"], "Size2")
                mt.bind(["alt+3", "3"], "Size3")
                mt.bind(["alt+4", "4"], "Size4")
                mt.bind(["alt+6", "6"], "Size6")

                mt.bind("i", "ProjectionEquidistant")
                mt.bind("o", "ProjectionRobinson")
                mt.bind("p", "ProjectionMollweide")

                mt.bind("a", "ToolbarLayout")
                mt.bind("s", "ToolbarCrop")
                mt.bind("d", "ToolbarSelect")
                mt.bind("f", "ToolbarAnimation")
                mt.bind("g", "ToggleGroups")

                mt.bind("?", "ToggleVariableSelection")

                mt.bind("space", "ToggleViewLock", stop_propagation=True)

                mt.bind("esc", "RemoveAllToolbars")

            with v3.VLayout():
                drawers.Tools(
                    reset_camera=self.view_manager.reset_camera,
                )

                with v3.VMain():
                    dialogs.FileOpen(self.file_browser)
                    dialogs.StateDownload()
                    drawers.FieldSelection(load_variables=self.data_load_variables)

                    with v3.VContainer(classes="h-100 pa-0", fluid=True):
                        with client.SizeObserver("main_size"):
                            # Take space to push content below the fixed overlay
                            html.Div(style=("`height: ${top_padding}px`",))

                            # Fixed overlay for toolbars
                            with html.Div(style=css.TOOLBARS_FIXED_OVERLAY):
                                toolbars.Layout(apply_size=self.view_manager.apply_size)
                                toolbars.Cropping()
                                toolbars.DataSelection()
                                toolbars.Animation()

                            # View of all the variables
                            client.ServerTemplate(
                                name=("active_layout", "auto_layout"),
                                v_if="variables_selected.length",
                            )

                            # Show documentation when no variable selected
                            with html.Div(v_if="!variables_selected.length"):
                                doc.LandingPage()

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
        state_content["origin"] = {
            "user": os.environ.get("USER", os.environ.get("USERNAME")),
            "created": f"{datetime.datetime.now()}",
            "comment": self.state.export_comment,
        }
        state_content["files"] = {
            "simulation": str(Path(self.file_browser.get("data_simulation")).resolve()),
            "connectivity": str(
                Path(self.file_browser.get("data_connectivity")).resolve()
            ),
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
        self.import_state(state_content)

    @controller.set("import_state")
    def import_state(self, state_content):
        asynchronous.create_task(self._import_state(state_content))

    async def _import_state(self, state_content):
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
        self.state.variables_loaded = True

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

        # Update filebrowser state
        with self.state:
            self.file_browser.set("state_loading", False)

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
                        available_tracks.append(constants.TRACK_ENTRIES[name])

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

    @change("active_tools")
    def _on_toolbar_change(self, active_tools, **_):
        top_padding = 0
        for name in active_tools:
            top_padding += toolbars.SIZES.get(name, 0)

        self.state.top_padding = top_padding

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

    def toggle_toolbar(self, toolbar_name=None):
        if toolbar_name is None:
            self.state.compact_drawer = True
            self.state.active_tools = []
            return

        if toolbar_name in self.state.active_tools:
            # remove
            self.state.active_tools = [
                n for n in self.state.active_tools if n != toolbar_name
            ]
        else:
            # add
            self.state.active_tools.append(toolbar_name)
            self.state.dirty("active_tools")


# -------------------------------------------------------------------------
# Standalone execution
# -------------------------------------------------------------------------
def main():
    app = EAMApp()
    app.server.start()


if __name__ == "__main__":
    main()

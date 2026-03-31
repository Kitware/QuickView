import asyncio
import datetime
import json
import math
import os
import time
from functools import partial
from pathlib import Path

from trame.app import TrameApp, asynchronous, file_upload
from trame.decorators import change, controller, life_cycle, trigger
from trame.ui.vuetify3 import VAppLayout
from trame.widgets import client, dataclass, html, rca, tauri
from trame.widgets import trame as tw
from trame.widgets import vuetify3 as v3

from e3sm_quickview import module as qv_module
from e3sm_quickview.assets import ASSETS
from e3sm_quickview.components import css, dialogs, doc, drawers, file_browser, toolbars
from e3sm_quickview.pipeline import EAMVisSource
from e3sm_quickview.utils import cli, compute

v3.enable_lab()


def create_view_manager(single_view, server, source):
    if single_view:
        from e3sm_quickview.view_manager2 import ViewManager

        return ViewManager(server, source)

    from e3sm_quickview.view_manager import ViewManager

    return ViewManager(server, source)


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
                "is_tauri": False,
                "animation_play": False,
                # All available variables
                "variables_listing": [],
                # Selected variables to load
                "variables_selected": [],
                # Control 'Load Variables' button availability
                "variables_loaded": False,
                # Dynamic type-color mapping (populated when data loads)
                "variable_types": [],
                # Dimension arrays (will be populated dynamically)
                "midpoints": [],
                "interfaces": [],
                "timestamps": [],
                # Fields summaries
                "fields_avgs": {},
            }
        )

        # Data input
        self.source = EAMVisSource()

        # Helpers
        self.view_manager = create_view_manager(args.fast, self.server, self.source)
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
        jupyter_url_prefix = os.environ.get("JUPYTERHUB_SERVICE_PREFIX")
        jupyter_url_api = os.environ.get("JUPYTERHUB_API_URL")
        if jupyter_url_prefix:
            base_url = "https://jupyter.nersc.gov"
            if jupyter_url_api:
                base_url = jupyter_url_api[:-8]

            os.write(
                1,
                "\nUse URL below to connect to the application:\n\n  => "
                f"{base_url}{jupyter_url_prefix}proxy/{self.server.port}"
                "/index.html?ui=main&reconnect=auto\n\n".encode(),
            )
        else:
            os.write(1, f"tauri-server-port={self.server.port}\n".encode())

    @life_cycle.client_connected
    def _tauri_show(self, **_):
        jupyter_url_prefix = os.environ.get("JUPYTERHUB_SERVICE_PREFIX")
        if not jupyter_url_prefix:
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
                SizeFlow=(self.view_manager.apply_size, "['flow']"),
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
                FileOpen=(self.toggle_toolbar, "['load-data']"),
                SaveState="trigger('download_state')",
                UploadState="utils.get('document').querySelector('#fileUpload').click()",
                ToggleHelp="compact_drawer = !compact_drawer",
            ) as mt:
                mt.bind(["z"], "ResetCamera")
                mt.bind(["alt+0", "0"], "SizeAuto")
                mt.bind(["alt+1", "1"], "Size1")
                mt.bind(["alt+2", "2"], "Size2")
                mt.bind(["alt+3", "3"], "Size3")
                mt.bind(["alt+4", "4"], "Size4")
                mt.bind(["alt+6", "6"], "Size6")
                mt.bind(["="], "SizeFlow")

                mt.bind("c", "ProjectionEquidistant")
                mt.bind("r", "ProjectionRobinson")
                mt.bind("m", "ProjectionMollweide")

                mt.bind("f", "FileOpen")
                mt.bind("d", "SaveState")
                mt.bind("u", "UploadState")
                mt.bind("h", "ToggleHelp")

                mt.bind("p", "ToolbarLayout")
                mt.bind("l", "ToolbarCrop")
                mt.bind("s", "ToolbarSelect")
                mt.bind("a", "ToolbarAnimation")
                mt.bind("g", "ToggleGroups")

                mt.bind("v", "ToggleVariableSelection")

                mt.bind("space", "ToggleViewLock", stop_propagation=True)

                mt.bind("esc", "RemoveAllToolbars")

            # Native Dialogs
            client.ClientTriggers(mounted="is_tauri = !!window.__TAURI__")
            with tauri.Dialog() as dialog:
                self.ctrl.save = dialog.save

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
                            if self.view_manager.use_image_stream:
                                with rca.ImageStream(
                                    self.view_manager._render_window,
                                    encoder="turbo-jpeg",
                                    ctx_name="view",
                                ):
                                    # To debug vtkRenderWindow content
                                    # html.Img(src=["image?.src"], height="300px")
                                    client.ServerTemplate(
                                        name=("active_layout", "auto_layout"),
                                        v_if="variables_selected.length",
                                    )
                            else:
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
        from collections import defaultdict

        vars_per_type = defaultdict(list)
        for name in self.state.variables_selected:
            type = self.source.variables[name].dimensions
            vars_per_type[type].append(name)

        return dict(vars_per_type)

    @property
    def selected_variable_names(self):
        # Remove var type (first char)
        return [var for var in self.state.variables_selected]

    # -------------------------------------------------------------------------
    # Methods connected to UI
    # -------------------------------------------------------------------------

    @trigger("download_state")
    @controller.set("download_state")
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
                            # lut
                            "preset": config.preset,
                            "invert": config.invert,
                            "use_log_scale": config.use_log_scale,
                            # layout
                            "order": config.order,
                            "size": config.size,
                            "offset": config.offset,
                            "break_row": config.break_row,
                            # color range
                            "override_range": config.override_range,
                            "color_range": config.color_range,
                            "color_value_min": config.color_value_min,
                            "color_value_max": config.color_value_max,
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
                        {
                            "name": var.name,
                            "type": ", ".join(var.dimensions),
                            "id": f"{var.name}",
                        }
                        for _, var in self.source.variables.items()
                    ),
                ]

                # Build dynamic type-color mapping
                from e3sm_quickview.utils.colors import get_type_color

                dim_types = sorted(
                    set(
                        ", ".join(var.dimensions)
                        for var in self.source.variables.values()
                    )
                )
                self.state.variable_types = [
                    {"name": t, "color": get_type_color(i)}
                    for i, t in enumerate(dim_types)
                ]

                # Update Layer/Time values and ui layout
                n_cols = 0
                available_tracks = []
                for name, dim in self.source.dimensions.items():
                    values = dim.data
                    # Convert to list for JSON serialization
                    self.state[name] = (
                        values.tolist()
                        if hasattr(values, "tolist")
                        else list(values)
                        if values is not None
                        else []
                    )

                    if values is not None and len(values) > 1:
                        n_cols += 1
                        available_tracks.append(name)
                self.state.toolbar_slider_cols = 12 / n_cols if n_cols else 12
                self.state.animation_tracks = available_tracks
                self.state.animation_track = (
                    self.state.animation_tracks[0] if available_tracks else None
                )

                # Initialize dynamic index variables for each dimension
                for dim_name in available_tracks:
                    index_var = f"{dim_name}_idx"
                    if "time" in index_var:
                        self.state[index_var] = 50
                    else:
                        self.state[index_var] = 0
                    self.state.change(index_var)(
                        partial(self._on_slicing_change, dim_name, index_var)
                    )

    @controller.set("file_selection_cancel")
    def data_loading_hide(self):
        self.state.active_tools = [
            tool for tool in self.state.active_tools if tool != "load-data"
        ]

    def data_load_variables(self):
        self.state.loading = True
        asynchronous.create_task(self._data_load_variables())

    async def _data_load_variables(self):
        """Called at 'Load Variables' button click"""
        t0 = time.perf_counter()
        # Give some room
        await asyncio.sleep(0.1)

        vars_to_show = self.selected_variables

        # Flatten the list of lists
        flattened_vars = [var for var_list in vars_to_show.values() for var in var_list]

        # Compute used dimensions
        used_dims = set()
        for dims in self.selected_variables.keys():
            used_dims.update(dims)
        self.state.available_animation_tracks = [
            n for n in self.state.animation_tracks if n in used_dims
        ]
        self.state.animation_track = (
            self.state.available_animation_tracks[0]
            if self.state.available_animation_tracks
            else None
        )

        self.source.LoadVariables(flattened_vars)

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

        # Done with the loading
        t1 = time.perf_counter()
        with self.state:
            self.state.loading = False
            self.state.loading_time = t1 - t0

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

    @change("active_tools", "available_animation_tracks")
    def _on_toolbar_change(self, active_tools, **_):
        top_padding = 0
        for name in active_tools:
            if name == "select-slice-time":
                track_count = len(self.state.available_animation_tracks or [])
                rows_needed = 1
                if track_count > 3:
                    if track_count % 3 == 0 or (track_count + 1) % 3 == 0:
                        rows_needed = math.ceil(track_count / 3)
                    elif track_count % 2 == 0:
                        rows_needed = track_count / 2
                    else:
                        rows_needed = math.ceil(track_count / 3)

                top_padding += 70 * rows_needed
            else:
                top_padding += toolbars.SIZES.get(name, 0)

        self.state.top_padding = top_padding

    def _on_slicing_change(self, var, ind_var, **_):
        self.source.UpdateSlicing(var, self.state[ind_var])
        self.source.UpdatePipeline()

        self.view_manager.update_color_range()
        self.view_manager.render()

        # Update avg computation
        # Get area variable to calculate weighted average
        data = self.source.views["atmosphere_data"]
        self.state.fields_avgs = compute.extract_avgs(
            data, self.selected_variable_names
        )

    @change(
        "variables_loaded",
        "crop_longitude",
        "crop_latitude",
        "projection",
    )
    def _on_downstream_change(
        self,
        variables_loaded,
        crop_longitude,
        crop_latitude,
        projection,
        **_,
    ):
        if not variables_loaded:
            return

        self.source.ApplyClipping(crop_longitude, crop_latitude)
        self.source.UpdateProjection(projection[0])
        self.source.UpdatePipeline()

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
    app.server.start(show_connection_info=False, open_browser=False)


if __name__ == "__main__":
    main()

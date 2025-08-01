import os
import json
import numpy as np
import xml.etree.ElementTree as ET

from pathlib import Path
from typing import Union

from trame.app import get_server
from trame.decorators import TrameApp, life_cycle, trigger
from trame.ui.vuetify import SinglePageWithDrawerLayout

from trame.widgets import vuetify as v2, html, client
from trame.widgets import paraview as pvWidgets
from trame.widgets import grid

from trame_server.core import Server

from quickview.pipeline import EAMVisSource

from quickview.ui.slice_selection import SliceSelection
from quickview.ui.projection_selection import ProjectionSelection
from quickview.ui.variable_selection import VariableSelection
from quickview.ui.view_settings import ViewProperties, ViewControls
from quickview.ui.toolbar import Toolbar

# Build color cache here
from quickview.view_manager import build_color_information
from quickview.view_manager import ViewManager

from paraview.simple import ImportPresets, GetLookupTableNames


# -----------------------------------------------------------------------------
# trame setup
# -----------------------------------------------------------------------------

noncvd = [
    {
        "text": "Rainbow Desat.",
        "value": "Rainbow Desaturated",
    },
    {
        "text": "Cool to Warm",
        "value": "Cool to Warm",
    },
    {
        "text": "Jet",
        "value": "Jet",
    },
    {
        "text": "Yellow-Gray-Blue",
        "value": "Yellow - Gray - Blue",
    },
]
cvd = []

save_state_keys = [
    # Data files
    "data_file",
    "conn_file",
    # Data slice related variables
    "tstamp",
    "midpoint",
    "interface",
    # Latitude/Longitude clipping
    "cliplat",
    "cliplong",
    # Projection and centering
    "projection",
    "center",
    # Color map related variables
    "variables",
    "varcolor",
    "uselogscale",
    "invert",
    "varmin",
    "varmax",
    "override_range",  # Track manual color range override per variable
    "varaverage",  # Track computed average per variable
    # Color options from toolbar
    "use_cvd_colors",
    "use_standard_colors",
    # Grid layout
    "layout",
]


try:
    existing = GetLookupTableNames()
    presdir = os.path.join(os.path.dirname(__file__), "presets")
    presets = os.listdir(path=presdir)
    for preset in presets:
        prespath = os.path.abspath(os.path.join(presdir, preset))
        if os.path.isfile(prespath):
            name = ET.parse(prespath).getroot()[0].attrib["name"]
            if name not in existing:
                print("Importing non existing preset ", name)
                ImportPresets(prespath)
            cvd.append({"text": name.title(), "value": name})
except Exception as e:
    print("Error loading presets :", e)


@TrameApp()
class EAMApp:
    def __init__(
        self,
        source: EAMVisSource = None,
        initserver: Union[Server, str] = None,
        initstate: dict = None,
        workdir: Union[str, Path] = None,
    ) -> None:
        server = get_server(initserver, client_type="vue2")
        state = server.state
        ctrl = server.controller

        self._ui = None
        self._cached_layout = {}  # Cache for layout positions by variable name

        self.workdir = workdir
        self.server = server
        pvWidgets.initialize(server)

        self.source = source
        self.viewmanager = ViewManager(source, server, state)

        # Load state variables from the source object

        state.data_file = source.data_file if source.data_file else ""
        state.conn_file = source.conn_file if source.conn_file else ""

        # Initialize slice selection state variables with defaults
        state.midpoint = 0  # Selected midpoint index
        state.interface = 0  # Selected interface index
        state.tstamp = 0
        state.timesteps = []
        state.midpoints = []  # Array of midpoint values
        state.interfaces = []  # Array of interface values
        state.cliplong = [-180.0, 180.0]
        state.cliplat = [-90.0, 90.0]

        # Initialize variable lists
        state.surface_vars = []
        state.midpoint_vars = []
        state.interface_vars = []
        state.surface_vars_state = []
        state.midpoint_vars_state = []
        state.interface_vars_state = []

        # Initialize other required state variables
        state.pipeline_valid = False
        state.extents = [-180.0, 180.0, -90.0, 90.0]
        state.variables = []
        state.colormaps = noncvd  # Initialize with default colormaps
        state.use_cvd_colors = False
        state.use_standard_colors = True

        # Initialize UI panel visibility states
        state.show_surface_vars = False
        state.show_midpoint_vars = False
        state.show_interface_vars = False
        state.show_slice = True  # Show slice selection by default
        state.show_projection = False

        # Only update from source if it's valid
        if source.valid:
            self.update_state_from_source()

        self.ind_surface = None
        self.ind_midpoint = None
        self.ind_interface = None
        state.views = []
        # state.projection    = "Cyl. Equidistant"
        # state.cliplong      = [self.source.extents[0], self.source.extents[1]],
        # state.cliplat       = [self.source.extents[2], self.source.extents[3]],
        # Removed cmaps initialization - now handled by toolbar toggle buttons
        state.layout = []
        state.variables = []
        state.ccardscolor = [None] * len(
            source.surface_vars + source.interface_vars + source.midpoint_vars
        )
        state.varcolor = []
        state.uselogscale = []
        state.invert = []
        state.varmin = []
        state.varmax = []
        state.override_range = []
        state.colorbar_images = []
        state.varaverage = []

        state.probe_enabled = False
        state.probe_location = []  # Default probe

        ctrl.view_update = self.viewmanager.render_all_views
        ctrl.view_reset_camera = self.viewmanager.reset_camera
        ctrl.on_server_ready.add(ctrl.view_update)
        server.trigger_name(ctrl.view_reset_camera)

        state.colormaps = noncvd

        self.state.pipeline_valid = source.valid
        # User controlled state variables
        if initstate is None:
            self.init_app_configuration()
        else:
            self.update_state_from_config(initstate)

    @property
    def state(self):
        return self.server.state

    @property
    def ctrl(self):
        return self.server.controller

    @life_cycle.server_ready
    def _tauri_ready(self, **_):
        os.write(1, f"tauri-server-port={self.server.port}\n".encode())

    @life_cycle.client_connected
    def _tauri_show(self, **_):
        os.write(1, "tauri-client-ready\n".encode())

    def init_app_configuration(self):
        source = self.source
        with self.state as state:
            state.midpoint = 0
            state.interface = 0
            state.tstamp = 0
            state.surface_vars_state = [False] * len(source.surface_vars)
            state.midpoint_vars_state = [False] * len(source.midpoint_vars)
            state.interface_vars_state = [False] * len(source.interface_vars)
        self.surface_vars_state = np.array([False] * len(source.surface_vars))
        self.midpoint_vars_state = np.array([False] * len(source.midpoint_vars))
        self.interface_vars_state = np.array([False] * len(source.interface_vars))

    def update_state_from_source(self):
        source = self.source
        with self.state as state:
            state.timesteps = source.timestamps
            state.midpoints = source.midpoints
            state.interfaces = source.interfaces
            state.extents = list(source.extents)
            state.surface_vars = source.surface_vars
            state.interface_vars = source.interface_vars
            state.midpoint_vars = source.midpoint_vars
            state.pipeline_valid = source.valid
            # Update clipping ranges from source extents
            if source.extents and len(source.extents) >= 4:
                state.cliplong = [source.extents[0], source.extents[1]]
                state.cliplat = [source.extents[2], source.extents[3]]

    def update_state_from_config(self, initstate):
        source = self.source
        with self.state as state:
            state.surface_vars = source.surface_vars
            state.interface_vars = source.interface_vars
            state.midpoint_vars = source.midpoint_vars
            state.update(initstate)

            selection = state.variables
            selection_surface = np.isin(state.surface_vars, selection).tolist()
            selection_midpoint = np.isin(state.midpoint_vars, selection).tolist()
            selection_interface = np.isin(state.interface_vars, selection).tolist()
            state.surface_vars_state = selection_surface
            state.midpoint_vars_state = selection_midpoint
            state.interface_vars_state = selection_interface

        self.surface_vars_state = np.array(selection_surface)
        self.midpoint_vars_state = np.array(selection_midpoint)
        self.interface_vars_state = np.array(selection_interface)

        self.viewmanager.registry = build_color_information(initstate)
        self.load_variables(use_cached_layout=True)

    @trigger("layout_changed")
    def on_layout_changed_trigger(self, layout, **kwargs):
        """Cache layout changes to ensure they are properly saved"""
        # Cache the layout data with variable names as keys for easier lookup
        self._cached_layout = {}
        if layout and hasattr(self.state, "variables"):
            for item in layout:
                if isinstance(item, dict) and "i" in item:
                    idx = item["i"]
                    if idx < len(self.state.variables):
                        var_name = self.state.variables[idx]
                        self._cached_layout[var_name] = {
                            "x": item.get("x", 0),
                            "y": item.get("y", 0),
                            "w": item.get("w", 4),
                            "h": item.get("h", 3),
                        }

    def generate_state(self):
        # Force state synchronization
        self.state.flush()

        all = self.state.to_dict()
        to_export = {k: all[k] for k in save_state_keys}

        # Convert cached layout back to array format for saving
        if self._cached_layout and hasattr(self.state, "variables"):
            layout_array = []
            for idx, var_name in enumerate(self.state.variables):
                if var_name in self._cached_layout:
                    pos = self._cached_layout[var_name]
                    layout_array.append(
                        {
                            "x": pos["x"],
                            "y": pos["y"],
                            "w": pos["w"],
                            "h": pos["h"],
                            "i": idx,
                        }
                    )
            if layout_array:
                to_export["layout"] = layout_array

        return to_export

    def load_state(self, state_file):
        from_state = json.loads(Path(state_file).read_text())
        data_file = from_state["data_file"]
        conn_file = from_state["conn_file"]
        # Convert loaded layout to variable-name-based cache
        self._cached_layout = {}
        if (
            "layout" in from_state
            and from_state["layout"]
            and "variables" in from_state
        ):
            for item in from_state["layout"]:
                if isinstance(item, dict) and "i" in item:
                    idx = item["i"]
                    if idx < len(from_state["variables"]):
                        var_name = from_state["variables"][idx]
                        self._cached_layout[var_name] = {
                            "x": item.get("x", 0),
                            "y": item.get("y", 0),
                            "w": item.get("w", 4),
                            "h": item.get("h", 3),
                        }
        self.source.Update(
            data_file=data_file,
            conn_file=conn_file,
        )
        self.update_state_from_source()
        self.update_state_from_config(from_state)

    def load_data(self):
        with self.state as state:
            # Update returns True/False for validity
            is_valid = self.source.Update(
                data_file=self.state.data_file,
                conn_file=self.state.conn_file,
            )
            state.pipeline_valid = is_valid

            # Update state based on pipeline validity
            if is_valid:
                self.update_state_from_source()
                self.init_app_configuration()
            else:
                # Keep the defaults that were set in __init__
                # but ensure arrays are empty if pipeline failed
                state.timesteps = []
                state.midpoints = []
                state.interfaces = []

    def load_variables(self, use_cached_layout=False):
        surf = []
        mid = []
        intf = []
        # Use the original unfiltered lists from source and the full selection state
        if len(self.source.surface_vars) > 0:
            v_surf = np.array(self.source.surface_vars)
            f_surf = (
                self.surface_vars_state
            )  # Use the full state array, not the filtered one
            if len(v_surf) == len(f_surf):  # Ensure arrays are same length
                surf = v_surf[f_surf].tolist()
        if len(self.source.midpoint_vars) > 0:
            v_mid = np.array(self.source.midpoint_vars)
            f_mid = self.midpoint_vars_state  # Use the full state array
            if len(v_mid) == len(f_mid):  # Ensure arrays are same length
                mid = v_mid[f_mid].tolist()
        if len(self.source.interface_vars) > 0:
            v_intf = np.array(self.source.interface_vars)
            f_intf = self.interface_vars_state  # Use the full state array
            if len(v_intf) == len(f_intf):  # Ensure arrays are same length
                intf = v_intf[f_intf].tolist()
        self.source.LoadVariables(surf, mid, intf)

        vars = surf + mid + intf

        # Tracking variables to control camera and color properties
        with self.state as state:
            state.variables = vars
            state.varcolor = [state.colormaps[0]["value"]] * len(vars)
            state.uselogscale = [False] * len(vars)
            state.invert = [False] * len(vars)
            state.varmin = [np.nan] * len(vars)
            state.varmax = [np.nan] * len(vars)
            state.override_range = [False] * len(vars)
            state.colorbar_images = [""] * len(vars)  # Initialize empty images
            state.varaverage = [np.nan] * len(vars)

            # Only use cached layout when explicitly requested (i.e., when loading state)
            layout_to_use = self._cached_layout if use_cached_layout else None
            self.viewmanager.rebuild_visualization_layout(layout_to_use)
            # Update cached layout after rebuild
            if state.layout and state.variables:
                self._cached_layout = {}
                for item in state.layout:
                    if isinstance(item, dict) and "i" in item:
                        idx = item["i"]
                        if idx < len(state.variables):
                            var_name = state.variables[idx]
                            self._cached_layout[var_name] = {
                                "x": item.get("x", 0),
                                "y": item.get("y", 0),
                                "w": item.get("w", 4),
                                "h": item.get("h", 3),
                            }

    def update_colormap(self, index, value):
        """Update the colormap for a variable."""
        self.viewmanager.update_colormap(index, value)

    def update_log_scale(self, index, value):
        """Update the log scale setting for a variable."""
        self.viewmanager.update_log_scale(index, value)

    def update_invert_colors(self, index, value):
        """Update the color inversion setting for a variable."""
        self.viewmanager.update_invert_colors(index, value)

    def update_scalar_bars(self, event):
        self.viewmanager.update_scalar_bars(event)

    def update_available_color_maps(self):
        with self.state as state:
            # Directly use the toggle states to determine which colormaps to show
            if state.use_cvd_colors and state.use_standard_colors:
                state.colormaps = cvd + noncvd
            elif state.use_cvd_colors:
                state.colormaps = cvd
            elif state.use_standard_colors:
                state.colormaps = noncvd
            else:
                # Fallback to standard colors if nothing is selected
                state.colormaps = noncvd

    def set_manual_color_range(self, index, type, value):
        # Get current values from state to handle min/max independently
        min_val = self.state.varmin[index] if type.lower() == "max" else value
        max_val = self.state.varmax[index] if type.lower() == "min" else value
        # Delegate to view manager which will update both the view and sync state
        self.viewmanager.set_manual_color_range(index, min_val, max_val)

    def revert_to_auto_color_range(self, index):
        self.viewmanager.revert_to_auto_color_range(index)

    def zoom(self, type):
        if type.lower() == "in":
            self.viewmanager.zoom_in()
        elif type.lower() == "out":
            self.viewmanager.zoom_out()

    def pan_camera(self, dir):
        if dir.lower() == "up":
            self.viewmanager.pan_camera(1, 0)
        elif dir.lower() == "down":
            self.viewmanager.pan_camera(1, 1)
        elif dir.lower() == "left":
            self.viewmanager.pan_camera(0, 1)
        elif dir.lower() == "right":
            self.viewmanager.pan_camera(0, 0)

    def update_surface_var_selection(self, index, event):
        self.state.surface_vars_state[index] = event
        self.state.dirty("surface_vars_state")
        if self.ind_surface is not None:
            ind = self.ind_surface[index]
            self.surface_vars_state[ind] = event
        else:
            self.surface_vars_state[index] = event

    def update_midpoint_var_selection(self, index, event):
        self.state.midpoint_vars_state[index] = event
        self.state.dirty("midpoint_vars_state")
        if self.ind_midpoint is not None:
            ind = self.ind_midpoint[index]
            self.midpoint_vars_state[ind] = event
        else:
            self.midpoint_vars_state[index] = event

    def update_interface_var_selection(self, index, event):
        self.state.interface_vars_state[index] = event
        self.state.dirty("interface_vars_state")
        if self.ind_interface is not None:
            ind = self.ind_interface[index]
            self.interface_vars_state[ind] = event
        else:
            self.interface_vars_state[index] = event

    def search_surface_vars(self, search: str):
        if search is None or len(search) == 0:
            filtVars = self.source.surface_vars
            self.ind_surface = None
            self.state.surface_vars = self.source.surface_vars
            self.state.surface_vars_state = self.surface_vars_state.tolist()
            self.state.dirty("surface_vars_state")
        else:
            filtered = [
                (idx, var)
                for idx, var in enumerate(self.source.surface_vars)
                if search.lower() in var.lower()
            ]
            filtVars = [var for (_, var) in filtered]
            self.ind_surface = [idx for (idx, _) in filtered]
        if self.ind_surface is not None:
            self.state.surface_vars = list(filtVars)
            self.state.surface_vars_state = self.surface_vars_state[
                self.ind_surface
            ].tolist()
            self.state.dirty("surface_vars_state")

    def search_midpoint_vars(self, search: str):
        if search is None or len(search) == 0:
            filtVars = self.source.midpoint_vars
            self.ind_midpoint = None
            self.state.midpoint_vars = self.source.midpoint_vars
            self.state.midpoint_vars_state = self.midpoint_vars_state.tolist()
            self.state.dirty("midpoint_vars_state")
        else:
            filtered = [
                (idx, var)
                for idx, var in enumerate(self.source.midpoint_vars)
                if search.lower() in var.lower()
            ]
            filtVars = [var for (_, var) in filtered]
            self.ind_midpoint = [idx for (idx, _) in filtered]
        if self.ind_midpoint is not None:
            self.state.midpoint_vars = list(filtVars)
            self.state.midpoint_vars_state = self.midpoint_vars_state[
                self.ind_midpoint
            ].tolist()
            self.state.dirty("midpoint_vars_state")

    def search_interface_vars(self, search: str):
        if search is None or len(search) == 0:
            filtVars = self.source.interface_vars
            self.ind_interface = None
            self.state.interface_vars = self.source.interface_vars
            self.state.interface_vars_state = self.interface_vars_state.tolist()
            self.state.dirty("interface_vars_state")
        else:
            filtered = [
                (idx, var)
                for idx, var in enumerate(self.source.interface_vars)
                if search.lower() in var.lower()
            ]
            filtVars = [var for (_, var) in filtered]
            self.ind_interface = [idx for (idx, _) in filtered]
        if self.ind_interface is not None:
            self.state.interface_vars = list(filtVars)
            self.state.interface_vars_state = self.interface_vars_state[
                self.ind_interface
            ].tolist()
            self.state.dirty("interface_vars_state")

    def clear_surface_vars(self):
        self.state.surface_vars_state = [False] * len(self.state.surface_vars_state)
        self.surface_vars_state = np.array([False] * len(self.surface_vars_state))
        self.state.dirty("surface_vars_state")

    def clear_midpoint_vars(self):
        self.state.midpoint_vars_state = [False] * len(self.state.midpoint_vars_state)
        self.midpoint_vars_state = np.array([False] * len(self.midpoint_vars_state))
        self.state.dirty("midpoint_vars_state")

    def clear_interface_vars(self):
        self.state.interface_vars_state = [False] * len(self.state.interface_vars_state)
        self.interface_vars_state = np.array([False] * len(self.interface_vars_state))
        self.state.dirty("interface_vars_state")

    def start(self, **kwargs):
        """Initialize the UI and start the server for GeoTrame."""
        self.ui.server.start(**kwargs)

    @property
    def ui(self) -> SinglePageWithDrawerLayout:
        if self._ui is None:
            self._ui = SinglePageWithDrawerLayout(self.server)
            with self._ui as layout:
                # layout.footer.clear()
                layout.title.set_text("EAM QuickView v1.0")

                with layout.toolbar as toolbar:
                    Toolbar(
                        toolbar,
                        self.server,
                        load_data=self.load_data,
                        load_state=self.load_state,
                        load_variables=self.load_variables,
                        update_available_color_maps=self.update_available_color_maps,
                        generate_state=self.generate_state,
                    )

                card_style = """
                    position: fixed;
                    bottom: 1rem;
                    right: 1rem;
                    height: 2.4rem;
                    z-index: 2;
                    display: flex;
                    align-items: center;
                """
                ViewControls(
                    zoom=self.zoom,
                    move=self.pan_camera,
                    style=card_style,
                )

                with layout.drawer as drawer:
                    drawer.width = 400
                    drawer.style = (
                        "background: none; border: none; pointer-events: none;"
                    )
                    drawer.tile = True

                    with v2.VCard(
                        classes="ma-2",
                        # elevation=5,
                        style="pointer-events: auto;",
                        flat=True,
                    ):
                        SliceSelection(self.source, self.viewmanager)

                        ProjectionSelection(self.source, self.viewmanager)

                        VariableSelection(
                            title="Surface Variables",
                            panel_name="show_surface_vars",
                            var_list="surface_vars",
                            var_list_state="surface_vars_state",
                            on_search=self.search_surface_vars,
                            on_clear=self.clear_surface_vars,
                            on_update=self.update_surface_var_selection,
                        )

                        VariableSelection(
                            title="Variables at Layer Midpoints",
                            panel_name="show_midpoint_vars",
                            var_list="midpoint_vars",
                            var_list_state="midpoint_vars_state",
                            on_search=self.search_midpoint_vars,
                            on_clear=self.clear_midpoint_vars,
                            on_update=self.update_midpoint_var_selection,
                        )

                        VariableSelection(
                            title="Variables at Layer Interfaces",
                            panel_name="show_interface_vars",
                            var_list="interface_vars",
                            var_list_state="interface_vars_state",
                            on_search=self.search_interface_vars,
                            on_clear=self.clear_interface_vars,
                            on_update=self.update_interface_var_selection,
                        )

                with layout.content:
                    with grid.GridLayout(
                        layout=("layout"),
                        col_num=12,
                        row_height=100,
                        is_draggable=True,
                        is_resizable=True,
                        vertical_compact=True,
                        layout_updated="layout = $event; trigger('layout_changed', [$event])",
                    ):
                        with grid.GridItem(
                            v_for="vref, idx in views",
                            key="vref",
                            v_bind=("layout[idx]",),
                            style="transition-property: none;",
                        ):
                            with v2.VCard(
                                classes="fill-height", style="overflow: hidden;"
                            ):
                                with v2.VCardText(
                                    style="height: calc(100% - 0.66rem); position: relative;",
                                    classes="pa-0",
                                ) as cardcontent:
                                    # VTK View fills entire space
                                    cardcontent.add_child(
                                        """
                                        <vtk-remote-view :ref="(el) => ($refs[vref] = el)" :viewId="get(`${vref}Id`)" class="pa-0 drag-ignore" style="width: 100%; height: 100%;" interactiveRatio="1" >
                                        </vtk-remote-view>
                                        """,
                                    )
                                    client.ClientTriggers(
                                        beforeDestroy="trigger('view_gc', [vref])",
                                        # mounted="""
                                        #        $nextTick(() => setTimeout(() => trigger('resetview', [
                                        #            idx,
                                        #            {
                                        #              width: Math.floor($refs[vref].vtkContainer.getBoundingClientRect().width),
                                        #              height: Math.floor($refs[vref].vtkContainer.getBoundingClientRect().height)
                                        #            }
                                        #        ]), 500))
                                        #        """,
                                        # mounted="$nextTick(() => setTimeout(() => console.log($refs[vref].vtkContainer.getBoundingClientRect()), 500))",
                                        # mounted="$nextTick(() => setTimeout(() => $refs[vref].render(), 500))",
                                        # mounted=(self.viewmanager.reset_specific_view, '''[idx,
                                        #         {width: $refs[vref].vtkContainer.getBoundingClientRect().width,
                                        #         height: $refs[vref].vtkContainer.getBoundingClientRect().height}]
                                        #         ''')
                                    )
                                    # Mask to prevent VTK view from getting scroll/mouse events
                                    html.Div(
                                        style="position:absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 1;"
                                    )
                                    # Top-left info: time and level info
                                    with html.Div(
                                        style="position: absolute; top: 8px; left: 8px; padding: 4px 8px; background-color: rgba(0, 0, 0, 0.7); color: white; font-size: 0.875rem; border-radius: 4px; z-index: 2;",
                                        classes="drag-ignore font-monospace",
                                    ):
                                        # Show time
                                        html.Div(
                                            "t = {{ tstamp }}",
                                            style="color: white;",
                                            classes="font-weight-medium",
                                        )
                                        # Show level for midpoint variables
                                        html.Div(
                                            v_if="midpoint_vars.includes(variables[idx])",
                                            children="k = {{ midpoint }}",
                                            style="color: white;",
                                            classes="font-weight-medium",
                                        )
                                        # Show level for interface variables
                                        html.Div(
                                            v_if="interface_vars.includes(variables[idx])",
                                            children="k = {{ interface }}",
                                            style="color: white;",
                                            classes="font-weight-medium",
                                        )
                                    # Top-right info: variable name and average
                                    with html.Div(
                                        style="position: absolute; top: 8px; right: 8px; padding: 4px 8px; background-color: rgba(0, 0, 0, 0.7); color: white; font-size: 0.875rem; border-radius: 4px; z-index: 2; text-align: right;",
                                        classes="drag-ignore font-monospace",
                                    ):
                                        # Variable name
                                        html.Div(
                                            "{{ variables[idx] }}",
                                            style="color: white;",
                                            classes="font-weight-medium",
                                        )
                                        # Average value
                                        html.Div(
                                            (
                                                "(avg: {{ "
                                                "varaverage[idx] !== null && !isNaN(varaverage[idx]) ? "
                                                "varaverage[idx].toExponential(2) : "
                                                "'N/A' "
                                                "}})"
                                            ),
                                            style="color: white;",
                                            classes="font-weight-medium",
                                        )
                                    # Colorbar container (horizontal layout at bottom)
                                    with html.Div(
                                        style="position: absolute; bottom: 8px; left: 8px; right: 8px; display: flex; align-items: center; justify-content: center; padding: 4px 8px 4px 8px; background-color: rgba(255, 255, 255, 0.1); height: 28px; z-index: 3; overflow: visible; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);",
                                        classes="drag-ignore",
                                    ):
                                        # View Properties button (small icon)
                                        ViewProperties(
                                            update_colormap=self.update_colormap,
                                            update_log_scale=self.update_log_scale,
                                            update_invert=self.update_invert_colors,
                                            update_range=self.set_manual_color_range,
                                            reset=self.revert_to_auto_color_range,
                                            style="margin-right: 8px; display: flex; align-items: center;",
                                        )
                                        # Color min value
                                        html.Span(
                                            (
                                                "{{ "
                                                "varmin[idx] !== null && !isNaN(varmin[idx]) ? ("
                                                "uselogscale[idx] && varmin[idx] > 0 ? "
                                                "'10^(' + Math.log10(varmin[idx]).toFixed(2) + ')' : "
                                                "varmin[idx].toExponential(3)"
                                                ") : 'Auto' "
                                                "}}"
                                            ),
                                            style="color: white;",
                                            classes="font-weight-medium",
                                        )
                                        # Colorbar
                                        with html.Div(
                                            style="flex: 1; display: flex; align-items: center; margin: 0 8px; height: 0.6rem; position: relative;",
                                            classes="drag-ignore",
                                        ):
                                            # Colorbar image
                                            html.Img(
                                                src=(
                                                    "colorbar_images[idx] || 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='",
                                                    None,
                                                ),
                                                style="height: 100%; width: 100%; object-fit: fill;",
                                                classes="rounded-lg border-thin",
                                                v_on=(
                                                    "{"
                                                    "mousemove: (e) => { "
                                                    "const rect = e.target.getBoundingClientRect(); "
                                                    "const x = e.clientX - rect.left; "
                                                    "const width = rect.width; "
                                                    "const fraction = Math.max(0, Math.min(1, x / width)); "
                                                    "probe_location = [x, width, fraction, idx]; "
                                                    "}, "
                                                    "mouseenter: () => { probe_enabled = true; }, "
                                                    "mouseleave: () => { probe_enabled = false; probe_location = null; } "
                                                    "}"
                                                ),
                                            )
                                            # Probe tooltip (pan3d style - as sibling to colorbar)
                                            html.Div(
                                                v_if="probe_enabled && probe_location && probe_location[3] === idx",
                                                v_bind_style="{position: 'absolute', bottom: '100%', left: probe_location[0] + 'px', transform: 'translateX(-50%)', marginBottom: '0.25rem', backgroundColor: '#000000', color: '#ffffff', padding: '0.25rem 0.5rem', borderRadius: '0.25rem', fontSize: '0.875rem', whiteSpace: 'nowrap', pointerEvents: 'none', zIndex: 1000, fontFamily: 'monospace', boxShadow: '0 2px 4px rgba(0,0,0,0.3)'}",
                                                children=(
                                                    "{{ "
                                                    "probe_location && varmin[idx] !== null && varmax[idx] !== null ? ("
                                                    "uselogscale[idx] && varmin[idx] > 0 && varmax[idx] > 0 ? "
                                                    "'10^(' + ("
                                                    "Math.log10(varmin[idx]) + "
                                                    "(Math.log10(varmax[idx]) - Math.log10(varmin[idx])) * probe_location[2]"
                                                    ").toFixed(2) + ')' : "
                                                    "(varmin[idx] + (varmax[idx] - varmin[idx]) * probe_location[2]).toExponential(3)"
                                                    ") : '' "
                                                    "}}"
                                                ),
                                            )
                                        # Color max value
                                        html.Span(
                                            (
                                                "{{ "
                                                "varmax[idx] !== null && !isNaN(varmax[idx]) ? ("
                                                "uselogscale[idx] && varmax[idx] > 0 ? "
                                                "'10^(' + Math.log10(varmax[idx]).toFixed(2) + ')' : "
                                                "varmax[idx].toExponential(3)"
                                                ") : 'Auto' "
                                                "}}"
                                            ),
                                            style="color: white;",
                                            classes="font-weight-medium",
                                        )

        return self._ui

import os
import json
import base64
import numpy as np
import xml.etree.ElementTree as ET

from pathlib import Path
from typing import Union

from trame.app import TrameApp
from trame.decorators import life_cycle, trigger, change
from trame.ui.vuetify import SinglePageWithDrawerLayout

from trame.widgets import vuetify as v2, client
from trame.widgets import paraview as pvWidgets

from trame_server.core import Server

from e3sm_quickview.pipeline import EAMVisSource

from e3sm_quickview.ui.slice_selection import SliceSelection
from e3sm_quickview.ui.projection_selection import ProjectionSelection
from e3sm_quickview.ui.variable_selection import VariableSelection
from e3sm_quickview.ui.toolbar import Toolbar
from e3sm_quickview.ui.grid import Grid

# Build color cache here
from e3sm_quickview.view_manager import build_color_information
from e3sm_quickview.view_manager import ViewManager

from paraview.simple import ImportPresets, GetLookupTableNames

from paraview.modules import vtkRemotingCore as rc

try:
    from trame.widgets import tauri
except ImportError:
    # Fallback if tauri is not available
    tauri = None

rc.vtkProcessModule.GetProcessModule().UpdateProcessType(
    rc.vtkProcessModule.PROCESS_BATCH, 0
)

# -----------------------------------------------------------------------------
# Load logo image as base64
# -----------------------------------------------------------------------------


def get_logo_base64():
    """Load the QuickView logo as base64 encoded string."""
    logo_path = Path(__file__).parent / "assets" / "quick-view-text.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""  # Return empty string if logo not found


# Cache the logo at module load time
LOGO_BASE64 = get_logo_base64()

# -----------------------------------------------------------------------------
# trame setup
# -----------------------------------------------------------------------------

noncvd = [
    {
        "text": "Rainbow Desat.",
        "value": "Rainbow Desaturated",
    },
    {
        "text": "Yellow-Gray-Blue",
        "value": "Yellow - Gray - Blue",
    },
    {
        "text": "Blue Orange (div.)",
        "value": "Blue Orange (divergent)",
    },
    {
        "text": "Cool to Warm (Ext.)",
        "value": "Cool to Warm (Extended)",
    },
    {
        "text": "Black-Body Rad.",
        "value": "Black-Body Radiation",
    },
    {
        "text": "Blue-Green-Orange",
        "value": "Blue - Green - Orange",
    },
]

cvd = [
    {
        "text": "Inferno (matplotlib)",
        "value": "Inferno (matplotlib)",
    },
    {
        "text": "Viridis (matplotlib)",
        "value": "Viridis (matplotlib)",
    },
]

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


class EAMApp(TrameApp):
    def __init__(
        self,
        source: EAMVisSource = None,
        initserver: Union[Server, str] = None,
        initstate: dict = None,
        workdir: Union[str, Path] = None,
    ) -> None:
        super().__init__(initserver, client_type="vue2")

        self._ui = None
        self._cached_layout = {}  # Cache for layout positions by variable name

        pvWidgets.initialize(self.server)

        self.source = source
        self.viewmanager = ViewManager(source, self.server, self.state)

        state = self.state
        state.tauri_avail = False
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

        ctrl = self.ctrl
        ctrl.view_update = self.viewmanager.render_all_views
        ctrl.view_reset_camera = self.viewmanager.reset_camera
        ctrl.on_server_ready.add(ctrl.view_update)

        self.server.trigger_name(ctrl.view_reset_camera)

        state.colormaps = noncvd

        self.state.pipeline_valid = source.valid
        # User controlled state variables
        if initstate is None:
            self.init_app_configuration()
        else:
            self.update_state_from_config(initstate)

    @life_cycle.server_ready
    def _tauri_ready(self, **_):
        os.write(1, f"tauri-server-port={self.server.port}\n".encode())

    @life_cycle.client_connected
    def _tauri_show(self, **_):
        os.write(1, "tauri-client-ready\n".encode())

    @change("pipeline_valid")
    def _on_change_pipeline_valid(self, pipeline_valid, **kwargs):
        if not pipeline_valid:
            source = self.source
            state = self.state
            state.surface_vars_state = [False] * len(source.surface_vars)
            state.midpoint_vars_state = [False] * len(source.midpoint_vars)
            state.interface_vars_state = [False] * len(source.interface_vars)

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
        self.state.update(initstate)

        with self.state as state:
            state.surface_vars = source.surface_vars
            state.interface_vars = source.interface_vars
            state.midpoint_vars = source.midpoint_vars
            selection = state.variables
            selection_surface = np.isin(state.surface_vars, selection).tolist()
            selection_midpoint = np.isin(state.midpoint_vars, selection).tolist()
            selection_interface = np.isin(state.interface_vars, selection).tolist()
            state.surface_vars_state = selection_surface
            state.midpoint_vars_state = selection_midpoint
            state.interface_vars_state = selection_interface
        self.update_available_color_maps()
        self.surface_vars_state = np.array(selection_surface)
        self.midpoint_vars_state = np.array(selection_midpoint)
        self.interface_vars_state = np.array(selection_interface)

        self.viewmanager.registry = build_color_information(initstate)
        self.load_variables(use_cached_layout=True)

    @trigger("layout_changed")
    def on_layout_changed_trigger(self, layout, **kwargs):
        # There should always be a 1:1 correspondence
        # between the layout and the variables
        assert len(layout) == len(self.state.variables)
        # Cache the layout data with variable names as keys for easier lookup
        self._cached_layout = {}
        for idx, item in enumerate(layout):
            if idx < len(self.state.variables):
                var_name = self.state.variables[idx]
                self._cached_layout[var_name] = {
                    "i": idx,
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
        self._on_change_pipeline_valid(False)
        self.viewmanager._on_change_pipeline_valid(False)
        self.state.pipeline_valid = False
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
        is_valid = self.source.Update(
            data_file=data_file,
            conn_file=conn_file,
        )
        if is_valid:
            self.update_state_from_source()
            self.update_state_from_config(from_state)
        self.state.pipeline_valid = is_valid

        self.ctrl.view_reset_camera()

    def load_data(self):
        self._on_change_pipeline_valid(False)
        self.viewmanager._on_change_pipeline_valid(False)
        state = self.state
        # Update returns True/False for validity
        # force_reload=True since user explicitly clicked Load Files button
        is_valid = self.source.Update(
            data_file=self.state.data_file,
            conn_file=self.state.conn_file,
            force_reload=True,
        )

        # Update state based on pipeline validity
        if is_valid:
            self.update_state_from_source()
            self.init_app_configuration()
        else:
            # Keep the defaults that were set in __init__
            # but ensure arrays are empty if pipeline
            state.timesteps = []
            state.midpoints = []
            state.interfaces = []

        state.pipeline_valid = is_valid

    def get_default_colormap(self):
        """
        Determine the default colormap based on availability.
        Returns 'Batlow' if CVD colormaps are available,
        'Cool to Warm (Extended)' for non-CVD, or falls back to first available.
        """
        if cvd:  # CVD colormaps are available
            # Look for Batlow in current colormaps
            for cmap in self.state.colormaps:
                if cmap["value"].lower() == "batlow":
                    return cmap["value"]
        else:  # Only non-CVD colormaps available
            # Look for Cool to Warm (Extended)
            for cmap in self.state.colormaps:
                if cmap["value"] == "Cool to Warm (Extended)":
                    return cmap["value"]

        # Fallback to first available colormap
        return (
            self.state.colormaps[0]["value"]
            if self.state.colormaps
            else "Cool to Warm (Extended)"
        )

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

        print("Load surf", surf)
        print("Load mid", mid)
        print("Load intf", intf)
        self.source.LoadVariables(surf, mid, intf)

        vars = surf + mid + intf
        varorigin = [0] * len(surf) + [1] * len(mid) + [2] * len(intf)

        # Tracking variables to control camera and color properties
        with self.state as state:
            state.variables = vars
            state.varorigin = varorigin

            # Initialize arrays that are always needed regardless of cache status
            # Color configuration arrays will be populated by ViewContext via sync_color_config_to_state
            if not use_cached_layout:
                # Initialize empty arrays - ViewContext will populate them through sync
                state.varcolor = [""] * len(vars)
                state.uselogscale = [False] * len(vars)
                state.invert = [False] * len(vars)
                state.varmin = [np.nan] * len(vars)
                state.varmax = [np.nan] * len(vars)
                state.override_range = [False] * len(vars)
                state.colorbar_images = [""] * len(vars)  # Initialize empty images
                state.varaverage = [np.nan] * len(vars)
            else:
                # Preserve loaded values but ensure arrays match variable count
                # Extend or trim arrays to match new variable count if needed
                current_len = (
                    len(state.varcolor)
                    if hasattr(state, "varcolor") and state.varcolor
                    else 0
                )
                if current_len != len(vars):
                    # If array lengths don't match, extend with empty strings or trim
                    # ViewContext will populate correct values through sync
                    state.varcolor = (state.varcolor + [""] * len(vars))[: len(vars)]
                    state.uselogscale = (state.uselogscale + [False] * len(vars))[
                        : len(vars)
                    ]
                    state.invert = (state.invert + [False] * len(vars))[: len(vars)]
                    state.varmin = (state.varmin + [np.nan] * len(vars))[: len(vars)]
                    state.varmax = (state.varmax + [np.nan] * len(vars))[: len(vars)]
                    state.override_range = (state.override_range + [False] * len(vars))[
                        : len(vars)
                    ]
                    state.varaverage = (state.varaverage + [np.nan] * len(vars))[
                        : len(vars)
                    ]
                # Always reset colorbar images as they need to be regenerated
                state.colorbar_images = [""] * len(vars)

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
            state.colormaps.sort(key=lambda x: x["text"])

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
        with self.state as state:
            state.surface_vars_state[index] = event
        if self.ind_surface is not None:
            ind = self.ind_surface[index]
            self.surface_vars_state[ind] = event
        else:
            self.surface_vars_state[index] = event
        self.state.dirty("surface_vars_state")

    def update_midpoint_var_selection(self, index, event):
        with self.state as state:
            state.midpoint_vars_state[index] = event
        if self.ind_midpoint is not None:
            ind = self.ind_midpoint[index]
            self.midpoint_vars_state[ind] = event
        else:
            self.midpoint_vars_state[index] = event
        self.state.dirty("midpoint_vars_state")

    def update_interface_var_selection(self, index, event):
        with self.state as state:
            state.interface_vars_state[index] = event
        if self.ind_interface is not None:
            ind = self.ind_interface[index]
            self.interface_vars_state[ind] = event
        else:
            self.interface_vars_state[index] = event
        self.state.dirty("interface_vars_state")

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

    def clear_surface_vars(self, clear_var_name):
        self.state[clear_var_name] = ""
        self.ind_surface = None
        self.state.surface_vars = self.source.surface_vars
        self.state.surface_vars_state = [False] * len(self.source.surface_vars)
        self.surface_vars_state = np.array([False] * len(self.source.surface_vars))
        self.state.dirty("surface_vars_state")

    def clear_midpoint_vars(self, clear_var_name):
        self.state[clear_var_name] = ""
        self.ind_midpoint = None
        self.state.midpoint_vars = self.source.midpoint_vars
        self.state.midpoint_vars_state = [False] * len(self.source.midpoint_vars)
        self.midpoint_vars_state = np.array([False] * len(self.source.midpoint_vars))
        self.state.dirty("midpoint_vars_state")

    def clear_interface_vars(self, clear_var_name):
        self.state[clear_var_name] = ""
        self.ind_interface = None
        self.state.interface_vars = self.source.interface_vars
        self.state.interface_vars_state = [False] * len(self.source.interface_vars)
        self.interface_vars_state = np.array([False] * len(self.source.interface_vars))
        self.state.dirty("interface_vars_state")

    def close_view(self, index):
        var = self.state.variables.pop(index)
        origin = self.state.varorigin.pop(index)
        self._cached_layout.pop(var)
        self.state.dirty("variables")
        self.state.dirty("varorigin")
        self.viewmanager.close_view(var, index, self._cached_layout)
        state = self.state

        # Find variable to unselect from the UI
        if origin == 0:
            # Find and clear surface display
            if var in state.surface_vars:
                var_index = state.surface_vars.index(var)
                self.update_surface_var_selection(var_index, False)
        elif origin == 1:
            # Find and clear midpoints display
            if var in state.midpoint_vars:
                var_index = state.midpoint_vars.index(var)
                self.update_midpoint_var_selection(var_index, False)
        elif origin == 2:
            # Find and clear interface display
            if var in state.interface_vars:
                var_index = state.interface_vars.index(var)
                self.update_interface_var_selection(var_index, False)

    def start(self, **kwargs):
        """Initialize the UI and start the server for GeoTrame."""
        self.ui.server.start(**kwargs)

    @property
    def ui(self) -> SinglePageWithDrawerLayout:
        if self._ui is None:
            self._ui = SinglePageWithDrawerLayout(self.server)
            with self._ui as layout:
                layout.footer.clear()
                layout.title.clear()

                # Initialize Tauri if available
                if tauri:
                    tauri.initialize(self.server)
                    with tauri.Dialog() as dialog:
                        self.ctrl.open = dialog.open
                        self.ctrl.save = dialog.save
                else:
                    # Fallback for non-tauri environments
                    self.ctrl.open = lambda title: None
                    self.ctrl.save = lambda title: None

                client.ClientTriggers(
                    mounted="tauri_avail = window.__TAURI__ !== undefined;"
                )

                """
                with html.Div(
                    style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 4px 8px;",
                ):
                    (
                        html.Img(
                            src=f"data:image/png;base64,{LOGO_BASE64}",
                            style="height: 30px; width: 60px; border-radius: 4px; margin-bottom: 2px;",
                        ),
                    )
                    html.Span(
                        f"v{version}",
                        style="font-size: 12px; color: rgba(0, 0, 0, 0.8); font-weight: 700; letter-spacing: 0.3px; line-height: 1;",
                    )
                """
                with layout.toolbar as toolbar:
                    Toolbar(
                        toolbar,
                        self.server,
                        load_data=self.load_data,
                        load_state=self.load_state,
                        load_variables=self.load_variables,
                        update_available_color_maps=self.update_available_color_maps,
                        generate_state=self.generate_state,
                        zoom=self.zoom,
                        move=self.pan_camera,
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
                    Grid(
                        self.server,
                        self.viewmanager,
                        self.close_view,
                    )
        return self._ui

import os
import json
import numpy as np
import xml.etree.ElementTree as ET

from pathlib import Path
from typing import Union

from trame.app import get_server
from trame.decorators import TrameApp, life_cycle
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

from quickview.utilities import EventType

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
    "vlev",
    "vilev",
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
    # Color options from toolbar
    "use_cvd_colors",
    "use_standard_colors",
    "show_color_bar",
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

        self.workdir = workdir
        self.server = server
        pvWidgets.initialize(server)

        self.source = source
        self.viewmanager = ViewManager(source, server, state)

        # Load state variables from the source object

        state.data_file = source.data_file if source.data_file else ""
        state.conn_file = source.conn_file if source.conn_file else ""

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
            state.vlev = 0
            state.vilev = 0
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
            state.lev = source.lev
            state.ilev = source.ilev
            state.extents = list(source.extents)
            state.surface_vars = source.surface_vars
            state.interface_vars = source.interface_vars
            state.midpoint_vars = source.midpoint_vars
            state.pipeline_valid = source.valid

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
        self.load_variables()

    def generate_state(self):
        all = self.state.to_dict()
        to_export = {k: all[k] for k in save_state_keys}
        # with open(os.path.join(self.workdir, "state.json"), "w") as outfile:
        return to_export

    def load_state(self, state_file):
        from_state = json.loads(Path(state_file).read_text())
        data_file = from_state["data_file"]
        conn_file = from_state["conn_file"]
        self.source.Update(
            data_file=data_file,
            conn_file=conn_file,
        )
        self.update_state_from_source()
        self.update_state_from_config(from_state)

    def load_data(self):
        with self.state as state:
            state.pipeline_valid = self.source.Update(
                data_file=self.state.data_file,
                conn_file=self.state.conn_file,
            )
            self.init_app_configuration()
            self.update_state_from_source()

    def load_variables(self):
        surf = []
        mid = []
        intf = []
        if len(self.state.surface_vars) > 0:
            v_surf = np.array(self.state.surface_vars)
            f_surf = np.array(self.state.surface_vars_state)
            surf = v_surf[f_surf].tolist()
        if len(self.state.midpoint_vars) > 0:
            v_mid = np.array(self.state.midpoint_vars)
            f_mid = np.array(self.state.midpoint_vars_state)
            mid = v_mid[f_mid].tolist()
        if len(self.state.interface_vars) > 0:
            v_intf = np.array(self.state.interface_vars)
            f_intf = np.array(self.state.interface_vars_state)
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

            self.viewmanager.rebuild_visualization_layout()

    def update_view_color_settings(self, index, type, value):
        with self.state as state:
            if type == EventType.COL.value:
                state.varcolor[index] = value
                state.dirty("varcolor")
            elif type == EventType.LOG.value:
                state.uselogscale[index] = value
                state.dirty("uselogscale")
            elif type == EventType.INV.value:
                state.invert[index] = value
                state.dirty("invert")
            self.viewmanager.update_view_color_settings(index, type, value)

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
        with self.state as state:
            if type.lower() == "min":
                state.varmin[index] = value
                state.dirty("varmin")
            elif type.lower() == "max":
                state.varmax[index] = value
                state.dirty("varmax")
            self.viewmanager.set_manual_color_range(
                index, state.varmin[index], state.varmax[index]
            )

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
                        update_scalar_bars=self.update_scalar_bars,
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
                        layout=("layout", []),
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
                                    html.Div(
                                        style="position:absolute; top: 0; left: 0; width: 100%; height: calc(100% - 0.66rem); z-index: 1;"
                                    )
                                    # with v2.VCardActions(classes="pa-0"):
                                    with html.Div(
                                        style="position:absolute; bottom: 1rem; left: 1rem; height: 2rem; z-index: 2;"
                                    ):
                                        ViewProperties(
                                            apply=self.update_view_color_settings,
                                            update=self.set_manual_color_range,
                                            reset=self.revert_to_auto_color_range,
                                        )

        return self._ui

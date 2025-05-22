import os
import json
import numpy as np
import xml.etree.ElementTree as ET

from pathlib import Path
from typing import Union

from trame.app import get_server
from trame.decorators import TrameApp, change, life_cycle
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
    "DataFile",
    "ConnFile",
    # Data slice related related variables
    "vlev",
    "vilev",
    "vars2Dstate",
    "vars3Distate",
    "vars3Dmstate",
    # Latitude/Longitude clipping
    "cliplat",
    "cliplong",
    # Projection
    "projection",
    # Color map related variables
    "ccardsentry",
    "varcolor",
    "uselogscale",
    "varmin",
    "varmax",
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
        self.state = state
        self.ctrl = ctrl
        pvWidgets.initialize(server)

        self.source = source
        self.viewmanager = ViewManager(source, server, state)

        # Load state variables from the source object

        state.DataFile = source.data_file if source.data_file else ""
        state.ConnFile = source.conn_file if source.conn_file else ""

        self.update_state_from_source()

        self.ind2d = None
        self.ind3dm = None
        self.ind3di = None
        state.views = []
        # state.projection    = "Cyl. Equidistant"
        # state.cliplong      = [self.source.extents[0], self.source.extents[1]],
        # state.cliplat       = [self.source.extents[2], self.source.extents[3]],
        state.cmaps = ["1"]
        state.layout = []
        state.ccardsentry = []
        state.ccardscolor = [None] * len(
            source.vars2D + source.vars3Di + source.vars3Dm
        )
        state.varcolor = []
        state.uselogscale = []
        state.invert = []
        state.varmin = []
        state.varmax = []

        state.export_config = False
        state.exported_state = None
        state.export_completed = False
        state.state_save_file = None

        ctrl.view_update = self.viewmanager.reset_views
        ctrl.view_reset_camera = self.viewmanager.reset_camera
        ctrl.on_server_ready.add(ctrl.view_update)
        server.trigger_name(ctrl.view_reset_camera)

        state.colormaps = noncvd

        # User controlled state varialbes
        if initstate is None:
            self.init_app_configuration()
        else:
            state.update(initstate)
            # Build color cache here
            from quickview.view_manager import build_color_information

            self.viewmanager.cache = build_color_information(initstate)
            self.load_variables()

    @life_cycle.server_ready
    def _tauri_ready(self, **_):
        print(f"\ntauri-server-port={self.server.port}", flush=True)

    @life_cycle.client_connected
    def _tauri_show(self, **_):
        print("\ntauri-client-ready", flush=True)

    def init_app_configuration(self):
        state = self.state
        source = self.source
        state.vlev = 0
        state.vilev = 0
        state.tstamp = 0
        state.vars2Dstate = [False] * len(source.vars2D)
        state.vars3Dmstate = [False] * len(source.vars3Dm)
        state.vars3Distate = [False] * len(source.vars3Di)
        self.vars2Dstate = np.array([False] * len(source.vars2D))
        self.vars3Dmstate = np.array([False] * len(source.vars3Dm))
        self.vars3Distate = np.array([False] * len(source.vars3Di))

    def update_state_from_source(self):
        state = self.state
        source = self.source
        state.timesteps = source.timestamps
        state.lev = source.lev
        state.ilev = source.ilev
        state.extents = list(source.extents)
        state.vars2D = source.vars2D
        state.vars3Di = source.vars3Di
        state.vars3Dm = source.vars3Dm

    def generate_state(self):
        all = self.state.to_dict()
        to_export = {k: all[k] for k in save_state_keys}
        # with open(os.path.join(self.workdir, "state.json"), "w") as outfile:
        return json.dumps(to_export, indent=2)

    def load_data(self):
        self.source.Update(
            data_file=self.state.DataFile,
            conn_file=self.state.ConnFile,
        )
        self.init_app_configuration()
        self.update_state_from_source()

    def load_variables(self):
        s2d = []
        s3dm = []
        s3di = []
        if len(self.state.vars2D) > 0:
            v2d = np.array(self.state.vars2D)
            f2d = np.array(self.state.vars2Dstate)
            s2d = v2d[f2d].tolist()
        if len(self.state.vars3Dm) > 0:
            v3dm = np.array(self.state.vars3Dm)
            f3dm = np.array(self.state.vars3Dmstate)
            s3dm = v3dm[f3dm].tolist()
        if len(self.state.vars3Di) > 0:
            v3di = np.array(self.state.vars3Di)
            f3di = np.array(self.state.vars3Distate)
            s3di = v3di[f3di].tolist()
        self.source.LoadVariables(s2d, s3dm, s3di)

        vars = s2d + s3dm + s3di

        self.state.ccardsentry = vars

        self.state.ccardsvars = [{"text": var, "value": var} for var in vars]
        self.state.varcolor = [self.state.colormaps[0]["value"]] * len(vars)
        self.state.uselogscale = [False] * len(vars)
        self.state.invert = [False] * len(vars)
        self.state.varmin = [np.nan] * len(vars)
        self.state.varmax = [np.nan] * len(vars)

        with self.state:
            self.viewmanager.create_or_update_views()

    def apply_colormap(self, index, type, value):
        if type == EventType.COL.value:
            self.state.varcolor[index] = value
            self.state.dirty("varcolor")
        elif type == EventType.LOG.value:
            self.state.uselogscale[index] = value
            self.state.dirty("uselogscale")
        elif type == EventType.INV.value:
            self.state.invert[index] = value
            self.state.dirty("invert")
        self.viewmanager.apply_colormap(index, type, value)

    def update_scalar_bars(self, event):
        self.viewmanager.update_scalar_bars(event)

    def update_available_color_maps(self, event):
        if len(event) == 0:
            self.state.colormaps = noncvd
        elif len(event) == 2:
            self.state.colormaps = cvd + noncvd
        elif "0" in event:
            self.state.colormaps = cvd
        elif "1" in event:
            self.state.colormaps = noncvd

    def update_view_color_properties(self, index, type, value):
        if type.lower() == "min":
            self.state.varmin[index] = value
            self.state.dirty("varmin")
        elif type.lower() == "max":
            self.state.varmax[index] = value
            self.state.dirty("varmax")
        self.viewmanager.update_view_color_properties(
            index, self.state.varmin[index], self.state.varmax[index]
        )

    def reset_view_color_properties(self, index):
        self.viewmanager.reset_view_color_properties(index)

    def zoom(self, type):
        if type.lower() == "in":
            self.viewmanager.zoom_in()
        elif type.lower() == "out":
            self.viewmanager.zoom_out()
        pass

    def move(self, dir):
        if dir.lower() == "up":
            self.viewmanager.move(1, 0)
        elif dir.lower() == "down":
            self.viewmanager.move(1, 1)
        elif dir.lower() == "left":
            self.viewmanager.move(0, 1)
        elif dir.lower() == "right":
            self.viewmanager.move(0, 0)

    '''
    def export_config(self, config_file: Union[str, Path, None] = None) -> None:
        """Export the current state to a JSON configuration file.

        Parameters:
            config_file: Can be a string or Path representing the destination of the JSON configuration file.
                If None, a dictionary containing the current configuration will be returned.
                For details, see Configuration Files documentation.
        """
        # Populate config as a map
        config = {

        }
        if config_file:
            Path(config_file).write_text(json.dumps(config))
        return config
    '''

    def update_2D_variable_selection(self, index, event):
        self.state.vars2Dstate[index] = event
        self.state.dirty("vars2Dstate")
        if self.ind2d is not None:
            ind = self.ind2d[index]
            self.vars2Dstate[ind] = event
        else:
            self.vars2Dstate[index] = event

    def update_3Dm_variable_selection(self, index, event):
        self.state.vars3Dmstate[index] = event
        self.state.dirty("vars3Dmstate")
        if self.ind3dm is not None:
            ind = self.ind3dm[index]
            self.vars3Dmstate[ind] = event
        else:
            self.vars3Dmstate[index] = event

    def update_3Di_variable_selection(self, index, event):
        self.state.vars3Distate[index] = event
        self.state.dirty("vars3Distate")
        if self.ind3di is not None:
            ind = self.ind3di[index]
            self.vars3Distate[ind] = event
        else:
            self.vars3Distate[index] = event

    def search_2D_variables(self, search: str):
        if search is None or len(search) == 0:
            filtVars = self.source.vars2D
            self.ind2d = None
            self.state.vars2D = self.source.vars2D
            self.state.vars2Dstate = self.vars2Dstate.tolist()
            self.state.dirty("vars2Dstate")
        else:
            filtered = [
                (idx, var)
                for idx, var in enumerate(self.source.vars2D)
                if search.lower() in var.lower()
            ]
            filtVars = [var for (_, var) in filtered]
            self.ind2d = [idx for (idx, _) in filtered]
        if self.ind2d is not None:
            self.state.vars2D = list(filtVars)
            self.state.vars2Dstate = self.vars2Dstate[self.ind2d].tolist()
            self.state.dirty("vars2Dstate")

    def search_3Dm_variables(self, search: str):
        if search is None or len(search) == 0:
            filtVars = self.source.vars3Dm
            self.ind3dm = None
            self.state.vars3Dm = self.source.vars3Dm
            self.state.vars3Dmstate = self.vars3Dmstate.tolist()
            self.state.dirty("vars3Dmstate")
        else:
            filtered = [
                (idx, var)
                for idx, var in enumerate(self.source.vars3Dm)
                if search.lower() in var.lower()
            ]
            filtVars = [var for (_, var) in filtered]
            self.ind3dm = [idx for (idx, _) in filtered]
        if self.ind3dm is not None:
            self.state.vars3Dm = list(filtVars)
            self.state.vars3Dmstate = self.vars3Dmstate[self.ind3dm].tolist()
            self.state.dirty("vars3Dmstate")

    def search_3Di_variables(self, search: str):
        if search is None or len(search) == 0:
            filtVars = self.source.vars3Di
            self.ind3di = None
            self.state.vars3Di = self.source.vars3Di
            self.state.vars3Distate = self.vars3Distate.tolist()
            self.state.dirty("vars3Distate")
        else:
            filtered = [
                (idx, var)
                for idx, var in enumerate(self.source.vars3Di)
                if search.lower() in var.lower()
            ]
            filtVars = [var for (_, var) in filtered]
            self.ind3di = [idx for (idx, _) in filtered]
        if self.ind3dm is not None:
            self.state.vars3Di = list(filtVars)
            self.state.vars3Distate = self.vars3Distate[self.ind3di].tolist()
            self.state.dirty("vars3Distate")

    def clear_2D_variables(self):
        self.state.vars2Dstate = [False] * len(self.state.vars2Dstate)
        self.vars2Dstate = np.array([False] * len(self.vars2Dstate))
        self.state.dirty("vars2Dstate")

    def clear_3Dm_variables(self):
        self.state.vars3Dmstate = [False] * len(self.state.vars3Dmstate)
        self.vars3Dmstate = np.array([False] * len(self.vars3Dmstate))
        self.state.dirty("vars3Dmstate")

    def clear_3Di_variables(self):
        self.state.vars3Distate = [False] * len(self.state.vars3Distate)
        self.vars3Distate = np.array([False] * len(self.vars3Distate))
        self.state.dirty("vars3Distate")

    def start(self, **kwargs):
        """Initialize the UI and start the server for GeoTrame."""
        self.ui.server.start(**kwargs)

    def import_config(self):
        return

    def export_config(self, config_file: Union[str, Path, None] = None) -> None:
        pass

    @change("export_config")
    def export(self, export_config, **kwargs):
        self.state.export_completed = False
        self.state.exported_state = self.generate_state()

    @property
    def ui(self) -> SinglePageWithDrawerLayout:
        if self._ui is None:
            self._ui = SinglePageWithDrawerLayout(self.server)
            with self._ui as layout:
                layout.footer.clear()
                layout.title.set_text("EAM QuickView v1.0")

                with layout.toolbar as toolbar:
                    Toolbar(
                        toolbar,
                        self.server,
                        load_data=self.load_data,
                        load_variables=self.load_variables,
                        zoom=self.zoom,
                        move=self.move,
                        update_available_color_maps=self.update_available_color_maps,
                        update_scalar_bars=self.update_scalar_bars,
                    )

                card_style = """
                    position: absolute; 
                    bottom: 1rem; 
                    right: 1rem; 
                    height: 2.4rem; 
                    z-index: 2; 
                    display: flex; 
                    align-items: center;
                """
                ViewControls(
                    zoom=self.zoom,
                    move=self.move,
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
                            title="2D Variables",
                            panel_name="show_vars2D",
                            var_list="vars2D",
                            var_list_state="vars2Dstate",
                            on_search=self.search_2D_variables,
                            on_clear=self.clear_2D_variables,
                            on_update=self.update_2D_variable_selection,
                        )

                        VariableSelection(
                            title="3D Middle Layer Variables",
                            panel_name="show_vars3Dm",
                            var_list="vars3Dm",
                            var_list_state="vars3Dmstate",
                            on_search=self.search_3Dm_variables,
                            on_clear=self.clear_3Dm_variables,
                            on_update=self.update_3Dm_variable_selection,
                        )

                        VariableSelection(
                            title="3D Interface Layer Variables",
                            panel_name="show_vars3Di",
                            var_list="vars3Di",
                            var_list_state="vars3Distate",
                            on_search=self.search_3Di_variables,
                            on_clear=self.clear_3Di_variables,
                            on_update=self.update_3Di_variable_selection,
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
                                            apply=self.apply_colormap,
                                            update=self.update_view_color_properties,
                                            reset=self.reset_view_color_properties,
                                        )

        return self._ui

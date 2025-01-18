from pathlib import Path
from typing import Union

from trame.app import get_server

from trame.decorators import TrameApp, change

from trame.widgets import vuetify as v2, html, client
from trame.widgets import paraview as pvWidgets
from trame.widgets import grid

from trame.ui.vuetify import SinglePageWithDrawerLayout

from trame_server.core import Server

from eamapp.pipeline import EAMVisSource
from eamapp.view_manager import ViewManager
from eamapp.ui.file_selection import FileSelect
from eamapp.ui.slice_selection import SliceSelection
from eamapp.ui.projection_selection import ProjectionSelection
from eamapp.ui.variable_selection import VariableSelection
from eamapp.ui.view_settings import ViewControls, ViewProperties

import numpy as np

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

import os

try:
    presdir = os.path.join(os.path.dirname(__file__), "presets")
    presets = os.listdir(path=presdir)
    for preset in presets:
        prespath = os.path.abspath(os.path.join(presdir, preset))
        if os.path.isfile(prespath):
            name = preset.split("_")[0]
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

        state.DataFile = source.DataFile
        state.ConnFile = source.ConnFile
        state.timesteps = source.timestamps
        state.lev = source.lev
        state.ilev = source.ilev
        state.extents = list(source.extents)
        state.vars2D = source.vars2D
        state.vars3Di = source.vars3Di
        state.vars3Dm = source.vars3Dm

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

        ctrl.view_update = self.viewmanager.UpdateCamera
        ctrl.view_reset_camera = self.viewmanager.ResetCamera
        ctrl.on_server_ready.add(ctrl.view_update)
        server.trigger_name(ctrl.view_reset_camera)

        cvd = [{"text": ele.title(), "value": ele} for ele in self.viewmanager.colors]

        state.colormaps = noncvd

        # User controlled state varialbes
        if initstate == None:
            state.vlev = 0
            state.vilev = 0
            state.vars2Dstate = [False] * len(source.vars2D)
            state.vars3Dmstate = [False] * len(source.vars3Dm)
            state.vars3Distate = [False] * len(source.vars3Di)
            self.vars2Dstate = np.array([False] * len(source.vars2D))
            self.vars3Dmstate = np.array([False] * len(source.vars3Dm))
            self.vars3Distate = np.array([False] * len(source.vars3Di))
        else:
            state.update(initstate)
            # Build color cache here
            from eamapp.view_manager import BuildColorInformationCache

            self.viewmanager.cache = BuildColorInformationCache(initstate)
            self.Apply()

    def GenerateState(self):
        import json, os

        all = self.state.to_dict()
        to_export = {k: all[k] for k in save_state_keys}
        # with open(os.path.join(self.workdir, "state.json"), "w") as outfile:
        return json.dumps(to_export)

    def Apply(self):
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
            self.viewmanager.UpdateView()

    def ApplyColor(self, index, type, value):
        if type.lower() == "color":
            self.state.varcolor[index] = value
            self.state.dirty("varcolor")
        elif type.lower() == "log":
            self.state.uselogscale[index] = value
            self.state.dirty("uselogscale")
        elif type.lower() == "inv":
            self.state.invert[index] = value
            self.state.dirty("invert")
        self.viewmanager.UpdateColor(index, type, value)

    def updatecolors(self, event):
        if len(event) == 0:
            self.state.colormaps = noncvd
        elif len(event) == 2:
            self.state.colormaps = cvd + noncvd
        elif "0" in event:
            self.state.colormaps = cvd
        elif "1" in event:
            self.state.colormaps = noncvd

    def UpdateColorProps(self, index, type, value):
        if type.lower() == "min":
            self.state.varmin[index] = value
            self.state.dirty("varmin")
        elif type.lower() == "max":
            self.state.varmax[index] = value
            self.state.dirty("varmax")
        self.viewmanager.UpdateColorProps(
            index, self.state.varmin[index], self.state.varmax[index]
        )

    def ResetColorProps(self, index):
        self.viewmanager.ResetColorProps(index)

    def Zoom(self, type, index):
        if type.lower() == "in":
            self.viewmanager.ZoomIn(index)
        elif type.lower() == "out":
            self.viewmanager.ZoomOut(index)
        pass

    def Move(self, dir, index):
        if dir.lower() == "up":
            self.viewmanager.Move(index, 1, 0)
        elif dir.lower() == "down":
            self.viewmanager.Move(index, 1, 1)
        elif dir.lower() == "left":
            self.viewmanager.Move(index, 0, 1)
        elif dir.lower() == "right":
            self.viewmanager.Move(index, 0, 0)

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

    def Update2DVarSelection(self, index, event):
        self.state.vars2Dstate[index] = event
        self.state.dirty("vars2Dstate")
        if not self.ind2d is None:
            ind = self.ind2d[index]
            self.vars2Dstate[ind] = event
        else:
            self.vars2Dstate[index] = event

    def Update3DmVarSelection(self, index, event):
        self.state.vars3Dmstate[index] = event
        self.state.dirty("vars3Dmstate")
        if not self.ind3dm is None:
            ind = self.ind3dm[index]
            self.vars3Dmstate[ind] = event
        else:
            self.vars3Dmstate[index] = event

    def Update3DiVarSelection(self, index, event):
        self.state.vars3Distate[index] = event
        self.state.dirty("vars3Distate")
        if not self.ind3di is None:
            ind = self.ind3di[index]
            self.vars3Distate[ind] = event
        else:
            self.vars3Distate[index] = event

    def Search2DVars(self, search: str):
        if search == None or len(search) == 0:
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
        if not self.ind2d is None:
            self.state.vars2D = list(filtVars)
            self.state.vars2Dstate = self.vars2Dstate[self.ind2d].tolist()
            self.state.dirty("vars2Dstate")

    def Search3DmVars(self, search: str):
        if search == None or len(search) == 0:
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
        if not self.ind3dm is None:
            self.state.vars3Dm = list(filtVars)
            self.state.vars3Dmstate = self.vars3Dmstate[self.ind3dm].tolist()
            self.state.dirty("vars3Dmstate")

    def Search3DiVars(self, search: str):
        if search == None or len(search) == 0:
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
        if not self.ind3dm is None:
            self.state.vars3Di = list(filtVars)
            self.state.vars3Distate = self.vars3Distate[self.ind3di].tolist()
            self.state.dirty("vars3Distate")

    def Clear2D(self):
        self.state.vars2Dstate = [False] * len(self.state.vars2Dstate)
        self.vars2Dstate = [False] * len(self.vars2Dstate)
        self.state.dirty("vars2Dstate")

    def Clear3Dm(self):
        self.state.vars3Dmstate = [False] * len(self.state.vars3Dmstate)
        self.vars3Dmstate = [False] * len(self.vars3Dmstate)
        self.state.dirty("vars3Dmstate")

    def Clear3Di(self):
        self.state.vars3Distate = [False] * len(self.state.vars3Distate)
        self.vars3Distate = [False] * len(self.vars3Distate)
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
        print(f"Exporting config : {export_config}")
        self.state.export_completed = False
        self.state.exported_state = self.GenerateState()

    def toggle_drawer(self):
        print("Toggling main drawer : ", self.state.main_drawer)
        self.state.main_drawer = self.state.main_drawer
        self.state.flush()

    @property
    def ui(self) -> SinglePageWithDrawerLayout:
        if self._ui is None:
            self._ui = SinglePageWithDrawerLayout(self.server)
            with self._ui as layout:
                layout.title.set_text("EAM QuickView")
                with layout.toolbar as toolbar:
                    toolbar.density = "compact"
                    v2.VSpacer()
                    v2.VDivider(vertical=True, classes="mx-2")
                    with v2.VListItemGroup(dense=True):
                        v2.VCheckbox(
                            label="Use CVD friendly colormaps",
                            value=0,
                            v_model=("cmaps",),
                            dense=True,
                            style="min-height : unset",
                            hide_details=True,
                            change=(self.updatecolors, "[$event]"),
                        ),
                        v2.VCheckbox(
                            label="Use non-CVD friendly colormaps",
                            value=1,
                            v_model=("cmaps",),
                            dense=True,
                            style="min-height : unset",
                            hide_details=True,
                            change=(self.updatecolors, "[$event]"),
                        )
                    v2.VDivider(vertical=True, classes="mx-2")
                    html.Div(
                        f'Connectivity File :  "{self.state.ConnFile}" <br> Data File :  "{self.state.DataFile}"',
                        style="padding: 10px;",
                    )
                    v2.VDivider(vertical=True, classes="mx-2")
                    v2.VBtn(
                        "Export",
                        click="export_config = true",
                    )
                    with v2.VDialog(v_model=("export_config",), max_width=800):
                        with v2.VContainer(
                            fluid=True, classes="d-flex justify-center align-center"
                        ):
                            FileSelect()
                    v2.VDivider(vertical=True, classes="mx-2")
                    with v2.VBtn(icon=True, click=self.ctrl.view_reset_camera):
                        v2.VIcon("mdi-restore")

                style = dict(density="compact", hide_details=True)
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
                        with v2.VContainer(
                            fluid=True, classes="d-flex justify-center align-center"
                        ):
                            v2.VBtn(
                                "Update Views",
                                click=self.Apply,
                                style="background-color: gray; color: white; width: 200px; height: 50px;",
                            )

                        SliceSelection(self.source)

                        ProjectionSelection(self.source)

                        VariableSelection(
                            title="2D Variables",
                            panel_name="show_vars2D",
                            var_list="vars2D",
                            var_list_state="vars2Dstate",
                            on_search=self.Search2DVars,
                            on_clear=self.Clear2D,
                            on_update=self.Update2DVarSelection,
                        )

                        VariableSelection(
                            title="3D Middle Layer Variables",
                            panel_name="show_vars3Dm",
                            var_list="vars3Dm",
                            var_list_state="vars3Dmstate",
                            on_search=self.Search3DmVars,
                            on_clear=self.Clear3Dm,
                            on_update=self.Update3DmVarSelection,
                        )

                        VariableSelection(
                            title="3D Interface Layer Variables",
                            panel_name="show_vars3Di",
                            var_list="vars3Di",
                            var_list_state="vars3Distate",
                            on_search=self.Search3DiVars,
                            on_clear=self.Clear3Di,
                            on_update=self.Update3DiVarSelection,
                        )

                with layout.content:
                    with grid.GridLayout(
                        layout=("layout", []),
                    ):
                        with grid.GridItem(
                            v_for="vref, idx in views",
                            key="vref",
                            v_bind=("layout[idx]",),
                        ) as griditem:
                            with v2.VCard(
                                classes="fill-height", style="overflow: hidden;"
                            ):
                                with v2.VCardText(
                                    style="height: 100%; position: relative;",
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
                                    )
                                    html.Div(
                                        style="position:absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 1;"
                                    )
                                    # with v2.VCardActions(classes="pa-0"):
                                    with html.Div(
                                        style="position:absolute; bottom: 1rem; left: 1rem; height: 2rem; z-index: 2;"
                                    ):
                                        ViewProperties(
                                            apply=self.ApplyColor,
                                            update=self.UpdateColorProps,
                                            reset=self.ResetColorProps,
                                        )
                                        ViewControls(zoom=self.Zoom, move=self.Move)

        return self._ui

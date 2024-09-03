import json
from pathlib import Path
from typing import Union

from trame.app import get_server

from trame.decorators import TrameApp, change

from trame.widgets import vuetify, html
from trame.widgets import paraview as pvWidgets
from trame.widgets import grid

from trame.ui.vuetify import SinglePageWithDrawerLayout

from trame_server.core import Server

from eamapp.vissource  import  EAMVisSource
from eamapp.viewmanager import ViewManager
from eamapp.ui.VariableSelect import VariableSelect
from eamapp.ui.UICard import UICard
from eamapp.ui.FileSelect import FileSelect

import numpy as np

from paraview.simple import (
    ImportPresets
)

# -----------------------------------------------------------------------------
# trame setup
# -----------------------------------------------------------------------------

noncvd = [
            {"text" : 'Rainbow Desat.',    "value"  : 'Rainbow Desaturated',   },
            {"text" : 'Cool to Warm',      "value"  : 'Cool to Warm',},
            {"text" : 'Yellow-Gray-Blue',  "value"  : 'Yellow - Gray - Blue', },
        ]
cvd    = []

save_state_keys = [
    # Data files
    "DataFile", "ConnFile", 
    # Data slice related related variables
    "vlev", "vilev", "vars2Dstate", "vars3Distate", "vars3Dmstate",
    # Latitude/Longitude clipping
    "cliplat", "cliplong",
    # Projection
    "projection",
    # Color map related variables
    "ccardsentry", "varcolor", "uselogscale", "varmin", "varmax"     
]

import os
try:
    presdir    = os.path.join(os.path.dirname(__file__), 'presets')
    presets    = os.listdir(path=presdir)
    for preset in presets:
        prespath = os.path.abspath(os.path.join(presdir, preset))
        if os.path.isfile(prespath):
            name = preset.split('_')[0]
            ImportPresets(prespath)
            cvd.append({"text" : name.title(), "value" : name})
except Exception as e:
    print("Error loading presets :", e)

@TrameApp()
class EAMApp:
    def __init__(
            self,
            source : EAMVisSource = None,
            initserver: Union[Server, str] = None,
            initstate : dict = None,
            workdir : Union[str, Path] = None,
    ) -> None:
        server = get_server(initserver, client_type = "vue2")
        state  = server.state
        ctrl   = server.controller

        self._ui = None

        self.workdir = workdir
        self.server = server
        self.state  = state
        self.ctrl   = ctrl
        pvWidgets.initialize(server)

        self.source = source
        self.viewmanager = ViewManager(source, server, state)

        # Load state variables from the source object

        state.DataFile      = source.DataFile
        state.ConnFile      = source.ConnFile
        state.timesteps     = source.timestamps
        state.lev           = source.lev
        state.ilev          = source.ilev
        state.extents       = list(source.extents)
        state.vars2D        = source.vars2D
        state.vars3Di       = source.vars3Di
        state.vars3Dm       = source.vars3Dm

        self.ind2d          = None
        self.ind3dm         = None
        self.ind3di         = None
        state.views         = []
        #state.projection    = "Cyl. Equidistant"
        #state.cliplong      = [self.source.extents[0], self.source.extents[1]],
        #state.cliplat       = [self.source.extents[2], self.source.extents[3]],
        state.cmaps         = ["1"]
        state.layout        = []
        state.ccardsentry   = []
        state.ccardscolor   = [None] * len(source.vars2D + source.vars3Di + source.vars3Dm)
        state.varcolor      = []
        state.uselogscale   = []
        state.varmin        = []
        state.varmax        = []

        state.export_config     = False
        state.exported_state    = None
        state.export_completed  = False 
        state.state_save_file   = None

        ctrl.view_update = self.viewmanager.UpdateCamera
        ctrl.view_reset_camera = self.viewmanager.ResetCamera
        ctrl.on_server_ready.add(ctrl.view_update)
        server.trigger_name(ctrl.view_reset_camera)

        cvd = [ {"text" : ele.title(), "value" : ele} for ele in self.viewmanager.colors]

        state.colormaps = noncvd

        # User controlled state varialbes
        if initstate == None:
            state.vlev          = 0
            state.vilev         = 0
            state.vars2Dstate   = [False] * len(source.vars2D)
            state.vars3Dmstate  = [False] * len(source.vars3Dm)
            state.vars3Distate  = [False] * len(source.vars3Di)
            self.vars2Dstate    = np.array([False] * len(source.vars2D))
            self.vars3Dmstate   = np.array([False] * len(source.vars3Dm))
            self.vars3Distate   = np.array([False] * len(source.vars3Di))
        else:
            state.update(initstate)
            # Build color cache here
            from eamapp.viewmanager import BuildColorInformationCache
            self.viewmanager.cache = BuildColorInformationCache(initstate)
            self.Apply()

    def GenerateState(self):
        import json, os
        all = self.state.to_dict()
        to_export = { k : all[k] for k in save_state_keys}
        #with open(os.path.join(self.workdir, "state.json"), "w") as outfile: 
        return json.dumps(to_export)

    @change('vcols')
    def Columns(self, vcols, **kwargs):
        self.viewmanager.SetCols(vcols)

    def Apply(self):
        s2d     = []
        s3dm    = []
        s3di    = []
        if len(self.state.vars2D) > 0 :
            v2d     = np.array(self.state.vars2D)
            f2d     = np.array(self.state.vars2Dstate)
            s2d     = v2d[f2d].tolist()
        if len(self.state.vars3Dm) > 0 :
            v3dm    = np.array(self.state.vars3Dm)
            f3dm    = np.array(self.state.vars3Dmstate)
            s3dm    = v3dm[f3dm].tolist()
        if len(self.state.vars3Di) > 0 :
            v3di    = np.array(self.state.vars3Di)
            f3di    = np.array(self.state.vars3Distate)
            s3di    = v3di[f3di].tolist()
        self.source.LoadVariables(s2d, s3dm, s3di)

        vars = s2d + s3dm + s3di

        self.state.ccardsentry = vars

        self.state.ccardsvars  = [{"text" : var, "value" : var} for var in vars]
        self.state.varcolor    = [self.state.colormaps[0]['value']] * len(vars)
        self.state.uselogscale = [False] * len(vars)
        self.state.varmin      = [np.nan] * len(vars)
        self.state.varmax      = [np.nan] * len(vars)

        with self.state:
            self.viewmanager.UpdateView()

    def ApplyColor(self, index, type, value):
        if type.lower() == "color":
            self.state.varcolor[index] = value
        elif type.lower() == "log":
            self.state.uselogscale[index]
        self.viewmanager.UpdateColor(index, type, value)

    def updatecolors(self, event):
        if len(event) == 0:
            self.state.colormaps = noncvd
        elif len(event) == 2:
            self.state.colormaps = cvd + noncvd
        elif '0' in event:
            self.state.colormaps = cvd
        elif '1' in event:
            self.state.colormaps = noncvd

    def UpdateColorProps(self, index, type, value):
        print(f"Updating value at {index} : {type, value}")
        if type.lower() == 'min':
            self.state.varmin[index] = value
        elif type.lower() == 'max':
            self.state.varmax[index] = value
        self.viewmanager.UpdateColorProps(index,
                                          self.state.varmin[index],
                                          self.state.varmax[index])

    def ResetColorProps(self, index):
        self.viewmanager.ResetColorProps(index)

    def Zoom(self, type, index):
        if type.lower() == 'in':
            self.viewmanager.ZoomIn(index)
        elif type.lower() == 'out':
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
        if not self.ind3Di is None:
            ind = self.ind3di[index]
            self.vars3Distate[ind] = event
        else:
            self.vars3Distate[index] = event

    def Search2DVars(self, search : str):
        if search == None or len(search) == 0:
            filtVars = self.source.vars2D
            self.ind2d  = None
            self.state.vars2D       = self.source.vars2D
            self.state.vars2Dstate  = self.vars2Dstate.tolist()
            self.state.dirty("vars2Dstate")
        else:
            filtered    = [(idx, var) for idx, var in enumerate(self.source.vars2D) if search.lower() in var.lower()]
            filtVars    = [var for (_, var) in filtered]
            self.ind2d  = [idx for (idx, _) in filtered]
        if not self.ind2d is None:
            print(filtVars, self.ind2d, self.vars2Dstate[self.ind2d]) 
            self.state.vars2D       = list(filtVars)
            self.state.vars2Dstate  = self.vars2Dstate[self.ind2d].tolist()
            self.state.dirty("vars2Dstate")

    def Search3DmVars(self, search : str):
        if search == None or len(search) == 0:
            filtVars = self.source.vars3Dm
            self.ind3dm  = None
            self.state.vars3Dm       = self.source.vars3Dm
            self.state.vars3Dmstate  = self.vars3Dmstate.tolist()
            self.state.dirty("vars3Dmstate")
        else:
            filtered    = [(idx, var) for idx, var in enumerate(self.source.vars3Dm) if search.lower() in var.lower()]
            filtVars    = [var for (_, var) in filtered]
            self.ind3dm  = [idx for (idx, _) in filtered]
        if not self.ind3dm is None:
            print(filtVars, self.ind3dm, self.vars3Dmstate[self.ind3dm]) 
            self.state.vars3Dm       = list(filtVars)
            self.state.vars3Dmstate  = self.vars3Dmstate[self.ind3dm].tolist()
            self.state.dirty("vars3Dmstate")

    def Search3DiVars(self, search : str):
        if search == None or len(search) == 0:
            filtVars = self.source.vars3Di
            self.ind3di  = None
            self.state.vars3Di       = self.source.vars3Di
            self.state.vars3Distate  = self.vars3Distate.tolist()
            self.state.dirty("vars3Distate")
        else:
            filtered    = [(idx, var) for idx, var in enumerate(self.source.vars3Di) if search.lower() in var.lower()]
            filtVars    = [var for (_, var) in filtered]
            self.ind3di  = [idx for (idx, _) in filtered]
        if not self.ind3dm is None:
            print(filtVars, self.ind3di, self.vars3Dmstate[self.ind3di]) 
            self.state.vars3Di       = list(filtVars)
            self.state.vars3Distate  = self.vars3Distate[self.ind3di].tolist()
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

    @property
    def ui(self) -> SinglePageWithDrawerLayout:
        if self._ui is None:
            self._ui = SinglePageWithDrawerLayout(self.server)
            with self._ui as layout:
                layout.icon.click = self.ctrl.view_reset_camera
                layout.title.set_text("EAM QuickView")
                with layout.toolbar:
                    vuetify.VSpacer()
                    vuetify.VDivider(vertical=True, classes="mx-2")
                    with vuetify.VListItemGroup(dense=True):
                            vuetify.VCheckbox(label="Use CVD friendly colormaps", value=0, v_model = ("cmaps",), dense=True, style="min-height : unset", hide_details=True , change=(self.updatecolors, "[$event]")),
                            vuetify.VCheckbox(label="Use non-CVD friendly colormaps", value=1, v_model = ("cmaps",), dense=True, style="min-height : unset", hide_details=True, change=(self.updatecolors, "[$event]"))
                    vuetify.VDivider(vertical=True, classes="mx-2")
                    html.Div(
                        f"Connectivity File :  \"{self.state.ConnFile}\" <br> Data File :  \"{self.state.DataFile}\"",
                        style="padding: 10px;",
                    )
                    vuetify.VDivider(vertical=True, classes="mx-2")
                    #vuetify.VTextField(v_model=("statefile", None))
                    #vuetify.VBtn("Save State", click=self.SaveState,)
                    vuetify.VBtn(
                        "Export",
                        click="export_config = true",
                    )
                    with vuetify.VDialog(v_model=("export_config",), max_width=800):
                        with vuetify.VContainer(fluid=True, classes="d-flex justify-center align-center"):
                            FileSelect()
                    vuetify.VDivider(vertical=True, classes="mx-2")
                    with vuetify.VBtn(icon=True, click=self.ctrl.view_reset_camera):
                        vuetify.VIcon("mdi-restore")

                with layout.drawer as drawer:
                    drawer.width = 400
                    vuetify.VDivider(classes="mb-2")
                    with vuetify.VContainer(fluid=True, classes="d-flex justify-center align-center"):
                            vuetify.VBtn("Update Views", click=self.Apply, style="background-color: gray; color: white; width: 200px; height: 50px;")
                    vuetify.VDivider(classes="mx-2")
                    with vuetify.VContainer(fluid=True):
                        with UICard(title="Select Data Slice", varname="true").content:
                            with vuetify.VRow():
                                with vuetify.VCol(cols=6):
                                    vuetify.VSlider(
                                        label='Lev',
                                        v_model=("vlev", 0),
                                        min=0,
                                        max=("lev.length - 1", )
                                    )
                                with vuetify.VCol(cols=2):
                                    html.Div("{{'(k=' + String(vlev) + ')'}}")
                                with vuetify.VCol(cols=3):
                                    html.Div("{{parseFloat(lev[vlev]).toFixed(2)}}")
                            with vuetify.VRow():
                                with vuetify.VCol(cols=6):
                                    vuetify.VSlider(
                                        label='iLev',
                                        v_model=("vilev", 0),
                                        min=0,
                                        max=("ilev.length - 1", )
                                    )
                                with vuetify.VCol(cols=2):
                                    html.Div("{{'k=(' + String(vilev) + ')'}}")
                                with vuetify.VCol(cols=3):
                                    html.Div("{{parseFloat(ilev[vilev]).toFixed(2)}}")
                            with vuetify.VRow():
                                with vuetify.VCol(cols=6):
                                    vuetify.VSlider(
                                        label='Time',
                                        v_model=("tstamp", 0),
                                        min=0,
                                        max=("timesteps.length - 1", )
                                    )
                                with vuetify.VCol(cols=2):
                                    html.Div("{{'t=(' + String(tstamp) + ')'}}")
                                with vuetify.VCol(cols=3):
                                    html.Div("{{parseFloat(timesteps[tstamp]).toFixed(2)}}")
                            vuetify.VCheckbox(
                                label="Lat/Long Clipping",
                                v_model=("clipping", False),
                                dense=True
                            )
                            with vuetify.VContainer(fluid=True):
                                with UICard(title=None, varname="clipping").content:
                                    with vuetify.VRow():
                                        with vuetify.VCol(cols=3):
                                            vuetify.VTextField(
                                                v_model=("cliplong[0]",)
                                            )
                                        with vuetify.VCol(cols=6):
                                           html.Div("Longitude", classes="text-center align-center justify-center text-subtitle-1", style="color: blue")
                                        with vuetify.VCol(cols=3):
                                            vuetify.VTextField(
                                                v_model=("cliplong[1]",)
                                            )
                                    with vuetify.VRow():
                                        vuetify.VRangeSlider(
                                            v_model=("cliplong", [self.source.extents[0], self.source.extents[1]]),
                                            min=("extents[0]", ),
                                            max=("extents[1]", ),
                                        )
                                    vuetify.VDivider(classes="mx-2")
                                    with vuetify.VRow():
                                        with vuetify.VCol(cols=3):
                                            vuetify.VTextField(
                                                v_model=("cliplat[0]",)
                                            )
                                        with vuetify.VCol(cols=6):
                                           html.Div("Latitude", classes="text-center align-center justify-center text-subtitle-1", style="color: blue")
                                        with vuetify.VCol(cols=3):
                                            vuetify.VTextField(
                                                v_model=("cliplat[1]",)
                                            )
                                    with vuetify.VRow():
                                        vuetify.VRangeSlider(
                                            v_model=("cliplat", [self.source.extents[2], self.source.extents[3]]),
                                            min=("extents[2]", ),
                                            max=("extents[3]", ),
                                        )
                    vuetify.VDivider(classes="mx-2")
                    with vuetify.VContainer(fluid=True):
                        with UICard(title="Map Projection Selection", varname="true").content:
                            vuetify.VSelect(
                                outlined=True,
                                items=("options", ["Cyl. Equidistant","Robinson", "Mollweide"]),
                                v_model=("projection", "Cyl. Equidistant")
                            )
                    vuetify.VDivider(classes="mx-2")
                    with vuetify.VContainer(fluid=True):
                        with UICard(title="Variable Selection", varname="true").content:
                            html.A("2D Variables", style="padding: 10px;",)
                            vuetify.VTextField(label="variable search", change=(self.Search2DVars, "[$event]"))
                            VariableSelect("vars2D", "vars2Dstate", self.Update2DVarSelection) 
                            vuetify.VDivider(classes="mx-2")
                            html.A("3D Middle Layer Variables", style="padding: 10px;",)
                            vuetify.VTextField(label="variable search", change=(self.Search3DmVars, "[$event]"))
                            VariableSelect("vars3Dm", "vars3Dmstate") 
                            vuetify.VDivider(classes="mx-2")
                            html.A("3D Interface Layer Variables", style="padding: 10px;",)
                            vuetify.VTextField(label="variable search", change=(self.Search3DiVars, "[$event]"))
                            VariableSelect("vars3Di", "vars3Distate") 
                    vuetify.VDivider(classes="mx-2")
                    with layout.content:
                        with grid.GridLayout(
                            layout=("layout", []),
                        ):
                            with grid.GridItem(
                                v_for="vref, idx in views",
                                key="idx",
                                v_bind=("layout[idx]", ),
                            ) as griditem:
                                with vuetify.VCard(classes="fill-height", style="overflow: hidden;"):
                                    with vuetify.VCardText(style="height: calc(100% - 4.75rem); position: relative;", classes="pa-0") as cardcontent:
                                        cardcontent.add_child(
                                            '<vtk-remote-view :ref="(el) => ($refs[vref] = el)" :viewId="get(`${vref}Id`)" class="pa-0 drag-ignore" style="width: 100%; height: 100%;" interactiveRatio="1" ></vtk-remote-view>',
                                        )
                                        html.Div(style="position:absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 1;")
                                    with vuetify.VCardActions():
                                        with vuetify.VMenu(
                                            transition="slide-y-transition",
                                            close_on_content_click=False,
                                            persistent=True,
                                            no_click_animation=True,
                                        ):
                                            with vuetify.Template(v_slot_activator="{ on, attrs }"):
                                                with vuetify.VBtn(
                                                    "View Settings",
                                                    color="primary",
                                                    icon=True, v_bind="attrs", v_on="on", style="z-index:2",):
                                                    vuetify.VIcon("mdi-dots-vertical")
                                            with vuetify.VCard():
                                                with vuetify.VCardText():
                                                        vuetify.VSelect(
                                                            v_model=("varcolor[idx]",),
                                                            items=("colormaps",),
                                                            outlined=True,
                                                            dense=True,
                                                            hide_details=True,
                                                            change=(self.ApplyColor, "[idx, 'color', $event]")
                                                        )
                                                        vuetify.VCheckbox(
                                                            label="log scale",
                                                            v_model=("uselogscale[idx]",),
                                                            change=(self.ApplyColor, "[idx, 'log', $event]")
                                                        )
                                                        html.Div("Color Range")
                                                        vuetify.VTextField(v_model=("varmin[idx]", ), label="min", outlined=True, change=(self.UpdateColorProps, "[idx, 'min', $event]"), style="height=50px")
                                                        vuetify.VTextField(v_model=("varmax[idx]", ), label="max", outlined=True, change=(self.UpdateColorProps, "[idx, 'max', $event]"), style="height=50px")
                                                        with vuetify.VBtn(icon=True, outlined=True, style="height: 40px; width: 40px", click=(self.ResetColorProps, "[idx]")):
                                                            vuetify.VIcon("mdi-restore")
                                        vuetify.VSpacer()
                                        vuetify.VDivider(vertical=True, classes="mx-2")
                                        with vuetify.VBtn(icon=True, outlined=True, style="height: 20px; width: 20px", click=(self.Zoom, "['in', idx]")):
                                            vuetify.VIcon("mdi-plus")
                                        with vuetify.VBtn(icon=True, outlined=True, style="height: 20px; width: 20px", click=(self.Zoom, "['out', idx]")):
                                            vuetify.VIcon("mdi-minus")
                                        with vuetify.VBtn(icon=True, outlined=True, style="height: 20px; width: 20px", click=(self.Move, "['up', idx]")):
                                            vuetify.VIcon("mdi-arrow-up")
                                        with vuetify.VBtn(icon=True, outlined=True, style="height: 20px; width: 20px", click=(self.Move, "['down', idx]")):
                                            vuetify.VIcon("mdi-arrow-down")
                                        with vuetify.VBtn(icon=True, outlined=True, style="height: 20px; width: 20px", click=(self.Move, "['left', idx]")):
                                            vuetify.VIcon("mdi-arrow-left")
                                        with vuetify.VBtn(icon=True, outlined=True, style="height: 20px; width: 20px", click=(self.Move, "['right', idx]")):
                                            vuetify.VIcon("mdi-arrow-right")
        return self._ui

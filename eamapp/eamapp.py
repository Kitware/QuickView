from typing import Union

from trame.app import get_server

from trame.decorators import TrameApp, change

from trame.widgets import vuetify, html
from trame.widgets import paraview as pvWidgets
from trame.widgets import grid

from trame.ui.vuetify import SinglePageWithDrawerLayout

from trame_server.core import Server

from eamapp.vissource.vissource  import  EAMVisSource
from eamapp.vissource.viewmanager import ViewManager

import numpy as np

# -----------------------------------------------------------------------------
# trame setup
# -----------------------------------------------------------------------------

noncvd = [
            {"text" : 'Rainbow Desat.',    "value"  : 'Rainbow Desaturated',   },
            {"text" : 'Cool to Warm',      "value"  : 'Cool to Warm',}, 
            {"text" : 'Yellow-Gray-Blue',  "value"  : 'Yellow - Gray - Blue', },
        ]
 
cvd    = []

@TrameApp()
class EAMApp:
    def __init__(
            self,
            source : EAMVisSource = None,
            initserver: Union[Server, str] = None,
            initstate : dict = None
    ) -> None:
        server = get_server(initserver, client_type = "vue2")
        state  = server.state
        ctrl   = server.controller

        self._ui = None

        self.server = server
        self.state  = state
        self.ctrl   = ctrl
        pvWidgets.initialize(server)
        
        self.source = source
        self.viewmanager = ViewManager(source, server, state)
        
        state.vlev = 0 
        state.timesteps     = source.timestamps
        state.lev           = source.lev
        state.ilev          = source.ilev
        state.extents       = list(source.extents)
        state.vars2D        = source.vars2D
        state.vars3Di       = source.vars3Di
        state.vars3Dm       = source.vars3Dm
        state.vars2Dstate   = [False] * len(source.vars2D)
        state.vars3Distate  = [False] * len(source.vars3Di)
        state.vars3Dmstate  = [False] * len(source.vars3Dm)
 
        state.views         = []
        state.cmaps         = ["1"]
        state.layout        = []
 
        state.ccardsentry   = []
        state.ccardscolor   = [None] * len(source.vars2D + source.vars3Di + source.vars3Dm)
        state.varcolor      = []
        state.uselogscale   = []
        state.varmin        = []
        state.varmax        = []
 
        ctrl.view_update = self.viewmanager.UpdateCamera
        ctrl.view_reset_camera = self.viewmanager.ResetCamera
        ctrl.on_server_ready.add(ctrl.view_update)
        server.trigger_name(ctrl.view_reset_camera)
 
        noncvd = [
            {"text" : 'Rainbow Desat.',    "value"  : 'Rainbow Desaturated',   },
            {"text" : 'Cool to Warm',      "value"  : 'Cool to Warm',}, 
            {"text" : 'Yellow-Gray-Blue',  "value"  : 'Yellow - Gray - Blue', },
        ]
 
        cvd = [ {"text" : ele.title(), "value" : ele} for ele in self.viewmanager.colors]
 
        state.colormaps = noncvd

    @change('vcols')
    def Columns(self, vcols, **kwargs):
        self.viewmanager.SetCols(vcols)

    def update2DVars(self, index, visibility):
        self.state.vars2Dstate[index] = visibility
        self.state.dirty("vars2Dstate")

    def update3DmVars(self, index, visibility):
        self.state.vars3Dmstate[index] = visibility
        self.state.dirty("vars3Dmstate")

    def update3DiVars(self, index, visibility):
        self.state.vars3Distate[index] = visibility
        self.state.dirty("vars3Distate")

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

    def SaveState(self):
        print(f"Saving state to {self.state.statefile}")
        print(self.state)
        pass    

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

    def ui_card(self, title, varname):
        with vuetify.VCard(v_show=f"{varname} == true"):
            vuetify.VCardTitle(
                title,
                classes="grey lighten-1 py-1 grey--text text--darken-3",
                style="user-select: none; cursor: pointer",
                hide_details=True,
                dense=True,
            )
            content = vuetify.VCardText(classes="py-2")
        return content
    """
    def Search2DVars(self, search : str):
        if search == None or len(search) == 0:
            filtVars = self.source.vars2D
        else:
            filtVars = filter(lambda x: search.lower() in x.lower(), self.source.vars2D)
        self.state.vars2D = list(filtVars)
        pass

    def Search3DmVars(search : str):
        if search == None or len(search) == 0:
            filtVars = source.vars3Dm
        else:
            filtVars = filter(lambda x: search.lower() in x.lower(), source.vars3Dm)
        state.vars3Dm = list(filtVars)
        pass

    def Search3DiVars(search : str):
        if search == None or len(search) == 0:
            filtVars = source.vars3Di
        else:
            filtVars = filter(lambda x: search.lower() in x.lower(), source.vars3Di)
        state.vars3Di = list(filtVars)
        pass
    """
    def start(self, **kwargs):
        """Initialize the UI and start the server for GeoTrame."""
        self.ui.server.start(**kwargs)

    @property
    def ui(self) -> SinglePageWithDrawerLayout:
        if self._ui is None:
        # Build UI
            self._ui = SinglePageWithDrawerLayout(self.server)
            with self._ui as layout:
            # client.Style("html { overflow: hidden; }")
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
                    vuetify.VTextField(v_model=("statefile", None))
                    vuetify.VBtn("Save State", click=self.SaveState)
                    vuetify.VDivider(vertical=True, classes="mx-2")
                    with vuetify.VBtn(icon=True, click=self.ctrl.view_reset_camera):
                        vuetify.VIcon("mdi-restore")
   
                items = []
                with layout.drawer as drawer:
                    drawer.width = 400
                    vuetify.VDivider(classes="mb-2")
                    with vuetify.VContainer(fluid=True, classes="d-flex justify-center align-center"):
                            vuetify.VBtn("Update Views", click=self.Apply, style="background-color: gray; color: white; width: 200px; height: 50px;")
                    vuetify.VDivider(classes="mx-2") 
                    with vuetify.VContainer(fluid=True):
                        with self.ui_card(title="Select Data Slice", varname="true"):
                            with vuetify.VRow():
                                with vuetify.VCol(cols=6):
                                    vuetify.VSlider(
                                        label='Lev',
                                        v_model=("vlev", 0),
                                        min=0,
                                        max=("lev.length - 1", )
                                    )
                                with vuetify.VCol(cols=2):
                                    html.Div("{{'(' + String(vlev) + ')'}}")
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
                                    html.Div("{{'(' + String(vilev) + ')'}}")
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
                                    html.Div("{{'(' + String(tstamp) + ')'}}")
                                with vuetify.VCol(cols=3):
                                    html.Div("{{parseFloat(timesteps[tstamp]).toFixed(2)}}")
                            vuetify.VCheckbox(
                                label="Lat/Long Clipping",
                                v_model=("clipping", False),
                                dense=True
                            )
                            with vuetify.VContainer(fluid=True):
                                with self.ui_card(title=None, varname="clipping"):
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
                        with self.ui_card(title="Map Projection Selection", varname="true"):
                            vuetify.VSelect(
                                outlined=True,
                                items=("options", ["Cyl. Equidistant","Robinson", "Mollweide"]),
                                v_model=("projection", "Cyl. Equidistant")
                            )
                    vuetify.VDivider(classes="mx-2")
                    with vuetify.VContainer(fluid=True):
                        with self.ui_card(title="Variable Selection", varname="true"):
                            html.A(
                                "2D Variables",
                                style="padding: 10px;",
                            )
                            #vuetify.VTextField("var search", change=(Search2DVars, "[$event]"))
                            with vuetify.VContainer(fluid=True, style="max-height: 200px", classes="overflow-y-auto"):
                                with vuetify.VListItemGroup(dense=True, label="2D Variables"):
                                    vuetify.VCheckbox(
                                        v_for="v, i in vars2D",
                                        key="i",
                                        label=("vars2D[i]",),
                                        v_model=("vars2Dstate[i]",),
                                        change=(self.update2DVars, "[i, $event]"),
                                        style="max-height: 20px",
                                        dense=True
                                    )
                            vuetify.VDivider(classes="mx-2")
                            html.A(
                                "3D Middle Layer Variables",
                                style="padding: 10px;",
                            )
                            #vuetify.VTextField("var search", change=(Search3DmVars, "[$event]"))
                            with vuetify.VContainer(fluid=True, style="max-height: 200px", classes="overflow-y-auto"):
                                with vuetify.VListItemGroup(dense=True, label="3D Middle Layer Variables"):
                                    vuetify.VCheckbox(
                                        v_for="v, i in vars3Dm",
                                        key="i",
                                        label=("vars3Dm[i]",),
                                        v_model=("vars3Dmstate[i]",),
                                        change=(self.update3DmVars, "[i, $event]"),
                                        style="max-height: 20px",
                                        dense=True
                                    )
                            vuetify.VDivider(classes="mx-2")
                            html.A(
                            "3D Interface Layer Variables",
                            style="padding: 10px;",
                            )
                            #vuetify.VTextField("var search", change=(Search3DiVars, "[$event]"))
                            with vuetify.VContainer(fluid=True, style="max-height: 200px", classes="overflow-y-auto"):
                                with vuetify.VListItemGroup(dense=True, label="3D Interface Layer Variables"):
                                    vuetify.VCheckbox(
                                        v_for="v, i in vars3Di",
                                        key="i",
                                        label=("vars3Di[i]",),
                                        v_model=("vars3Distate[i]",),
                                        change=(self.update3DiVars, "[i, $event]"),
                                        style="max-height: 20px",
                                        dense=True
                                    )
                    vuetify.VDivider(classes="mx-2") 
                    #temp = server.trigger_name(ctrl.view_reset_camera)
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
                                                with vuetify.VBtn(icon=True, v_bind="attrs", v_on="on", style="position: absolute; z-index:2",):
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

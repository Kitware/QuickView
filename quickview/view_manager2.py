from trame.app import TrameComponent
from trame.ui.html import DivLayout
from trame.widgets import paraview as pvw, vuetify3 as v3, client, html
from trame.decorators import hot_reload

from paraview import simple


def auto_size_to_col(size):
    if size == 1:
        return 12

    if size >= 8 and size % 2 == 0:
        return 3

    if size % 3 == 0:
        return 4

    if size % 2 == 0:
        return 6

    return auto_size_to_col(size + 1)


COL_SIZE_LOOKUP = {
    "auto": auto_size_to_col,
    "1": 12,
    "2": 6,
    "3": 4,
    "4": 3,
    "6": 2,
    "12": 1,
}

TYPE_COLOR = {
    "s": "success",
    "i": "info",
    "m": "warning",
}


class VariableView(TrameComponent):
    def __init__(self, server, source, variable_name):
        super().__init__(server)
        self.source = source
        self.variable_name = variable_name
        self.name = f"view_{self.variable_name}"
        self.view = simple.CreateRenderView()
        self.view.GetRenderWindow().SetOffScreenRendering(True)
        self.view.InteractionMode = "2D"
        self.view.OrientationAxesVisibility = 0
        self.view.UseColorPaletteForBackground = 0
        self.view.BackgroundColorMode = "Gradient"
        self.view.CameraParallelProjection = 1
        self.representation = simple.Show(
            proxy=source.views["atmosphere_data"],
            view=self.view,
        )
        simple.ColorBy(self.representation, ("CELLS", variable_name))
        self.lut = simple.GetColorTransferFunction(variable_name)
        self.lut.NanOpacity = 0.0

        self.view.ResetActiveCameraToNegativeZ()
        self.view.ResetCamera(True, 0.9)
        self.disable_render = False
        # FIXME use preset/logscale/invert/range

        self._build_ui()

    def render(self):
        if self.disable_render:
            return
        self.ctx[self.name].update()

    def set_camera_modified(self, fn):
        self._observer = self.camera.AddObserver("ModifiedEvent", fn)

    @property
    def camera(self):
        return self.view.GetActiveCamera()

    def reset_camera(self):
        self.view.InteractionMode = "2D"
        self.view.ResetActiveCameraToNegativeZ()
        self.view.ResetCamera(True, 0.9)
        self.ctx[self.name].update()

    def _build_ui(self):
        with DivLayout(
            self.server, template_name=self.name, connect_parent=False
        ) as self.ui:
            with v3.VCard(variant="tonal"):
                v3.VCardSubtitle(
                    self.variable_name,
                    classes="pt-1 pb-0 px-2 bg-black opacity-90 text-subtitle-2",
                )
                with html.Div(style=("`aspect-ratio: ${aspect_ratio};`",)):
                    pvw.VtkRemoteView(
                        self.view, interactive_ratio=1, ctx_name=self.name
                    )


class ViewManager(TrameComponent):
    def __init__(self, server, source):
        super().__init__(server)
        self.source = source
        self._var2view = {}
        self._camera_sync_in_progress = False

        pvw.initialize(self.server)

    def reset_camera(self):
        views = list(self._var2view.values())
        for view in views:
            view.disable_render = True

        for view in views:
            view.reset_camera()

        for view in views:
            view.disable_render = False

    def get_view(self, variable_name):
        view = self._var2view.get(variable_name)
        if view is None:
            view = self._var2view.setdefault(
                variable_name,
                VariableView(self.server, self.source, variable_name),
            )
            view.set_camera_modified(self.sync_camera)

        return view

    def sync_camera(self, camera, *_):
        if self._camera_sync_in_progress:
            return
        self._camera_sync_in_progress = True

        for var_view in self._var2view.values():
            cam = var_view.camera
            if cam is camera:
                continue
            cam.DeepCopy(camera)
            var_view.render()

        self._camera_sync_in_progress = False

    @hot_reload
    def build_auto_layout(self, variables):
        with DivLayout(self.server, template_name="auto_layout") as self.ui:
            size_to_col = COL_SIZE_LOOKUP[self.state.col_mode]
            with v3.VCol(classes="pa-1"):
                if callable(size_to_col):
                    for var_type in "smi":
                        var_names = variables[var_type]
                        total_size = len(var_names)

                        if total_size == 0:
                            continue

                        n_cols = size_to_col(total_size)
                        with v3.VAlert(
                            border="start",
                            classes="pr-1 py-1 pl-3 mb-1",
                            variant="flat",
                            border_color=TYPE_COLOR[var_type],
                        ):
                            with v3.VRow(dense=True):
                                for name in var_names:
                                    view = self.get_view(name)
                                    with v3.VCol(cols=n_cols):
                                        client.ServerTemplate(name=view.name)
                else:
                    n_cols = size_to_col
                    with v3.VRow(dense=True):
                        for var_type in "smi":
                            var_names = variables[var_type]
                            for name in var_names:
                                view = self.get_view(name)
                                with v3.VCol(cols=n_cols):
                                    client.ServerTemplate(name=view.name)

import math

from trame.app import TrameComponent
from trame.ui.html import DivLayout
from trame.widgets import paraview as pvw, vuetify3 as v3, client, html
from trame.decorators import controller

from trame_dataclass.core import StateDataModel

from paraview import simple

from e3sm_quickview.utils.color import get_cached_colorbar_image
from e3sm_quickview.utils.color import COLORBAR_CACHE
from e3sm_quickview.presets import COLOR_BLIND_SAFE


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
    0: auto_size_to_col,
    1: 12,
    2: 6,
    3: 4,
    4: 3,
    6: 2,
    12: 1,
}

TYPE_COLOR = {
    "s": "success",
    "i": "info",
    "m": "warning",
}


class ViewConfiguration(StateDataModel):
    variable: str
    preset: str = "Inferno (matplotlib)"
    preset_img: str
    invert: bool = False
    color_blind: bool = False
    use_log_scale: bool = False
    color_range: list[float] = (0, 1)
    override_range: bool = False
    order: int = 0
    size: int = 4
    offset: int = 0
    break_row: bool = False
    menu: bool = False
    swap_group: list[str]


class VariableView(TrameComponent):
    def __init__(self, server, source, variable_name, variable_type):
        super().__init__(server)
        self.config = ViewConfiguration(server, variable=variable_name)
        self.source = source
        self.variable_name = variable_name
        self.variable_type = variable_type
        self.name = f"view_{self.variable_name}"
        self.view = simple.CreateRenderView()
        self.view.GetRenderWindow().SetOffScreenRendering(True)
        self.view.InteractionMode = "2D"
        self.view.OrientationAxesVisibility = 0
        self.view.UseColorPaletteForBackground = 0
        self.view.BackgroundColorMode = "Gradient"
        self.view.CameraParallelProjection = 1
        self.view.Size = 0 # make the interactive widget non responsive
        self.representation = simple.Show(
            proxy=source.views["atmosphere_data"],
            view=self.view,
        )

        # Lookup table color management
        simple.ColorBy(self.representation, ("CELLS", variable_name))
        self.lut = simple.GetColorTransferFunction(variable_name)
        self.lut.NanOpacity = 0.0

        self.view.ResetActiveCameraToNegativeZ()
        self.view.ResetCamera(True, 0.9)
        self.disable_render = False

        # Add annotation to the view
        # - continents
        globe = source.views["continents"]
        repG = simple.Show(globe, self.view)
        simple.ColorBy(repG, None)
        repG.SetRepresentationType("Wireframe")
        repG.RenderLinesAsTubes = 1
        repG.LineWidth = 1.0
        repG.AmbientColor = [0.67, 0.67, 0.67]
        repG.DiffuseColor = [0.67, 0.67, 0.67]
        self.rep_globe = repG
        # - gridlines
        annot = source.views["grid_lines"]
        repAn = simple.Show(annot, self.view)
        repAn.SetRepresentationType("Wireframe")
        repAn.AmbientColor = [0.67, 0.67, 0.67]
        repAn.DiffuseColor = [0.67, 0.67, 0.67]
        repAn.Opacity = 0.4
        self.rep_grid = repAn

        # Reactive behavior
        self.config.watch(
            ["override_range", "color_range"], self.update_color_range, eager=True
        )
        self.config.watch(
            ["preset", "invert", "use_log_scale"], self.update_color_preset, eager=True
        )

        # GUI
        self._build_ui()

    def render(self):
        if self.disable_render or not self.ctx.has(self.name):
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

    def update_color_preset(self, name, invert, log_scale):
        self.config.preset = name
        self.config.preset_img = get_cached_colorbar_image(
            self.config.preset,
            self.config.invert,
        )
        self.lut.ApplyPreset(self.config.preset, True)
        if invert:
            self.lut.InvertTransferFunction()
        if log_scale:
            self.lut.MapControlPointsToLogSpace()
            self.lut.UseLogScale = 1
        self.render()

    def update_color_range(self, *_):
        if self.config.override_range:
            if math.isnan(self.config.color_range[0]) or math.isnan(
                self.config.color_range[1]
            ):
                return
            self.lut.RescaleTransferFunction(*self.config.color_range)
        else:
            self.representation.RescaleTransferFunctionToDataRange(False, True)
            data_array = (
                self.source.views["atmosphere_data"]
                .GetCellDataInformation()
                .GetArray(self.variable_name)
            )
            if data_array:
                data_range = data_array.GetRange()
                self.config.color_range = data_range
                self.lut.RescaleTransferFunction(*data_range)
        self.render()

    def _build_ui(self):
        with DivLayout(
            self.server, template_name=self.name, connect_parent=False, classes="h-100"
        ) as self.ui:
            self.ui.root.classes = "h-100"
            with v3.VCard(
                variant="tonal",
                style=(
                    "active_layout !== 'auto_layout' ? `height: calc(100% - ${top_padding}px;` : 'overflow-hidden'",
                ),
                tile=("active_layout !== 'auto_layout'",),
            ):
                with v3.VRow(
                    dense=True,
                    classes="ma-0 pa-0 bg-black opacity-90 d-flex align-center",
                ):
                    with v3.VBtn(
                        icon=True,
                        density="compact",
                        variant="plain",
                        classes="mx-1",
                        size="small",
                    ):
                        v3.VIcon(
                            "mdi-arrow-expand",
                            size="x-small",
                            style="transform: scale(-1, 1);",
                        )
                        with v3.VMenu(activator="parent"):
                            with self.config.provide_as("config"):
                                with v3.VList(density="compact"):
                                    v3.VListItem(
                                        subtitle="Full Screen",
                                        click=f"active_layout = '{self.name}'",
                                    )
                                    v3.VDivider()
                                    with v3.VListItem(
                                        subtitle="Line Break",
                                        click="config.break_row = !config.break_row",
                                    ):
                                        with v3.Template(v_slot_append=True):
                                            v3.VSwitch(
                                                v_model="config.break_row",
                                                hide_details=True,
                                                density="compact",
                                                color="primary",
                                            )
                                    with v3.VListItem(subtitle="Offset"):
                                        v3.VBtn(
                                            "0",
                                            classes="text-none ml-2",
                                            size="small",
                                            variant="outined",
                                            click="config.offset = 0",
                                            active=("config.offset === 0",),
                                        )
                                        v3.VBtn(
                                            "1",
                                            classes="text-none ml-2",
                                            size="small",
                                            variant="outined",
                                            click="config.offset = 1",
                                            active=("config.offset === 1",),
                                        )
                                        v3.VBtn(
                                            "2",
                                            classes="text-none ml-2",
                                            size="small",
                                            variant="outined",
                                            click="config.offset = 2",
                                            active=("config.offset === 2",),
                                        )
                                        v3.VBtn(
                                            "3",
                                            classes="text-none ml-2",
                                            size="small",
                                            variant="outined",
                                            click="config.offset = 3",
                                            active=("config.offset === 3",),
                                        )
                                        v3.VBtn(
                                            "4",
                                            classes="text-none ml-2",
                                            size="small",
                                            variant="outined",
                                            click="config.offset = 4",
                                            active=("config.offset === 4",),
                                        )
                                        v3.VBtn(
                                            "5",
                                            classes="text-none ml-2",
                                            size="small",
                                            variant="outined",
                                            click="config.offset = 5",
                                            active=("config.offset === 5",),
                                        )
                                    v3.VDivider()

                                    v3.VListItem(
                                        subtitle="Full width",
                                        click="active_layout = 'auto_layout';config.size = 12",
                                    )
                                    v3.VListItem(
                                        subtitle="1/2 width",
                                        click="active_layout = 'auto_layout';config.size = 6",
                                    )
                                    v3.VListItem(
                                        subtitle="1/3 width",
                                        click="active_layout = 'auto_layout';config.size = 4",
                                    )
                                    v3.VListItem(
                                        subtitle="1/4 width",
                                        click="active_layout = 'auto_layout';config.size = 3",
                                    )
                                    v3.VListItem(
                                        subtitle="1/6 width",
                                        click="active_layout = 'auto_layout';config.size = 2",
                                    )
                    with html.Div(
                        self.variable_name,
                        classes="text-subtitle-2 pr-2",
                        style="user-select: none;",
                    ):
                        with v3.VMenu(activator="parent"):
                            with v3.VList(density="compact", style="max-height: 40vh;"):
                                with self.config.provide_as("config"):
                                    v3.VListItem(
                                        subtitle=("name",),
                                        v_for="name, idx in config.swap_group",
                                        key="name",
                                        click=(
                                            self.ctrl.swap_variables,
                                            "[config.variable, name]",
                                        ),
                                    )

                    v3.VIcon(
                        "mdi-lock-outline",
                        size="x-small",
                        v_show=("lock_views", False),
                    )

                    v3.VSpacer()
                    html.Div(
                        "t = {{ time_idx }}",
                        classes="text-caption px-1",
                        v_if="timestamps.length > 1",
                    )
                    if self.variable_type == "m":
                        html.Div(
                            "[k = {{ midpoint_idx }}]",
                            classes="text-caption px-1",
                            v_if="midpoints.length > 1",
                        )
                    if self.variable_type == "i":
                        html.Div(
                            "[k = {{ interface_idx }}]",
                            classes="text-caption px-1",
                            v_if="interfaces.length > 1",
                        )
                    v3.VSpacer()
                    html.Div(
                        "avg = {{"
                        f"fields_avgs['{self.variable_name}']?.toExponential(2) || 'N/A'"
                        "}}",
                        classes="text-caption px-1",
                    )

                with html.Div(
                    style=(
                        """
                        {
                            aspectRatio: active_layout === 'auto_layout' ? aspect_ratio : null,
                            height: active_layout !== 'auto_layout' ? 'calc(100% - 2.4rem)' : null,
                            pointerEvents: lock_views ? 'none': null,
                        }
                        """,
                    ),
                ):
                    pvw.VtkRemoteView(
                        self.view, interactive_ratio=1, ctx_name=self.name
                    )

                with self.config.provide_as("config"):
                    with html.Div(
                        classes="bg-blue-grey-darken-2 d-flex align-center",
                        style="height:1rem;position:relative;top:0;user-select:none;cursor:context-menu;",
                    ):
                        with v3.VMenu(
                            v_model="config.menu",
                            activator="parent",
                            location=(
                                "active_layout !== 'auto_layout' || config.size == 12 ? 'top' : 'end'",
                            ),
                            close_on_content_click=False,
                        ):
                            with v3.VCard(style="max-width: 360px;"):
                                with v3.VCardItem(classes="pb-0"):
                                    v3.VIconBtn(
                                        raw_attrs=[
                                            '''v-tooltip:bottom="config.color_blind ? 'Colorblind safe presets' : 'All color presets'"'''
                                        ],
                                        icon=(
                                            "config.color_blind ? 'mdi-shield-check-outline' : 'mdi-palette'",
                                        ),
                                        click="config.color_blind = !config.color_blind",
                                        size="small",
                                        text="Colorblind safe",
                                        variant="text",
                                    )
                                    v3.VIconBtn(
                                        raw_attrs=[
                                            '''v-tooltip:bottom="config.invert ? 'Inverted preset' : 'Normal preset'"'''
                                        ],
                                        icon=(
                                            "config.invert ? 'mdi-invert-colors' : 'mdi-invert-colors-off'",
                                        ),
                                        click="config.invert = !config.invert",
                                        size="small",
                                        text="Invert",
                                        variant="text",
                                    )
                                    v3.VIconBtn(
                                        raw_attrs=[
                                            '''v-tooltip:bottom="config.use_log_scale ? 'Use log scale' : 'Use linear scale'"'''
                                        ],
                                        icon=(
                                            "config.use_log_scale ? 'mdi-math-log' : 'mdi-stairs'",
                                        ),
                                        click="config.use_log_scale = !config.use_log_scale",
                                        size="small",
                                        text=(
                                            "config.use_log_scale ? 'Log scale' : 'Linear scale'",
                                        ),
                                        variant="text",
                                    )
                                    v3.VIconBtn(
                                        raw_attrs=[
                                            '''v-tooltip:bottom="config.override_range ? 'Use custom range' : 'Use data range'"'''
                                        ],
                                        icon=(
                                            "config.override_range ? 'mdi-arrow-expand-horizontal' : 'mdi-pencil'",
                                        ),
                                        click="config.override_range = !config.override_range",
                                        size="small",
                                        text="Use data range",
                                        variant="text",
                                    )

                                    with v3.Template(v_slot_append=True):
                                        v3.VLabel(
                                            "{{ config.preset }}",
                                            classes="mr-2 text-caption",
                                        )
                                        v3.VIconBtn(
                                            icon="mdi-close",
                                            size="small",
                                            text="Close",
                                            click="config.menu=false",
                                        )
                                with v3.VCardItem(
                                    v_show="config.override_range", classes="py-0"
                                ):
                                    v3.VNumberInput(
                                        model_value=("config.color_range[0]",),
                                        update_modelValue="config.color_range = [Number($event), config.color_range[1]]",
                                        hide_details=True,
                                        density="compact",
                                        variant="outlined",
                                        flat=True,
                                        label="Min",
                                        classes="mt-2",
                                        control_variant="hidden",
                                        precision=("15",),
                                        step=(
                                            "Math.max(0.0001, (config.color_range[1] - config.color_range[0]) / 255)",
                                        ),
                                    )
                                    v3.VNumberInput(
                                        model_value=("config.color_range[1]",),
                                        update_modelValue="config.color_range = [config.color_range[0], Number($event)]",
                                        hide_details=True,
                                        density="compact",
                                        variant="outlined",
                                        flat=True,
                                        label="Max",
                                        classes="mt-2",
                                        control_variant="hidden",
                                        precision=("15",),
                                        step=(
                                            "Math.max(0.0001, (config.color_range[1] - config.color_range[0]) / 255)",
                                        ),
                                    )
                                v3.VDivider(classes="mt-2")
                                with v3.VList(density="compact", max_height="40vh"):
                                    with v3.VListItem(
                                        v_for="url, name in (config.invert ? luts_inverted : luts_normal)",
                                        v_show="!config.color_blind || safe_color[name]",
                                        key="name",
                                        subtitle=("name",),
                                        click=(
                                            self.update_color_preset,
                                            "[name, config.invert, config.use_log_scale]",
                                        ),
                                        active=("config.preset === name",),
                                    ):
                                        html.Img(
                                            src=("url",),
                                            style="width:100%;min-width:20rem;height:1rem;",
                                            classes="rounded",
                                        )
                        html.Div(
                            "{{ utils.quickview.formatRange(config.color_range?.[0], config.use_log_scale) }}",
                            classes="text-caption px-2 text-no-wrap",
                        )
                        with html.Div(
                            classes="overflow-hidden rounded w-100", style="height:70%;"
                        ):
                            html.Img(
                                src=("config.preset_img",),
                                style="width:100%;height:2rem;",
                                draggable=False,
                            )
                        html.Div(
                            "{{ utils.quickview.formatRange(config.color_range?.[1], config.use_log_scale) }}",
                            classes="text-caption px-2 text-no-wrap",
                        )


class ViewManager(TrameComponent):
    def __init__(self, server, source):
        super().__init__(server)
        self.source = source
        self._var2view = {}
        self._camera_sync_in_progress = False
        self._last_vars = {}
        self._active_configs = {}

        pvw.initialize(self.server)

        self.state.luts_normal = {k: v["normal"] for k, v in COLORBAR_CACHE.items()}
        self.state.luts_inverted = {k: v["inverted"] for k, v in COLORBAR_CACHE.items()}
        self.state.safe_color = {name: True for name in COLOR_BLIND_SAFE}

    def refresh_ui(self, **_):
        for view in self._var2view.values():
            view._build_ui()

    def reset_camera(self):
        views = list(self._var2view.values())
        for view in views:
            view.disable_render = True

        for view in views:
            view.reset_camera()

        for view in views:
            view.disable_render = False

    def render(self):
        for view in list(self._var2view.values()):
            view.render()

    def update_color_range(self):
        for view in list(self._var2view.values()):
            view.update_color_range()

    def get_view(self, variable_name, variable_type):
        view = self._var2view.get(variable_name)
        if view is None:
            view = self._var2view.setdefault(
                variable_name,
                VariableView(self.server, self.source, variable_name, variable_type),
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

    @controller.set("swap_variables")
    def swap_variable(self, variable_a, variable_b):
        config_a = self._active_configs[variable_a]
        config_b = self._active_configs[variable_b]
        config_a.order, config_b.order = config_b.order, config_a.order
        config_a.size, config_b.size = config_b.size, config_a.size

    def apply_size(self, n_cols):
        if not self._last_vars:
            return

        if n_cols == 0:
            # Auto based on group size
            if self.state.layout_grouped:
                for var_type in "smi":
                    var_names = self._last_vars[var_type]
                    total_size = len(var_names)

                    if total_size == 0:
                        continue

                    size = auto_size_to_col(total_size)
                    for name in var_names:
                        config = self.get_view(name, var_type).config
                        config.size = size

            else:
                size = auto_size_to_col(len(self._active_configs))
                for config in self._active_configs.values():
                    config.size = size
        else:
            # uniform size
            for config in self._active_configs.values():
                config.size = COL_SIZE_LOOKUP[n_cols]

    def build_auto_layout(self, variables=None):
        if variables is None:
            variables = self._last_vars

        self._last_vars = variables

        # Create UI based on variables
        self.state.swap_groups = {}
        with DivLayout(self.server, template_name="auto_layout") as self.ui:
            if self.state.layout_grouped:
                with v3.VCol(classes="pa-1"):
                    for var_type in "smi":
                        var_names = variables[var_type]
                        total_size = len(var_names)

                        if total_size == 0:
                            continue

                        with v3.VAlert(
                            border="start",
                            classes="pr-1 py-1 pl-3 mb-1",
                            variant="flat",
                            border_color=TYPE_COLOR[var_type],
                        ):
                            with v3.VRow(dense=True):
                                for name in var_names:
                                    view = self.get_view(name, var_type)
                                    view.config.swap_group = sorted(
                                        [n for n in var_names if n != name]
                                    )
                                    with view.config.provide_as("config"):
                                        v3.VCol(
                                            v_if="config.break_row",
                                            cols=12,
                                            classes="pa-0",
                                            style=("`order: ${config.order};`",),
                                        )
                                        with v3.VCol(
                                            offset=("config.offset * config.size",),
                                            cols=("config.size",),
                                            style=("`order: ${config.order};`",),
                                        ):
                                            client.ServerTemplate(name=view.name)
            else:
                all_names = [name for names in variables.values() for name in names]
                with v3.VRow(dense=True, classes="pa-2"):
                    for var_type in "smi":
                        var_names = variables[var_type]
                        for name in var_names:
                            view = self.get_view(name, var_type)
                            view.config.swap_group = [n for n in all_names if n != name]
                            with view.config.provide_as("config"):
                                v3.VCol(
                                    v_if="config.break_row",
                                    cols=12,
                                    classes="pa-0",
                                    style=("`order: ${config.order};`",),
                                )
                                with v3.VCol(
                                    offset=("config.offset * config.size",),
                                    cols=("config.size",),
                                    style=("`order: ${config.order};`",),
                                ):
                                    client.ServerTemplate(name=view.name)

        # Assign any missing order
        self._active_configs = {}
        existed_order = set()
        order_max = 0
        orders_to_update = []
        for var_type in "smi":
            var_names = variables[var_type]
            for name in var_names:
                config = self.get_view(name, var_type).config
                self._active_configs[name] = config
                if config.order:
                    order_max = max(order_max, config.order)
                    assert config.order not in existed_order, "Order already assigned"
                    existed_order.add(config.order)
                else:
                    orders_to_update.append(config)

        next_order = order_max + 1
        for config in orders_to_update:
            config.order = next_order
            next_order += 1

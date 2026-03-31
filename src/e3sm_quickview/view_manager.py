import math

from paraview import simple
from trame.app import TrameComponent, dataclass
from trame.decorators import controller
from trame.ui.html import DivLayout
from trame.widgets import client, html, rca
from trame.widgets import vuetify3 as v3
from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper

from e3sm_quickview.components import view as tview
from e3sm_quickview.presets import COLOR_BLIND_SAFE
from e3sm_quickview.utils.color import COLORBAR_CACHE, lut_to_img


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
    "flow": None,
}


def lut_name(element):
    return element.get("name").lower()


class ViewConfiguration(dataclass.StateDataModel):
    variable: str = dataclass.Sync(str)
    preset: str = dataclass.Sync(str, "BuGnYl")
    invert: bool = dataclass.Sync(bool, False)
    color_blind: bool = dataclass.Sync(bool, False)
    use_log_scale: bool = dataclass.Sync(bool, False)
    color_value_min: str = dataclass.Sync(str, "0")
    color_value_max: str = dataclass.Sync(str, "1")
    color_value_min_valid: bool = dataclass.Sync(bool, True)
    color_value_max_valid: bool = dataclass.Sync(bool, True)
    color_range: list[float] = dataclass.Sync(tuple[float, float], (0, 1))
    override_range: bool = dataclass.Sync(bool, False)
    order: int = dataclass.Sync(int, 0)
    size: int = dataclass.Sync(int, 6)
    offset: int = dataclass.Sync(int, 0)
    break_row: bool = dataclass.Sync(bool, False)
    menu: bool = dataclass.Sync(bool, False)
    swap_group: list[str] = dataclass.Sync(list[str], list)
    search: str | None = dataclass.Sync(str)
    n_colors: int = dataclass.Sync(int, 255)
    lut_img: str = dataclass.Sync(str)


class VariableView(TrameComponent):
    def __init__(self, server, source, variable_name, variable_type):
        super().__init__(server)
        self.source = source
        self.variable_name = variable_name
        self.variable_type = variable_type
        self.disable_render = False
        self.name = f"view_{self.variable_name}"
        self.config = ViewConfiguration(server, variable=variable_name)

        # ParaView
        self.view = simple.CreateRenderView()
        self.view.InteractionMode = "2D"
        self.view.OrientationAxesVisibility = 0
        self.view.UseColorPaletteForBackground = 0
        self.view.BackgroundColorMode = "Gradient"
        self.view.CameraParallelProjection = 1

        # VTK
        self._camera = self.view.GetActiveCamera()
        self.renderer = self.view.GetRenderer()
        self.render_window = self.view.GetRenderWindow()
        self.render_window.SetOffScreenRendering(True)

        input = source.data_reader.vtk_geometry
        self.mapper = vtkPolyDataMapper(input_connection=input.output_port)
        self.actor = vtkActor(mapper=self.mapper)
        self.renderer.AddActor(self.actor)

        # Lookup table color management
        self.lut = simple.GetColorTransferFunction(variable_name)
        self.lut.NanOpacity = 0.0

        # Color mapping
        self.mapper.SetScalarVisibility(1)
        self.mapper.SetScalarModeToUseCellFieldData()
        self.mapper.SelectColorArray(variable_name)
        self.mapper.SetLookupTable(self.lut.GetClientSideObject())

        # Add annotation to the view (continents, gridlines)
        self.renderer.AddActor(source.continent.actor)
        self.renderer.AddActor(source.grid_lines.actor)

        # Reactive behavior
        self.config.watch(
            ["color_value_min", "color_value_max"],
            self.color_range_str_to_float,
        )
        self.config.watch(
            ["override_range", "color_range"], self.update_color_range, eager=True
        )
        self.config.watch(
            ["preset", "invert", "use_log_scale", "n_colors"],
            self.update_color_preset,
            eager=True,
        )

        # Initial flush
        simple.Render(self.view)

        # GUI
        self._build_ui()

        # Need to be after RCA initialization (gui build)
        self.reset_camera()

    def render(self):
        if self.disable_render or not self.ctx.has(self.name):
            return
        self.ctx[self.name].update()

    def set_camera_modified(self, fn):
        self._observer = self.camera.AddObserver("ModifiedEvent", fn)

    @property
    def camera(self):
        return self._camera

    def reset_camera(self):
        self.view.ResetCamera(True, 0.9)
        self.render()

    def update_color_preset(self, name, invert, log_scale, n_colors=255):
        self.config.preset = name
        self.lut.UseLogScale = 0
        self.lut.ApplyPreset(self.config.preset, True)
        if invert:
            self.lut.InvertTransferFunction()

        if log_scale:
            self.lut.MapControlPointsToLogSpace()
            self.lut.UseLogScale = 1

        if n_colors is not None:
            self.lut.NumberOfTableValues = n_colors

        self.config.lut_img = lut_to_img(self.lut)

        self.render()

    def color_range_str_to_float(self, color_value_min, color_value_max):
        try:
            min_value = float(color_value_min)
            self.config.color_value_min_valid = not math.isnan(min_value)
        except ValueError:
            self.config.color_value_min_valid = False

        try:
            max_value = float(color_value_max)
            self.config.color_value_max_valid = not math.isnan(max_value)
        except ValueError:
            self.config.color_value_max_valid = False

        if self.config.color_value_min_valid and self.config.color_value_max_valid:
            self.config.color_range = (min_value, max_value)

    @property
    def data_array(self):
        self.source.data_reader.vtk_geometry.Update()
        ds = self.source.data_reader.vtk_geometry.GetOutput()
        return ds.GetCellData().GetArray(self.variable_name)

    def update_color_range(self, *_):
        if self.config.override_range:
            skip_update = False
            if math.isnan(self.config.color_range[0]):
                skip_update = True
                self.config.color_value_min_valid = False

            if math.isnan(self.config.color_range[1]):
                skip_update = True
                self.config.color_value_max_valid = False

            if skip_update:
                return

            self.lut.RescaleTransferFunction(*self.config.color_range)
        else:
            data_array = self.data_array
            if data_array:
                data_range = data_array.GetRange()
                self.config.color_range = data_range
                self.config.color_value_min = str(data_range[0])
                self.config.color_value_max = str(data_range[1])
                self.config.color_value_min_valid = True
                self.config.color_value_max_valid = True
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
                    classes="ma-0 pa-0 bg-black opacity-90 d-flex align-center flex-nowrap",
                ):
                    tview.create_size_menu(self.name, self.config)
                    with html.Div(
                        self.variable_name,
                        classes="text-subtitle-2 pr-2 text-truncate",
                        style="user-select: none;",
                        title=self.variable_name,
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
                        v_show=("lock_views", True),
                        style="transform: scale(0.75);",
                    )

                    v3.VSpacer()
                    html.Div(
                        "t = {{ time_idx }}",
                        classes="text-caption px-1 text-no-wrap",
                        v_if="timestamps.length > 1",
                    )
                    if self.variable_type == "m":
                        html.Div(
                            "[k = {{ midpoint_idx }}]",
                            classes="text-caption px-1 text-no-wrap",
                            v_if="midpoints.length > 1",
                        )
                    if self.variable_type == "i":
                        html.Div(
                            "[k = {{ interface_idx }}]",
                            classes="text-caption px-1 text-no-wrap",
                            v_if="interfaces.length > 1",
                        )
                    v3.VSpacer()
                    html.Div(
                        "avg = {{"
                        f"fields_avgs['{self.variable_name}']?.toExponential(2) || 'N/A'"
                        "}}",
                        classes="text-caption px-1 text-no-wrap",
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
                    display = rca.RemoteControlledArea(display="image")
                    handler = display.create_view_handler(
                        self.view.GetRenderWindow(),
                        encoder="turbo-jpeg",
                    )
                    self.ctx[self.name] = handler

                tview.create_bottom_bar(self.config, self.update_color_preset)


class ViewManager(TrameComponent):
    def __init__(self, server, source):
        super().__init__(server)
        self.use_image_stream = False
        self.source = source
        self._var2view = {}
        self._camera_sync_in_progress = False
        self._last_vars = {}
        self._active_configs = {}

        rca.initialize(self.server)

        self.state.luts_normal = [
            {"name": k, "url": v["normal"], "safe": k in COLOR_BLIND_SAFE}
            for k, v in COLORBAR_CACHE.items()
        ]
        self.state.luts_inverted = [
            {"name": k, "url": v["inverted"], "safe": k in COLOR_BLIND_SAFE}
            for k, v in COLORBAR_CACHE.items()
        ]

        # Sort lists
        self.state.luts_normal.sort(key=lut_name)
        self.state.luts_inverted.sort(key=lut_name)

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
            view = VariableView(self.server, self.source, variable_name, variable_type)
            self._var2view[variable_name] = view
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
        config_a.offset, config_b.offset = config_b.offset, config_a.offset
        config_a.break_row, config_b.break_row = config_b.break_row, config_a.break_row

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
        # Build a lookup from type name to color from state.variable_types
        type_to_color = {vt["name"]: vt["color"] for vt in self.state.variable_types}
        with DivLayout(self.server, template_name="auto_layout") as self.ui:
            if self.state.layout_grouped:
                with v3.VCol(classes="pa-1"):
                    for var_type in variables.keys():
                        var_names = variables[var_type]
                        total_size = len(var_names)

                        if total_size == 0:
                            continue

                        # Look up color from variable_types to match chip colors
                        border_color = type_to_color.get(", ".join(var_type), "primary")
                        with v3.VAlert(
                            border="start",
                            classes="pr-1 py-1 pl-3 mb-1",
                            variant="flat",
                            border_color=border_color,
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
                                        # For flow handling
                                        with v3.Template(v_if="!config.size"):
                                            v3.VCol(
                                                v_for="i in config.offset",
                                                key="i",
                                                style=("{ order: config.order }",),
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
                    for var_type in variables.keys():
                        var_names = variables[var_type]
                        for name in var_names:
                            view = self.get_view(name, var_type)
                            view.config.swap_group = sorted(
                                [n for n in all_names if n != name]
                            )
                            with view.config.provide_as("config"):
                                v3.VCol(
                                    v_if="config.break_row",
                                    cols=12,
                                    classes="pa-0",
                                    style=("`order: ${config.order};`",),
                                )

                                # For flow handling
                                with v3.Template(v_if="!config.size"):
                                    v3.VCol(
                                        v_for="i in config.offset",
                                        key="i",
                                        style=("{ order: config.order }",),
                                    )
                                with v3.VCol(
                                    offset=(
                                        "config.size ? config.offset * config.size : 0",
                                    ),
                                    cols=("config.size",),
                                    style=("`order: ${config.order};`",),
                                ):
                                    client.ServerTemplate(name=view.name)

        # Assign any missing order
        self._active_configs = {}
        existed_order = set()
        order_max = 0
        orders_to_update = []
        for var_type, var_names in variables.items():
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

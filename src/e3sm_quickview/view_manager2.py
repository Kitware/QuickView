import asyncio
import math

import numpy as np

# Rendering Factory
import vtkmodules.vtkRenderingOpenGL2  # noqa: F401
from paraview import simple
from paraview.modules.vtkPVVTKExtensionsInteractionStyle import (
    vtkPVInteractorStyle,
    vtkPVTrackballZoom,
    vtkTrackballPan,
)
from trame.app import TrameComponent, dataclass
from trame.decorators import controller
from trame.ui.html import DivLayout
from trame.widgets import client, html, rca
from trame.widgets import vuetify3 as v3
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkCamera,
    vtkPolyDataMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)

from e3sm_quickview.components import view as tview
from e3sm_quickview.presets import COLOR_BLIND_SAFE
from e3sm_quickview.utils.color import COLORBAR_CACHE, lut_to_img
from e3sm_quickview.utils.math import (
    calculate_linthresh,
    compute_color_ticks,
    tick_contrast_color,
)


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
    use_log_scale: str = dataclass.Sync(str, "linear")
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
    color_ticks: list = dataclass.Sync(list, list)
    effective_color_range: list[float] = dataclass.Sync(tuple[float, float], (0, 1))


class VariableView(TrameComponent):
    def __init__(self, server, source, variable_name, variable_type, camera):
        super().__init__(server)
        self.source = source
        self.variable_name = variable_name
        self.variable_type = variable_type
        self.disable_render = False
        self.name = f"view_{self.variable_name}"
        self._bounds_key = f"{self.name}_bounds"
        self.config = ViewConfiguration(server, variable=variable_name)
        self._size = (0, 0)

        # VTK
        self.renderer = vtkRenderer(
            active_camera=camera,
            background=(84 / 255, 89 / 255, 109 / 255),
            background2=(0, 0, 42 / 255),
            gradient_background=1,
        )
        self._camera = camera

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

        # GUI
        self._build_ui()

    @property
    def bounds(self):
        return self.state[self._bounds_key]

    @bounds.setter
    def bounds(self, v):
        self.renderer.SetViewport(*v)
        with self.state as s:
            s[self._bounds_key] = v

    def reset_camera(self):
        self.renderer.ResetCameraScreenSpace(0.9)

    def update_size(self, size):
        new_size = (int(size["w"] * size["p"]), int(size["h"] * size["p"]))
        if self._size != new_size:
            self._size = new_size
            self.ctrl.size_update()

    @property
    def size(self):
        return self._size

    def render(self):
        if self.ctx.view:
            self.ctx.view.update()

    def update_color_preset(self, name, invert, log_scale, n_colors=255):
        self.config.preset = name

        # ApplyPreset resets range to [0,1], so always apply the linear
        # preset first, rescale to the current range, then apply transforms
        self._apply_linear_to_lut(invert)
        self.lut.RescaleTransferFunction(*self.config.color_range)

        if n_colors is not None:
            self.lut.NumberOfTableValues = n_colors

        # Capture the linear colorbar image (always the same regardless of scale)
        ctf = self.lut.GetClientSideObject()
        self.config.effective_color_range = ctf.GetRange()
        self.config.lut_img = lut_to_img(self.lut)

        # Rebuild LUT with non-linear control points after capturing the
        # linear colorbar image.  Compute linthresh once from data for symlog.
        linthresh = None
        if log_scale == "log":
            self._apply_log_to_lut()
        elif log_scale == "symlog":
            from vtkmodules.util.numpy_support import vtk_to_numpy

            arr = self.data_array
            if arr is not None:
                linthresh = calculate_linthresh(vtk_to_numpy(arr))
            else:
                linthresh = 1.0
            self._apply_symlog_to_lut(linthresh)

        self._compute_ticks(linthresh=linthresh)

        # Force mapper to pick up LUT changes
        ctf = self.lut.GetClientSideObject()
        self.mapper.SetLookupTable(ctf)
        self.mapper.Modified()

        self.render()

    def _apply_linear_to_lut(self, invert=False):
        """Apply preset with linear scale."""
        self.lut.UseLogScale = 0
        self.lut.ApplyPreset(self.config.preset, True)
        if invert:
            self.lut.InvertTransferFunction()

    def _apply_log_to_lut(self):
        """Transform the already-prepared LUT to log scale.

        Log scale requires all positive values, so clamp the range if needed.
        """
        ctf = self.lut.GetClientSideObject()
        x_min, x_max = ctf.GetRange()
        if x_max <= 0:
            return
        if x_min <= 0:
            x_min = x_max * 1e-6
            self.lut.RescaleTransferFunction(x_min, x_max)
        self.lut.MapControlPointsToLogSpace()
        self.lut.UseLogScale = 1

    def _apply_symlog_to_lut(self, linthresh):
        """Build a symlog LUT with decade control points.

        Control points are placed at powers of 10 (and ±linthresh, 0 for
        mixed-sign data).  The RGB color for each control point is sampled
        from the linear colorbar at the position where that value falls in
        symlog space: t = (symlog(v) - symlog(min)) / (symlog(max) - symlog(min)).
        """
        ctf = self.lut.GetClientSideObject()
        x_min, x_max = ctf.GetRange()
        data_range = x_max - x_min
        if data_range == 0:
            return

        def symlog(v):
            v = np.asarray(v, dtype=float)
            return np.sign(v) * np.log10(1.0 + np.abs(v) / linthresh)

        # Build decade breakpoints
        breakpoints = set()

        if x_min < 0:
            lo = max(linthresh, 1e-30)
            for e in range(
                int(np.floor(np.log10(lo))), int(np.floor(np.log10(abs(x_min)))) + 1
            ):
                val = -(10.0**e)
                if x_min <= val < 0:
                    breakpoints.add(val)

        if x_max > 0:
            lo = max(linthresh, 1e-30)
            for e in range(
                int(np.floor(np.log10(lo))), int(np.floor(np.log10(x_max))) + 1
            ):
                val = 10.0**e
                if 0 < val <= x_max:
                    breakpoints.add(val)

        if x_min < 0 and x_max > 0:
            breakpoints.update((-linthresh, 0.0, linthresh))
        elif x_min < 0 and x_max <= 0:
            if -linthresh >= x_min:
                breakpoints.add(-linthresh)
        elif x_min >= 0 and x_max > 0:
            if linthresh <= x_max:
                breakpoints.add(linthresh)

        breakpoints.add(x_min)
        breakpoints.add(x_max)
        breakpoints = sorted(breakpoints)

        # Symlog range for normalization
        s_min = float(symlog(x_min))
        s_max = float(symlog(x_max))
        s_range = s_max - s_min
        if s_range == 0:
            return

        # Sample RGB from the linear LUT at symlog-normalized positions
        rgb = [0.0, 0.0, 0.0]
        new_rgb_points = []
        for v in breakpoints:
            t = (float(symlog(v)) - s_min) / s_range
            x_lookup = x_min + t * data_range
            ctf.GetColor(x_lookup, rgb)
            new_rgb_points.extend(
                [float(v), float(rgb[0]), float(rgb[1]), float(rgb[2])]
            )

        self.lut.RGBPoints = new_rgb_points

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

        self.update_color_preset(
            self.config.preset,
            self.config.invert,
            self.config.use_log_scale,
            self.config.n_colors,
        )

    def _compute_ticks(self, linthresh=None):
        vmin, vmax = self.config.color_range
        ticks = compute_color_ticks(
            vmin, vmax, scale=self.config.use_log_scale, n=5, linthresh=linthresh
        )
        # Sample colors exactly as lut_to_img does: use RGBPoints range
        rgb_points = self.lut.RGBPoints
        if len(rgb_points) < 4:
            self.config.color_ticks = []
            return
        ctf = self.lut.GetClientSideObject()
        rgb = [0.0, 0.0, 0.0]
        img_min = rgb_points[0]
        img_max = rgb_points[-4]
        img_range = img_max - img_min
        if img_range == 0:
            self.config.color_ticks = []
            return
        for tick in ticks:
            t = tick["position"] / 100.0
            value = img_min + t * img_range
            ctf.GetColor(value, rgb)
            tick["color"] = tick_contrast_color(rgb[0], rgb[1], rgb[2])
        self.config.color_ticks = ticks

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
                    rca.ImageRegion(
                        enable_interaction=True,
                        bounds=(self._bounds_key, (0, 0, 1, 1)),
                        size=(self.update_size, "[$event]"),
                    )

                tview.create_bottom_bar(self.config, self.update_color_preset)


class ViewManager(TrameComponent):
    def __init__(self, server, source):
        super().__init__(server)
        self.use_image_stream = True
        self._camera = vtkCamera(parallel_projection=1)
        self._render_window = vtkRenderWindow()
        self._render_window.OffScreenRenderingOn()
        self._style = vtkPVInteractorStyle()
        self._style.AddManipulator(
            vtkPVTrackballZoom(
                button=3,
                shift=0,
                control=0,
            )
        )
        self._style.AddManipulator(
            vtkPVTrackballZoom(
                button=1,
                shift=1,
                control=0,
            )
        )
        self._style.AddManipulator(
            vtkTrackballPan(
                button=1,
                shift=0,
                control=0,
            )
        )

        self._render_window_interactor = vtkRenderWindowInteractor(
            interactor_style=self._style
        )
        self._render_window_interactor.SetRenderWindow(self._render_window)

        self.loop = asyncio.get_event_loop()
        self.layout_dirty = True
        self.pending_reset_camera = 1
        self.pending_render = False
        self.source = source
        self._var2view = {}
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

    def reset_camera(self, render=True):
        if self.layout_dirty or not self._last_vars:
            self.pending_reset_camera = 1
            return

        view_to_reset = None

        if self.state.active_layout.startswith("view_"):
            for view in self._var2view.values():
                if view.name == self.state.active_layout:
                    view_to_reset = view
                    break

        if not view_to_reset:
            for var_type, var_names in self._last_vars.items():
                for name in var_names:
                    view_to_reset = self.get_view(name, var_type)
                    if view_to_reset:
                        break

                if view_to_reset:
                    break

        if view_to_reset:
            view_to_reset.reset_camera()
            self.pending_reset_camera = 0
        else:
            self.pending_reset_camera = 1

        if render and view_to_reset:
            self.render()

    @controller.set("size_update")
    def on_size_update(self):
        if not self.layout_dirty or not self.pending_render:
            self.pending_render = True
            self.loop.call_later(0.1, self.render)
        self.layout_dirty = True

    def render(self):
        if self.layout_dirty:
            self.compute_layout()

        if self.pending_reset_camera:
            self.reset_camera(False)

        if self.ctx.view:
            self.ctx.view.update()
            self.pending_render = False

    def update_color_range(self):
        for view in list(self._var2view.values()):
            view.update_color_range()
        self.render()

    def get_view(self, variable_name, variable_type):
        view = self._var2view.get(variable_name)
        if view is None:
            view = VariableView(
                self.server, self.source, variable_name, variable_type, self._camera
            )
            self._var2view[variable_name] = view

        return view

    def compute_layout(self, variables=None):
        if variables is None:
            variables = self._last_vars

        if not variables:
            return

        # reset dirty flag
        self.layout_dirty = False

        views = []
        view_size = [0, 0]
        fullscreen_view = None
        fullscreen_view_name = self.state.active_layout
        for var_type, var_names in variables.items():
            for name in var_names:
                view = self.get_view(name, var_type)

                if view.name == fullscreen_view_name:
                    fullscreen_view = view
                    break
                if view.size[1]:
                    views.append(view)
                    view_size[0] = max(view_size[0], view.size[0])
                    view_size[1] = max(view_size[1], view.size[1])
                else:
                    # layout is still dirty
                    self.layout_dirty = True

            if fullscreen_view:
                break

        if fullscreen_view:
            view_size = fullscreen_view.size
            views = [fullscreen_view]

        size = len(views)
        if size == 0:
            return

        width_count = math.ceil(math.sqrt(size))
        height_count = math.ceil(size / width_count)
        full_size = [
            view_size[0] * width_count,
            view_size[1] * height_count,
        ]

        # Update RenderView
        self._render_window.SetSize(*full_size)
        renderers = list(self._render_window.GetRenderers())
        for r in renderers:
            self._render_window.RemoveRenderer(r)

        # Compute Viewport
        dx = 1.0 / width_count
        dy = 1.0 / height_count
        for idx, view in enumerate(views):
            i = idx % width_count
            j = int(idx / width_count)
            bounds = (i * dx, j * dy, (i + 1) * dx, (j + 1) * dy)
            view.bounds = bounds
            self._render_window.AddRenderer(view.renderer)

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
        self.compute_layout()

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

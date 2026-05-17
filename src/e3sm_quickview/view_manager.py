import asyncio
import math
import time

# Rendering Factory
import vtkmodules.vtkRenderingOpenGL2  # noqa: F401
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

from trame.dataclasses.colormaps import ColormapConfig
from trame.widgets.colormaps import HorizontalScalarBar
from trame_colormaps import module as colormaps_module
from e3sm_quickview.components import view as tview
from e3sm_quickview.utils import perf


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


class ViewConfiguration(dataclass.StateDataModel):
    # --- View identity ---
    variable: str = dataclass.Sync(str)

    # --- Layout ---
    order: int = dataclass.Sync(int, 0)
    size: int = dataclass.Sync(int, 6)
    offset: int = dataclass.Sync(int, 0)
    break_row: bool = dataclass.Sync(bool, False)
    swap_group: list[str] = dataclass.Sync(list[str], list)


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

        # Add annotation to the view (continents, gridlines)
        self.renderer.AddActor(source.continent.actor)
        self.renderer.AddActor(source.grid_lines.actor)

        # colormaps module: creates LUT, wires mapper, manages presets/range/ticks
        self.colormap = ColormapConfig(
            server,
            mapper=self.mapper,
            data_array_fn=lambda: self.data_array,
        ).set_data_array(variable_name, lambda: self.data_array, "cell")
        self.colormap.watch(["mapper_change"], lambda *_: self.render())

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

    @property
    def data_array(self):
        self.source.data_reader.vtk_geometry.Update()
        ds = self.source.data_reader.vtk_geometry.GetOutput()
        return ds.GetCellData().GetArray(self.variable_name)

    def _build_ui(self):
        with DivLayout(
            self.server, template_name=self.name, connect_parent=False, classes="h-100"
        ) as self.ui:
            self.ui.root.classes = "h-100"
            with v3.VCard(
                variant="tonal",
                style=(
                    "active_layout !== 'auto_layout' ? `height: calc(100% - ${toolbar_size?.size?.height || 0}px)` : 'overflow-hidden'",
                ),
                tile=("active_layout !== 'auto_layout'",),
                raw_attrs=[f'data-field-name="{self.variable_name}"'],
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

                    v3.VIconBtn(
                        v_tooltip_bottom="'Capture as png'",
                        icon="mdi-camera-outline",
                        size="small",
                        variant="plain",
                        click=f"utils.quickview.capturePanel('{self.variable_name}')",
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
                            aspectRatio: active_layout === 'auto_layout' ? (1.0 / aspect_ratio) : null,
                            height: active_layout !== 'auto_layout' ? 'calc(100% - 2.4rem)' : null,
                            pointerEvents: 'none',
                        }
                        """,
                    ),
                ):
                    rca.ImageRegion(
                        enable_interaction=False,
                        bounds=(self._bounds_key, (0, 0, 1, 1)),
                        size=(self.update_size, "[$event]"),
                    )

                with self.colormap.provide_as(self.name):
                    HorizontalScalarBar(self.name, popup_location="top")


class ViewManager(TrameComponent):
    def __init__(self, server, source):
        super().__init__(server)
        self.use_image_stream = True
        self._camera = vtkCamera(parallel_projection=1)
        self._render_window = vtkRenderWindow()
        self._render_window.OffScreenRenderingOn()

        # Perf: time the actual VTK render on the shared render window.
        # Emits `view.shared.render_window` with the elapsed time for
        # each render. See VariableView._on_render_* in view_manager.py.
        self._render_t0 = None
        self._render_window.AddObserver("StartEvent", self._on_render_start)
        self._render_window.AddObserver("EndEvent", self._on_render_end)
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
        self.server.enable_module(colormaps_module)

    def _on_render_start(self, *_):
        if perf.is_enabled():
            self._render_t0 = time.perf_counter()

    def _on_render_end(self, *_):
        if perf.is_enabled() and self._render_t0 is not None:
            dt_ms = (time.perf_counter() - self._render_t0) * 1000.0
            perf.log("view.shared.render_window", dt_ms)
            self._render_t0 = None

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

    def zoom(self, factor):
        self._camera.SetParallelScale(self._camera.GetParallelScale() * factor)
        self.render()

    def get_zoom(self):
        return self._camera.GetParallelScale()

    def set_zoom(self, scale):
        if scale is None:
            return
        self._camera.SetParallelScale(scale)
        self.render()

    def pan(self, dx, dy):
        cam = self._camera
        scale = cam.GetParallelScale()
        step = scale * 0.1
        pos = list(cam.GetPosition())
        foc = list(cam.GetFocalPoint())
        pos[0] += dx * step
        pos[1] += dy * step
        foc[0] += dx * step
        foc[1] += dy * step
        cam.SetPosition(*pos)
        cam.SetFocalPoint(*foc)
        self.render()

    def get_camera_state(self):
        cam = self._camera
        return {
            "zoom": cam.GetParallelScale(),
            "position": list(cam.GetPosition()),
            "focal_point": list(cam.GetFocalPoint()),
            "view_up": list(cam.GetViewUp()),
            "clipping_range": list(cam.GetClippingRange()),
        }

    def set_camera_state(self, camera_state):
        if camera_state is None:
            return
        cam = self._camera
        cam.SetParallelScale(camera_state["zoom"])
        cam.SetPosition(*camera_state["position"])
        cam.SetFocalPoint(*camera_state["focal_point"])
        if "view_up" in camera_state:
            cam.SetViewUp(*camera_state["view_up"])
        if "clipping_range" in camera_state:
            cam.SetClippingRange(*camera_state["clipping_range"])
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
        """Update color range on all views via colormaps module."""
        for view in list(self._var2view.values()):
            view.colormap.update_color_range()  # colormaps module

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
        # Vuetify color per dimension type (e.g. midpoint, interface) via utils/colors.py
        type_to_color = {vt["name"]: vt["color"] for vt in self.state.variable_types}
        with DivLayout(self.server, template_name="auto_layout") as self.ui:
            self.ui.root.classes = "all-variables"
            if self.state.layout_grouped:
                with v3.VCol(classes="pa-1"):
                    for var_type in variables.keys():
                        var_names = variables[var_type]
                        total_size = len(var_names)

                        if total_size == 0:
                            continue

                        # Border color matches dimension type chips via utils/colors.py
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

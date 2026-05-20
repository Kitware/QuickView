import asyncio
import math
import time

from paraview.modules.vtkPVVTKExtensionsInteractionStyle import (
    vtkPVInteractorStyle,
    vtkPVTrackballZoom,
    vtkTrackballPan,
)
from trame.app import TrameComponent
from trame.decorators import controller
from trame.ui.html import DivLayout
from trame.widgets import client, colormaps, rca
from trame.widgets import vuetify3 as v3
from vtkmodules.vtkRenderingCore import (
    vtkCamera,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)

from e3sm_quickview.utils import perf
from e3sm_quickview.view_panel import VariableView


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

        # Initialize deferred widgets
        rca.initialize(self.server)
        colormaps.initialize(self.server)

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

    def guarded_zoom(self, factor):
        if (
            "adjust-layout" not in self.state.active_tools
            or not self.state.show_zoom_controls
        ):
            return
        self.zoom(factor)

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

    def guarded_pan(self, dx, dy):
        if (
            "adjust-layout" not in self.state.active_tools
            or not self.state.show_pan_controls
        ):
            return

        self.pan(dx, dy)

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

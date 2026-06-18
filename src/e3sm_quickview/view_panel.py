# Rendering Factory
import vtkmodules.vtkRenderingOpenGL2  # noqa: F401

# Trame imports
from trame.app import TrameComponent, dataclass
from trame.dataclasses.colormaps import ColormapConfig
from trame.ui.html import DivLayout
from trame.widgets import colormaps, html, rca
from trame.widgets import vuetify3 as v3
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderer,
)

from e3sm_quickview.components import view as tview


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
        self.actor.ForceOpaqueOn()
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
                v_on_mouseenter=f"hover_info = '{self.variable_name}'",
                v_on_mouseleave="hover_info = null",
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

                with v3.VTooltip(classes="tooltip-no-padding"):
                    with v3.Template(v_slot_activator="{props}"):
                        with html.Div(
                            v_bind="props",
                            style=(
                                """
                        {
                            aspectRatio: active_layout === 'auto_layout' ? (1.0 / aspect_ratio) : null,
                            height: active_layout !== 'auto_layout' ? 'calc(100% - 2.4rem)' : null,
                        }
                        """,
                            ),
                        ):
                            rca.ImageRegion(
                                enable_interaction=False,
                                bounds=(self._bounds_key, (0, 0, 1, 1)),
                                size=(self.update_size, "[$event]"),
                                send_mouse_move=(
                                    f"hover_info === '{self.variable_name}'",
                                ),
                                v_on_wheel="window.scrollBy(0, $event.deltaY)",
                            )

                    with v3.VTable(density="compact", theme="dark", striped="even"):
                        with html.Tbody():
                            with html.Tr(
                                v_for="v, k in hover_tooltip || {}",
                                key="k",
                            ):
                                html.Td("{{k}}")
                                html.Td("{{v[0]}}")

                with self.colormap.provide_as(self.name):
                    colormaps.HorizontalScalarBar(self.name, popup_location="top")

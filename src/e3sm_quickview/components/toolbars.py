import asyncio

from trame.app import asynchronous
from trame.decorators import change
from trame.widgets import vuetify3 as v3

from e3sm_quickview.utils import js, constants

DENSITY = {
    "adjust-layout": "compact",
    "adjust-databounds": "default",
    "select-slice-time": "default",
    "animation-controls": "compact",
}

SIZES = {
    "adjust-layout": 49,
    "adjust-databounds": 65,
    "select-slice-time": 65,
    "animation-controls": 49,
}

VALUES = list(DENSITY.keys())

DEFAULT_STYLES = {
    "color": "white",
    "classes": "border-b-thin",
}


def to_kwargs(value):
    return {
        "v_show": js.is_active(value),
        "density": DENSITY[value],
        **DEFAULT_STYLES,
    }


class Layout(v3.VToolbar):
    def __init__(self, apply_size=None):
        super().__init__(**to_kwargs("adjust-layout"))

        with self:
            v3.VIcon("mdi-collage", classes="px-6 opacity-50")
            v3.VLabel("Layout Controls", classes="text-subtitle-2")
            v3.VSpacer()

            v3.VSlider(
                v_model=("aspect_ratio", 2),
                prepend_icon="mdi-aspect-ratio",
                min=1,
                max=2,
                step=0.1,
                density="compact",
                hide_details=True,
                style="max-width: 400px;",
            )
            v3.VSpacer()
            v3.VCheckbox(
                v_model=("layout_grouped", True),
                label=("layout_grouped ? 'Grouped' : 'Uniform'",),
                hide_details=True,
                inset=True,
                false_icon="mdi-apps",
                true_icon="mdi-focus-field",
                density="compact",
            )

            with v3.VBtn(
                "Size",
                classes="text-none mx-4",
                prepend_icon="mdi-view-module",
                append_icon="mdi-menu-down",
            ):
                with v3.VMenu(activator="parent"):
                    with v3.VList(density="compact"):
                        v3.VListItem(
                            title="Auto",
                            click=(
                                apply_size,
                                "[0]",
                            ),
                        )
                        v3.VListItem(
                            title="Full Width",
                            click=(
                                apply_size,
                                "[1]",
                            ),
                        )
                        v3.VListItem(
                            title="2 Columns",
                            click=(
                                apply_size,
                                "[2]",
                            ),
                        )
                        v3.VListItem(
                            title="3 Columns",
                            click=(
                                apply_size,
                                "[3]",
                            ),
                        )
                        v3.VListItem(
                            title="4 Columns",
                            click=(
                                apply_size,
                                "[4]",
                            ),
                        )
                        v3.VListItem(
                            title="6 Columns",
                            click=(
                                apply_size,
                                "[6]",
                            ),
                        )


class Cropping(v3.VToolbar):
    def __init__(self):
        super().__init__(**to_kwargs("adjust-databounds"))

        with self:
            v3.VIcon("mdi-crop", classes="pl-6 opacity-50")
            with v3.VRow(classes="ma-0 px-2 align-center"):
                with v3.VCol(cols=6):
                    with v3.VRow(classes="mx-2 my-0"):
                        v3.VLabel(
                            "Longitude",
                            classes="text-subtitle-2",
                        )
                        v3.VSpacer()
                        v3.VLabel(
                            "{{ crop_longitude }}",
                            classes="text-body-2",
                        )
                    v3.VRangeSlider(
                        v_model=("crop_longitude", [-180, 180]),
                        min=-180,
                        max=180,
                        step=1,
                        density="compact",
                        hide_details=True,
                    )
                with v3.VCol(cols=6):
                    with v3.VRow(classes="mx-2 my-0"):
                        v3.VLabel(
                            "Latitude",
                            classes="text-subtitle-2",
                        )
                        v3.VSpacer()
                        v3.VLabel(
                            "{{ crop_latitude }}",
                            classes="text-body-2",
                        )
                    v3.VRangeSlider(
                        v_model=("crop_latitude", [-90, 90]),
                        min=-90,
                        max=90,
                        step=1,
                        density="compact",
                        hide_details=True,
                    )


class DataSelection(v3.VToolbar):
    def __init__(self):
        super().__init__(**to_kwargs("select-slice-time"))

        with self:
            v3.VIcon("mdi-tune-variant", classes="ml-3 opacity-50")
            with v3.VRow(classes="ma-0 pr-2 align-center", dense=True):
                # midpoint layer
                with v3.VCol(
                    cols=("toolbar_slider_cols", 4),
                    v_show="midpoints.length > 1",
                ):
                    with v3.VRow(classes="mx-2 my-0"):
                        v3.VLabel(
                            "Layer Midpoints",
                            classes="text-subtitle-2",
                        )
                        v3.VSpacer()
                        v3.VLabel(
                            "{{ parseFloat(midpoints[midpoint_idx] || 0).toFixed(2) }} hPa (k={{ midpoint_idx }})",
                            classes="text-body-2",
                        )
                    v3.VSlider(
                        v_model=("midpoint_idx", 0),
                        min=0,
                        max=("Math.max(0, midpoints.length - 1)",),
                        step=1,
                        density="compact",
                        hide_details=True,
                    )

                # interface layer
                with v3.VCol(
                    cols=("toolbar_slider_cols", 4),
                    v_show="interfaces.length > 1",
                ):
                    with v3.VRow(classes="mx-2 my-0"):
                        v3.VLabel(
                            "Layer Interfaces",
                            classes="text-subtitle-2",
                        )
                        v3.VSpacer()
                        v3.VLabel(
                            "{{ parseFloat(interfaces[interface_idx] || 0).toFixed(2) }} hPa (k={{interface_idx}})",
                            classes="text-body-2",
                        )
                    v3.VSlider(
                        v_model=("interface_idx", 0),
                        min=0,
                        max=("Math.max(0, interfaces.length - 1)",),
                        step=1,
                        density="compact",
                        hide_details=True,
                    )

                # time
                with v3.VCol(
                    cols=("toolbar_slider_cols", 4),
                    v_show="timestamps.length > 1",
                ):
                    self.state.setdefault("time_value", 80.50)
                    with v3.VRow(classes="mx-2 my-0"):
                        v3.VLabel("Time", classes="text-subtitle-2")
                        v3.VSpacer()
                        v3.VLabel(
                            "{{ parseFloat(timestamps[time_idx]).toFixed(2) }} (t={{time_idx}})",
                            classes="text-body-2",
                        )
                    v3.VSlider(
                        v_model=("time_idx", 0),
                        min=0,
                        max=("Math.max(0, timestamps.length - 1)",),
                        step=1,
                        density="compact",
                        hide_details=True,
                    )


class Animation(v3.VToolbar):
    def __init__(self):
        super().__init__(**to_kwargs("animation-controls"))

        with self:
            v3.VIcon(
                "mdi-movie-open-cog-outline",
                classes="px-6 opacity-50",
            )
            with v3.VRow(classes="ma-0 px-2 align-center"):
                v3.VSelect(
                    v_model=("animation_track", "timestamps"),
                    items=("animation_tracks", []),
                    flat=True,
                    variant="plain",
                    hide_details=True,
                    density="compact",
                    style="max-width: 10rem;",
                )
                v3.VDivider(vertical=True, classes="mx-2")
                v3.VSlider(
                    v_model=("animation_step", 1),
                    min=0,
                    max=("amimation_step_max", 0),
                    step=1,
                    hide_details=True,
                    density="compact",
                    classes="mx-4",
                )
                v3.VDivider(vertical=True, classes="mx-2")
                v3.VIconBtn(
                    icon="mdi-page-first",
                    flat=True,
                    disabled=("animation_step === 0",),
                    click="animation_step = 0",
                )
                v3.VIconBtn(
                    icon="mdi-chevron-left",
                    flat=True,
                    disabled=("animation_step === 0",),
                    click="animation_step = Math.max(0, animation_step - 1)",
                )
                v3.VIconBtn(
                    icon="mdi-chevron-right",
                    flat=True,
                    disabled=("animation_step === amimation_step_max",),
                    click="animation_step = Math.min(amimation_step_max, animation_step + 1)",
                )
                v3.VIconBtn(
                    icon="mdi-page-last",
                    disabled=("animation_step === amimation_step_max",),
                    flat=True,
                    click="animation_step = amimation_step_max",
                )
                v3.VDivider(vertical=True, classes="mx-2")
                v3.VIconBtn(
                    icon=("animation_play ? 'mdi-stop' : 'mdi-play'",),
                    flat=True,
                    click="animation_play = !animation_play",
                )

    @change("animation_track")
    def _on_animation_track_change(self, animation_track, **_):
        self.state.animation_step = 0
        self.state.amimation_step_max = 0

        if animation_track:
            self.state.amimation_step_max = len(self.state[animation_track]) - 1

    @change("animation_step")
    def _on_animation_step(self, animation_track, animation_step, **_):
        if animation_track:
            self.state[constants.TRACK_STEPS[animation_track]] = animation_step

    @change("animation_play")
    def _on_animation_play(self, animation_play, **_):
        if animation_play:
            asynchronous.create_task(self._run_animation())

    async def _run_animation(self):
        with self.state as s:
            while s.animation_play:
                await asyncio.sleep(0.1)
                if s.animation_step < s.amimation_step_max:
                    with s:
                        s.animation_step += 1
                    await self.server.network_completion
                else:
                    s.animation_play = False

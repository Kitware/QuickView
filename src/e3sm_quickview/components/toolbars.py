import asyncio

from trame.app import asynchronous
from trame.decorators import change
from trame.widgets import client, html
from trame.widgets import vuetify3 as v3

from e3sm_quickview.utils import js

DENSITY = {
    "adjust-layout": "compact",
    "adjust-databounds": "default",
    "select-slice-time": "default",
    "animation-controls": "compact",
}

SIZES = {
    "adjust-layout": 49,
    "adjust-databounds": 65,
    "select-slice-time": 70,
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
    def __init__(
        self,
        apply_size=None,
        zoom=None,
        pan=None,
        reset_camera=None,
    ):
        super().__init__(**to_kwargs("adjust-layout"))

        self.state.setdefault("show_zoom_controls", False)
        self.state.setdefault("show_pan_controls", False)
        self.state.setdefault("show_aspect_ratio", False)

        with self:
            v3.VIcon("mdi-view-module", classes="px-6 opacity-50")
            v3.VSpacer()

            # --- Aspect ratio toggle + slider ---
            with v3.VSheet(
                classes="d-flex align-center rounded px-1",
                color=("show_aspect_ratio ? 'grey-lighten-3' : 'transparent'",),
            ):
                v3.VIconBtn(
                    v_tooltip_bottom="'Toggle aspect ratio'",
                    icon="mdi-arrow-expand-vertical",
                    flat=True,
                    click="show_aspect_ratio = !show_aspect_ratio; show_zoom_controls = false; show_pan_controls = false",
                    color=("show_aspect_ratio ? 'primary' : ''",),
                )
                v3.VSlider(
                    v_if="show_aspect_ratio",
                    v_tooltip_bottom="'Reduce (left) / Increase (right) vertical aspect'",
                    v_model=("aspect_ratio", 0.5),
                    min=0,
                    max=4,
                    step=0.25,
                    show_ticks="always",
                    density="compact",
                    hide_details=True,
                    style="min-width: 200px; max-width: 300px;",
                )

            # --- Zoom toggle + in/out ---
            with v3.VSheet(
                classes="d-flex align-center rounded px-1",
                color=("show_zoom_controls ? 'grey-lighten-3' : 'transparent'",),
            ):
                v3.VIconBtn(
                    v_tooltip_bottom="'Toggle zoom controls'",
                    icon="mdi-magnify",
                    flat=True,
                    click="show_zoom_controls = !show_zoom_controls; show_pan_controls = false; show_aspect_ratio = false",
                    color=("show_zoom_controls ? 'primary' : ''",),
                )
                v3.VIconBtn(
                    v_if="show_zoom_controls",
                    v_tooltip_bottom="'Zoom in'",
                    icon="mdi-plus",
                    flat=True,
                    click=(zoom, "[0.8333333]"),
                )
                v3.VIconBtn(
                    v_if="show_zoom_controls",
                    v_tooltip_bottom="'Zoom out'",
                    icon="mdi-minus",
                    flat=True,
                    click=(zoom, "[1.2]"),
                )

            # --- Pan toggle + directions ---
            with v3.VSheet(
                classes="d-flex align-center rounded px-1",
                color=("show_pan_controls ? 'grey-lighten-3' : 'transparent'",),
            ):
                v3.VIconBtn(
                    v_tooltip_bottom="'Toggle pan controls'",
                    icon="mdi-arrow-all",
                    flat=True,
                    click="show_pan_controls = !show_pan_controls; show_zoom_controls = false; show_aspect_ratio = false",
                    color=("show_pan_controls ? 'primary' : ''",),
                )
                v3.VIconBtn(
                    v_if="show_pan_controls",
                    v_tooltip_bottom="'Pan up'",
                    icon="mdi-arrow-up",
                    flat=True,
                    click=(pan, "[0, -1]"),
                )
                v3.VIconBtn(
                    v_if="show_pan_controls",
                    v_tooltip_bottom="'Pan down'",
                    icon="mdi-arrow-down",
                    flat=True,
                    click=(pan, "[0, 1]"),
                )
                v3.VIconBtn(
                    v_if="show_pan_controls",
                    v_tooltip_bottom="'Pan left'",
                    icon="mdi-arrow-left",
                    flat=True,
                    click=(pan, "[1, 0]"),
                )
                v3.VIconBtn(
                    v_if="show_pan_controls",
                    v_tooltip_bottom="'Pan right'",
                    icon="mdi-arrow-right",
                    flat=True,
                    click=(pan, "[-1, 0]"),
                )

            # --- Reset view ---
            v3.VIconBtn(
                v_tooltip_bottom="'Reset view'",
                icon="mdi-fit-to-page-outline",
                flat=True,
                click=reset_camera,
            )

            v3.VDivider(vertical=True, classes="mx-1")

            # --- Grouped/Uniform toggle ---
            v3.VCheckbox(
                v_tooltip_bottom="layout_grouped ? 'Switch to uniform' : 'Switch to grouped'",
                v_model=("layout_grouped", True),
                hide_details=True,
                inset=True,
                false_icon="mdi-apps",
                true_icon="mdi-focus-field",
                density="compact",
            )

            # --- Size menu ---
            with v3.VBtn(
                v_tooltip_bottom="'Column layout'",
                flat=True,
                size="small",
            ):
                v3.VIcon("mdi-view-column")
                with v3.VMenu(activator="parent"):
                    with v3.VList(density="compact"):
                        with v3.VListItem(
                            title="Auto flow",
                            click=(
                                apply_size,
                                "['flow']",
                            ),
                        ):
                            with v3.Template(v_slot_append=True):
                                v3.VHotkey(
                                    keys="=",
                                    variant="contained",
                                    inline=True,
                                    classes="ml-6 mt-n1",
                                )
                        with v3.VListItem(
                            title="Auto",
                            click=(
                                apply_size,
                                "[0]",
                            ),
                        ):
                            with v3.Template(v_slot_append=True):
                                v3.VHotkey(
                                    keys="0",
                                    variant="contained",
                                    inline=True,
                                    classes="ml-6 mt-n1",
                                )
                        with v3.VListItem(
                            title="Full Width",
                            click=(
                                apply_size,
                                "[1]",
                            ),
                        ):
                            with v3.Template(v_slot_append=True):
                                v3.VHotkey(
                                    keys="1",
                                    variant="contained",
                                    inline=True,
                                    classes="ml-6 mt-n1",
                                )
                        with v3.VListItem(
                            title="2 Columns",
                            click=(
                                apply_size,
                                "[2]",
                            ),
                        ):
                            with v3.Template(v_slot_append=True):
                                v3.VHotkey(
                                    keys="2",
                                    variant="contained",
                                    inline=True,
                                    classes="ml-6 mt-n1",
                                )
                        with v3.VListItem(
                            title="3 Columns",
                            click=(
                                apply_size,
                                "[3]",
                            ),
                        ):
                            with v3.Template(v_slot_append=True):
                                v3.VHotkey(
                                    keys="3",
                                    variant="contained",
                                    inline=True,
                                    classes="ml-6 mt-n1",
                                )
                        with v3.VListItem(
                            title="4 Columns",
                            click=(
                                apply_size,
                                "[4]",
                            ),
                        ):
                            with v3.Template(v_slot_append=True):
                                v3.VHotkey(
                                    keys="4",
                                    variant="contained",
                                    inline=True,
                                    classes="ml-6 mt-n1",
                                )
                        with v3.VListItem(
                            title="6 Columns",
                            click=(
                                apply_size,
                                "[6]",
                            ),
                        ):
                            with v3.Template(v_slot_append=True):
                                v3.VHotkey(
                                    keys="6",
                                    variant="contained",
                                    inline=True,
                                    classes="ml-6 mt-n1",
                                )


class Cropping(v3.VToolbar):
    def __init__(self):
        super().__init__(**to_kwargs("adjust-databounds"))

        with self:
            with v3.VTooltip(
                text=(
                    "crop_slider_edit ? 'Toggle to text edit' : 'Toggle to slider edit'",
                ),
            ):
                with v3.Template(v_slot_activator="{ props }"):
                    v3.VIcon(
                        "mdi-web",
                        v_bind="props",
                        classes="pl-6 opacity-50",
                        click="crop_slider_edit = !crop_slider_edit",
                    )
            with v3.VRow(
                classes="ma-0 px-2 align-center", v_if=("crop_slider_edit", True)
            ):
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
            with v3.VRow(classes="ma-0 pl-6 pr-2 align-center ga-4", v_else=True):
                v3.VNumberInput(
                    label="Longitude (min)",
                    v_model=("crop_longitude_min", -180),
                    min=[-180],
                    max=("crop_longitude_max", 180),
                    step=[1],
                    hide_details=True,
                    density="comfortable",
                    variant="plain",
                    flat=True,
                    control_variant="stacked",
                )
                v3.VNumberInput(
                    label="Longitude (max)",
                    v_model=("crop_longitude_max", 180),
                    min=("crop_longitude_min", -180),
                    max=[180],
                    step=[1],
                    hide_details=True,
                    density="comfortable",
                    variant="plain",
                    flat=True,
                    control_variant="stacked",
                    inset=True,
                )
                v3.VNumberInput(
                    label="Latitude (min)",
                    v_model=("crop_latitude_min", -90),
                    min=[-90],
                    max=("crop_latitude_max", 90),
                    step=[1],
                    hide_details=True,
                    density="comfortable",
                    variant="plain",
                    flat=True,
                    control_variant="stacked",
                    inset=True,
                )
                v3.VNumberInput(
                    label="Latitude (max)",
                    v_model=("crop_latitude_max", 90),
                    min=("crop_latitude_min", -90),
                    max=[90],
                    step=[1],
                    hide_details=True,
                    density="comfortable",
                    variant="plain",
                    flat=True,
                    control_variant="stacked",
                    inset=True,
                )

    @change("crop_longitude_min", "crop_longitude_max")
    def _on_crop_lon(self, crop_longitude_min, crop_longitude_max, **_):
        if crop_longitude_min is None or crop_longitude_max is None:
            return
        data_range = [float(crop_longitude_min), float(crop_longitude_max)]
        if data_range[0] < data_range[1]:
            self.state.crop_longitude = data_range

    @change("crop_latitude_min", "crop_latitude_max")
    def _on_crop_lat(self, crop_latitude_min, crop_latitude_max, **_):
        if crop_latitude_min is None or crop_latitude_max is None:
            return
        data_range = [float(crop_latitude_min), float(crop_latitude_max)]
        if data_range[0] < data_range[1]:
            self.state.crop_latitude = data_range


class DataSelection(html.Div):
    def __init__(self):
        style = to_kwargs("select-slice-time")
        # Use style instead of d-flex class to avoid !important override of v-show
        # Add background color to match VToolbar appearance
        style["style"] = (
            "display: flex; align-items: center; background: rgb(var(--v-theme-surface));"
        )
        super().__init__(**style)

        with self:
            with v3.VTooltip(
                text=(
                    "slice_slider_edit ? 'Toggle to text edit' : 'Toggle to slider edit'",
                ),
            ):
                with v3.Template(v_slot_activator="{ props }"):
                    v3.VIcon(
                        "mdi-tune-variant",
                        v_bind="props",
                        classes="ml-3 mr-2 opacity-50",
                        click="slice_slider_edit = !slice_slider_edit",
                    )

            with v3.VRow(
                classes="ma-0 pr-2 flex-wrap flex-grow-1",
                dense=True,
                v_if=("slice_slider_edit", True),
            ):
                # Debug: Show animation_tracks array
                # html.Div(
                #     "Animation Tracks: {{ JSON.stringify(available_animation_tracks) }}",
                #     classes="col-12",
                # )
                # Each track gets a column (3 per row)
                with v3.VCol(
                    cols=("utils.quickview.cols(available_animation_tracks.length)",),
                    v_for="(track, idx) in available_animation_tracks",
                    key="idx",
                    classes="pa-2",
                ):
                    with client.Getter(name=("track",), value_name="t_values"):
                        with client.Getter(
                            name=("track + '_idx'",), value_name="t_idx"
                        ):
                            with v3.VRow(classes="ma-0 align-center", dense=True):
                                v3.VLabel(
                                    "{{track}}",
                                    classes="text-subtitle-2",
                                )
                                v3.VSpacer()
                                v3.VLabel(
                                    "{{ dim_units[track] ? parseFloat(t_values[t_idx]).toFixed(2) + ' ' + dim_units[track] : 'Index value: ' + t_idx }} (k={{ t_idx }})",
                                    classes="text-body-2",
                                )
                            v3.VSlider(
                                model_value=("t_idx",),
                                update_modelValue=(
                                    self.on_update_slider,
                                    "[track, $event]",
                                ),
                                min=0,
                                # max=100,#("get(track.value).length - 1",),
                                max=("t_values.length - 1",),
                                step=1,
                                density="compact",
                                hide_details=True,
                            )
            with v3.VRow(
                classes="ma-0 pl-6 pr-2 align-center ga-4",
                v_if="!slice_slider_edit",
            ):
                with v3.VCol(
                    v_for="(track, idx) in available_animation_tracks",
                    key="idx",
                ):
                    with client.Getter(name=("track",), value_name="t_values"):
                        with client.Getter(
                            name=("track + '_idx'",), value_name="t_idx"
                        ):
                            with v3.VRow(classes="ma-0 align-center", dense=True):
                                v3.VNumberInput(
                                    model_value=("Number(t_idx)",),
                                    update_modelValue=(
                                        self.on_update_slider,
                                        "[track, Number($event)]",
                                    ),
                                    key=("track + '_' + t_idx",),
                                    min=[0],
                                    max=["t_values ? t_values.length - 1 : 0"],
                                    step=[1],
                                    hide_details=True,
                                    density="comfortable",
                                    variant="plain",
                                    flat=True,
                                    control_variant="stacked",
                                    style="max-width: 100px;",
                                    reverse=True,
                                )
                                v3.VLabel(
                                    "{{track}}",
                                    classes="text-subtitle-2 ml-2 mt-1",
                                )
                                v3.VLabel(
                                    "{{ dim_units[track] ? parseFloat(t_values[Number(t_idx)]).toFixed(2) + ' ' + dim_units[track] : 'Index value: ' + t_idx }}",
                                    classes="text-body-2 text-no-wrap ml-2 mt-1",
                                )

    def on_update_slider(self, dimension, index, *_, **__):
        with self.state:
            self.state[f"{dimension}_idx"] = int(index)


class Animation(v3.VToolbar):
    def __init__(self):
        super().__init__(**to_kwargs("animation-controls"))
        with self:
            v3.VIcon(
                "mdi-video",
                classes="px-6 opacity-50",
            )
            with v3.VRow(classes="ma-0 px-2 align-center"):
                v3.VSelect(
                    v_model=("animation_track", None),
                    items=("available_animation_tracks", []),
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
                    max=("animation_step_max", 0),
                    step=1,
                    hide_details=True,
                    density="compact",
                    classes="mx-4",
                )
                v3.VDivider(vertical=True, classes="mx-2")
                v3.VIconBtn(
                    v_tooltip_bottom="'First step'",
                    icon="mdi-page-first",
                    flat=True,
                    disabled=("animation_step === 0",),
                    click="animation_step = 0",
                )
                v3.VIconBtn(
                    v_tooltip_bottom="'Previous step'",
                    icon="mdi-chevron-left",
                    flat=True,
                    disabled=("animation_step === 0",),
                    click="animation_step = Math.max(0, animation_step - 1)",
                )
                v3.VIconBtn(
                    v_tooltip_bottom="'Next step'",
                    icon="mdi-chevron-right",
                    flat=True,
                    disabled=("animation_step === animation_step_max",),
                    click="animation_step = Math.min(animation_step_max, animation_step + 1)",
                )
                v3.VIconBtn(
                    v_tooltip_bottom="'Last step'",
                    icon="mdi-page-last",
                    disabled=("animation_step === animation_step_max",),
                    flat=True,
                    click="animation_step = animation_step_max",
                )
                v3.VDivider(vertical=True, classes="mx-2")
                v3.VIconBtn(
                    v_tooltip_bottom="'Play reverse'",
                    icon=(
                        "animation_play && animation_direction === 'reverse' ? 'mdi-stop' : 'mdi-play'",
                    ),
                    flat=True,
                    click="if (animation_play && animation_direction === 'reverse') { animation_play = false } else { animation_direction = 'reverse'; animation_play = true }",
                    disabled=(
                        "capture_recording || (animation_play && animation_direction === 'forward')",
                    ),
                    style="transform: scaleX(-1);",
                )
                v3.VIconBtn(
                    v_tooltip_bottom="'Play forward'",
                    icon=(
                        "animation_play && animation_direction === 'forward' ? 'mdi-stop' : 'mdi-play'",
                    ),
                    flat=True,
                    click="if (animation_play && animation_direction === 'forward') { animation_play = false } else { animation_direction = 'forward'; animation_play = true }",
                    disabled=(
                        "capture_recording || (animation_play && animation_direction === 'reverse')",
                    ),
                )
                v3.VDivider(vertical=True, classes="mx-2")

                with v3.VIconBtn(
                    classes="position-relative",
                    flat=True,
                    v_if=("animation_export", False),
                    click="animation_export = false",
                ):
                    v3.VIcon("mdi-download-multiple-outline")
                    v3.VProgressCircular(
                        color="error",
                        bg_color="white",
                        width=2,
                        size=28,
                        indeterminate=True,
                        classes="position-absolute",
                    )
                with v3.VMenu(
                    v_else=True,
                    close_on_content_click=False,
                    v_model=("show_animation_export_menu", False),
                ):
                    with v3.Template(v_slot_activator="{ props }"):
                        v3.VIconBtn(
                            v_bind="props",
                            v_tooltip_bottom="'Export animation (ZIP)'",
                            icon="mdi-download-multiple-outline",
                            flat=True,
                            loading=("animation_export", False),
                            disabled=(
                                "!animation_track || animation_play || animation_export",
                            ),
                        )
                    with v3.VList(
                        density="compact",
                        v_model_activated=("animation_export_fields", []),
                        activatable=True,
                        active_strategy="independent",
                    ):
                        v3.VListItem(title="Full grid", value=("false",))
                        v3.VDivider()
                        v3.VListItem(
                            v_for="name in variables_selected",
                            key="name",
                            title=("name",),
                            value=("name",),
                        )
                        v3.VDivider()
                        v3.VListItem(
                            active=False,
                            title="Export animation",
                            value=("null",),
                            click="utils.quickview.captureAnimation(animation_export_fields)",
                        )

    @change("animation_track")
    def _on_animation_track_change(self, animation_track, **_):
        self.state.animation_step = 0
        self.state.animation_step_max = 0

        if animation_track:
            values = self.state[animation_track]
            if values:
                self.state.animation_step_max = len(values) - 1

    @change("animation_step")
    def _on_animation_step(self, animation_track, animation_step, **_):
        if animation_track:
            self.state[f"{animation_track}_idx"] = animation_step

    @change("animation_play")
    def _on_animation_play(self, animation_play, **_):
        if animation_play:
            asynchronous.create_task(self._run_animation())

    async def _step_to(self, step):
        """Advance animation to a given step and wait for render."""
        with self.state:
            self.state.animation_step = step
        await self.server.network_completion

    async def _run_animation(self):
        with self.state as s:
            while s.animation_play:
                await asyncio.sleep(0.1)
                if s.animation_direction == "reverse":
                    if s.animation_step > 0:
                        await self._step_to(s.animation_step - 1)
                    else:
                        await self._step_to(s.animation_step_max)
                else:
                    if s.animation_step < s.animation_step_max:
                        await self._step_to(s.animation_step + 1)
                    else:
                        await self._step_to(0)

from trame.app import asynchronous
from trame.decorators import TrameApp, change
from trame.widgets import html, vuetify2 as v2

from e3sm_quickview.ui.collapsible import CollapsableSection

from e3sm_quickview.view_manager import ViewManager
from e3sm_quickview.pipeline import EAMVisSource

import asyncio


@TrameApp()
class SliceSelection(CollapsableSection):
    def __init__(self, source: EAMVisSource, view_manager: ViewManager):
        super().__init__("Slice Selection", "show_slice")

        self.source = source
        self.views = view_manager

        style = dict(dense=True, hide_details=True)
        with self.content:
            with v2.VRow(
                classes="text-center align-center justify-center text-subtitle-1 pt-3 px-3"
            ):
                with v2.VCol(classes="text-left py-0"):
                    html.Div("Layer Midpoints", classes="mb-1")
                with v2.VCol(classes="py-0", cols=1):
                    with v2.VBtn(
                        icon=True,
                        flat=True,
                        **style,
                        click=(self.on_click_advance_middle, "[-1]"),
                    ):
                        v2.VIcon("mdi-skip-previous", small=True)
                with v2.VCol(classes="py-0", cols=1):
                    with v2.VBtn(
                        icon=True,
                        flat=True,
                        **style,
                        click=(self.on_click_advance_middle, "[1]"),
                    ):
                        v2.VIcon("mdi-skip-next", small=True)
                with v2.VCol(classes="mr-4 py-0", cols=1):
                    v2.VCheckbox(
                        v_model=("play_lev", False),
                        off_icon="mdi-play-circle",
                        on_icon="mdi-stop-circle",
                        classes="ma-0 pa-0",
                        **style,
                    )

            with v2.VRow(
                classes="text-center align-center justify-center text-subtitle-1 pb-2 px-3"
            ):
                with v2.VCol(cols=8, classes="py-0 pl-3"):
                    v2.VSlider(
                        v_model=("midpoint", 0),
                        min=0,
                        max=("Math.max(0, midpoints.length - 1)",),
                        color="primary",
                        classes="py-0 pl-3",
                        **style,
                    )
                with v2.VCol(cols=4, classes="text-left py-0"):
                    html.Div(
                        "{{midpoints.length > 0 ? parseFloat(midpoints[midpoint]).toFixed(2) + ' hPa (k=' + midpoint + ')' : '0.00 hPa (k=0)'}}",
                        classes="font-weight-medium",
                    )
            # v2.VDivider(classes="my-2")

            with v2.VRow(
                classes="text-center align-center justify-center text-subtitle-1 pt-3 px-3"
            ):
                with v2.VCol(classes="text-left py-0"):
                    html.Div("Layer Interfaces", classes="mb-1")
                with v2.VCol(classes="py-0", cols=1):
                    with v2.VBtn(
                        icon=True,
                        flat=True,
                        **style,
                        click=(self.on_click_advance_interface, "[-1]"),
                    ):
                        v2.VIcon("mdi-skip-previous", small=True)
                with v2.VCol(classes="py-0", cols=1):
                    with v2.VBtn(
                        icon=True,
                        flat=True,
                        **style,
                        click=(self.on_click_advance_interface, "[1]"),
                    ):
                        v2.VIcon("mdi-skip-next", small=True)
                with v2.VCol(classes="mr-4 py-0", cols=1):
                    v2.VCheckbox(
                        v_model=("play_ilev", False),
                        off_icon="mdi-play-circle",
                        on_icon="mdi-stop-circle",
                        classes="ma-0 pa-0",
                        **style,
                    )

            with v2.VRow(
                classes="text-center align-center justify-center text-subtitle-1 pb-2 px-3"
            ):
                with v2.VCol(cols=8, classes="py-0"):
                    v2.VSlider(
                        v_model=("interface", 0),
                        min=0,
                        max=("Math.max(0, interfaces.length - 1)",),
                        color="secondary",
                        classes="py-0 pl-3",
                        **style,
                    )
                with v2.VCol(cols=4, classes="text-left py-0"):
                    html.Div(
                        "{{interfaces.length > 0 ? parseFloat(interfaces[interface]).toFixed(2) + ' hPa (k=' + interface + ')' : '0.00 hPa (k=0)'}}",
                        classes="font-weight-medium",
                    )
            # v2.VDivider(classes="my-2")

            with v2.VRow(
                classes="text-center align-center justify-center text-subtitle-1 pt-3 px-3"
            ):
                with v2.VCol(classes="text-left py-0"):
                    html.Div("Time", classes="mb-1")
                with v2.VCol(classes="py-0", cols=1):
                    with v2.VBtn(
                        icon=True,
                        flat=True,
                        **style,
                        click=(self.on_click_advance_time, "[-1]"),
                    ):
                        v2.VIcon("mdi-skip-previous", small=True)
                with v2.VCol(classes="py-0", cols=1):
                    with v2.VBtn(
                        icon=True,
                        flat=True,
                        **style,
                        click=(self.on_click_advance_time, "[1]"),
                    ):
                        v2.VIcon("mdi-skip-next", small=True)
                with v2.VCol(classes="mr-4 py-0", cols=1):
                    v2.VCheckbox(
                        v_model=("play_time", False),
                        off_icon="mdi-play-circle",
                        on_icon="mdi-stop-circle",
                        classes="ma-0 pa-0",
                        **style,
                    )

            with v2.VRow(
                classes="text-center align-center justify-center text-subtitle-1 pb-2 px-3"
            ):
                with v2.VCol(cols=8, classes="py-0"):
                    v2.VSlider(
                        v_model=("tstamp", 0),
                        min=0,
                        max=("Math.max(0, timesteps.length - 1)",),
                        color="accent",
                        classes="py-0 pl-3",
                        **style,
                    )
                with v2.VCol(cols=4, classes="text-left py-0"):
                    html.Div(
                        "{{timesteps.length > 0 ? parseFloat(timesteps[tstamp]).toFixed(2) + ' (t=' + tstamp + ')' : '0.00 (t=0)'}}",
                        classes="font-weight-medium",
                    )
            # v2.VDivider(classes="my-4")

            with v2.VRow(classes="text-center align-center text-subtitle-1 pt-2 pa-2"):
                with v2.VCol(cols=3, classes="py-0"):
                    html.Div(
                        "{{ cliplong[0].toFixed(1) }}°",
                        classes="font-weight-medium text-center",
                    )
                with v2.VCol(cols=6, classes="py-0"):
                    html.Div("Longitude")
                with v2.VCol(cols=3, classes="py-0"):
                    html.Div(
                        "{{ cliplong[1].toFixed(1) }}°",
                        classes="font-weight-medium text-center",
                    )
            v2.VRangeSlider(
                v_model=("cliplong", [self.source.extents[0], self.source.extents[1]]),
                min=-180,
                max=180,
                step=0.5,
                color="blue-grey",
                **style,
                flat=True,
                variant="solo",
                classes="pt-2 px-6",
            )
            # v2.VDivider(classes="my-4")

            with v2.VRow(classes="text-center align-center text-subtitle-1 pt-4 px-2"):
                with v2.VCol(cols=3, classes="py-0"):
                    html.Div(
                        "{{ cliplat[0].toFixed(1) }}°",
                        classes="font-weight-medium text-center",
                    )
                with v2.VCol(cols=6, classes="py-0"):
                    html.Div("Latitude")
                with v2.VCol(cols=3, classes="py-0"):
                    html.Div(
                        "{{ cliplat[1].toFixed(1) }}°",
                        classes="font-weight-medium text-center",
                    )
            v2.VRangeSlider(
                v_model=("cliplat", [self.source.extents[2], self.source.extents[3]]),
                min=-90,
                max=90,
                step=0.5,
                color="blue-grey",
                **style,
                flat=True,
                variant="solo",
                classes="pt-2 px-6",
            )

    @change("midpoint", "interface", "tstamp", "cliplat", "cliplong")
    def update_pipeline_interactive(self, **kwargs):
        lev = self.state.midpoint
        ilev = self.state.interface
        tstamp = self.state.tstamp
        long = self.state.cliplong
        lat = self.state.cliplat
        time = 0.0 if len(self.state.timesteps) == 0 else self.state.timesteps[tstamp]

        self.source.UpdateLev(lev, ilev)
        self.source.UpdateTimeStep(tstamp)
        self.source.ApplyClipping(long, lat)
        self.source.UpdatePipeline(time)

        # update_views_for_timestep will handle fitting and rendering
        self.views.update_views_for_timestep()
        # Render once after all updates
        self.views.render_all_views()

    def on_click_advance_middle(self, diff):
        if len(self.state.midpoints) > 0:
            current = self.state.midpoint
            update = current + diff
            self.state.midpoint = update % len(self.state.midpoints)

    @change("play_lev")
    @asynchronous.task
    async def play_lev(self, **kwargs):
        state = self.state
        while state.play_lev:
            state.play_ilev = False
            state.play_time = False
            with state:
                self.on_click_advance_middle(1)
                await asyncio.sleep(0.1)

    def on_click_advance_interface(self, diff):
        if len(self.state.interfaces) > 0:
            current = self.state.interface
            update = current + diff
            self.state.interface = update % len(self.state.interfaces)

    @change("play_ilev")
    @asynchronous.task
    async def play_ilev(self, **kwargs):
        state = self.state
        while state.play_ilev:
            state.play_lev = False
            state.play_time = False
            with state:
                self.on_click_advance_interface(1)
                await asyncio.sleep(0.1)

    def on_click_advance_time(self, diff):
        if len(self.state.timesteps) > 0:
            current = self.state.tstamp
            update = current + diff
            self.state.tstamp = update % len(self.state.timesteps)

    @change("play_time")
    @asynchronous.task
    async def play_time(self, **kwargs):
        state = self.state
        while state.play_time:
            state.play_lev = False
            state.play_ilev = False
            with state:
                self.on_click_advance_time(1)
                await asyncio.sleep(0.1)

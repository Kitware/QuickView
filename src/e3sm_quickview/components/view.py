from trame.widgets import html
from trame.widgets import vuetify3 as v3


def create_size_menu(name, config):
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
            with config.provide_as("config"):
                with v3.VList(density="compact"):
                    v3.VListItem(
                        subtitle="Full Screen",
                        click=f"active_layout = '{name}'",
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


def create_bottom_bar(config, update_color_preset):
    with config.provide_as("config"):
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
                with v3.VCard(style="max-width: 360px;min-width: 360px;"):
                    with v3.VCardItem(classes="py-0 px-2"):
                        with html.Div(classes="d-flex align-center"):
                            v3.VIconBtn(
                                v_tooltip_bottom=(
                                    "config.color_blind ? 'Toggle for all color presets' : 'Toggle for colorblind safe color presets'",
                                ),
                                icon=(
                                    "config.color_blind ? 'mdi-shield-check-outline' : 'mdi-palette'",
                                ),
                                click="config.color_blind = !config.color_blind",
                                size="small",
                                text=(
                                    "config.color_blind ? 'Colorblind Safe' : 'All Colors'",
                                ),
                                variant="text",
                            )
                            v3.VIconBtn(
                                v_tooltip_bottom=(
                                    "config.invert ? 'Toggle to normal preset' : 'Toggle to inverted preset'",
                                ),
                                icon=(
                                    "config.invert ? 'mdi-invert-colors' : 'mdi-invert-colors-off'",
                                ),
                                click="config.invert = !config.invert",
                                size="small",
                                text=(
                                    "config.invert ? 'Inverted Preset' : 'Normal Preset'",
                                ),
                                variant="text",
                            )
                            v3.VIconBtn(
                                v_tooltip_bottom=(
                                    "config.use_log_scale === 'linear' ? 'Toggle to log scale' : config.use_log_scale === 'log' ? 'Toggle to symlog scale' : 'Toggle to linear scale'",
                                ),
                                icon=(
                                    "config.use_log_scale === 'log' ? 'mdi-math-log' : config.use_log_scale === 'symlog' ? 'mdi-sine-wave mdi-rotate-330' : 'mdi-stairs'",
                                ),
                                click="config.use_log_scale = config.use_log_scale === 'linear' ? 'log' : config.use_log_scale === 'log' ? 'symlog' : 'linear'",
                                size="small",
                                text=(
                                    "config.use_log_scale === 'log' ? 'Log' : config.use_log_scale === 'symlog' ? 'SymLog' : 'Linear'",
                                ),
                                variant="text",
                            )
                            v3.VIconBtn(
                                v_tooltip_bottom=(
                                    "config.override_range ? 'Toggle to use data range' : 'Toggle to use custom range'",
                                ),
                                icon=(
                                    "config.override_range ? 'mdi-arrow-expand-horizontal' : 'mdi-pencil'",
                                ),
                                click="config.override_range = !config.override_range",
                                size="small",
                                text=(
                                    "config.override_range ? 'Custom Range' : 'Data Range'",
                                ),
                                variant="text",
                            )
                            v3.VIconBtn(
                                v_show="config.use_log_scale === 'symlog'",
                                v_tooltip_bottom=(
                                    "config.discrete_log ? 'Switch to continuous colormap' : 'Switch to discrete colormap'",
                                ),
                                icon=(
                                    "config.discrete_log ? 'mdi-view-sequential' : 'mdi-gradient-horizontal'",
                                ),
                                click="config.discrete_log = !config.discrete_log",
                                size="small",
                                text=(
                                    "config.discrete_log ? 'Discrete' : 'Continuous'",
                                ),
                                variant="text",
                            )

                            v3.VTextField(
                                v_model="config.search",
                                clearable=True,
                                placeholder=("config.preset",),
                                click_clear="config.search = null",
                                single_line=True,
                                variant="solo",
                                density="compact",
                                flat=True,
                                hide_details="auto",
                                # style="min-width: 150px;",
                                classes="d-inline",
                                reverse=True,
                            )
                            v3.VIconBtn(
                                icon="mdi-close",
                                size="small",
                                text="Close",
                                click="config.menu=false",
                            )

                    with v3.VCardItem(classes="py-0 mb-2"):
                        v3.VNumberInput(
                            v_model="config.n_colors",
                            hide_details=True,
                            density="compact",
                            variant="outlined",
                            flat=True,
                            label="Number of colors",
                            classes="mt-2",
                            step=[1],
                            min=[2],
                            max=[255],
                        )
                    with v3.VCardItem(
                        v_show="config.override_range", classes="py-0 mb-2"
                    ):
                        v3.VTextField(
                            v_model="config.color_value_min",
                            hide_details=True,
                            density="compact",
                            variant="outlined",
                            flat=True,
                            label="Min",
                            classes="mt-2",
                            error=("!config.color_value_min_valid",),
                        )
                        v3.VTextField(
                            v_model="config.color_value_max",
                            hide_details=True,
                            density="compact",
                            variant="outlined",
                            flat=True,
                            label="Max",
                            classes="mt-2",
                            error=("!config.color_value_max_valid",),
                        )
                    v3.VDivider()
                    with v3.VList(density="compact", max_height="40vh"):
                        with v3.VListItem(
                            v_for="entry in (config.invert ? luts_inverted : luts_normal)",
                            v_show="(config.search?.length ? entry.name.toLowerCase().includes(config.search.toLowerCase()) : 1) && (!config.color_blind || entry.safe)",
                            key="entry.name",
                            subtitle=("entry.name",),
                            click=(
                                update_color_preset,
                                "[entry.name, config.invert, config.use_log_scale, config.discrete_log, config.n_colors]",
                            ),
                            active=("config.preset === entry.name",),
                        ):
                            html.Img(
                                src=("entry.url",),
                                style="width:100%;min-width:20rem;height:1rem;",
                                classes="rounded",
                            )
            html.Div(
                "{{ utils.quickview.formatRange(config.color_range?.[0], config.use_log_scale, config.color_range?.[0], config.color_range?.[1]) }}",
                classes="text-caption px-2 text-no-wrap",
            )
            with html.Div(
                classes="rounded w-100",
                style="height:70%;position:relative;",
            ):
                html.Img(
                    src=("config.lut_img",),
                    style="width:100%;height:2rem;",
                    draggable=False,
                )
                with html.Div(
                    style="position:absolute;top:0;left:0;right:0;bottom:0;pointer-events:none;",
                ):
                    with html.Div(
                        v_for="(tick, i) in config.color_ticks",
                        key="i",
                        style=(
                            "`position:absolute;left:${tick.position}%;top:0;height:100%;transform:translateX(-50%);display:flex;flex-direction:column;align-items:center;`",
                        ),
                    ):
                        html.Div(
                            style=(
                                "`width:1.5px;height:30%;background:${tick.color};`",
                            ),
                        )
                        html.Span(
                            "{{ tick.label }}",
                            style=(
                                "`font-size:0.5rem;line-height:1;white-space:nowrap;color:${tick.color};`",
                            ),
                        )
                        html.Div(
                            style=("`width:1.5px;flex:1;background:${tick.color};`",),
                        )
            html.Div(
                "{{ utils.quickview.formatRange(config.color_range?.[1], config.use_log_scale, config.color_range?.[0], config.color_range?.[1]) }}",
                classes="text-caption px-2 text-no-wrap",
            )

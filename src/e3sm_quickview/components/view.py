from trame.widgets import html, vuetify3 as v3


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
                    with v3.VCardItem(v_show="config.override_range", classes="py-0"):
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
                        # v3.VNumberInput(
                        #     model_value=("config.color_range[1]",),
                        #     update_modelValue="config.color_range = [config.color_range[0], Number($event)]",
                        #     hide_details=True,
                        #     density="compact",
                        #     variant="outlined",
                        #     flat=True,
                        #     label="Max",
                        #     classes="mt-2",
                        #     control_variant="hidden",
                        #     precision=("15",),
                        #     step=(
                        #         "Math.max(0.0001, (config.color_range[1] - config.color_range[0]) / 255)",
                        #     ),
                        # )
                    v3.VDivider(classes="mt-2")
                    with v3.VList(density="compact", max_height="40vh"):
                        with v3.VListItem(
                            v_for="url, name in (config.invert ? luts_inverted : luts_normal)",
                            v_show="!config.color_blind || safe_color[name]",
                            key="name",
                            subtitle=("name",),
                            click=(
                                update_color_preset,
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
            with html.Div(classes="overflow-hidden rounded w-100", style="height:70%;"):
                html.Img(
                    src=("config.preset_img",),
                    style="width:100%;height:2rem;",
                    draggable=False,
                )
            html.Div(
                "{{ utils.quickview.formatRange(config.color_range?.[1], config.use_log_scale) }}",
                classes="text-caption px-2 text-no-wrap",
            )

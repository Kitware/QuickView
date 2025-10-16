from trame.widgets import vuetify2 as v2, html
from trame.decorators import TrameApp


@TrameApp()
class ViewProperties(v2.VMenu):
    def __init__(
        self,
        update_colormap=None,
        update_log_scale=None,
        update_invert=None,
        update_range=None,
        reset=None,
        **kwargs,
    ):
        super().__init__(
            transition="slide-y-transition",
            close_on_content_click=False,
            persistent=True,
            no_click_animation=True,
            offset_y=True,
            **kwargs,
        )
        with self:
            with v2.Template(v_slot_activator="{ on, attrs }"):
                with v2.VBtn(
                    icon=True,
                    dense=True,
                    small=True,
                    outlined=True,
                    classes="pa-0",
                    style="background: white; width: 24px; height: 24px;",
                    v_bind="attrs",
                    v_on="on",
                ):
                    v2.VIcon("mdi-cog", small=True)
            style = dict(dense=True, hide_details=True)
            with v2.VCard(
                classes="overflow-hidden pa-2",
                rounded="lg",
            ):
                with v2.VCardText(classes="pa-2"):
                    v2.VSelect(
                        label="Color Map",
                        v_model=("varcolor[idx]",),
                        items=("colormaps",),
                        outlined=True,
                        change=(
                            update_colormap,
                            "[idx, $event]",
                        ),
                        **style,
                    )
                    html.Div("Color Map Options", classes="pt-2")
                    with v2.VRow():
                        with v2.VCol():
                            v2.VCheckbox(
                                label="Log Scale",
                                v_model=("uselogscale[idx]",),
                                change=(
                                    update_log_scale,
                                    "[idx, $event]",
                                ),
                                **style,
                            )
                        with v2.VCol():
                            v2.VCheckbox(
                                label="Revert Colors",
                                v_model=("invert[idx]",),
                                change=(
                                    update_invert,
                                    "[idx, $event]",
                                ),
                                **style,
                            )
                    with html.Div(classes="pt-2 d-flex align-center"):
                        html.Span("Value Range", classes="mr-2")
                        with v2.VChip(
                            v_if=("override_range[idx]",),
                            x_small=True,
                            color="primary",
                            dark=True,
                            classes="ml-auto",
                        ):
                            v2.VIcon("mdi-lock", x_small=True, left=True)
                            html.Span("Manual")
                    with v2.VRow():
                        with v2.VCol():
                            v2.VTextField(
                                v_model=("varmin[idx]",),
                                label="min",
                                outlined=True,
                                change=(
                                    update_range,
                                    "[idx, 'min', $event]",
                                ),
                                style="height=50px",
                                color=("override_range[idx] ? 'primary' : ''",),
                                **style,
                            )
                        with v2.VCol():
                            v2.VTextField(
                                v_model=("varmax[idx]",),
                                label="max",
                                outlined=True,
                                change=(
                                    update_range,
                                    "[idx, 'max', $event]",
                                ),
                                style="height=50px",
                                color=("override_range[idx] ? 'primary' : ''",),
                                **style,
                            )
                    with html.Div(classes="pt-2 align-center text-center"):
                        v2.VBtn(
                            "Reset Colors to Data Range",
                            outlined=True,
                            style="background-color: gray; color: white;",
                            click=(
                                reset,
                                "[idx]",
                            ),
                        )


@TrameApp()
class ViewControls(v2.VCard):
    def __init__(self, zoom=None, move=None, **kwargs):
        # Merge any incoming style with our default style
        default_style = "background-color: #f5f5f5; border-radius: 4px;"
        incoming_style = kwargs.pop("style", "")
        merged_style = f"{default_style} {incoming_style}".strip()

        super().__init__(
            flat=True,
            classes="d-flex align-center px-2 py-1 mx-1",
            style=merged_style,
            **kwargs,
        )
        with self:
            """
            with v2.Template(v_slot_activator="{ on, attrs }"):
                with v2.VBtn(
                    icon=True,
                    outlined=True,
                    classes="pa-1",
                    style="background: white;",
                    v_bind="attrs",
                    v_on="on",
                ):
                    v2.VIcon("mdi-camera")
            style = dict(dense=True, hide_details=True)
            """
            btn_style = dict(
                icon=True,
                flat=True,
                outlined=False,
                density="compact",
                hide_details=True,
                height="28px",
                width="28px",
                classes="ma-0",
            )

            with v2.VCardText(classes="pa-1", style="opacity: 85%"):
                with v2.VTooltip(bottom=True):
                    with html.Template(v_slot_activator="{ on, attrs }"):
                        with html.Div(
                            v_bind="attrs",
                            v_on="on",
                            classes="d-flex flex-column",
                            style="gap: 2px;",
                        ):
                            # First row: Up, Left, Zoom In
                            with html.Div(
                                classes="d-flex justify-center", style="gap: 2px;"
                            ):
                                with v2.VBtn(
                                    **btn_style,
                                    click=(move, "['up']"),
                                ):
                                    v2.VIcon("mdi-arrow-up-thick", size="18")
                                with v2.VBtn(
                                    **btn_style,
                                    click=(move, "['left']"),
                                ):
                                    v2.VIcon("mdi-arrow-left-thick", size="18")
                                with v2.VBtn(
                                    **btn_style,
                                    click=(zoom, "['in']"),
                                ):
                                    v2.VIcon("mdi-magnify-plus", size="18")

                            # Second row: Down, Right, Zoom Out
                            with html.Div(
                                classes="d-flex justify-center", style="gap: 2px;"
                            ):
                                with v2.VBtn(
                                    **btn_style,
                                    click=(move, "['down']"),
                                ):
                                    v2.VIcon("mdi-arrow-down-thick", size="18")
                                with v2.VBtn(
                                    **btn_style,
                                    click=(move, "['right']"),
                                ):
                                    v2.VIcon("mdi-arrow-right-thick", size="18")
                                with v2.VBtn(
                                    **btn_style,
                                    click=(zoom, "['out']"),
                                ):
                                    v2.VIcon("mdi-magnify-minus", size="18")
                    html.Span("View Camera Controls", classes="text-caption mt-1")

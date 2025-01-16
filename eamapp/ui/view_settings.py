from trame.widgets import vuetify2 as v2, html
from trame.decorators import TrameApp


@TrameApp()
class ViewController(v2.VCardActions):
    def __init__(self, apply=None, update=None, reset=None, zoom=None, move=None):
        super().__init__()
        with self:
            with v2.VMenu(
                transition="slide-y-transition",
                close_on_content_click=False,
                persistent=True,
                no_click_animation=True,
            ):
                with v2.Template(v_slot_activator="{ on, attrs }"):
                    v2.VBtn(
                        "View Settings",
                        color="primary",
                        v_bind="attrs",
                        v_on="on",
                        style="z-index:2",
                    )
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
                                apply,
                                "[idx, 'color', $event]",
                            ),
                            **style,
                        )
                        html.Div("Mapping Options", classes="pt-2")
                        with v2.VRow():
                            with v2.VCol():
                                v2.VCheckbox(
                                    label="Log Scale",
                                    v_model=("uselogscale[idx]",),
                                    change=(
                                        apply,
                                        "[idx, 'log', $event]",
                                    ),
                                    **style,
                                )
                            with v2.VCol():
                                v2.VCheckbox(
                                    label="Invert Colors",
                                    v_model=("invert[idx]",),
                                    change=(
                                        apply,
                                        "[idx, 'inv', $event]",
                                    ),
                                    **style,
                                )
                        html.Div("Scalar Range", classes="pt-2")
                        with v2.VRow():
                            with v2.VCol():
                                v2.VTextField(
                                    v_model=("varmin[idx]",),
                                    label="min",
                                    outlined=True,
                                    change=(
                                        update,
                                        "[idx, 'min', $event]",
                                    ),
                                    style="height=50px",
                                    **style,
                                )
                            with v2.VCol():
                                v2.VTextField(
                                    v_model=("varmax[idx]",),
                                    label="max",
                                    outlined=True,
                                    change=(
                                        update,
                                        "[idx, 'max', $event]",
                                    ),
                                    style="height=50px",
                                    **style,
                                )
                        with html.Div(classes="pt-2 align-center text-center"):
                            v2.VBtn(
                                "Reset Colors to Range",
                                outlined=True,
                                style="background-color: gray; color: white;",
                                click=(
                                    reset,
                                    "[idx]",
                                ),
                            )

        with v2.VBtn(
            icon=True,
            outlined=True,
            style="height: 20px; width: 20px",
            click=(zoom, "['in', idx]"),
        ):
            v2.VIcon("mdi-plus")
        with v2.VBtn(
            icon=True,
            outlined=True,
            style="height: 20px; width: 20px",
            click=(zoom, "['out', idx]"),
        ):
            v2.VIcon("mdi-minus")
        with v2.VBtn(
            icon=True,
            outlined=True,
            style="height: 20px; width: 20px",
            click=(move, "['up', idx]"),
        ):
            v2.VIcon("mdi-arrow-up")
        with v2.VBtn(
            icon=True,
            outlined=True,
            style="height: 20px; width: 20px",
            click=(move, "['down', idx]"),
        ):
            v2.VIcon("mdi-arrow-down")
        with v2.VBtn(
            icon=True,
            outlined=True,
            style="height: 20px; width: 20px",
            click=(move, "['left', idx]"),
        ):
            v2.VIcon("mdi-arrow-left")
        with v2.VBtn(
            icon=True,
            outlined=True,
            classes="pa-1",
            style="height: 20px; width: 20px",
            click=(move, "['right', idx]"),
        ):
            v2.VIcon("mdi-arrow-right")

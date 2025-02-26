from trame.decorators import TrameApp, change
from trame.widgets import html, vuetify2 as v2

from eamapp.ui.collapsible import CollapsableSection


@TrameApp()
class ProjectionSelection(CollapsableSection):
    def __init__(self, source):
        super().__init__("Map Projection Properties", "show_projection")

        style = dict(dense=True, hide_details=True)
        self.state.center = 0.0
        with self.content:
            with v2.VRow(classes="text-center align-center"):
                with v2.VCol(**style):
                    html.Span("Projection", **style)
                with v2.VCol(**style):
                    v2.VSelect(
                        items=(
                            "options",
                            ["Cyl. Equidistant", "Robinson", "Mollweide"],
                        ),
                        v_model=("projection", "Cyl. Equidistant"),
                        **style,
                        solo=True,
                        flat=True,
                    )
            # v2.VDivider()
            # with v2.VRow(classes="text-center align-center pa-2"):
            #    with v2.VCol(**style):
            #        html.Span("Center at", **style)
            #    with v2.VCol(**style):
            #        v2.VTextField(v_model=("center", 0.0), **style, classes="py-0")

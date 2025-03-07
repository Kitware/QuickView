from trame.decorators import TrameApp, change
from trame.widgets import html, vuetify2 as v2

from eamapp.ui.collapsible import CollapsableSection

from eamapp.view_manager import ViewManager
from eamapp.pipeline import EAMVisSource


@TrameApp()
class ProjectionSelection(CollapsableSection):
    def __init__(self, source: EAMVisSource, view_manager: ViewManager):
        super().__init__("Map Projection Properties", "show_projection")

        self.source = source
        self.views = view_manager

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

    @change("projection")
    def update_pipeline_interactive(self, **kwargs):
        projection = self.state.projection
        self.source.UpdateProjection(projection)
        self.source.UpdatePipeline()
        self.views.step_update_existing_views()
        self.views.reset_views()

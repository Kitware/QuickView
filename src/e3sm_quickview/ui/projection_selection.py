from trame.decorators import TrameApp, change
from trame.widgets import html, vuetify2 as v2

from e3sm_quickview.ui.collapsible import CollapsableSection

from e3sm_quickview.view_manager import ViewManager
from e3sm_quickview.pipeline import EAMVisSource


@TrameApp()
class ProjectionSelection(CollapsableSection):
    def __init__(self, source: EAMVisSource, view_manager: ViewManager):
        super().__init__("Map Projection", "show_projection")

        self.source = source
        self.views = view_manager

        self.state.center = 0.0

        with self.content:
            with v2.VCard(flat=True, elevation=0, classes="pa-2"):
                with v2.VRow(classes="align-center", no_gutters=True):
                    with v2.VCol(cols=4, classes="text-right pr-3"):
                        html.Div(
                            "Projection:",
                            classes="text-body-2 font-weight-medium",
                            style="color: #616161;",
                        )
                    with v2.VCol(cols=8):
                        v2.VSelect(
                            items=(
                                "options",
                                ["Cyl. Equidistant", "Robinson", "Mollweide"],
                            ),
                            v_model=("projection", "Cyl. Equidistant"),
                            outlined=True,
                            dense=True,
                            hide_details=True,
                            color="primary",
                            classes="elevation-0",
                        )

    @change("projection")
    def update_pipeline_interactive(self, **kwargs):
        projection = self.state.projection
        self.source.UpdateProjection(projection)
        tstamp = self.state.tstamp
        time = 0.0 if len(self.state.timesteps) == 0 else self.state.timesteps[tstamp]
        self.source.UpdatePipeline(time)
        # For projection changes, we need to fit viewports to new bounds
        self.views.update_views_for_timestep()
        # Render once after all updates
        self.views.render_all_views()

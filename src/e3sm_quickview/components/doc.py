from trame.widgets import vuetify3 as v3, html
from e3sm_quickview.assets import ASSETS


# -----------------------------------------------------------------------------
# Tools
# -----------------------------------------------------------------------------


class Tool(v3.VListItem):
    def __init__(self, icon, title, description):
        super().__init__(classes="px-0")
        with self:
            with v3.VListItemTitle():
                with html.P(classes="text-body-2 font-weight-bold pb-2") as p:
                    v3.VIcon(classes="mr-2", size="small", icon=icon)
                    p.add_child(title)
            with v3.VListItemSubtitle():
                html.P(description, classes="ps-7")


class ToolFileLoading(Tool):
    def __init__(self):
        super().__init__(
            icon="mdi-file-document-outline",
            title="File loading",
            description="Load files to explore. Those could be simulation and connectivity files or even a state file pointing to those files.",
        )


class ToolFieldSelection(Tool):
    def __init__(self):
        super().__init__(
            icon="mdi-list-status",
            title="Fields selection",
            description="""
                Select the variables to visualize. You need to load files prior any field selection.
            """,
        )


class ToolResetCamera(Tool):
    def __init__(self):
        super().__init__(
            icon="mdi-crop-free",
            title="Reset camera",
            description="Recenter the visualizations to the full data.",
        )


class ToolStateImportExport(Tool):
    def __init__(self):
        super().__init__(
            icon="mdi-folder-arrow-left-right-outline",
            title="State import/export",
            description="Export the application state into a small text file. The same file can then be imported to restore that application state.",
        )


class ToolMapProjection(Tool):
    def __init__(self):
        super().__init__(
            icon="mdi-earth",
            title="Map Projection",
            description="Select projection to use for the visualizations. (Cylindrical Equidistant, Robinson, Mollweide)",
        )


class ToolLayoutManagement(Tool):
    def __init__(self):
        super().__init__(
            icon="mdi-collage",
            title="Layout management",
            description="Toggle layout toolbar for adjusting aspect-ratio, width and grouping options.",
        )


class ToolCropping(Tool):
    def __init__(self):
        super().__init__(
            icon="mdi-crop",
            title="Lat/Long cropping",
            description="Toggle cropping toolbar for adjusting spacial bounds.",
        )


class ToolDataSelection(Tool):
    def __init__(self):
        super().__init__(
            icon="mdi-tune-variant",
            title="Slice selection",
            description="Toggle data selection toolbar for selecting a given layer, midpoint or time.",
        )


class ToolAnimation(Tool):
    def __init__(self):
        super().__init__(
            icon="mdi-movie-open-cog-outline",
            title="Animation controls",
            description="Toggle animation toolbar.",
        )


# -----------------------------------------------------------------------------
# Utils
# -----------------------------------------------------------------------------


class Title(html.P):
    def __init__(self, content=None):
        super().__init__(
            content, classes="mt-6 mb-4 text-h6 font-weight-bold text-medium-emphasis"
        )


class Paragraph(html.P):
    def __init__(self, content):
        super().__init__(content, classes="mt-4 mb-6 text-body-1")


# -----------------------------------------------------------------------------


class LandingPage(v3.VContainer):
    def __init__(self):
        super().__init__(classes="pa-6 pa-md-12")

        with self:
            with html.P(
                classes="mt-2 text-h5 font-weight-bold text-sm-h4 text-medium-emphasis"
            ):
                html.A(
                    "QuickView",
                    classes="text-primary text-decoration-none",
                    href="https://quickview.readthedocs.io/en/latest/",
                    target="_blank",
                )

            Paragraph("""
                <b class="text-medium-emphasis">EAM QuickView</b> is an open-source, interactive visualization
                tool designed for scientists working with the atmospheric component
                of the <a class="text-primary text-decoration-none" href="https://e3sm.org/" target="_blank">Energy Exascale Earth System Model (E3SM)</a>,
                known as the E3SM Atmosphere Model (EAM). 
                Its Python- and <a class="text-primary text-decoration-none" href="https://www.kitware.com/trame/" target="_blank">Trame</a>-based
                Graphical User Interface (GUI) provides intuitive access to <a class="text-primary text-decoration-none" href="https://www.paraview.org/" target="_blank">ParaView's</a> powerful analysis
                and visualization capabilities, without the steep learning curve.
            """)

            v3.VImg(
                classes="rounded-lg",
                src=ASSETS.banner,
            )

            Title("Getting started")

            with v3.VRow():
                with v3.VCol(cols=6):
                    ToolFileLoading()
                    ToolFieldSelection()
                    ToolMapProjection()
                    ToolResetCamera()

                with v3.VCol(cols=6):
                    ToolLayoutManagement()
                    ToolCropping()
                    ToolDataSelection()
                    ToolAnimation()
                    ToolStateImportExport()

            Title("Simulation Files")

            Paragraph(
                """
                QuickView has been developed using EAM's history output on
                the physics grids (pg2 grids) written by EAMv2, v3, and an
                intermediate version towards v4 (EAMxx). 
                Those sample output files can be found on Zenodo.
                """
            )
            Paragraph(
                """
                Developers and users of EAM often use tools like NCO and CDO
                or write their own scripts to calculate time averages and/or
                select a subset of variables from the original model output.
                For those use cases, we clarify below the features of the data
                format that QuickView expects in order to properly read and
                visualize the simulation data.
                """
            )

            Title("Connectivity Files")

            Paragraph(
                """
                The horizontal grids used by EAM are cubed spheres.
                Since these are unstructed grids, QuickView needs
                to know how to map data to the globe. Therefore,
                for each simulation data file, a "connectivity file"
                needs to be provided.
                """
            )

            Paragraph(
                """
                In EAMv2, v3, and v4, most of the variables
                (physical quantities) are written out on a
                "physics grid" (also referred to as "physgrid",
                "FV grid", or "control volume mesh") described
                in Hannah et al. (2021). The naming convention
                for such grids is ne*pg2, with * being a number,
                e.g., 4, 30, 120, 256. Further details about EAM's
                cubed-sphere grids can be found in EAM's documention,
                for example in this overview and this description.
                """
            )
            Paragraph(
                """
                Future versions of QuickView will also support the
                cubed-sphere meshes used by EAM's dynamical core,
                i.e., the ne*np4 grids (also referred to as
                "native grids" or "GLL grids").
                """
            )

            Title("Project Background")

            Paragraph(
                """
                The lead developer of EAM QuickView is Abhishek Yenpure (abhi.yenpure@kitware.com)
                at Kitware, Inc.. Other key contributors at Kitware, Inc. include Berk Geveci and
                Sebastien Jourdain. Key contributors on the atmospheric science side are Hui Wan
                and Kai Zhang at Pacific Northwest National Laboratory.
                """
            )

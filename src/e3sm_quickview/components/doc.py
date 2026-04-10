from trame.widgets import html
from trame.widgets import vuetify3 as v3

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
            icon="mdi-file-upload-outline",
            title="File loading",
            description="Load files to explore. Those could be simulation and connectivity files or even a state file pointing to those files.",
        )
        with self, v3.Template(v_slot_append=True):
            v3.VHotkey(keys="f", variant="contained", inline=True)


class ToolFieldSelection(Tool):
    def __init__(self):
        super().__init__(
            icon="mdi-list-status",
            title="Variable selection",
            description="""
                Select the variables to visualize. You need to load files prior any variable selection.
            """,
        )
        with self, v3.Template(v_slot_append=True):
            v3.VHotkey(keys="v", variant="contained", inline=True)


class ToolResetCamera(Tool):
    def __init__(self):
        super().__init__(
            icon="mdi-fit-to-page-outline",
            title="Auto zoom",
            description="Recenter the visualizations to the full data.",
        )
        with self, v3.Template(v_slot_append=True):
            v3.VHotkey(keys="z", variant="contained", inline=True)


class ToolStateImportExport(Tool):
    def __init__(self):
        super().__init__(
            icon="mdi-folder-arrow-left-right-outline",
            title="State import/export",
            description="Export the application state into a small text file. The same file can then be imported to restore that application state.",
        )
        with self, v3.Template(v_slot_append=True):
            v3.VHotkey(keys="d", variant="contained", inline=True)
            v3.VHotkey(keys="u", variant="contained", inline=True)


class ToolMapProjection(Tool):
    def __init__(self):
        super().__init__(
            icon="mdi-earth",
            title="Map Projection",
            description="Select projection to use for the visualizations. (Cylindrical Equidistant, Robinson, Mollweide)",
        )
        with self, v3.Template(v_slot_append=True):
            v3.VHotkey(keys="c", variant="contained", inline=True)
            v3.VHotkey(keys="r", variant="contained", inline=True)
            v3.VHotkey(keys="m", variant="contained", inline=True)


class ToolLayoutManagement(Tool):
    def __init__(self):
        super().__init__(
            icon="mdi-view-module",
            title="Viewport layout",
            description="Toggle viewport layout toolbar for adjusting aspect-ratio, width and grouping options.",
        )
        with self, v3.Template(v_slot_append=True):
            v3.VHotkey(keys="p", variant="contained", inline=True)


class ToolCropping(Tool):
    def __init__(self):
        super().__init__(
            icon="mdi-web",
            title="Lat/Lon cropping",
            description="Toggle cropping toolbar for adjusting spacial bounds.",
        )
        with self, v3.Template(v_slot_append=True):
            v3.VHotkey(keys="l", variant="contained", inline=True)


class ToolDataSelection(Tool):
    def __init__(self):
        super().__init__(
            icon="mdi-tune-variant",
            title="Slice selection",
            description="Toggle data selection toolbar for selecting a given layer, midpoint or time.",
        )
        with self, v3.Template(v_slot_append=True):
            v3.VHotkey(keys="s", variant="contained", inline=True)


class ToolAnimation(Tool):
    def __init__(self):
        super().__init__(
            icon="mdi-video",
            title="Animation controls",
            description="Toggle animation toolbar.",
        )
        with self, v3.Template(v_slot_append=True):
            v3.VHotkey(keys="a", variant="contained", inline=True)


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


class Link(html.A):
    def __init__(self, text, url):
        super().__init__(
            text,
            classes="text-primary text-decoration-none",
            href=url,
            target="_blank",
            connect_parent=False,
        )

    def __str__(self):
        return self.html


class Bold(html.B):
    def __init__(self, text):
        super().__init__(text, classes="text-medium-emphasis", connect_parent=False)

    def __str__(self):
        return self.html


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
                    href="https://kitware.github.io/QuickView/guides/quickview/",
                    target="_blank",
                )

            Paragraph(f"""
                {Bold("QuickView")} is an open-source, interactive visualization
                tool designed to help Earth system modelers take a quick look at
                a collection of physical quantities in their simulation files.
                The physical quantities are presented in the form of global or regional maps.
                Currently, QuickView supports only the cubed-sphere "physics" grids,
                i.e., the ne*pg2 meshes used by the atmosphere component of the
                {Link("Energy Exascale Earth System Model (E3SM)","https://e3sm.org/")},
                but extensions to other grids are underway. 
                QuickView's Python and {Link("trame", "https://www.kitware.com/trame/")}-based
                graphical User Interface (UI) provides the users with intuitive access to
                {Link("ParaView", "https://www.paraview.org/")}'s powerful analysis
                and visualization capabilities without requiring a steep learning curve.
                A detailed {Bold("User's Guide")} can be found through
                {Link("this link","https://kitware.github.io/QuickView/guides/quickview/")}.
                {Bold("Bug reports")} and feature requests can be submitted on
                {Link("GitHub","https://github.com/Kitware/QuickView/issues")}.
            """)

#           v3.VImg(
#               classes="rounded-lg",
#               src=ASSETS.banner,
#           )


            Title("Toolbar Icons")

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

            Title("Keyboard Shortcuts")

            with v3.VRow():
                with v3.VCol(cols=6):
                    with v3.VRow(classes="ma-0 pb-4"):
                        v3.VLabel("Toggle help")
                        v3.VSpacer()
                        v3.VHotkey(keys="h", variant="contained", inline=True)

                    with v3.VRow(classes="ma-0 pb-4"):
                        v3.VLabel("Auto zoom")
                        v3.VSpacer()
                        v3.VHotkey(keys="z", variant="contained", inline=True)

                    with v3.VRow(classes="ma-0 pb-4"):
                        v3.VLabel("Toggle view interaction lock")
                        v3.VSpacer()
                        v3.VHotkey(keys="space", variant="contained", inline=True)

                    v3.VDivider(classes="mb-4")

                    with v3.VRow(classes="ma-0 pb-4"):
                        v3.VLabel("File Open")
                        v3.VSpacer(classes="mt-2")
                        v3.VHotkey(keys="f", variant="contained", inline=True)

                    with v3.VRow(classes="ma-0 pb-4"):
                        v3.VLabel("Download state")
                        v3.VSpacer(classes="mt-2")
                        v3.VHotkey(keys="d", variant="contained", inline=True)

                    with v3.VRow(classes="ma-0 pb-4"):
                        v3.VLabel("Upload state")
                        v3.VSpacer(classes="mt-2")
                        v3.VHotkey(keys="u", variant="contained", inline=True)

                    v3.VDivider(classes="mb-4")

                    with v3.VRow(classes="ma-0 pb-4"):
                        v3.VLabel("Toggle viewport layout toolbar")
                        v3.VSpacer(classes="mt-2")
                        v3.VHotkey(keys="p", variant="contained", inline=True)
                    with v3.VRow(classes="ma-0 pb-4"):
                        v3.VLabel("Toggle Lat/Lon cropping toolbar")
                        v3.VSpacer()
                        v3.VHotkey(keys="l", variant="contained", inline=True)
                    with v3.VRow(classes="ma-0 pb-4"):
                        v3.VLabel("Toggle Slice selection toolbar")
                        v3.VSpacer()
                        v3.VHotkey(keys="s", variant="contained", inline=True)
                    with v3.VRow(classes="ma-0 pb-4"):
                        v3.VLabel("Toggle Animation controls toolbar")
                        v3.VSpacer()
                        v3.VHotkey(keys="a", variant="contained", inline=True)

                    v3.VDivider(classes="mb-4")

                    with v3.VRow(classes="ma-0 pb-4"):
                        v3.VLabel("Toggle group layout")
                        v3.VSpacer()
                        v3.VHotkey(keys="g", variant="contained", inline=True)

                    with v3.VRow(classes="ma-0 pb-4"):
                        v3.VLabel("Toggle variable selection drawer")
                        v3.VSpacer()
                        v3.VHotkey(keys="v", variant="contained", inline=True)

                    v3.VDivider(classes="mb-4")

                    with v3.VRow(classes="ma-0 pb-4"):
                        v3.VLabel("Disable all toolbars and drawers")
                        v3.VSpacer()
                        v3.VHotkey(keys="esc", variant="contained", inline=True)

                with v3.VCol(cols=6):
                    with v3.VRow(classes="ma-0 pb-2"):
                        v3.VLabel("Projections")

                    with v3.VList(density="compact", classes="pa-0 ma-0"):
                        with v3.VListItem(subtitle="Cylindrical Equidistant"):
                            with v3.Template(v_slot_append="True"):
                                v3.VHotkey(keys="c", variant="contained", inline=True)
                        with v3.VListItem(subtitle="Robinson"):
                            with v3.Template(v_slot_append="True"):
                                v3.VHotkey(keys="r", variant="contained", inline=True)
                        with v3.VListItem(subtitle="Mollweide"):
                            with v3.Template(v_slot_append="True"):
                                v3.VHotkey(keys="m", variant="contained", inline=True)

                    v3.VDivider(classes="my-4")

                    with v3.VRow(classes="ma-0 pb-2"):
                        v3.VLabel("Apply size")

                    with v3.VList(density="compact", classes="pa-0 ma-0"):
                        with v3.VListItem(subtitle="Auto flow"):
                            with v3.Template(v_slot_append="True"):
                                v3.VHotkey(keys="=", variant="contained", inline=True)
                        with v3.VListItem(subtitle="Auto"):
                            with v3.Template(v_slot_append="True"):
                                v3.VHotkey(keys="0", variant="contained", inline=True)
                        with v3.VListItem(subtitle="1 column"):
                            with v3.Template(v_slot_append="True"):
                                v3.VHotkey(keys="1", variant="contained", inline=True)
                        with v3.VListItem(subtitle="2 columns"):
                            with v3.Template(v_slot_append="True"):
                                v3.VHotkey(keys="2", variant="contained", inline=True)
                        with v3.VListItem(subtitle="3 columns"):
                            with v3.Template(v_slot_append="True"):
                                v3.VHotkey(keys="3", variant="contained", inline=True)
                        with v3.VListItem(subtitle="4 columns"):
                            with v3.Template(v_slot_append="True"):
                                v3.VHotkey(keys="4", variant="contained", inline=True)
                        with v3.VListItem(subtitle="6 columns"):
                            with v3.Template(v_slot_append="True"):
                                v3.VHotkey(keys="6", variant="contained", inline=True)

            Title("Project Background")

            Paragraph(f"""
                QuickView was collaboratively developed by
                {Link("Kitware", "https://www.kitware.com")} and
                {Link("Pacific Northwest National Laboratory", "https://www.pnnl.gov/")}
                using funding from the U.S. Department of Energy's SciDAC program
                through a partnership between
                the {Link("Advanced Scientific Computing Reaserch (ASCR)",
                "https://www.energy.gov/science/ascr/advanced-scientific-computing-research")} program and
                the {Link("Biological and Environmental Research (BER)",
                "https://www.energy.gov/science/ber/biological-and-environmental-research")} program.
            """
            )

            Paragraph(f"""
                The development of QuickView used resources of the
                {Link("National Energy Research Scientific Computing Center (NERSC)","https://www.nersc.gov/")},
                a U.S. Department of Energy User Facility.
            """
            )

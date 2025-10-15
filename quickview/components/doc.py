from trame.widgets import vuetify3 as v3, html
from quickview.assets import ASSETS


class LandingPage(v3.VContainer):
    def __init__(self):
        super().__init__(classes="pa-6 pa-md-12")

        with self:
            with html.P(
                classes="mt-2 text-h5 font-weight-bold text-sm-h4 text-medium-emphasis",
            ):
                html.A(
                    "QuickView",
                    classes="text-primary text-decoration-none",
                    href="https://quickview.readthedocs.io/en/latest/",
                    target="_blank",
                )

            with html.P(classes="mt-4 mb-6 text-body-1") as p:
                p.add_child(
                    """
                    <b class="text-medium-emphasis">EAM QuickView</b> is an open-source, interactive visualization
                    tool designed for scientists working with the atmospheric component
                    of the <a class="text-primary text-decoration-none" href="https://e3sm.org/" target="_blank">Energy Exascale Earth System Model (E3SM)</a>,
                    known as the E3SM Atmosphere Model (EAM). 
                    Its Python- and <a class="text-primary text-decoration-none" href="https://www.kitware.com/trame/" target="_blank">Trame</a>-based
                    Graphical User Interface (GUI) provides intuitive access to <a class="text-primary text-decoration-none" href="https://www.paraview.org/" target="_blank">ParaView's</a> powerful analysis
                    and visualization capabilities, without the steep learning curve.
                    """
                )

            v3.VImg(
                classes="rounded-lg",
                src=ASSETS.banner,
            )

            html.P(
                "Getting started",
                classes="mt-6 mb-4 text-h6 font-weight-bold text-medium-emphasis",
            )

            with v3.VRow():
                with v3.VCol(cols=6):
                    with v3.VListItem(classes="px-0"):
                        with v3.VListItemTitle():
                            with html.P(
                                classes="text-body-2 font-weight-bold pb-2"
                            ) as p:
                                v3.VIcon(
                                    classes="mr-2",
                                    size="small",
                                    icon="mdi-file-document-outline",
                                )
                                p.add_child("File loading")
                        with v3.VListItemSubtitle():
                            with html.P(classes="ps-7") as p:
                                p.add_child(
                                    """
                                    Load files to explore. Those could be simulation and connectivity files or even a state file pointing to those files.
                                    """
                                )

                    with v3.VListItem(classes="px-0"):
                        with v3.VListItemTitle():
                            with html.P(
                                classes="text-body-2 font-weight-bold pb-2"
                            ) as p:
                                v3.VIcon(
                                    classes="mr-2", size="small", icon="mdi-list-status"
                                )
                                p.add_child("Fields selection")
                        with v3.VListItemSubtitle():
                            with html.P(classes="ps-7") as p:
                                p.add_child(
                                    """
                                    Select the variables to visualize. You need to load files prior any field selection.
                                    """
                                )

                    with v3.VListItem(classes="px-0"):
                        with v3.VListItemTitle():
                            with html.P(
                                classes="text-body-2 font-weight-bold pb-2"
                            ) as p:
                                v3.VIcon(
                                    classes="mr-2", size="small", icon="mdi-crop-free"
                                )
                                p.add_child("Reset camera")
                        with v3.VListItemSubtitle():
                            with html.P(classes="ps-7") as p:
                                p.add_child(
                                    """
                                    Recenter the visualizations to the full data.
                                    """
                                )

                    with v3.VListItem(classes="px-0"):
                        with v3.VListItemTitle():
                            with html.P(
                                classes="text-body-2 font-weight-bold pb-2"
                            ) as p:
                                v3.VIcon(
                                    classes="mr-2",
                                    size="small",
                                    icon="mdi-folder-arrow-left-right-outline",
                                )
                                p.add_child("State import/export")
                        with v3.VListItemSubtitle():
                            with html.P(classes="ps-7") as p:
                                p.add_child(
                                    """
                                    Export the application state into a small text file. The same file can then be imported to restore that application state.
                                    """
                                )

                    with v3.VListItem(classes="px-0"):
                        with v3.VListItemTitle():
                            with html.P(
                                classes="text-body-2 font-weight-bold pb-2"
                            ) as p:
                                v3.VIcon(
                                    classes="mr-2", size="small", icon="mdi-lifebuoy"
                                )
                                p.add_child("Toggle Help")
                        with v3.VListItemSubtitle():
                            with html.P(classes="ps-7") as p:
                                p.add_child(
                                    """
                                    Toggle side bar width to show/hide action title.
                                    """
                                )

                with v3.VCol(cols=6):
                    with v3.VListItem(classes="px-0"):
                        with v3.VListItemTitle():
                            with html.P(
                                classes="text-body-2 font-weight-bold pb-2"
                            ) as p:
                                v3.VIcon(classes="mr-2", size="small", icon="mdi-earth")
                                p.add_child("Map Projection")
                        with v3.VListItemSubtitle():
                            with html.P(classes="ps-7") as p:
                                p.add_child(
                                    """
                                    Select projection to use for the visualizations. (Cylindrical Equidistant, Robinson, Mollweide)
                                    """
                                )

                    with v3.VListItem(classes="px-0"):
                        with v3.VListItemTitle():
                            with html.P(
                                classes="text-body-2 font-weight-bold pb-2"
                            ) as p:
                                v3.VIcon(
                                    classes="mr-2", size="small", icon="mdi-collage"
                                )
                                p.add_child("Layout management")
                        with v3.VListItemSubtitle():
                            with html.P(classes="ps-7") as p:
                                p.add_child(
                                    """
                                    Toggle layout toolbar for adjusting aspect-ratio, width and grouping options.
                                    """
                                )

                    with v3.VListItem(classes="px-0"):
                        with v3.VListItemTitle():
                            with html.P(
                                classes="text-body-2 font-weight-bold pb-2"
                            ) as p:
                                v3.VIcon(classes="mr-2", size="small", icon="mdi-crop")
                                p.add_child("Lat/Long cropping")
                        with v3.VListItemSubtitle():
                            with html.P(classes="ps-7") as p:
                                p.add_child(
                                    """
                                    Toggle cropping toolbar for adjusting spacial bounds.
                                    """
                                )

                    with v3.VListItem(classes="px-0"):
                        with v3.VListItemTitle():
                            with html.P(
                                classes="text-body-2 font-weight-bold pb-2"
                            ) as p:
                                v3.VIcon(
                                    classes="mr-2",
                                    size="small",
                                    icon="mdi-tune-variant",
                                )
                                p.add_child("Slice selection")
                        with v3.VListItemSubtitle():
                            with html.P(classes="ps-7") as p:
                                p.add_child(
                                    """
                                    Toggle data selection toolbar for selecting a given layer, midpoint or time.
                                    """
                                )

                    with v3.VListItem(classes="px-0"):
                        with v3.VListItemTitle():
                            with html.P(
                                classes="text-body-2 font-weight-bold pb-2"
                            ) as p:
                                v3.VIcon(
                                    classes="mr-2",
                                    size="small",
                                    icon="mdi-movie-open-cog-outline",
                                )
                                p.add_child("Animation controls")
                        with v3.VListItemSubtitle():
                            with html.P(classes="ps-7") as p:
                                p.add_child(
                                    """
                                    Toggle animation toolbar.
                                    """
                                )

            html.P(
                "Simulation Files",
                classes="mt-6 text-h6 font-weight-bold text-medium-emphasis",
            )

            with html.P(classes="mt-4 mb-6 text-body-1") as p:
                p.add_child(
                    """
                    QuickView has been developed using EAM's history output on
                    the physics grids (pg2 grids) written by EAMv2, v3, and an
                    intermediate version towards v4 (EAMxx). 
                    Those sample output files can be found on Zenodo.
                    """
                )
            with html.P(classes="mt-4 mb-6 text-body-1") as p:
                p.add_child(
                    """
                    Developers and users of EAM often use tools like NCO and CDO
                    or write their own scripts to calculate time averages and/or
                    select a subset of variables from the original model output.
                    For those use cases, we clarify below the features of the data
                    format that QuickView expects in order to properly read and
                    visualize the simulation data.
                    """
                )

            html.P(
                "Connectivity Files",
                classes="mt-6 text-h6 font-weight-bold text-medium-emphasis",
            )

            with html.P(classes="mt-4 mb-6 text-body-1") as p:
                p.add_child(
                    """
                    The horizontal grids used by EAM are cubed spheres.
                    Since these are unstructed grids, QuickView needs
                    to know how to map data to the globe. Therefore,
                    for each simulation data file, a "connectivity file"
                    needs to be provided.
                    """
                )

            with html.P(classes="mt-4 mb-6 text-body-1") as p:
                p.add_child(
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
            with html.P(classes="mt-4 mb-6 text-body-1") as p:
                p.add_child(
                    """
                    Future versions of QuickView will also support the
                    cubed-sphere meshes used by EAM's dynamical core,
                    i.e., the ne*np4 grids (also referred to as
                    "native grids" or "GLL grids").
                    """
                )

            html.P(
                "Project Background",
                classes="mt-6 text-h6 font-weight-bold text-medium-emphasis",
            )

            with html.P(classes="mt-4 mb-6 text-body-1") as p:
                p.add_child(
                    """
                    The lead developer of EAM QuickView is Abhishek Yenpure (abhi.yenpure@kitware.com)
                    at Kitware, Inc.. Other key contributors at Kitware, Inc. include Berk Geveci and
                    Sebastien Jourdain. Key contributors on the atmospheric science side are Hui Wan
                    and Kai Zhang at Pacific Northwest National Laboratory.
                    """
                )

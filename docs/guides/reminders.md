
# The QuickView family

![app icons](/guides/QuickView_family_app_icons_with_text.png){ width="50%", align=right }

The QuickView family is a collection of interactive tools for visualizing and analyzing Earth system simulation data on the model’s native grid. Compared with diagnostic packages that generate static figures for comprehensive model evaluation, these tools focus on the exploratory work often needed early in an investigation or during code debugging.

Each tool in the QuickView family focuses on a small set of tasks. This limited scope keeps the graphical interfaces simple and intuitive, speeds up initial development, and simplifies long-term maintenance. We envision supporting substantially different workflows and emerging needs by adding new members to the family.


The first three members of the family are

- [QuickView](/guides/quickview/index)
  for simultaneously presenting 2D contour plots of
  multiple physical quantities (variables) on
  global or regional maps,
- [QuickCompare](/guides/quickcompare/index)
  for contrasting two or more simulations, also using 2D contour plots, and
- [SiteView](/guides/siteview/index)
  for process-level analysis of an atmospheric column and its
  regional environment.

The tools currently support cubed-sphere horizontal meshes
consisting of either Gauss-Lobatto-Legendre (GLL) nodes (i.e., the `ne*np4` grids)
or finite-volume style grid cells (`ne*pg2`, `ne*pg3`, etc.).
Sample visualizations showing
simulation output from the EAM, ELM, and CAM-SE models
can be found in the [gallery](/gallery/).

## Documentation conventions

We use the following conventions on this documentation site.

- **Bold** marks labels on buttons, menus, and other controls in the apps,
  matching each app’s capitalization. Some list items in this
  documentation also use bold for short headings.
- A fixed-width font marks keyboard keys such as `Esc` and
  text to read or type exactly, such as the command-line option `--state`
  or the filename `quickview-state.json`.
- *Italics* indicate occasional emphasis.
- Page titles and section headings use sentence case.
  The left navigation uses title case.

## Key reminders

::: warning Two modes of use
All tools in the family support two ways of usage:
a *new-vis* mode for starting a new analysis and
a *resume* mode for continuing an earlier, saved analysis.
Further details can be found in, e.g.,
the [QuickView user's guide](/guides/quickview/file_selection#state-files) and
the [QuickCompare user's guide](/guides/quickcompare/file_selection#state-files).
:::

::: info Connectivity files
Since cubed spheres are unstructured horizontal meshes,
connectivity files need to be provided to the tools alongside the simulation files.
Please note that such connectivity files are, typically, *not* the mapping files
used for interpolating data to regular lat-lon grids.
Further information can be found in the [introduction to connectivity files](/guides/connectivity).
:::

::: tip Consistency between connectivity and simulation files
One of the often encountered causes of error when loading files is
that the connectivity information does not match the
horizontal dimension in the simulation file.
In such a case, after the user clicks the **Load files** button (e.g., in
[QuickView](/guides/quickview/file_selection#new-analysis) or
[QuickCompare](/guides/quickcompare/file_selection#new-analysis)),
the file loading window will remain open and appear non-responsive.
If the app was launched from the command line,
the terminal window will display a message prompting the user to check
if the simulation and connectivity files exist and are compatible.
:::

::: warning Applying variable selections
Most controls in our tools apply changes immediately.
However, after variables are selected or deselected,
the user *must* click the load button at the top of the
[variable selection panel](/guides/quickview/variable_selection)
in order for the updated list of variables to be loaded
into memory and displayed in the viewport.
:::

::: info Show/hide control panels
Each tool in the QuickView family contains multiple control panels
for setting properties of the visualization.
These control panels can be shown/expanded for easy access or
be hidden/collapsed to maximize the screen space for visualization.
The apps provide both keyboard shortcuts and toggles in the main toolbar
to show or hide these control panels.
:::

::: tip Viewport layout
All tools in the QuickView family are designed to simultaneously present multiple
images and/or charts to help the user identify relationships and distinctions.
In QuickView,
the size, sequence, and arrangement of the contour plots can be easily adjusted
through the [viewport-layout control panel](/guides/quickview/viewport_layout) and
[keyboard shortcuts](/guides/quickview/shortcuts).
In QuickCompare, additional buttons and mini-menus are provided for
configuring a comparison [between two simulations](/guides/quickcompare/two-sim_comparison.md)
or [across an ensemble](/guides/quickcompare/multi-sim_comparison.md).


Furthermore, if a user saves a state file after these
adjustments, they can later resume their analysis with the customized arrangement.
The use of state files in [QuickView](/guides/quickview/file_selection#state-files)
and [QuickCompare](/guides/quickcompare/file_selection#state-files)
is explained on the linked pages.
:::

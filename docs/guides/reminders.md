# The QuickView Family

The QuickView family is a collection of tools for interactive
visualization and analysis of Earth system simulation data.
Compared to standardized and formalized diagnostic packages
that produce hundreds of static figures for comprehensive and
in-depth analysis for model evaluation, the focus of the QuickView
family is on interactive explorations that often happen
during the initial stage of an investigation or code debugging,
using simulation output on the model's native grid.

Each tool in the family focuses on a small set of actions
that we believe are frequently taken by Earth system model
developers and users. The focused attention allows the graphical user interface
to stay simple and intuitive.
On the other hand, we are continually summarizing typical analysis
workflows and assessing new needs to add members to the family.

The first two members of the family are
- [QuickView](/guides/quickview/index)
  for simultaneously presenting 2D contour plots of
  multiple physical quantities (variables) on 
  global or regional maps, and
- [QuickCompare](/guides/quickcompare/index)
  for contrasting two or more simulations, also using 2D contour plots.

As for the computational mesh over the globe,
the tools currently support only the E3SM Atmosphere Model's
cubed-sphere `ne*pg2` grids, but extensions to other grids are planned.

## Key Reminders

::: warning Two modes of use
QuickView can be used in two modes:
a *new-vis* mode (for starting a new visualization) or
a *resume* mode (for resuming an analysis). Further details can be found on, e.g.,
[this page](/guides/quickview/file_selection.md).
:::

::: info Connectivity files
Since E3SM's cubed-sphere horizontal grids are unstructured meshes from ParaView's perspective,
the so-called connectivity files are needed in addition to the simulation data files
for the visualization.
Further information about connectivity files can be found on 
[this page](/guides/connectivity.md).
:::

::: tip Consistency between connecitivity and simulation files
One of the often encountered causes of error when loading files in the QuickView family is
that the grid described by the connecitivity file does not match the grid in the
simulation data file. In such a case, after the user specified the two files
and clicked `Load files` (see more detailed description [here](/guides/quickview/file_selection#new-analysis)),
the file loading dialogue window will
remain open and appear non-responsive, and the terminal window will display
a message like the following:
```
Error occurred in UpdatePipeline. Please check if the data and connectivity files exist and are compatible
```
:::

::: warning The `Load ... Variables` button
Most buttons, sliders, and selection boxes in the graphical User Interfaces (UIs)
apply their effects
immediately upon user interaction. An important exception is variable
selection: After variables are chosen for the first time following file loading
or after the selection is changed, the user **must** click the `Load ... Variables`
button at the top of the [variable selection control panel](/guides/quickview/variable_selection)
in order for the new selection to take effect,
i.e., for the selected variables to be loaded into memory and shown
as images in the viewport.
:::

::: info Show/hide control panels
Each tool in the QuickView family contains multiple control panels
for setting properties of the visualization.
These control panels can be shown/expanded for easy access or
be hidden/folded to maximize the screen space for visualization
The UIs provide both keyboard shortcuts and toggles in the toolbar
to show or hide these control panels.
:::

::: tip Viewport layout
All tools in the QuickView family are designed to simultaneously present multiple
images and charts etc. to help the user identify relationships and distinctions.
The sizes and the layout of the different images etc. can be easily adjusted. See, e.g., [this page](/guides/quickview/viewport_layout).

Furthermore, if a user saves a state file after these
adjustments, they can later resume their analysis with the customized
arrangement. For example, the use of state files in QuickView
can be found in [this section](/guides/quickview/file_selection#state-files).
:::


![toolbar](../images/toolbar.png)

The toolbar located at the top of the GUI contains UI elements (buttons
and text boxes) that control global features of the current
visualization session ("global" in the sense of being shared by
all the variables being displayed).
In the following, we explain in detail the elements
that support the two modes of usage of the app, new-viz and resume, and
then introduce the other elements. 

----
## New-viz mode: starting a new visualization

![connectivity and data file buttons](../images/toolbar_conn_and_data_load.png)

To start a new analysis/visualization, the user needs to specify
a [connecitivy file](connectivity.md) and
a [simulation data file](data_requirements.md) using
the portion of the toolbar shown above, by either typing
the file paths and names in the corresponding boxes
or using the file folder icons to bring up system dialogue windows to
select files.

After both files have been specified, click on the `Load Files` button
(the icon of a page with a check mark). If the red circle with an exclamation
mark shown in the picture above becomes a green circle with a check mark,
the files have been loaded and the ParaView Reader behind the GUI has
identified variables in the data file that the app can visualize.
The user can then move on to using the [Toolbar](toolbar.md) to select
variables and spatial/temporal slices to display.

If the red circle persists, then the variable dimensions in the data file
have not been parsed correctly. Possible reasons for the error are:

- The data file and connectivity file correspond to different cubed-sphere
  meshes. E.g., one is ne30pg2 and the other is ne4pg2.
- The data file is missing some of the coordinate variables needed by the
  app, or the dimensions are named or ordered in ways not yet known by
  the app, see [data format requirements](data_requirements.md).

----
## Resume mode: pick up where you left off

![state save and load](../images/toolbar_state_save_and_load.png)

The current state of the visualization can be saved—and reloaded later to
resume the analysis—using the `Save State` and `Load State` icons shown above.

Note that a state file is a JSON file that contains the paths and names of
the connectivity and data files being used as well as the settings
the user has chosen for the visualization; the *contents* of the
connectivity and data files are *not* included.
If the user wished to use the same settings but for a different set of files
or for files located under different paths, then the file names and paths
at the beginning of the state file need to be edited before the state
file is loaded in the app.

----
## Other elements of the toolbar

![toolbar misc](../images/toolbar_misc.png)

1. The hamburger icon hides or shows the [control panel](control_panel.md).
1. The `LOAD VARIABLES` button, when clicked, executes the action of loading
   the [user-selected variables](control_panel.md) from the data file and
   displaying them in the [viewport](viewport.md).
1. The eye icon is a toggle for loading a group of colorblind-friendly colormaps
   to the GUI for the user to choose from in the [viewport](viewport.md).
   A lot of these colormaps are from
   [Crameri, F. (2018)](https://doi.org/10.5281/zenodo.1243862). 
   The paint palette icon is a toggle for loading a set of colormaps that
   may not be colorblind-friendly. Currently, these are mostly "presets"
   taken from [PareView](https://www.paraview.org/). 
1. The `Camera Reset` button refreshes all contents in the [viewport](viewport.md)
   so that the contour plots are recentered and resized to their
   individual windows ("views").

!!! tip "Tip on Camera Reset" 

    As mentioned on the [Reminders](reminders.md) page, the app may exhibit
    display issue after new variable selection or setting changes have been made.
    In those cases, a click on the `Camera Reset` should reload the visualization
    properly, and we are working on resolving the problem for future releases.

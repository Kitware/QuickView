
![toolbar](../images/toolbar.png)

The toolbar located at the top of the GUI contains UI elements (buttons
and text boxes) that control global features of the current
visualization session ("global" in the sense that they affect
the overall appearance and state of the GUI, including all the images
displayed in the [viewport](viewport.md)).
In the following, we first explain in detail the elements
that support the two modes of usage of the app, new-viz and resume, and
then introduce the other elements. 

----
## New-viz mode: starting a new visualization


To start a new analysis/visualization, the user needs to specify
a [connecitivy file](connectivity.md) and
a [simulation data file](data_requirements.md) using
the portion of the toolbar shown here, by either pasting/typing
the file paths and names in the corresponding boxes
or using the file folder icons to bring up system dialogue windows to
select files.

![connectivity and data file buttons](../images/toolbar_conn_and_data_load.png){ width="59%", align=right }

After both files have been specified, the `Load Files` button
(the icon of a page with a check mark) must be clicked.
If the red circle with an exclamation
mark shown in the picture here becomes a green circle with a check mark,
the files have been loaded and the ParaView Reader behind the GUI has
identified variables in the data file that the app can visualize.
The user can then start using the [control panel](control_panel.md) to select
variables and spatial/temporal slices to display.

!!! warning "Tip: Simulation File Loading Error"

    After the `Load Files` button is clicked,
    if the red circle-and-exclamation icon persists,
    then the variable dimensions in the data file
    are not parsed correctly. Possible reasons for the error include:
    
    - The data file and connectivity file correspond to different cubed-sphere
      meshes. E.g., one is ne30pg2 and the other is ne4pg2.
    - The data file is missing some of the coordinate variables needed by the
      app, or the dimensions are named or ordered in ways not yet known by
      the app, see [data format requirements](data_requirements.md).

----
## Resume mode: pick up where you left off

![state save and load](../images/toolbar_state_save_and_load.png){ width="10%", align=right }

The current state of the visualization can be saved—and reloaded later to
resume the analysis—using the `Save State` (downward arrow)
and `Load State` (upward arrow) buttons shown here.

For loading a state, the upward arrow button will bring up a windew for
the user to select a state file from the file system. After the file
is selected and the `Open` button is clicked, the app will immediately
start loading the state (i.e., the user is *not* expected to click on the 
"Load Files" meant for the new-viz scenario).
If the state file is successfully loaded (the contents correctly parsed),
the red circle-and-exclamation icon will turn into to a green-circle-and-check-mark icon,
like in the new-viz mode. Loading a state for an ne30 simulation
usually takes a second to a few seconds. 

!!! info "Info: What's in a State File?"

    A state file is a JSON file that contains the paths and names of
    the connectivity and data files being used as well as the settings
    the user has chosen for the visualization; the *contents* of the
    connectivity and data files are *not* included.
    If a state file is shared with multiple users or used across different
    file systems, or if a user wants to apply the same visualization settings
    to a different simulation data file, then the file names and paths
    at the beginning of the state file need to be edited before the state
    file is loaded in the app.

!!! warning "Tip: State File Loading Error"

    If the app seems nonresponsive after a state file has been chosen
    and the `Open` button has been clicked,
    there is a high chance that the paths and names of
    the connectivity and simulation data files contain errors.
    The user should consider using a text editor to inspect the first
    few lines of the state file and verify correctness.

----
## Other elements of the toolbar



![toolbar misc](../images/toolbar_hamburger.png){ width="6%", align=right }

**Control Panel Hide/Show**:
The hamburger icon (three stacked lines) hides or shows the [control panel](control_panel.md).



![toolbar misc](../images/toolbar_busy_indicator.png){ width="5%", align=right }

**Busy Indicator**:
The gray circle is a busy indicator. When a rotating segment is shown,
the app is processing data in the background, e.g., loading new data files or
a state file (see earlier sections on this page) or
loading newly selected variables (see [control panel](control_panel.md)),
etc.



![toolbar misc](../images/toolbar_load_variables.png){ width="18%", align=right }
   
**`LOAD VARIABLES` Button**:
The `LOAD VARIABLES` button, when clicked, executes the action of loading
the [user-selected variables](control_panel.md) from the data file and
displaying them in the [viewport](viewport.md).



![toolbar misc](../images/toolbar_colormap_groups.png){ width="12%", align=right }

**Colormap Groups**:
The eye icon is a toggle for loading a group of colorblind-friendly colormaps
to the GUI for the user to choose from in the [viewport](viewport.md).
A lot of these colormaps are from
[Crameri, F. (2018)](https://doi.org/10.5281/zenodo.1243862).
The paint palette icon is a toggle for loading a set of colormaps that
may not be colorblind-friendly. Currently, these are mostly "presets"
taken from [PareView](https://www.paraview.org/). 



![camera widget](../images/camera_actions.png){ width="25%", align=right }

**Camera Actions**:
A set of buttons are provided to simultaneously adjust all variables displayed
in the [viewport](viewport.md): move them up, down, left, or right with
respect to the GUI, zoom in or out, or
refresh all contents in the [viewport](viewport.md)
so that the contour plots are recentered and resized to their
individual windows ("views").

!!! tip "Tip: Camera Refresh for Addressing Display Error" 

    As mentioned on the [Reminders](reminders.md) page, the app may exhibit
    display issue after new variables are loaded or visualization
    settings are changed.
    In those cases, a click on the `Camera Reset` should reload the visualization
    properly, and we are working on resolving the problem for future releases.

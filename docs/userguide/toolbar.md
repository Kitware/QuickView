
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
The user can then move on to using the [control panel](control_panel.md) to select
variables and spatial/temporal slices to display.

!!! warning "Tip: File Loading Error"

    After the `Load Files` button is clicked,
    if the circle-shaped busy indicator on the left side of the toolbar
    does not start spinning in a second or two, and the red circle with an
    exclamation mark shown above persists,
    then the variable dimensions in the data file
    have not been parsed correctly. Possible reasons for the error are:
    
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
start loading the state. If successful, the icon of a red circle with
an exclamation mark will turn to a green circle with a check mark,
like in the new-viz mode. Loading a state for an ne30 simulation
usually takes a second or two. 

!!! info "Info: What is in a State File?"

    A state file is a JSON file that contains the paths and names of
    the connectivity and data files being used as well as the settings
    the user has chosen for the visualization; the *contents* of the
    connectivity and data files are *not* included.
    If a user passes a state file to another user or file system,
    or if they want to use the same visualization settings but for
    a different simulation data file, then the file names and paths
    at the beginning of the state file need to be edited before the state
    file is loaded in the app.

----
## Other elements of the toolbar



![toolbar misc](../images/toolbar_hamburger.png){ width="6%", align=right }

**Control Panel Hide/Show**:
The hamburger icon (three stacked lines) hides or shows the [control panel](control_panel.md).



![toolbar misc](../images/toolbar_busy_indicator.png){ width="5%", align=right }

**Busy Indicator**:
The gray circle is a busy indicator. When a rotating segment is shown,
the app is processing data in the background (e.g., loading data files or
a state file (see earlier sections on this page),
updating loading newly selected variables (see [control panel](control_panel.md)),
etc.


![toolbar misc](../images/toolbar_load_variables.png){ width="18%", align=right }
   
**`LOAD VARIABLES` Button**
The `LOAD VARIABLES` button, when clicked, executes the action of loading
the [user-selected variables](control_panel.md) from the data file and
displaying them in the [viewport](viewport.md).


![toolbar misc](../images/toolbar_colormap_groups.png){ width="12%", align=right }

**Colormap Groups**
The eye icon is a toggle for loading a group of colorblind-friendly colormaps
to the GUI for the user to choose from in the [viewport](viewport.md).
A lot of these colormaps are from
[Crameri, F. (2018)](https://doi.org/10.5281/zenodo.1243862).
The paint palette icon is a toggle for loading a set of colormaps that
may not be colorblind-friendly. Currently, these are mostly "presets"
taken from [PareView](https://www.paraview.org/). 


**Camera Reset**
The camera reset button refreshes all contents in the [viewport](viewport.md)
so that the contour plots are recentered and resized to their
individual windows ("views").

!!! warning "Tip on Camera Refresh" 

    As mentioned on the [Reminders](reminders.md) page, the app may exhibit
    display issue after new variable selection or setting changes have been made.
    In those cases, a click on the `Camera Reset` should reload the visualization
    properly, and we are working on resolving the problem for future releases.

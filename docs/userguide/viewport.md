# Viewport

![Four views](../images/viewport_four_views.png){ width="65%", align=right }

Once the user has selected variables using the [control panel](control_panel.md)
and clicked the `LOAD VARIABLES` button in the [toolbar](toolbar.md), the app
will show each variable in its own little frame (which we refer to as a "view") inside
the viewport. Below is an example showing six views.

At the top of each view, 
the indices of the vertical level (if applicable) and time slice being displayed
are shown in the top-left corner of each view.
The variable name is shown in the top-right corner
together with the area-weighted global average on that vertical level.
If the "area" variable is not present in the data file, then the arithmetic
average is calculated and displayed.


-----
## Custimizing the viewport

![Many views resized and rearranged](../images/multiview_rearranged.png){ width="40%", align=right}

To help present multiple variables in an informative way, the app allows users
to

- rearrange the views via ^^drag-and-drop^^, and
- resize each view separately by ^^clicking and dragging its bottom-right corner^^.

The screenshot on the right shows an example with rearranged views.

Furthermore, if a user saves a state file after these adjustments, they can
later continue their analysis with the customized arrangement
by using the app in the resume mode, as described in on the description
of the [toolbar](toolbar.md).


-----
## Custimizing individual views

Each view can be further customized individually by clicking on the gear button
in the bottom-left corner of the view. The click brings up a mini menu as shown
in the examples below.

The mini menu contains options to control various properties of the view:
a dropdown menu for colormap selection,
checkboxes to turn on/off logarithmic scale and to invert/restore the color sequence,
text boxes for changing the minimum and maximum values for color mapping, and
a button to reset the color mapping to fit the range of values in the data.

![gear menu with auto range](../images/gear_menu_range_auto.png){ width="48%"}
![gear menu with manual range](../images/gear_menu_range_manual.png){width="48%"}

!!! tip "Tip: Automatic or Fixed Colormap Ranges"


    By default, the app will automatically span the colormap over the range of values
    of the current time slice and vertical level. The max. and min. values can be found
    in the mini menu, as seen in the left example above.
    When the "play" button in the [control panel](control_panel.md) is used to cycle
    through different data slices in a dimension,
    the colormap will be automatically adjusted for each data slice.

    If the user specifies min. and/or max. values in the mini menu, a blue icon
    with a picture of a lock and the text "Manual" will show up above the max.
    value, as can be seen on the right in the example above.
    After that, when the "play" button in the [control panel](control_panel.md)
    is used to cycle through different data slices in a dimension,
    the colormap will be fixed for the user-specified range.
     

!!! tip "Tip: Field Value Lookup in Colorbar"

    ![colorbar hover over](../images/colorbar_hover_over.png){ width="55%", align=right }

    If the user hovers their cursor over a colorbar, the corresponding field
    value will be displayed, as shown by the example here.


!!! tip "Tip: Colormap Groups"

    The [toolbar](toolbar.md) at the top of the GUI includes icons for two colormap
    groups: colorblind-friendly and other. Only the colormaps belonging to the
    selected group (or groups) are shown in the `Color Map` drop-down menu.


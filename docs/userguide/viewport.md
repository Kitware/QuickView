# Viewport

Once the user has selected variables using the [control panel](control_panel.md)
and clicked the `LOAD VARIABLES` button in the [toolbar](toolbar.md), the app
will show each variable in its own frame (which we refer to as a "view") inside
the viewport. Below is an example showing six views.

At the top of each view, the variable name is shown in the top-left corner
together with the area-weighted global average on that vertical level. Indices
of the vertical level and time being displayed are indicated in the top-right
corner of each view.

![Six views in default layout](../images/six_variables_default.png){width="600"}

## Custimizing the viewport

To help present multiple variables in an informative way, the app allows users
to rearrange the views via drag-and-drop and resize each view separately by
clicking and dragging its bottom-right corner. Below is an example with
rearranged views.

Furthermore, if a user saves a state file after these adjustments, they can
later resume their analysis with the customized arrangement.

![Six views resized and rearranged](../images/six_variables_rearranged.png){width="700"}

## Custimizing individual views

Each view can be further customized individually by clicking on the gear button
in the bottom-left corner of the view. The click brings up a mini menu as shown
in the example below.

_[Hui's note from 4/30/2025: the title of the colorbar reads "Component". Is
this a bug? We'd like the title to show the variable name; or we could remove
the title.]_

![Mini menu for custimizing a view](../images/mini-menu.png){width="400"}

The mini menu contains options to control various properties of the view:

- A dropdown menu for color map selection.
- Checkboxes to turn on/off logarithmic scale and invert color map.
- Text boxes for changing the minimum and maximum values for color mapping.
- A button to reset the color mapping to fit the range of values in the data.

Note that the zoom level and centering (i.e., the size and relative position) of
the displayed variable within each view, as well as the visibility of the color
bar, can also be adjusted. These settings are controlled centrally—for all
views—via buttons in the [toolbar](toolbar.md) near the top of the GUI.

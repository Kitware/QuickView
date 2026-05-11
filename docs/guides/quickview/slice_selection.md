# Selecting Data Slices to Inspect

QuickView is designed to visualize variables in the simulation data files
that have horizontal dimensions representing the globe.
The variables are shown on global or regional maps.
If a variable has additional dimensions such as time, vertical level, etc.,
QuickView is designed to display one global or regional map at a time for that variable.

To choose the indices to inspect for the non-horizontal dimensions,
the slice selection button in the vertical toolbar can be clicked
to bring up the **slice selection control panel**, as shown in
the first screenshot below.

In this example, the selected variables together have six non-horizontal dimensions,
corresponding to the six stadium shapes highlighted in the red box.
The dimension names are shown inside the stadiums. The index values (counting from 0)
corresponding to the images in the viewport are shown in bold within parentheses.
When a dimension has an associated 1D dimension variable,
its value and unit are displayed in italics next to the parentheses.

![](./screenshots/slice_selection_panel.png){ width="100%" }

Each stadium can be clicked to expand the corresponding slice selection controls,
revealing a textbox and a slider for changing the data slice along that dimension.
In the expanded state, the stadium is shown in solid blue.

![](./screenshots/dimension_slider_expanded.png){ width="100%" }

Alternatively, the **animation control panel** shown in the screenshot below
can be used. This panel contains a drop-down menu for choosing a dimension to inspect,
a slider and a set of forward and backward buttons for manually stepping through the selected dimension,
as well as a two play/pause toggles for automatically stepping through the selected dimension
in forward or reverse order.
The rightmost button in the panel, with a downward arrow above two horizontal lines,
is for exporting animations and is explained on [a separate page](./miscellaneous#save-vis)

![](./screenshots/animation_control_panel_and_menu.png){ width="100%" }

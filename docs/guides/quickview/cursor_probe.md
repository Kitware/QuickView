# The Cursor Probe in QuickView {#cursor-probe}

Starting in version 2.8.3, QuickView provides a Cursor Probe for inspecting data values at the cursor location. Two modes are available:

| Icon | Mode | Description |
|------|------|-------------|
| <img src="https://cdn.jsdelivr.net/npm/@mdi/svg/svg/cursor-default-gesture-outline.svg" width="24"> | Hover Mode | Updates continuously as the cursor moves over contour plots in the viewport. |
| <img src="https://cdn.jsdelivr.net/npm/@mdi/svg/svg/cursor-default-click-outline.svg" width="24"> | Click Mode | Updates only when the user clicks a location in a contour plot. This mode may provide better responsiveness when working with very large datasets. |

![cursor probe information panel](./screenshots/cursor_probe_information_panel.png){ width="30%", align=right }

In both modes, information associated with the cursor location is displayed in
an **Information Panel**, as shown in the screenshot here.
The latitude and longitude of the cursor location are shown at the top,
followed by the name and value of the variable in the current view, as well as
the names and values of the other variables displayed in the viewport.
If a variable has non-horizontal dimensions, the value shown in the Information Panel
is the value at the cursor-selected lat-lon location in the currently data slice. 

![cursor probe icons](./screenshots/cursor_probe_icons_in_viewport.png){ width="50%", align=right }

The Cursor Probe is inactive by default and can be activated by clicking either the
Hover Mode or Click Mode icon in any viewport panel.
These icons are available in all views for convenient access.
However, the probe's activate/inactive state applies to the entire viewport
and is shared across all views. As a result, the Cursor Probe cannot be enabled
for some views (variables) while remaining disabled for others.


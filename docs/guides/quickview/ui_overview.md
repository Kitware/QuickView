# QuickView's Graphical UI

![QuickView UI](./screenshots/quickview_ui.png){ width="100%" }


## UI components

QuickView's UI contains three main components.

- **Viewport**: The viewport displays contour plots on global or regional maps
  for the user-selected physical quantities (variables in the NetCDF files).
  The sequence of the displayed variables and the size of the contour plots
  can be adjusted using the [viewport layout](./viewport_layout.md) control panel.
  For each variable shown on a map, the colormap, value ranges etc. can be adjusted
  individually using the [pop-up panel](./individual_views.md)
  activated by a click on the colorbar.

![Toolbar compact or expanded](./screenshots/toolbar_compact_or_expanded.png){ width="50%" align=right}

- **Control panels**: QuickView includes various control panels for
  changing the properties of contour plots shown in the viewport.
  The control panels can be collapsed (hidden)
  or expanded (shown) by clicking on their corresponding icons in the
  toolbar or by using [keyboard shortcuts](./shortcuts).

- **Main toolbar**: The vertical toolbar located on the left of the UI
  contains various buttons that either activate pop-up menus on a single click
  or serve as toggles for showing or hiding control panels.
  The toolbar is shown in a collapsed mode by default, but
  will change into an expanded mode if the user clicks on the
  colorful QuickView icon at the top of the toolbar or press the
  `H` key on the keyboard.

## Toolbar buttons {#toolbar-buttons}

From top to bottom, the main toolbar contains the buttons listed below.
In the collapsed toolbar, hovering over a button shows its name in a tooltip;
in the expanded toolbar, the names are shown next to the icons.
Buttons marked as toggles show or hide a control panel.

| Button | Shortcut | What it does |
| ------ | -------- | ------------ |
| QuickView icon | `H` | Expands or collapses the toolbar, i.e., shows or hides the button names. |
| **Auto zoom** | `Z` | Resets the zoom so that each plot fits its view. |
| **State Import/Export** | `E` / `I` | Menu to save the current state to a file or load a state file. See [Resume mode](./file_selection#state-files). |
| **File loading** (toggle) | `F` | Opens the window for selecting the simulation and connectivity files. See [Selecting Files](./file_selection). |
| **Variable selection** (toggle) | `V` | Panel for choosing the variables to visualize. See [Selecting Variables](./variable_selection). |
| **Slice selection** (toggle) | `S` | Panel for choosing the slice (e.g., time step, vertical level) of multi-dimensional variables. See [Selecting Data Slices](./slice_selection). |
| **Animation controls** (toggle) | `A` | Panel for stepping or playing through one dimension, and for exporting animations. See [Selecting Data Slices](./slice_selection). |
| **Viewport layout** (toggle) | `P` | Panel for the view sizes, grouping, and aspect ratio. See [Customizing Viewport Layout](./viewport_layout). |
| **Map Projection** | `C` `R` `M` `N` | Menu to choose the projection, the lat-lon grid line spacing, and the coastline resolution. See [Map projection](./map_related#map-projections). |
| **Lat/Lon cropping** (toggle) | `L` | Panel for restricting the plots to a longitude/latitude box and for moving the map center. See [Geographical region](./map_related#geographical-region). |
| **Capture viewport as png** | | Saves the whole viewport as a PNG image. See [Saving Images](./saving_images). |
| **Background Colors** | | Menu to choose the background color of the plots. See [Plot background color](./map_related#plot-background-color). |

Pressing `Esc` closes all open control panels and collapses the toolbar.
While no variable is selected, the viewport shows a help page that summarizes
the toolbar buttons and the [keyboard shortcuts](./shortcuts).
The version number of QuickView is shown at the bottom of the toolbar.

::: info Note for developers
When QuickView is started with trame's `--hot-reload` option, an extra
**Refresh UI** button appears at the end of the toolbar. It rebuilds the UI
after a code change without restarting the application.
:::

<!-- ## Tooltips and visual cues -->

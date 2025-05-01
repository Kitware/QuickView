# Key reminders for using EAM QuickView


- EAM QuickView can be [launched](launch.md) in two ways: from simulation data (for starting a new visualization) or from a state file (for resuming an analysis).

- Regardless of which way of launch is used, a [connectivity file](connectivity.md) is needed together with the simulation data file.

- Most buttons, sliders, and selection boxes in the GUI apply their effects immediately upon user interaction. The only exception is the variable selection: after variables are chosen for the first time following app launch, or after the selection is changed, the user must click the `LOAD VARIABLES` button in the [toolbar](toolbar.md) for the new selection to take effect. 

- In the current version, after the `LOAD VARIABLES` button is clicked, some of the variables showing up in the [viewport](viewport.md) might exhibit a display issue, e.g., erroneously showing the same color or a few color stripes over the entire globe or region. This can be remedied by clicking the refresh button at the right end of the [toolbar](toolbar.md), and we are hoping to resolve the issue for future versions.

- The QuickView app is designed to present multiple variables simultaneously in an informative way. Users can rearrange the individual views (i.e., global or regional maps of different variables) in the [viewport](viewport.md) via drag-and-drop, and resize each view separately by clicking and dragging its bottom-right corner. Furthermore, if a user saves a state file after these adjustments, they can later resume their analysis with the customized arrangement.


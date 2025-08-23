# Key Reminders for Using EAM QuickView

!!! tip "Tip: Two Modes of Use"

    EAM QuickView can be used in two modes:
    a ^^new-viz^^ mode (for starting a new visualization) or
    a ^^resume^^ mode (for resuming an analysis). Further details can be found on
    the [toolbar description page](toolbar.md).
     
!!! tip "Tip: Connectivity File"

    Regardless of which mode is used, a connectivity file is needed
    in addition to the simulation data file.
    Further details can be found on the documentation pages
    describing the [connectivity files](connectivity.md) and the
    [toolbar](toolbar.md).
     
!!! tip "Tip: The `LOAD VARIABLES` Button"

    Most buttons, sliders, and selection boxes in the GUI apply their effects
    immediately upon user interaction. The only exception is the variable
    selection: after variables are chosen for the first time following file load
    or after the selection is changed, the user ^^must^^ click the `LOAD VARIABLES`
    button in the [toolbar](toolbar.md) for the new selection to take effect.
     
!!! tip "Tip: Viewport Layout"

    The QuickView app is designed to present multiple variables simultaneously in
    an informative way. Users can ^^rearrange^^ the individual views
    (i.e., global or regional maps of different variables) in the
    [viewport](viewport.md) ^^via drag-and-drop^^,
    and ^^resize^^ each view separately ^^by clicking and dragging
    its bottom-right corner^^.


    Furthermore, if a user saves a state file after these
    adjustments, they can later resume their analysis with the customized
    arrangement.

!!! warning "Trick: Camera Refresh"

    In the current version, after the `LOAD VARIABLES` button is clicked or
    a visualization setting is changed, some (or all) of
    the images in the [viewport](viewport.md) might exhibit a display issue, e.g.,
    erroneously showing the same color or a few color stripes over the entire
    globe or region. This can be remedied by clicking the camera reset
    button at the right end of the [toolbar](toolbar.md), and we are working on
    resolving the issue for future versions.


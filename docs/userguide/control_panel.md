
!!! info inline end "Tip"

    The control panel can be collapsed or made visible using the hamburger icon
    (three horizontal lines stacked on top of each other ) on the left end of the
    [toolbar](toolbar.md).

# Control Panel

The control panel allows users to select variables from the data file
as well the spatial and temporal ranges of data to visualize,
as explained below.


-----
##  Variable selection

![variable selection sections](../images/variable_selection.png){ width="300", align=right }


###  Variable categories

EAM's simulation output files typically contain many variables
corresponding to physical quantities with spatial coverages over the
entire globe.

- Some of those variables may not have a vertical dimension;
  these are referred to as "surface variables" in our app.
- Some of those variables have "lev" or "ilev" as the vertical
  dimension; these are referred to as "variables at layer midpoints"
  and "variables at layer interfaces", respectively.

These three categories of variables each have their own collapsible
submenu in the control panel, as shown in the screenshot here.
Variables of other dimension sizes are currently igored by the app
but can be supported upon request


### Select and load

!!! tip inline end "The `LOAD VARIABLE` button"

    After a selection of variables is made or changed, the `LOAD VARIABLES`
    button in the [toolbar](toolbar.md) must be clicked in order for the
    (new) selection to take effect.
    In contrast, all other buttons, sliders, and text boxes
    apply their effects immediately upon user interaction.

After a simulation data file and a connectivity have been loaded and
the status icon in the [toolbar](toolbar.md) has turned into a green
circle with a check mark,
the variable selection submenu of each variable category,
if expanded, will show a list of variables that have been recognized
by the app. Checking the boxes to the left of the variable names
*and then clicking the* `LOAD VARIABLES` *button in the toolbar*
will render contour plots in the [viewport](viewport.md).

### Variable search

EAM output files often contain a large number of variables,
resulting in long lists in the varaible selection submenus.
In such cases, the user can hover their cursor over the list
and then scroll up and down to review the full list.

Typing a string in the `Search variables` box and then hitting
the `return` key on the keyboard will
replace the full variable list by a filtered list.

Clicking the `CLEAR` button in the submenu will unselect all
variables in the category.

*Here, we emphasize again that any changes in variable selection needs to be
followed by a click on the `LOAD VARIABLES` button in the [toolbar](toolbar.md)
in order for these changes to take effect.*



-----
## Data slice


The data slice selection allows users to slice and
   dice data spatio-temporally for analysis

   - a. It allows data slice selection along the dimensions of time, middle and
     interface layer.
   - b. It allows users to control the geo-spatial region by controlling the
     longitude, latitude ranges.

   Users can interactively select the data slice by interacting with the
   sliders, or using the media buttons to skip-previous, skip-next, or play an
   animation.

-----
## Map Projection

The map projection selection allows users to
   chose different representation of the data. Currently, it allows for
   Cylindrical-Equidistant, Robinson, and Mollweide projections. In the future,
   additional features are planned, e.g. selection of center meridian.


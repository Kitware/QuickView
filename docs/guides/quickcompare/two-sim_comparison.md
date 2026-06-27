# Comparing Two Simulations

Contents on this page:

[[toc]]

## The basics

The two-simulation comparison mode in QuickCompare displays two (potentially out of
many) simulations in a compact way. Below is an example of the default viewport layout.

![Two-sim comparison: typical layout](/guides/quickcompare/screenshots/two-sim_typical_layout.png){ width="100%", align=center }

When two (or more) simulations are loaded using the
[File Loading](./file_selection.md) dialogue,
QuickCompare enters the two-simulation (or multi-simulation) mode as the default.
The user can manually switch to a two-simulation mode by
clicking the **"Two Sim"** near the left end of the
Comparison Control panel (see screenshot below). In this mode, drop-down menus titled
**"Choose ctrl"** and **"Choose test"** allow the user to select
the control and test simulations to be compared in the viewport
(see screenshot below).

![Two-sim comparison: choose ctrl](/guides/quickcompare/screenshots/two-sim_choose_ctrl.png){ width="100%", align=center }
 
## Rows of plots

The different rows in the viewport correspond to different physical quantities,
i.e., variables from the simulation files.

- The variable names are shown in the top-left corner of each row.
  The vertical bar attached to the left of each row shows the color
  of the corresponding tab near the top of the
  [Variable Selection control panel](/guides/quickview/variable_selection#variable-groups)
  that indicates the shape (dimension combination) of the current variable.

![Two-sim comparison: variable rows](/guides/quickcompare/screenshots/two-sim_variable_rows.png){ width="100%", align=center }

- A click on a variable name activates a drop-down menu, allowing a different
  variable to be moved to the current row.
  Note that in order for a variable to be listed in the drop-down,
  that variable needs to have been selected and loaded using the
  [Variable Selection control panel](/guides/quickview/variable_selection). 

![Two-sim comparison: rearrange rows](/guides/quickcompare/screenshots/two-sim_rearrange_rows.png){ width="100%", align=center }

## Columns of plots

There can be up to five columns in the viewport displaying the following quantities:
  1. **Ctrl**: the variable in the control simulation;
  2. **Test**: the variable in the test simulating;
  3. **Diff**: the difference, `test - ctrl`;
  4. **Rel Diff (w.r.t. ctrl)**: `(test - ctrl)/ctrl`;
  5. **Rel Diff (w.r.t. mean)**: `(test - ctrl)/[0.5*(test+ctrl)]`.

Among these five, 1-4 are shown by default, but any of the five can be turned on or off
using the checkboxes in the "Comparison columns" drop-down menu.

![Two-sim comparison: choose metrics](/guides/quickcompare/screenshots/two-sim_choose_metrics.png){ width="100%", align=center }

The sequence of columns can be changed by the drop-down menus activated by clicks
on the panel titles "Ctrl", "Test", "Diff", etc.
Any column change triggered by the selection is applied to all rows in the viewport.

![Two-sim comparison: rearrange columns](/guides/quickcompare/screenshots/two-sim_rearrange_columns.png){ width="100%", align=center }

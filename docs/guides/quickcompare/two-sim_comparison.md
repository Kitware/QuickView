# Comparing Two Simualtions

The two-simulation comparison mode in QuickCompare displays two–potentially out of
many–smulations in a relatively compact way. Below is an example of the default layout.

![Two-sim comparison: typical layout](/guides/quickcompare/screenshots/two-sim_typical_layout.png){ width="100%", align=center }

Depending on whether two or more simulations are loaded using the
[File Loading](./file_selection.md) dialogue,
QuickCompare automatically enters into either the two-simulation or multi-simulation
mode by default. However, in the latter case, the user can manually switch
to a two-simulation mode by clicking the "Two Sim" tab near the left end of the
Comparison Control panel. In both modes, drop-down menus titled
"Choose ctrl" and "Choose test" allow the user to select
the control and test simulations to be compared in the viewport.

![Two-sim comparison: choose ctrl](/guides/quickcompare/screenshots/two-sim_choose_ctrl.png){ width="100%", align=center }
 
## Rows of plots

The different rows in the viewport correspond to different physical quantities,
i.e., different variables from the simulation files.

- The variable names are shown in the top-left corner of each row.
- A click on a variable name activates a drop-down menu, allowing a different
  variable to be moved to the current row.
  Note that in order for a variable to to be listed in the drop-down,
  that variable needs to have been selected and loaded using the
  [Variable Selection control panel](/guides/quickview/variable_selection). 

![Two-sim comparison: rearrange rows](/guides/quickcompare/screenshots/two-sim_rearrange_rows.png){ width="100%", align=center }

## Columns of plots

There can be up to five columns in the viewport displaying the following metrics:
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

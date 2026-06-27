# Comparing Multiple Simulations

For inspecting an ensemble of simulations, QuickCompare assumes
the user has specified a control simulation, and it treats
the rest of the loaded ensemble as test simulations.

## Control and test simulations to be displayed

By default, QuickCompare assumes the first simulated selected by by the user
in the [File Loading](./file_selection) dialogue is the control simulation while
all the other selected simulations ought to be displayed as test simulations.

This specification can be modified through the "organize simulation collection"
menu. 

![Multi-sim comparison: organize simulation collection](/guides/quickcompare/screenshots/multi-sim_organize_simulation_collection.png){ width="100%", align=center }

## Comparison types
 
Four types of comparison can be displayed:

1. **Value**: physical physical quantities from different simulations.
2. **Diff**:  differences of the other simulations with respect to ctrl, i.e., `test - ctrl`.
3. **Rel Diff (w.r.t. ctrl)**: `(test - ctrl)/ctrl`.
4. **Rel Diff (w.r.t. mean)**: `(test - ctrl)/[0.5(test+ctrl)`.

In 2-4, a "value" plot (i.e., the physical quantity itself) from the ctrl simulation
is also shown for reference.

At any time, the entire viewport shows a single type of comparison for
all user-selected variables. The "Comparison type" drop-down menu
is used to switch among types.

![Multi-sim comparison: comparison type](/guides/quickcompare/screenshots/multi-sim_comparison_type_drop-down.png){ width="100%", align=center }

## View size and layout 

Assuming the user has loaded $N_v$ variables and $N_s$ simulations.
The $N_v\cdot N_s$ plots in the viewport are grouped by variable.

- The number of plots per row can be changed using the [Viewport Layout](/guides/quickview/viewport_layout)
  control panel or using the number keys `1`, `2`, `3`, `4`, or `6`.
- Like in the [two-simulation mode](./two-sim_comparison) mode, a click on
  a variable name in the top-left corner of a plot group activates a drop-down
  menu to replace the current group by the corresponding plots of another variable
  on the list.
  (In order for a variable to be listed in the drop-down,
  that variable needs to have been selected and loaded using the
  [Variable Selection control panel](/guides/quickview/variable_selection).)

![Multi-sim comparison: rearrange variables](/guides/quickcompare/screenshots/multi-sim_rearrange_variables.png){ width="100%", align=center }

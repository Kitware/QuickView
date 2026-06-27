# Comparing Multiple Simulations

For inspecting an ensemble of simulations, QuickCompare assumes
the user has specified a control simulation, and it treats
the rest of the loaded ensemble as test simulations.

[[toc]]

## Control and test simulations

By default, QuickCompare assumes the first simulation selected by by the user
via the [File Loading](./file_selection) dialogue is the control (ctrl) simulation, while
all the other selected simulations ought to be displayed as test simulations.
This specification can be modified through the "Organize simulation collection"
menu, which allows the user to

- enter a custom label for each simulation to be used as a part of the plot titles in the viewport,
- exclude an already-loaded simulation from being displayed in the viewport
  (but still keep the simulation in a loaded state so that it can be re-included),
- change the simulation to be used as ctrl,
- change the sequence of simulations to be displayed.

![Multi-sim comparison: organize simulation collection](/guides/quickcompare/screenshots/multi-sim_organize_simulation_collection.png){ width="100%", align=center }

## Comparison types
 
Four types of comparison can be displayed:

1. **Value**: the values of the physical physical quantities loaded from simulation files.
2. **Diff**:  the differences between the other simulations and ctrl, i.e., `test - ctrl`.
3. **Rel Diff (w.r.t. ctrl)**: the differences normalized by ctrl, i.e., `(test - ctrl)/ctrl`.
4. **Rel Diff (w.r.t. mean)**: the differences normalized by the mean of the test simulation and the control one, i.e., `(test - ctrl)/[0.5(test+ctrl)]`.

In 2-4, a "value" plot (i.e., the physical quantity itself) from the control simulation
is also shown for reference.

At any time, the entire viewport shows a single type of comparison for
all user-selected variables. The "Comparison type" drop-down menu
is used to switch among types.

![Multi-sim comparison: comparison type](/guides/quickcompare/screenshots/multi-sim_comparison_type_drop-down.png){ width="100%", align=center }

## Viewport layout basics

Let us assume the user has loaded `Ns` simulations and `Nv` variables.
The viewport presents a total of `Nv*Ns` plots and group them by variable.
Each variable corresponds `Ns` plots (views) that forms a section.
Since `Ns` can be a large number, a section may contain multiple rows.
The number of plots (views) per row can be changed using the number keys `1`, `2`, `3`, `4`, or `6`.

## Variable sections

Each section in a viewport is marked by a vertical bar 
in the color that matches the corresponding variable shape tab
shown near the top of the
[Variable Selection control panel](/guides/quickview/variable_selection#variable-groups).

![Multi-sim comparison: variable sections](/guides/quickcompare/screenshots/multi-sim_variable_sections.png){ width="90%", align=center }

Like in the [two-simulation comparison](./two-sim_comparison) mode, a click on
a variable name in the top-left corner of a variable section activates a drop-down
menu to replace the current section by the corresponding plots of another variable.
(In order for a variable to be listed in the drop-down,
that variable needs to have been selected and loaded using the
[Variable Selection control panel](/guides/quickview/variable_selection).)

![Multi-sim comparison: rearrange variables](/guides/quickcompare/screenshots/multi-sim_rearrange_variables.png){ width="100%", align=center }

## Layout within section

Within a section, by default, the first view (the top-left plot)
shows the values of the variable from the control simulation (ctrl), and the
other views show the values from the test simulations or their differences
or relative differences relative to ctrl, depending on the currently-selected
comparison type.

If the user changes the designation of "ctrl" using the "Organize simulation collection"
diaglogue discussed above or the "Choose ctrl" drop-down menu near the top of the viewport,
the sequence of simulations shown in the viewport remains unchanged
but the plots and their titles are updated to reflect the new designation.

![Multi-sim comparison: change ctrl](/guides/quickcompare/screenshots/multi-sim_change_ctrl.png){ width="100%", align=center }

The sequence of simulations shown in each section
can be changed by either using the up and down bottons in the "Organize simulation collection"
diaglogue discussed above or using clicks on the simulation labels in each view.
A click on a label activates a drop-down menu of simulations for the user to chose
to move to the current location.
Any sequence change triggered by the selection is applied to all sections (variables) in the viewport.

![Multi-sim comparison: swap sims](/guides/quickcompare/screenshots/multi-sim_swap_sims.png){ width="100%", align=center }

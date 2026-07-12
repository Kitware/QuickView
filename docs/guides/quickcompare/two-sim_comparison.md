# Comparing Two Simulations

[[toc]]

## The basics

The two-simulation comparison mode in QuickCompare displays any two simulations
selected from the loaded ensemble in a compact layout.
The screenshot below shows an example of the viewport in its default layout.

![Two-sim comparison: typical layout](/guides/quickcompare/screenshots/two-sim_typical_layout.png){ width="100%", align=center }

When two simulations are loaded using the [File Loading](./file_selection.md) dialogue,
QuickCompare enters the two-simulation;
when more than two simulations are loaded, the default is to enter the multi-simulation mode,
but the user can manually switch to two-simulation mode by
clicking the **Two Sim** button near the left end of the Comparison Control panel highlighted in the screenshot below.
In this mode, drop-down menus titled
**"Choose ctrl"** and **"Choose test"**, also highlighted in the screenshot below, allow the user to
choose which simulations serve as the control and test simulations displayed in the viewport.

![Two-sim comparison: choose ctrl](/guides/quickcompare/screenshots/two-sim_choose_ctrl.png){ width="100%", align=center }

The viewport in the screenshot above shows a short introductory text.
After the user [selects and loads variables](/guides/quickview/variable_selection),
the viewport changes to a number of contour plots organized into rows and columns.
Each row represents a different variable, while each column represents a different comparison metric.
The following sections describe how to customize each.

## Rows of plots {#rows}

The rows in the viewport correspond to different physical quantities,
i.e., different variables from the simulation files.

- The variable names are shown in the upper-left corner of each row.
  The vertical bar along the left of each row uses the same color
  as the corresponding tab near the top of the
  [Variable Selection control panel](/guides/quickview/variable_selection#variable-groups),
  indicating the shape (dimension combination) of the current variable.

![Two-sim comparison: variable rows](/guides/quickcompare/screenshots/two-sim_variable_rows.png){ width="90%", align=center }

- Clicking a variable name opens a drop-down menu for replacing the current
  variable with another loaded variable.
  Only variables that have been selected and loaded using the
  [Variable Selection control panel](/guides/quickview/variable_selection)
  appear in the drop-down menu.

![Two-sim comparison: rearrange rows](/guides/quickcompare/screenshots/two-sim_rearrange_rows.png){ width="100%", align=center }

## Columns of plots {#columns}

The viewport can display up to five columns, corresponding to the following quantities:
  1. **Ctrl**: the variable from the control simulation;
  2. **Test**: the variable from the test simulation;
  3. **Diff**: the difference between the two simulations, using the control simulation as the reference, i.e. `test - ctrl`;
  4. **Rel Diff**: the relative difference with respect to the control simulation, i.e., `(test - ctrl)/ctrl`;
  5. **Sym Rel Diff**: the symmetric counterpart of **Rel Diff**, defined as `2(test - ctrl)/(test+ctrl)`.
     It normalizes the difference by the average of the control and test simulations
     and therefore treats the two simulations symmetrically.

By default, the first four quantities are displayed. Any of the five can be shown or hidden using the checkboxes
in the **Comparison columns** drop-down menu shown in the screenshot below.

![Two-sim comparison: choose metrics](/guides/quickcompare/screenshots/two-sim_choose_metrics.png){ width="100%", align=center }

The display order of the columns can be changed using the drop-down menus opened
by clicking the panel titles ("Ctrl", "Test", "Diff", etc.).
Any change in the column order is applied consistently to every row in the viewport.

![Two-sim comparison: rearrange columns](/guides/quickcompare/screenshots/two-sim_rearrange_columns.png){ width="100%", align=center }


## Color mapping

To facilitate quantitative comparisons between simulations, the two-simulation
mode in QuickCompare uses the following default color mapping choices:

- When both are displayed, the control and test variables share the same colormap
  and contour levels, allowing values to be compared directly by color.
- Difference and relative difference plots use diverging colormaps centered at zero.
- Difference and relative difference plots use different colormaps to
  distinguish signed (positive or negative) absolute differences from normalized (relative) differences.

Beyond these defaults, QuickCompare provides the same color-mapping
functionality as QuickView. Each plot in the viewport can be customized
individually through the dialogue window opened by clicking its colorbar, as
described in the
[QuickView user guide](/guides/quickview/individual_views).




QuickView has been developed using EAM's history output
on the physics grids (`pg2` grids) written by
EAMv2, v3, and an intermediate version towards v4 (EAMxx).
Those sample output files can be found on
[Zenodo](https://zenodo.org/records/16922607).

Developers and users of EAM often use tools like NCO and CDO
or write their own scripts to calculate time averages
and/or select a subset of variables from the original model output.
For those use cases, we clarify below the features of the data format
that QuickView expects in order to
properly read and visualize the simulation data.

!!! tip "Tip: Consistency Between Simulation File and Connecitivity File"

    One of the repeatedly encountered causes of error when loading files
    in QuickView
    is that the grid described by the connecitivity file does not match
    the grid in the simulation data file.
    If the `Load Files` button in the [toolbar](toolbar.md) has been clicked
    but the status icon continues to show a red circle with an exclamation mark
    after many seconds of time, the first thing we suggest
    checking is whether the two specified files correspond to the same grid.

!!! warning "Caution: Newer EAMxx Output Files"

    The EAMxx output file that QuickView has been tested for
    was generated in late 2024. As EAMxx further evolves and its output
    format changes, QuickView might need to be updated accordingly.
    If the user encounters such a case, we recommend reaching out to our lead developer
    [(abhi.yenpure@kitware.com)](https://www.kitware.com/abhishek-yenpure/)
    or using the [Issue tab on GitHub](https://github.com/ayenpure/QuickView/issues)
    to start a discussion.

----
## Overview 

The ParaView Reader behind the QuickView GUI detects and categorizes variables
based on their dimensions.
Variables with dimensions not matching the expected patterns are ignored.

----
## 2D variables

QuickView recognizes variables with—and only with—the
^^dimensions `time` and `ncol`^^ as 2D variables,
i.e., physical quantities varying with latitude and
longitude but without a vertical dimension.
These are referred to as "surface variables" in the
[control panel](control_panel.md).
For these variables, the only required ^^coordinate variable^^ is ^^`time`^^.
Grid information, including latitude and longitude, are obtained
from the [connecitivity file](connecitivity.md).

If an `area` variable with the dimension `ncol` is also present,
this variable is used for calculating the area-weighted horizontal averages
displayed in the [viewport](viewport.md).
If the `area` variable is not present, then an arithmetic average
is calculated and displayed.

----
## 3D variables

If a variables has not only `time` and `ncol` but also a vertical dimension,
QuickView expects the dimension to be named ^^`lev`^^ for variables defined at
layer midpoints and ^^`ilev`^^ for variables defined at layer interfaces.

For variables defined at layer midpoints, in order for the `Slice Selection`
section of the [control panel](control_panel.md) to work properly,
the simulation data
file needs to contain a 1D coordinate variable named `lev`,
the values of which are interpreted as pressure in hPa.
If `lev` is not present, QuickView attempts to find two 1D variables,
`hyam` and `hybm`, of that dimension size, from which QuickView calculates
`lev` using

```
lev = (hyam * P0) + (hybm * PS0)
```

where PS0 = 1000 hPa; P0 is read from the data file and set to 1000 hPa
if not found.

Similarly, for variables defined at layer interfaces, QuickView looks for
either `ilev` or `hyai` and `hybi` for parsing the vertical dimension.


----
## Variable with more dimensions 

QuickView currently only visualizes the variables types discussed above.
For variables that have extra dimensions in addition to `time`, `ncol`,
and `lev` or `ilev`, for example aggregated tracer arrays or
[COSP](https://climatedataguide.ucar.edu/climate-data/cosp-cloud-feedback-model-intercomparison-project-cfmip-observation-simulator-package)-related variables,
support can be provided if there is sufficient
interest from the users. Please contact our lead developer
[(abhi.yenpure@kitware.com)](https://www.kitware.com/abhishek-yenpure/)
for a discussion.


----
## Missing values

If a variable has an attribute named `missing_value` or `_FillValue`,
the value is converted to NaN and ignored
in the calculation of global averages and for the visualization.


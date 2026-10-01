# Simulation Files 

The QuickView family of tools has been developed using simulation files
from the E3SM Atmosphere Model, EAM, and the land model ELM.
A small collection of sample files can be found on
[Zenodo](https://zenodo.org/records/16922607).

## The horizontal dimension 

Starting from QuickView version 2 and QuickCompare version 1,
the data reader used in the tool family
has been generalized to handle all NetCDF
variables on cubed-sphere meshes regardless of what name is used
for the horizontal dimension (e.g., `ncol` and `ncol_d` in EAM files and
`lndgrid` in ELM files).

## Multi-dimensional variables {#nd-vars}

Starting from QuickView version 2 and QuickCompare version 1,
the tool family has been generalized to visualize any variable
in a NetCDF file that has a horizontal dimension matching the connectivity file,
regardless of how many additional dimensions the variables have.

Here are some examples of variable dimensions (array shapes) from EAM output files:

- `(ncol)`
- `(time,lev,ncol)`
- `(time,cosp_prs,cosp_tau,ncol)`
- `(time,ncol,swband,lev)`
- `(time,ncol,num_phys_constituents)`
- `(time,ncol_d,lev)`

And here are some examples of variable dimensions (array shapes) from ELM output files:

- `(levgrnd,lndgrid)`
- `(levlak,lndgrid)`
- `(time,lndgrid)`
- `(time,levgrnd,lndgrid)`
- `(time,natpft,lndgrid)`

## Global averages

When an `area` variable with the correct horizontal dimension is present
in the simulation file, this variable
is used for calculating the area-weighted horizontal averages displayed in the
viewport. If the `area` variable is not present, then an arithmetic average is
calculated and displayed.

## Missing values

When a variable has an attribute named `missing_value` or `_FillValue`, the value
is converted to NaN and ignored in the calculation of global averages and for
the visualization.


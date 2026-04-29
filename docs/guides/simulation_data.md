# Simulation Files 

The QuickView family of tools has been developed using history output
on the physics grids (`pg2` grids) of the E3SM Atmosphere Model, EAM,
generated using EAMv2, v3, and intermediate versions towards v4
(EAMxx). Some sample output files can be found on
[Zenodo](https://zenodo.org/records/16922607).

## The horizontal dimension 

Starting from QuickView version 2 and QuickCompare version 1,
the ParaView Reader used in the tool family
has been generalized to handle all NetCDF
variables on `ne*pg2` cubed-sphere meshes regardless of what name is used
for the horizontal dimension (e.g., `ncol` in EAM files or
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


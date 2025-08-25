# Connectivity files


!!! tip inline end "Tip: Connecitivity File Download"

    A collection of connectivity files can be found on
    [Zenodo](https://doi.org/10.5281/zenodo.16908566).
    The archive is continually updated as more users inform us
    about the grids their data files use.

The horizontal grids used by EAM are cubed spheres. Since these are unstructed
grids, QuickView needs to know how to map data to the globe. Therefore,
for each simulation data file, a "connectivity file" needs to be provided.

In EAMv2, v3, and v4, most of the variables (physical quantities) are
written out on a "physics grid" (also referred to as "physgrid", "FV grid",
or "control volume mesh") described in
[Hannah et al. (2021)](https://doi.org/10.1029/2020MS002419).
The naming convention for such grids is `ne*pg2`, with `*` being a number,
e.g., 4, 30, 120, 256. Further details about EAM's cubed-sphere grids
can be found in EAM's documention, for example in
[this overview](https://e3sm.atlassian.net/wiki/spaces/DOC/pages/34113147/SE+Atmosphere+Grid+Overview+EAM+CAM)
and [this description](https://e3sm.atlassian.net/wiki/spaces/DOC/pages/872579110/Running+E3SM+on+New+Atmosphere+Grids).

Future versions of QuickView will also support the cubed-sphere meshes
used by EAM's dynamical core, i.e., the `ne*np4` grids
(also referred to as "native grids" or "GLL grids").

## Generate connectivity files

Users can generate connectivity files with 
[`TempestRemap`](https://github.com/ClimateGlobalChange/tempestremap)
([Ullrich and Taylor, 2015](https://doi.org/10.1175/MWR-D-14-00343.1);
[Ullrich et al., 2016](https://doi.org/10.1175/MWR-D-15-0301.1)) 
using [this script](https://github.com/mt5555/remap-ncl/blob/master/makeSE.sh)
shared by Mark A. Taylor at Sandia National Laboratories.
(`TempestRemap` 
is available as a part of the [`E3SM-Unified`](https://github.com/E3SM-Project/e3sm-unified) conda environment.
It can also be installed following the instructions provided in its
[repo](https://github.com/ClimateGlobalChange/tempestremap).)

For example, using Mark's script, the command

```
./makeSE.sh 30
```

will generate serveral different files for the `ne30pg2` grid, including, e.g.,

- `TEMEPST_NE30pg2.g`  (Exodus format),
- `TEMPEST_ne30pg2.scrip.nc` (SCRIP format).


EAM QuickView uses the ^^SCRIP^^ format.


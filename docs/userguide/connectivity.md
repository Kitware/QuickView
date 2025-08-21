# Connectivity files


## Background

The horizontal grids used by EAM are cubed spheres. Since these are unstructed
grids, the QuickView app needs to know how to map data to the globe. Therefore,
for each simulation data file, a "connectivity file" needs to be provided.

In EAMv2, v3, and v4, most of the variables (physical quantities) are archived
on the "physics grid" described in
[Hannah et al. (2021)](https://doi.org/10.1029/2020MS002419).
The naming convention for such grids is `neXpg2`, with `X` being a number,
typically 4, 30, or 120. Further details about EAM's cubed-sphere grids
can be found in EAM's documention, for example in
[this overview](https://e3sm.atlassian.net/wiki/spaces/DOC/pages/34113147/SE+Atmosphere+Grid+Overview+EAM+CAM)
and [this description](https://e3sm.atlassian.net/wiki/spaces/DOC/pages/872579110/Running+E3SM+on+New+Atmosphere+Grids).

## Download

A collection of connectivity files can be found on [Zenodo](https://doi.org/10.5281/zenodo.16908567).

## Generation

Users can also generate connectivity files with 
[`TempestRemap`](https://github.com/ClimateGlobalChange/tempestremap) (
[Ullrich and Taylor, 2015](https://doi.org/10.1175/MWR-D-14-00343.1);
[Ullrich et al., 2016](https://doi.org/10.1175/MWR-D-15-0301.1)) 
using commands documented [here](https://e3sm.atlassian.net/wiki/spaces/DOC/pages/872579110/Running+E3SM+on+New+Atmosphere+Grids#2A.-Generate-control-volume-mesh-files-for-E3SM-v2-%22pg2%22-grids).
`TempestRemap` it is available as a part of the
[`E3SM-Unified`](https://github.com/E3SM-Project/e3sm-unified) conda environment;
it can also be installed following the instructions from the
[TempestRemap repo](https://github.com/ClimateGlobalChange/tempestremap).

EAM QuickView uses the SCRIP format of the connectivity files.

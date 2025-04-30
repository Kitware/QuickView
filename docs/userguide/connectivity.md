
# Connectivity files


The horizontal grids used by EAM are cubed spheres. Since these are unstructed grids, EAM QuickView needs to know how to map data to the globe. Therefore, each time the app is launched, a "connectivity file" needs to be provided together with the simulation data file.

In EAMv2, v3, and v4, most of the variables (physical quantities) are archived on the "physics grid" described in [Hannah et al. (2021)](https://doi.org/10.1029/2020MS002419). The naming convention for such grids is `neXpg2`, with `X` being a number, typically 4, 30, or 120.

*Hui's note from 4/29/2025: I am inclined to NOT include connectivity files in our repo or binary. How should we provide them, then? If we will be distributing binaries, then I imagine we could provide connectivity files from that web page. A related note: the script I used for generating those files was from Mark Taylor. I think we should ask him how he wants to be credited for that. One option could be including here the instructions he gave me together with a link to his script (see below), but would he be interested in involved in our work in some way? I can ask him.*

A collection of connectivity files can be downloaded from [here (where?)]().

Users can also generate connectivity files with the [`TempestRemap`](https://github.com/ClimateGlobalChange/tempestremap) tool using [this script](https://github.com/mt5555/remap-ncl/blob/master/makeSE.sh) shared by Mark A. Taylor at Sandia National Laboratories. (`TempestRemap` can be installed following the instructions at [https://github.com/ClimateGlobalChange/tempestremap](https://github.com/ClimateGlobalChange/tempestremap), and it is also available as a part of the [`E3SM-Unified`](https://github.com/E3SM-Project/e3sm-unified) conda environment.)


For example, the command

```
./makeSE.sh 30
```

will generate serveral different files for the `ne30pg2` grid, including, e.g.,

- `TEMEPST_NE30pg2.g`  (Exodus format),
- `TEMPEST_ne30pg2.scrip.nc` (SCRIP format).

EAM QuickView uses the SCRIP format.

## References

Hannah, W. M., Bradley, A. M., Guba, O., Tang, Q., Golaz, J.-C., & Wolfe, J. (2021). Separating physics and dynamics grids for improved computational efficiency in spectral element earth system models. Journal of Advances in Modeling Earth Systems, 13, e2020MS002419. [https://doi.org/10.1029/2020MS002419](https://doi.org/10.1029/2020MS002419)

Paul A. Ullrich and Mark A. Taylor, 2015: Arbitrary-Order Conservative and Consistent Remapping and a Theory of Linear Maps: Part 1. Mon. Wea. Rev., 143, 2419–2440, [doi:10.1175/MWR-D-14-00343.1](https://doi.org/10.1175/MWR-D-14-00343.1)

Paul A. Ullrich, Darshi Devendran and Hans Johansen, 2016: Arbitrary-Order Conservative and Consistent Remapping and a Theory of Linear Maps, Part 2. Mon. Wea. Rev., 144, 1529-1549, [doi:10.1175/MWR-D-15-0301.1](https://doi.org/10.1175/MWR-D-15-0301.1)



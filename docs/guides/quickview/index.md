# What is QuickView?

**QuickView** is an open-source, interactive visualization
tool designed to help Earth system modelers take a quick look at
a collection of physical quantities in their simulation files.
The physical quantities are presented in the form of global or regional maps.
Currently, QuickView supports only the cubed-sphere "physics" grids,
i.e., the ne\*pg2 meshes used by the atmosphere component of the
[Energy Exascale Earth System Model (E3SM)](https://e3sm.org),
but extensions to other grids are underway.
QuickView's Python- and
[trame](https://www.kitware.com/trame/)-based User Interface (UI)
provides intuitive access to [ParaView](https://www.paraview.org/)'s powerful
analysis and visualization capabilities without requiring a steep learning curve.

## Useful links: see [Quickstart](./quickstart).

## Why QuickView?

While comprehensive visualization tools like
[ParaView](https://www.paraview.org/) and
[VisIt](https://visit-dav.github.io/visit-website/index.html) are widely used in
the scientific community, they often have very steep learning curves—requiring
users who are not experts in visual analytics to navigate unfamiliar interfaces,
functions, and jargon. Moreover, these general-purpose tools may lack
out-of-the-box support for key requirements in atmospheric sciences, such as
globe and map projections or support for specific data formats and structures,
leading to time-consuming customization or feature requests. QuickView was
developed to address these limitations by offering a focused, user-friendly
platform that streamlines the analysis of atmospheric simulations. It minimizes
the need for E3SM developers and users to write custom scripts, thereby
shortening the path from data to insight.

The primary goal of QuickView is a first glance at the contents in a simulation
data file, i.e., a first inspection of the characteristic values of physical
quantities and their variations with respect to geographical location, altitude,
and time, as well as a quick inspection across different physical quantities for
similarities or distinctions. Compared to earlier and widely used tools like
[ncview](https://cirrus.ucsd.edu/ncview/) and
[ncvis](https://github.com/SEATStandards/ncvis), QuickView has an emphasis on
multivariate visualization and is currently focused on E3SM.

## Key Features

- Intuitive, minimalist interface tailored for Earth system modeling.
- Multi-variable visualization.
- Persistent sessions—pick up where you left off.
- Support for EAM v2, v3, and upcoming v4 output formats
  as well as the E3SM land model ELM's input and output files
  on ne*pg2 grids.

## Project Background

The lead developer of QuickView version 2 is
[Sebastien Jourdain](https://www.kitware.com/sebastien-jourdain/)
at [Kitware](https://www.kitware.com/).
Other key contributors include
Berk Geveci, Dan Lipsa, Patrick O'Leary and Will Dunklin at [Kitware](https://www.kitware.com/)
and
Hui Wan and Kai Zhang at
[Pacific Northwest National Laboratory](https://www.pnnl.gov/atmospheric-climate-and-earth-sciences-division).

QuickView is a product of an interdisciplinary collaboration supported by
the U.S. Department of Energy Office of Science’s
[Advanced Scientific Computing Research (ASCR)](https://www.energy.gov/science/ascr/advanced-scientific-computing-research)
and
[Biological and Environmental Research (BER)](https://www.energy.gov/science/ber/biological-and-environmental-research)
via the
[Scientific Discovery through Advanced Computing (SciDAC](https://www.scidac.gov/))
program.

The development of QuickView used resources of the National Energy Research Scientific Computing Center
([NERSC](https://www.nersc.gov/)), a U.S. Department of Energy User Facility.

![SciDAC, Kitware, and PNNL](/logos/SciDAC-Kitware-PNNL.png){ width="75%", align=center }

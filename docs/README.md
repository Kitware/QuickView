# QuickView Homepage


![eam-quickview-full](../images/eam-quickview-full.png)


## What is QuickView?

!!! info inline end "Useful links"

    - [Repository](https://github.com/ayenpure/QuickView) on GitHub
    - [Releases](https://github.com/ayenpure/QuickView/releases)
    - [Documentation](https://quickview.readthedocs.io/en/latest/)
    - [Quick start](https://github.com/ayenpure/QuickView?tab=readme-ov-file#quick-start)
    - [Connecitivity file download](https://zenodo.org/records/16908567)
    - [Sample data download](https://zenodo.org/records/16922608)


**EAM QuickView** is an open-source, interactive visualization tool
tailored for scientists working with the atmospheric component of the 
[Energy Exascale Earth System Model (E3SM)](https://e3sm.org/),
the E3SM Atmosphere Model (EAM).
The Graphical User Interface (GUI) built with Python and
powered by [Trame](https://www.kitware.com/trame/) gives users an intuitive
access to the powerful analysis and visualization capabilities of
[ParaView](https://www.paraview.org/)
without requiring a steep learning curve.

## Why QuickView?

While comprehensive visualization tools like
[ParaView](https://www.paraview.org/) and
[VisIt](https://visit-dav.github.io/visit-website/index.html) are widely used in
the scientific community, they often present a steep learning curve—requiring
users who are not experts in visual analytics
to navigate unfamiliar interfaces, functions, and jargon. Moreover, these
general-purpose tools may lack out-of-the-box support for key requirements in
atmospheric sciences, such as globe and map projections or support for specific
data formats and structures, leading to time-consuming customization or feature
requests. EAM QuickView was developed to address these limitations by offering a
focused, user-friendly platform that streamlines the analysis of atmospheric
simulations. It minimizes the need for EAM developers and users to write custom
scripts, thereby shortening the path from data to insight.

The core goal of EAM QuickView is a first glance at the contents in a simulation
data file, i.e., a first inspection of the characteristic values of
physical quantities and their variations
with respect to geographical location, altitude, and time,
as well as a quick inspection across different physical quantities
for similarities or distinctions.
Compared to earlier and widely used tools like
[ncview](https://cirrus.ucsd.edu/ncview/) and
[ncvis](https://github.com/SEATStandards/ncvis), QuickView has an emphasis on
multivariate visualization and is currently focused on the EAM model.

## Key Features

- Intuitive, minimalist user interface tailored for atmosphere modeling workflows.
- Push-button visualization of multiple variables.
- Persistent state: "Pick up where you left off".
- Support for EAM simulation data from current (EAMv2, v3) and upcoming (v4)
  versions.

## Bug reports and feature requests

Please use the [Issues tab on GitHub](https://github.com/ayenpure/QuickView/issues).

## Points of Contact

The lead developer of EAM QuickView is
[Abhishek Yenpure (abhi.yenpure@kitware.com)](https://www.kitware.com/abhishek-yenpure/)
at [Kitware, Inc.](https://www.kitware.com/). Other key contributors at Kitware, Inc.
include Berk Geveci and Sebastien Jourdain.
Key contributors on the atmospheric science side are Hui Wan and Kai Zhang at
[Pacific Northwest National Laboratory](https://www.pnnl.gov/atmospheric-climate-and-earth-sciences-division).

EAM QuickView is a product of an interdisciplinary collaboration supported by
the U.S. Department of Energy Office of Science’s
[Advanced Scientific Computing Research (ASCR)](https://www.energy.gov/science/ascr/advanced-scientific-computing-research)
and
[Biological and Environmental Research (BER)](https://www.energy.gov/science/ber/biological-and-environmental-research)
via the
[Scientific Discovery through Advanced Computing (SciDAC](https://www.scidac.gov/))
program.

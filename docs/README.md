# QuickView Homepage

![eam-quickview-full](../images/eam-quickview-full.png)

## What is QuickView?


**EAM QuickView** is an interactive visualization tool
tailored for scientists working with the atmospheric component of the 
[Energy Exascale Earth System Model](https://e3sm.org/) (EAM,
[Rasch et al., 2019](https://doi.org/10.1029/2019MS001629);
[Golaz et al., 2022](https://doi.org/10.1029/2022MS003156); 
[Donahue et al., 2024](10.1029/2024MS004314)).
The Graphical User Interface (GUI) built with Python and
powered by [Trame](https://www.kitware.com/trame/) 
gives users intuitive access to the powerful visualization capabilities of
[ParaView](https://www.paraview.org/)
without requiring a steep learning curve.

## Why QuickView?

While comprehensive tools like [ParaView](https://www.paraview.org/) and
[VisIt](https://visit-dav.github.io/visit-website/index.html) are widely used in
the scientific community, they often present a steep learning curve—requiring
users to navigate unfamiliar interfaces, functions, and jargon. Moreover, these
general-purpose tools may lack out-of-the-box support for key requirements in
atmospheric science, such as globe and map projections or support for specific
data formats and structures, leading to time-consuming customization or feature
requests. EAM QuickView was developed to address these limitations by offering a
focused, user-friendly platform that streamlines the analysis of atmospheric
simulations. It minimizes the need for EAM developers and users to write custom
scripts, thereby reducing “last-mile” effort and accelerating the path from data
to insight.

The core goal of EAM QuickView is a first glance at the contents in a simulation
data file—the characteristic values of physical quantities and their variations
with respect to geographical location, altitude, and time, a capability that is
especially valuable for tasks such as simulation/model verification, validation,
and qualitative data exploration. Compared to earlier and widely used tools like
[ncview](https://cirrus.ucsd.edu/ncview/) and
[ncvis](https://github.com/SEATStandards/ncvis), QuickView has an emphasis on
multivariate visualization and is currently focused on the EAM model.

## Key Features

- Minimalist user interface tailored for atmosphere modeling workflows.
- Push-button visualization of multiple variables.
- Persistent state: "Pick up where you left off".
- Supports EAM simulation data from current (EAMv2, v3) and upcoming (v4)
  versions.

## Further Reading

EAM QuickView leverages [ParaView](https://www.paraview.org/) for backend data
processing and [trame](https://kitware.github.io/trame/) for an intuitive,
browser-based user interface.

To learn more about the installation of EAM QuickView, checkout the
[installation guide](setup/requirements.md)

To learn more about using EAM QuickView, checkout the
[brief overview.](tutorials/eamapp.md)

For information about data file requirements and supported formats, see the
[data requirements documentation](data-requirements.md)

## Point of Contact

The lead developer of EAM QuickView is
[Abhishek Yenpure (abhi.yenpure@kitware.com)](https://www.kitware.com/abhishek-yenpure/)
at [Kitware, Inc.](https://www.kitware.com/). Other key contributors at Kitware, Inc. include [Berk Geveci](https://www.kitware.com/berk-geveci/) and [Sebastien Jourdain](https://www.kitware.com/sebastien-jourdain/). Key contributors on the atmospheric science side are Hui Wan and Kai Zhang at [Pacific Northwest National Laboratory](https://www.pnnl.gov/atmospheric-climate-and-earth-sciences-division).

EAM QuickView is a product of an interdisciplinary collaboration supported by
the U.S. Department of Energy Office of Science’s
[Advanced Scientific Computing Research (ASCR)](https://www.energy.gov/science/ascr/advanced-scientific-computing-research)
and
[Biological and Environmental Research (BER)](https://www.energy.gov/science/ber/biological-and-environmental-research)
via the
[Scientific Discovery through Advanced Computing (SciDAC](https://www.scidac.gov/))
program.

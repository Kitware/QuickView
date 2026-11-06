# What is QuickView?

![QuickView icon](/public/logos/quickview-icon-only.png){ width="12%", align=right }

**QuickView** is an open-source, interactive visualization
tool designed to help Earth system modelers take a quick look at
a collection of physical quantities in their simulation files.
The physical quantities are presented in the form of contour plots on global or regional maps.
Currently, QuickView supports cubed-sphere grids
consisting of either Gauss-Lobatto-Legendre (GLL) nodes (i.e., the `ne*np4` grids)
or finite-volume grid cells (`ne*pg2`, `ne*pg3`, etc.).

Under the hood, [ParaView](https://www.paraview.org/) and
[VTK](https://vtk.org/) supply the data-processing and graphics capabilities,
while [trame](https://www.kitware.com/trame/), a Python package,
is used to build a browser-based graphical User Interface (UI)
to provide intuitive and task-focused controls of the visualization
so that users do not need to operate ParaView or VTK themselves.

Under the hood, [ParaView](https://www.paraview.org/) and
[VTK](https://vtk.org/) supply the data-processing and graphics capabilities,
while [trame](https://www.kitware.com/trame/), a Python framework for
interactive applications, connects these capabilities to a browser-based
graphical user interface. Trame provides the interface controls,
communicates user selections to the visualization code,
and delivers updated images to the display.
Together, these tools let QuickView provide intuitive, task-focused controls
for exploring model output without requiring users to operate ParaView or VTK themselves.

Useful resources: see [linked page](./getting_started).

## Why QuickView?

While comprehensive visualization tools like
[ParaView](https://www.paraview.org/) and
[VisIt](https://visit-dav.github.io/visit-website/index.html) are widely used in
the scientific community, they often have very steep learning curves—requiring
users who are not experts in visual analytics to navigate unfamiliar interfaces,
functions, and jargon. Moreover, these general-purpose tools may lack
out-of-the-box support for key requirements in Earth system sciences, such as
globe and map projections or support for specific data formats and structures,
leading to time-consuming customization. QuickView was
developed to address these limitations by offering a focused, user-friendly
platform that streamlines the analysis of atmospheric simulations. It minimizes
the need for the model developers and users to write custom scripts, thereby
shortening the path from data to insight.

The primary goal of QuickView is a first glance at the contents in a simulation
data file, i.e., a first inspection of the characteristic values of physical
quantities and their variations with respect to geographical location, altitude,
and time, as well as a quick inspection across different physical quantities for
similarities or distinctions. Compared to earlier and widely used tools like
[ncview](https://cirrus.ucsd.edu/ncview/) and
[ncvis](https://github.com/SEATStandards/ncvis), QuickView has an emphasis on
multivariate visualization.

## Key Features

- Intuitive, minimalist interface tailored for Earth system modeling.
- Multi-variable visualization.
- Persistent sessions—pick up where you left off.
- Currently supporting cubed-sphere grids in a variety of configurations
  and representations. Examples can be found in the [visualization gallery](/gallery/index).

## Project Background

The lead developer of QuickView version 1 was Abhishek Yenpure.
The lead developer from version 2 onwards is
[Sebastien Jourdain](https://www.kitware.com/sebastien-jourdain/).
Other key contributors include
Patrick O'Leary, Berk Geveci, Dan Lipsa, and Will Dunklin at
[Kitware](https://www.kitware.com/), and
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

----

![SciDAC, Kitware, and PNNL](/logos/SciDAC-Kitware-PNNL.png){ width="55%", align=center }

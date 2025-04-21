# EAM QuickView

![eam-quickview-full](../images/eam-quickview-full.png)

## Overview

EAM QuickView is an open-source, Python-based application for interactive visual analysis of atmospheric data produced by E3SM/EAM simulations.

While comprehensive tools like ParaView and VisIt are widely used in the scientific community, they often present a steep learning curve—requiring users to navigate unfamiliar interfaces, functions, and jargon. Moreover, these general-purpose tools may lack out-of-the-box support for key requirements in atmospheric science, such as globe and map projections or support for novel data formats, leading to time-consuming customization or feature requests.
EAM QuickView was developed to address these limitations by offering a focused, user-friendly platform that streamlines the analysis of atmospheric simulations. It minimizes the need for domain scientists to write custom scripts, thereby reducing “last-mile” effort and accelerating the path from data to insight.

The core goal of QuickView is multivariate exploration—enabling users to visualize and compare multiple variables simultaneously. This capability is especially valuable for tasks such as simulation/model verification, validation, and qualitative data exploration.

QuickView leverages ParaView for backend visualization and Trame for an intuitive, browser-based user interface.

To learn more about the installation of QuickView checkout the [installation guide](setup/requirements.md)

To learn more about using QuickView, checkout the [brief overview.](tutorials/eamapp.md)

## Key Features

- Clean and minimalist UI tailored for atmospheric science workflows

- Push-button comparison of multiple variables

- Persistent state: "Pick up where you left off"

- Supports EAM atmospheric model data from current (E3SMv2, v3) and upcoming (v4) versions


# QuickView

[![Test](https://github.com/Kitware/QuickView/actions/workflows/test.yml/badge.svg)](https://github.com/Kitware/QuickView/actions/workflows/test.yml)
[![Release](https://github.com/Kitware/QuickView/actions/workflows/release.yml/badge.svg)](https://github.com/Kitware/QuickView/actions/workflows/release.yml)
[![Package](https://github.com/Kitware/QuickView/actions/workflows/package.yml/badge.svg)](https://github.com/Kitware/QuickView/actions/workflows/package.yml)
![PyPI](https://img.shields.io/pypi/v/e3sm-quickview?label=pypi%20package)
[![Conda Version](https://img.shields.io/conda/vn/conda-forge/e3sm-quickview.svg)](https://anaconda.org/conda-forge/e3sm-quickview)

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


![Application](https://raw.githubusercontent.com/Kitware/QuickView/master/QuickView-app.png)

## Key Features

- Intuitive, minimalist interface tailored for Earth system modeling.
- Multi-variable visualization.
- Persistent sessions—pick up where you left off.
- Support for EAM v2, v3, and upcoming v4 output formats
  as well as the E3SM land model ELM's input and output files
  on ne*pg2 grids.

## Quick Start

See [documentation page](https://kitware.github.io/QuickView/guides/quickview/quickstart.html).

## Project Background

QuickView is developed by [Kitware, Inc.](https://www.kitware.com/) in
collaboration with
[Pacific Northwest National Laboratory](https://www.pnnl.gov/), supported by the
U.S. Department of Energy's
[ASCR](https://www.energy.gov/science/ascr/advanced-scientific-computing-research)
and
[BER](https://www.energy.gov/science/ber/biological-and-environmental-research)
programs via [SciDAC](https://www.scidac.gov/).

### Contributors

- **Lead Developer**: Abhishek Yenpure (now at NVIDIA) for version 1; [Sebastien Jourdain](https://www.kitware.com/sebastien-jourdain/) ([Kitware, Inc.](https://www.kitware.com/)) from version 2 onwards.
- **Key Contributors**: Berk Geveci, Patrick O'Leary, Dan Lipsa, Will Dunklin (Kitware, Inc.); Hui Wan, Kai Zhang (PNNL)

## License

Apache Software License - see [LICENSE](LICENSE) file for details.

## Commit message convention

Semantic release rely on
[conventional commits](https://www.conventionalcommits.org/) to generate new
releases and changelog.

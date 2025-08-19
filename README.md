# QuickView

[![Test](https://github.com/ayenpure/QuickView/actions/workflows/test.yml/badge.svg)](https://github.com/ayenpure/QuickView/actions/workflows/test.yml)
[![Package and Release](https://github.com/ayenpure/QuickView/actions/workflows/package-and-release.yml/badge.svg)](https://github.com/ayenpure/QuickView/actions/workflows/package-and-release.yml)

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

## Key Features

- Intuitive, minimalist interface tailored for atmospheric modeling
- Multi-variable visualization with drag-and-drop layout
- Persistent sessions - pick up where you left off
- Support for EAM v2, v3, and upcoming v4 data formats

## Quick Start

- Install and launch for [end users](docs/setup/for_end_users.md)
  and [app developers](docs/setup/for_app_developers.md)
- Download sample simulation output and connectivity files from
  [Zenodo](https://zenodo.org/records/16895849)

## Documentation

- **[Installation Guide](docs/setup/requirements.md)** - Detailed setup
  instructions
- **[User Guide](docs/userguide/launch.md)** - How to use QuickView
- **[Data Requirements](docs/data-requirements.md)** - NetCDF file format
  specifications
- **[Control Panel Reference](docs/userguide/control_panel.md)** - UI components
  and features

## About

QuickView is developed by [Kitware, Inc.](https://www.kitware.com/) in
collaboration with
[Pacific Northwest National Laboratory](https://www.pnnl.gov/), supported by the
U.S. Department of Energy's
[ASCR](https://www.energy.gov/science/ascr/advanced-scientific-computing-research)
and
[BER](https://www.energy.gov/science/ber/biological-and-environmental-research)
programs via [SciDAC](https://www.scidac.gov/).

### Contributors

- **Lead Developer**: Abhishek Yenpure (Kitware, Inc.)
- **Key Contributors**: Berk Geveci, Sebastien Jourdain (Kitware, Inc.); Hui
  Wan, Kai Zhang (PNNL)

## License

Apache Software License - see [LICENSE](LICENSE) file for details.

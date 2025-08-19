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

![quickview](docs/images/main.png)

## Quick Start

- [Installation and launch for end users](docs/setup/installation_for_end_users.md)
- [Installation and launch for app developers](docs/setup/installation_for_app_developers.md)

## Data

QuickView works with E3SM Atmosphere Model (EAM) output files in NetCDF format.
Sample data files and their corresponding connectivity files are available at
[Zenodo](https://zenodo.org/records/16895849).

### Data Files

QuickView supports EAM output files from different model versions:

- **EAM Version 2**: Standard atmospheric simulation outputs (e.g.,
  `EAMv2_ne30pg2_F2010.eam.h0.nc`)
- **EAM Version 4 (interim)**: Newer format outputs (e.g.,
  `EAMxx_ne4pg2_202407.nc`)

These files contain atmospheric variables such as temperature, pressure, wind
fields, and other model diagnostics on finite-volume physics grids.

### Connectivity Files

Each data file requires a corresponding connectivity file that describes the
horizontal grid structure:

- Connectivity files follow the naming pattern:
  `connectivity_{resolution}_TEMPEST.scrip.nc`
- These files are generated using TempestRemap and contain grid topology
  information
- **Important**: The connectivity file resolution must match the data file
  resolution for proper visualization

For example:

- Data file: `EAMv2_ne30pg2_F2010.eam.h0.nc`
- Connectivity file: `connectivity_ne30pg2_TEMPEST.scrip.nc`

Both files use the same `ne30pg2` grid resolution and must be loaded together
for the application to function correctly.

## Documentation

- **[Installation Guide](docs/setup/requirements.md)** - Detailed setup
  instructions
- **[User Guide](docs/userguide/launch.md)** - How to use QuickView
- **[Data Requirements](docs/data-requirements.md)** - NetCDF file format
  specifications
- **[Control Panel Reference](docs/userguide/control_panel.md)** - UI components
  and features

## Key Features

- Clean, minimalist interface tailored for atmospheric modeling
- Multi-variable visualization with drag-and-drop layout
- Geographic projections (Plate Carrée, Robinson, etc.)
- Persistent sessions - pick up where you left off
- Support for EAM v2, v3, and upcoming v4 data formats

## Development

### Python Development Installation

```bash
# Clone the repository
git clone https://github.com/ayenpure/QuickView.git
cd QuickView

# Set up conda environment
conda env create -f quickview-env.yml
conda activate quickview

# Install QuickView
pip install -e .
```

### Running from Source

```bash
python -m quickview.app --data /path/to/your/data.nc --conn /path/to/connectivity.nc

# Launch server only (no browser popup)
python --server -m quickview.app --data /path/to/your/data.nc --conn /path/to/connectivity.nc
```

The application starts a web server at `http://localhost:8080`

### Development Utilities

```bash
# Run linter
ruff check quickview/

# Run tests
python -m quickview.app --help

# Bump version
bumpversion patch
```

## About

QuickView is developed by [Kitware, Inc.](https://www.kitware.com/) in
collaboration with
[Pacific Northwest National Laboratory](https://www.pnnl.gov/), supported by the
U.S. Department of Energy's
[BER](https://www.energy.gov/science/ber/biological-and-environmental-research)
and
[ASCR](https://www.energy.gov/science/ascr/advanced-scientific-computing-research)
programs via [SciDAC](https://www.scidac.gov/).

### Contributors

- **Lead Developer**: Abhishek Yenpure (Kitware, Inc.)
- **Key Contributors**: Berk Geveci, Sebastien Jourdain (Kitware, Inc.); Hui
  Wan, Kai Zhang (PNNL)

## License

Apache Software License - see [LICENSE](LICENSE) file for details.

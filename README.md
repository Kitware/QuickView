# QuickView

[![Test](https://github.com/ayenpure/QuickView/actions/workflows/test.yml/badge.svg)](https://github.com/ayenpure/QuickView/actions/workflows/test.yml)
[![Package and Release](https://github.com/ayenpure/QuickView/actions/workflows/package-and-release.yml/badge.svg)](https://github.com/ayenpure/QuickView/actions/workflows/package-and-release.yml)

**QuickView** is an interactive visualization tool for atmospheric scientists working with E3SM (Energy Exascale Earth System Model) data. It provides an intuitive interface for exploring atmospheric simulation outputs without the steep learning curve of general-purpose visualization tools.

![quickview](docs/images/main.png)

## Quick Start

### Installation

Download the latest release from the [releases page](https://github.com/ayenpure/QuickView/releases):

- **macOS**: `QuickView-{version}.dmg` - Double-click to install
- **Linux**: Coming soon
- **Windows**: Coming soon

Pre-built binaries include all dependencies - no Python or ParaView required.

## Documentation

- **[Installation Guide](docs/setup/requirements.md)** - Detailed setup instructions
- **[User Guide](docs/userguide/launch.md)** - How to use QuickView
- **[Data Requirements](docs/data-requirements.md)** - NetCDF file format specifications
- **[Control Panel Reference](docs/userguide/control_panel.md)** - UI components and features

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

QuickView is developed by [Kitware, Inc.](https://www.kitware.com/) in collaboration with [Pacific Northwest National Laboratory](https://www.pnnl.gov/), supported by the U.S. Department of Energy's [BER](https://www.energy.gov/science/ber/biological-and-environmental-research) and [ASCR](https://www.energy.gov/science/ascr/advanced-scientific-computing-research) programs via [SciDAC](https://www.scidac.gov/).

### Contributors

- **Lead Developer**: Abhishek Yenpure (Kitware, Inc.)
- **Key Contributors**: Berk Geveci, Sebastien Jourdain (Kitware, Inc.); Hui Wan, Kai Zhang (PNNL)

## License

Apache Software License - see [LICENSE](LICENSE) file for details.
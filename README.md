# QuickView

[![Test](https://github.com/ayenpure/QuickView/actions/workflows/test.yml/badge.svg)](https://github.com/ayenpure/QuickView/actions/workflows/test.yml)
[![Package and Release](https://github.com/ayenpure/QuickView/actions/workflows/package-and-release.yml/badge.svg)](https://github.com/ayenpure/QuickView/actions/workflows/package-and-release.yml)

**QuickView** is an interactive visualization tool designed specifically for
atmospheric scientists working with E3SM (Energy Exascale Earth System Model)
data. Built on ParaView and Trame, it provides an intuitive interface for
exploring atmospheric simulation outputs without the steep learning curve of
general-purpose visualization tools.

![quickview](docs/images/main.png)

## Why QuickView?

Traditional visualization tools like ParaView and VisIt, while powerful, often
require significant time investment to master their complex interfaces and may
lack atmospheric science-specific features out of the box. QuickView addresses
these challenges by:

- **Reducing the learning curve** - Atmospheric scientists can start visualizing
  their data immediately
- **Eliminating "last-mile" effort** - No need to write custom scripts or
  plugins for common tasks
- **Accelerating insights** - Focus on science, not software configuration
- **Building on proven technology** - Leverages ParaView's robust data
  processing with a tailored interface

## Installation

### Using Conda (Recommended)

1. Create and activate a conda environment:

```bash
conda env create -f quickview-env.yml
conda activate quickview
```

2. Install QuickView:

```bash
pip install .
```

### Requirements

- Python 3.13
- ParaView 5.13.3 (installed automatically with conda environment)
- Trame and other dependencies (installed automatically)

## Getting the Code

### Clone from GitHub

```bash
git clone https://github.com/ayenpure/QuickView.git
cd QuickView
```

### Download as Archive

```bash
wget https://github.com/ayenpure/QuickView/archive/main.tar.gz
tar -xvzf main.tar.gz
cd QuickView-main
```

## Running the Application

To run QuickView with a data file:

```bash
python -m quickview.app --data data/aerosol_F2010.eam.h0.2014-12.nc
```

### Command Line Options

- `--data`: Path to the NetCDF data file (required)
- `--conn`: Path to the connectivity file (optional)
- `--port`: Server port (default: 8080)
- `--host`: Server host (default: localhost)

### Example with Custom Files

```bash
python -m quickview.app --data /path/to/your/data.nc --conn /path/to/your/connectivity.nc
```

The application will start a Trame web server. Open your browser and navigate
to:

```
http://localhost:8080
```

## Sample Data

The repository includes sample data files in the `data/` directory for testing:

- `aerosol_F2010.eam.h0.2014-12.nc` - Sample atmospheric data
- Default connectivity file is automatically loaded

## Development

For development setup and contribution guidelines, please see
[CONTRIBUTING.md](CONTRIBUTING.md).

## Documentation

Comprehensive documentation is available in the [docs/](docs/) directory,
including:

- [User Guide](docs/userguide/launch.md) - Detailed usage instructions
- [Control Panel Guide](docs/userguide/control_panel.md) - Interface overview
- [Viewport Customization](docs/userguide/viewport.md) - Working with multiple
  variables

## About

QuickView is developed by [Kitware, Inc.](https://www.kitware.com/) in
collaboration with
[Pacific Northwest National Laboratory](https://www.pnnl.gov/). It is supported
by the U.S. Department of Energy's
[Biological and Environmental Research (BER)](https://www.energy.gov/science/ber/biological-and-environmental-research)
and
[Advanced Scientific Computing Research (ASCR)](https://www.energy.gov/science/ascr/advanced-scientific-computing-research)
programs via the
[Scientific Discovery through Advanced Computing (SciDAC)](https://www.scidac.gov/)
program.

### Contributors

- **Lead Developer**: Abhishek Yenpure (Kitware, Inc.)
- **Key Contributors**: Berk Geveci, Sebastien Jourdain (Kitware, Inc.); Hui
  Wan, Kai Zhang (PNNL)

## License

This project is licensed under the Apache Software License - see the
[LICENSE](LICENSE) file for details.

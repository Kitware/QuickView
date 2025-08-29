# Install and Launch for App Developers

At version 1.0, QuickView is expected to be installed and used from
a personal computer with the data files also being local.
Future versions will support the server-client model allowing access
to remote data.

Releases so far have focused on macOS. Support for
more systems will be added in the near [future](../future.md).

----
## Clone the repo

```
git clone https://github.com/ayenpure/QuickView.git
cd QuickView
```

----
## Install basic requirements

```
# Set up conda environment
conda env create -f quickview-env.yml
conda activate quickview

# Install QuickView
pip install -e .
```

----
## Launch the app from command line

To launch the EAM QuickView GUI in its dedicated window, use
```
python -m quickview.app --data /path/to/your/data.nc --conn /path/to/connectivity.nc
```

To launch server only (no browser popup), use
```
python --server -m quickview.app --data /path/to/your/data.nc --conn /path/to/connectivity.nc
```

----
## Development utilities

```
# Run linter
ruff check quickview/

# Run tests
python -m quickview.app --help

# Bump version
bumpversion patch
```

# Development setup

For Python development while you can use a mix of conda and pip install, it is generally not recommended. So we will provide 2 setups and it will be up to the user to choose what better match their usage.

## Conda setup

```sh
# Grab the code you aim to work with
git clone git@github.com:Kitware/QuickView.git
cd QuickView

# Set up conda environment
conda env create -f quickview-env.yml
conda activate quickview

# Install QuickView
pip install -e .
```

Then to run the application

```sh
quickview
```

## UV setup with Downloaded ParaView

This assume you already have ParaView installed on your system and that you've downloaded it from https://www.paraview.org/download/

For the current setup we will assume ParaView 6.2+.

```
# Grab the code you aim to work with
git clone git@github.com:Kitware/QuickView.git
cd QuickView

# Setup your python environment
uv venv -p 3.12 # force python version to match ParaView 6 Python version
uv sync --all-extras --dev

# Activate environment
source .venv/bin/activate

# Install commit analysis
pre-commit install
pre-commit install --hook-type commit-msg
```

Then to run the application, you will need ParaView. The example below provide an example for macOS.

```sh
/Applications/ParaView-6.2.1.app/Contents/bin/pvpython --venv .venv -m e3sm_quickview.app
```

With this setup, any commit will be automatically checked with the pre-commit hooks. But you can also run those manually via the command line below:

```sh
pre-commit run --all-files
```

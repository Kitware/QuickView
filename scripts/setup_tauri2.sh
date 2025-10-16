#!/bin/bash

set -e
set -x

pip install .

python -m PyInstaller --clean --noconfirm \
        --distpath src-tauri \
        --name server --hidden-import pkgutil \
        --collect-all trame \
        --collect-all trame_client \
        --collect-all trame_dataclass \
        --collect-all trame_vtk \
        --collect-all trame_vuetify \
        --collect-all trame_tauri \
        --collect-all pyproj \
        --collect-all netCDF4 \
        --collect-all paraview \
        --collect-all e3sm_quickview \
        --hidden-import pkgutil \
        --add-binary="$(which pvpython):."  \
        src/e3sm_quickview/app2.py

# Generate trame www + quickview
python -m trame.tools.www --output ./src-tauri/www
python -m trame.tools.www --output ./src-tauri/www e3sm_quickview.module

# Precompile install to speedup start (maybe?)
./src-tauri/server/server --timeout 1 --server

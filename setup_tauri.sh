#!/bin/bash

set -e
set -x

pip install .

python -m PyInstaller --clean --noconfirm \
        --distpath src-tauri \
        --name server --hidden-import pkgutil \
        --collect-all trame \
        --collect-all trame_client \
        --collect-all trame_components \
        --collect-all trame-grid-layout \
        --collect-all trame_vtk \
        --collect-all trame_vuetify \
        --collect-all pyproj \
        --collect-all netCDF4 \
        --collect-all paraview \
        --collect-all quickview \
        --hidden-import pkgutil \
        --add-binary="$(which pvpython):."  \
        quickview/app.py

python -m trame.tools.www --output ./src-tauri/www

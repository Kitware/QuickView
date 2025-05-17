#!/bin/bash

set -e
set -x

pip install .

python -m PyInstaller --clean --noconfirm \
        --distpath src-tauri \
        --name server --hidden-import pkgutil \
        --collect-data trame_vtk \
        --collect-data trame_client \
        --collect-data trame_vuetify \
        --collect-all paraview \
        --collect-all quickview \
        --hidden-import pkgutil \
        --add-binary="$(which pvpython):."  \
        quickview/app.py

python -m trame.tools.www --output ./src-tauri/www

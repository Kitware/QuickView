##Setting up conda environment

The dependencies for this trame app can be managed using Conda.
Following are the instructions to set up a Conda environment.

```
conda create --name eamapp python=3.10.0 ipython
conda activate eamapp
pip install --upgrade trame trame-vuetify trame-vtk trame-components trame-grid-layout pyproj netCDF4
conda install paraview
```

To clone this repository use the following commands
```
git clone https://gitlab.kitware.com/ayenpure/eamapp.git
cd eamapp
git lfs install
git lfs pull
```

To run the app, execute

```
pvpython --force-offscreen-rendering eamapp.py --server  --data data/aerosol_F2010.eam.h0.2014-12.nc
```

In the above execution the data file is provided as the sample data out of the repository.
The repository also contains the connectivity file that it uses by default.
If another connectivity and data files are to be used please specify the paths using the `--conn` and `--data` options.

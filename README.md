##Setting up conda environment

This trame application has two requirements.
1. Requires python version 3.10 on the system
Python can be installed using either `homebrew` or `apt`

2. Requires a ParaView 5.13 installed on the system
ParaView can be installed from the binaries found at https://www.paraview.org/download
  
The additional requirements for the app are satisfied once the app is launched for the very first time using Python virtual environments `venv`.
An additional step for the use is to provide the path to ParaView's Python client that is distributed with the ParaView binaries.
The `pvpython` binary is present in the `bin` directory of ParaView, on macOS the path is something like `/Applications/ParaView-5.13.0.app/Contents/bin/pvpython`

To clone this repository use the following commands

```
git clone https://gitlab.kitware.com/ayenpure/eamapp.git
cd eamapp
git lfs install
git lfs pull
```

To run the app, execute

```
python3 launch.py --data data/aerosol_F2010.eam.h0.2014-12.nc
```

In the above execution the data file is provided as the sample data out of the repository. The repository also contains the connectivity file that it uses by default.
If another connectivity and data files are to be used please specify the paths using the `--conn` and `--data` options.

The above command will start the Trame app server.
On the browser proceed to `http://localhost:8080` to use the app

## Setting up conda environment

This trame application has two requirements.
### Python version 3.10
Python can be installed using either `homebrew` if using macOS like

`brew install python3.10`

or `apt` if using Ubuntu Linux.

`sudo apt install python3.10`

Alternatively, python can also be installed using anaconda/miniconda

`
conda create --name eamapp python=3.10.0
conda activate eamapp
`

1However, this would require activating the conda environment before using the app.

### ParaView 5.13 installed on the system
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

Alternatively, the code can also be downloaded as a tarball

```
wget https://gitlab.kitware.com/ayenpure/eamapp/-/archive/master/eamapp-master.tar.gz
tar -xvzf eamapp-master.tar.gz
```

To run the app, execute

```
python3 launch.py --data data/aerosol_F2010.eam.h0.2014-12.nc
```

In the above execution the data file is provided as the sample data out of the repository. The repository also contains the connectivity file that it uses by default.
If another connectivity and data files are to be used please specify the paths using the `--conn` and `--data` options.

The above command will start the Trame app server.
On the browser proceed to `http://localhost:8080` to use the app

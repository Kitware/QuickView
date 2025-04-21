## Requirements 

EAM QuickView has two key requirements, python version `>=3.10` and ParaView `>=5.13`

### Python version 3.10

Python can be installed using either `homebrew` if using macOS like

```
brew install python3.10
```

or `apt` if using Ubuntu Linux.

```
sudo apt install python3.10
```

Alternatively, python can also be installed using anaconda/miniconda

```
conda create --name eamapp python=3.10.0
conda activate eamapp
```

However, this would require activating/deactivating the conda environment before/after using the application.

### ParaView 5.13 installed on the system
ParaView can be installed from the binaries found at https://www.paraview.org/download
  
The additional requirements for the app are satisfied once the app is launched for the very first time using Python virtual environments `venv`.
An additional step for the use is to provide the path to ParaView's Python client that is distributed with the ParaView binaries.
The `pvpython` binary is present in the `bin` directory of ParaView, on macOS the path is something like `/Applications/ParaView-5.13.0.app/Contents/bin/pvpython`

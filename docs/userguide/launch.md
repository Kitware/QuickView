# Launching the QuickView app

## Getting Data Files

Before launching QuickView, you'll need E3SM data files. Sample data files are
available at [Zenodo](https://zenodo.org/records/16895849). Each data file
requires a corresponding connectivity file with matching grid resolution. For
example:

- Data file: `EAMv2_ne30pg2_F2010.eam.h0.nc`
- Connectivity file: `connectivity_ne30pg2_TEMPEST.scrip.nc`

See the [Data Requirements](../data-requirements.md) documentation for detailed
information about file formats and available datasets.

## Usage

Following successful configuration of the application, i.e., satisfying the
python and ParaView requirement, the app can be launched in two ways.

1. Using the provided launch script which also takes care of all the
   dependencies.

```
python3 launch.py --data data/aerosol_F2010.eam.h0.2014-12.nc
```

2. Using the application executable with `pvpython`

```
/Applications/ParaView-5.13.1.app/Contents/bin/pvpython --force-offscreen-rendering eamapp.py --venv .pvenv --data aerosol_F2010.eam.h0.2014-12.nc
```

The application asks for four inputs

```
  -cf [CONN], --conn [CONN]
                        the netCDF file with connnectivity information
  -df DATA, --data DATA
                        the netCDF file with data/variables
  -sf [STATE], --state [STATE]
                        state file to be loaded
  -wd WORKDIR, --workdir WORKDIR
                        working directory (to store session data)
```

The following table provides additional information about the parameters and

| Param      | Description                                                                                                                                                                                                                                          |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| DATA/STATE | The application can either be initialized by providing a pair of connectivity and data file, or the state file containing the application configuration.                                                                                             |
| CONN       | By default the application contains a connectivity file in the `ne30pg2` resolution. If this is the resolution of the input data users need not provide the parameter. Additionally, the CONN parameter is not required is using the STATE parameter |
| WORKDIR    | An optional parameter to specify a working directory. By default, the application launch directory is used as a working directory                                                                                                                    |

## Components of QuickView

![eam-quickview-full-enum](../images/eam-quickview-full-enum.png)

The QuickView app has three main components, they are highlighted in the above
screen shot.

1. [Toolbar](toolbar.md) -- highlighted in green, let's the users control some
   global properties of the application and displays helpful information.

2. [Control Panel](control_panel.md) -- highlighted in red, let's the user
   control the data to represent, e.g. slicing or dicing the data to focus on
   certain regions/aspects of the data

3. [View Port(s)](view_port.md) -- highlighted in yellow, displays the data for
   the user, and control some properties for coloring and scalar mapping of the
   data.

# EAM QuickView Tutorial

## Usage

Following successful configuration of the application, i.e., satisfying the python
and ParaView requirement, the app can be launched in two ways.

1. Using the provided launch script which also takes care of all the dependencies.

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

| Param | Description |
| -- | -- |
| DATA/STATE |  The application can either be initialized by providing a pair of connectivity and data file, or the state file containing the application configuration. |
| CONN |  By default the application contains a connectivity file in the `ne30pg2` resolution. If this is the resolution of the input data users need not provide the parameter. Additionally, the CONN parameter is not required is using the STATE parameter |      
| WORKDIR | An optional parameter to specify a working directory. By default, the application launch directory is used as a working directory |                                                  

# Components EAM QucikView

## The Toolbar

![tool-bar](../images/tool-bar.png)

The toolbar is a means of presenting the user with global app controls, 
along with the display of some useful information.
Starting from the left and going to the right in the above image, the toolbar:

1. provides a button to show/hide the control panel for the application 
2. displays the information of the current version of the QuickView app 
3. contains a helpful widget to control the camera for the variables being currently explored -- by zooming in/out, and moving camera up/down or left/right.
4. contains the button used to load views with the current variable selection, this process does not happen interactively as the user selects/deselects variables to analyze.
5. contains some useful options for selecting color presets. 
6. displays data and connectivity file names and locations that are currently being used for analysis
7. provides a button to save the application configuration/state to the disk, which can be later imported.
8. provides a button to reset all the views at once.

## The Control Panel

![control-panel](../images/control-panel.png){ width="400" }

The control panel lets users control the context of visual analysis for the data, i.e,
it allows the users to select the time, middle and interface layers, and the variables for analysis, among other operations.
The panel can be divided into three main parts

1. **Data Slice Selection**
    The data slice selection allows users to slice and dice data spatio-temporally for analysis
    - a. It allows data slice selection along the dimensions of time, middle and interface layer.
    - b. It allows users to control the geo-spatial region by controlling the longitude, latitude ranges.
   
    Users can interactively select the data slice by interacting with the sliders, or using the media buttons to skip-previous, skip-next, or play an animation.

2. **Map Projection Selection**
    The map projection selection allows users to chose different representation of the data.
    Currently, it allows for Cylindrical-Equidistant, Robinson, and Mollweide projections.
    In the future, additional features are planned, e.g. selection of center meridian. 

3. **Variable Selections**

    ![variable-select](../images/variable-select.png){ width="400" }

    The variable selections allow users to control variables of interest for analysis.
    The variables are separated into three types -- the 2D (surface) variables, middle layer variables, and interface layer variables.
    Users can select and unselect the variables and to render the views, click the `Load Variables` button located in the tool bar.
    The reason for not making the views appear dynamically post variable selections is to allow for stable and better application behavior. 

## Views

Once the user has selected the necessary variables for their analysis and used the `Load Variables` button, the QuickView app will create a view for every variable. Each view would look like the once below. 

![view-collapsed](../images/view-collapsed.png){ width="400" }

The view, apart from showing the ParaView rendering of the variable, also has two key components. 

1. View Settings -- a button on the bottom left with a gear cog icon, which presents additional options related to the view. 
2. Expand View -- a drag-resize button on the bottom right, which lets users control the size of the specific view. 

The below image shows the expanded view settings panel. 

![view-expanded](../images/view-expanded.png){ width="400" }

The panel contains option to control the properties of the view 
- the color map used to color the variable
- options for mapping color -- log scale, inverted color map, or show/hide color bar
- options to control the min and max values for color mapping
- a button to reset the color mapping to the range of values in the data




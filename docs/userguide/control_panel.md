## The Control Panel

![control-panel](../images/control-panel.png){ width="400" }

The control panel lets users control the context of visual analysis for the
data, i.e, it allows the users to select the time, middle and interface layers,
and the variables for analysis, among other operations. The panel can be divided
into three main parts

1. **Data Slice Selection** The data slice selection allows users to slice and
   dice data spatio-temporally for analysis

   - a. It allows data slice selection along the dimensions of time, middle and
     interface layer.
   - b. It allows users to control the geo-spatial region by controlling the
     longitude, latitude ranges.

   Users can interactively select the data slice by interacting with the
   sliders, or using the media buttons to skip-previous, skip-next, or play an
   animation.

2. **Map Projection Selection** The map projection selection allows users to
   chose different representation of the data. Currently, it allows for
   Cylindrical-Equidistant, Robinson, and Mollweide projections. In the future,
   additional features are planned, e.g. selection of center meridian.

3. **Variable Selections**

   ![variable-select](../images/variable-select.png){ width="400" }

   The variable selections allow users to control variables of interest for
   analysis. The variables are separated into three types -- the 2D (surface)
   variables, middle layer variables, and interface layer variables. Users can
   select and unselect the variables and to render the views, click the
   `Load Variables` button located in the tool bar. The reason for not making
   the views appear dynamically post variable selections is to allow for stable
   and better application behavior.

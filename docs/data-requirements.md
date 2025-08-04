# QuickView Data File Requirements

This document describes the NetCDF file format and variable requirements for
QuickView to properly read and visualize E3SM atmospheric data.

## Overview

QuickView requires two NetCDF files:

1. **Data File** - Contains the atmospheric variables and time-varying data
2. **Connectivity File** - Contains the mesh geometry and grid structure

## Required Dimensions

The following dimensions must be present in the data files:

### In Data File:

- `time` - Time dimension for temporal data
- `ncol` - Number of columns (horizontal grid points)
- `lev` - Number of vertical levels at layer midpoints
- `ilev` - Number of vertical levels at layer interfaces

### In Connectivity File:

- `grid_size` or `ncol` - Total number of grid cells

## Required Variables

### 1. Coordinate Variables

#### Latitude and Longitude (Required)

The connectivity file must contain corner coordinates for grid cells:

- **Variables containing `corner_lat`** - Latitude coordinates of cell corners
- **Variables containing `corner_lon`** - Longitude coordinates of cell corners

These are used to construct the unstructured grid geometry.

#### Vertical Coordinate Variables

For proper vertical level display, the data file should contain either:

**Option A: Direct level values**

- `lev` - Pressure levels at layer midpoints (hPa)
- `ilev` - Pressure levels at layer interfaces (hPa)

**Option B: Hybrid coordinate coefficients** If `lev` and `ilev` are not
directly provided, they will be computed from:

- Variables containing `hyam` - Hybrid A coefficient at layer midpoints
- Variables containing `hybm` - Hybrid B coefficient at layer midpoints
- Variables containing `hyai` - Hybrid A coefficient at layer interfaces
- Variables containing `hybi` - Hybrid B coefficient at layer interfaces

The pressure levels are computed as:

```
pressure = (hyam * P0) + (hybm * PS0)
```

where P0 = 100000 Pa (reference pressure) and PS0 = 100000 Pa (surface
pressure).

### 2. Time Variable (Required)

- `time` - Time coordinate variable containing timestamps for each time step

### 3. Area Variable (Optional but Recommended)

- Variable containing `area` in its name - Grid cell areas used for computing
  area-weighted averages
  - If not present, simple arithmetic averaging will be used instead

## Variable Types Supported

QuickView categorizes variables based on their dimensions:

### 1D Variables (Info Variables)

- Dimensions: `(ncol)`
- Example: `area`
- These are typically time-invariant grid properties

### 2D Variables (Surface Variables)

- Dimensions: `(time, ncol)`
- Example: `TS` (surface temperature), `PS` (surface pressure)
- These represent surface or column-integrated quantities

### 3D Midpoint Variables

- Dimensions: `(time, lev, ncol)` or `(time, ncol, lev)`
- Example: `T` (temperature), `U` (zonal wind), `Q` (specific humidity)
- These are defined at layer midpoints

### 3D Interface Variables

- Dimensions: `(time, ilev, ncol)` or `(time, ncol, ilev)`
- Example: `OMEGA` (vertical velocity)
- These are defined at layer interfaces

## Variable Attributes

### Fill Values

Variables should include the `_FillValue` attribute to indicate missing or
undefined data. QuickView will convert these to NaN values for proper handling.

## Example Data Structure

### Data File Structure:

```
dimensions:
    time = 12 ;
    ncol = 48602 ;
    lev = 72 ;
    ilev = 73 ;

variables:
    double time(time) ;
    double T(time, lev, ncol) ;
        T:_FillValue = 9.96920996838687e+36 ;
    double TS(time, ncol) ;
        TS:_FillValue = 9.96920996838687e+36 ;
    double hyam(lev) ;
    double hybm(lev) ;
    double hyai(ilev) ;
    double hybi(ilev) ;
```

### Connectivity File Structure:

```
dimensions:
    grid_size = 48602 ;
    grid_corners = 4 ;

variables:
    double grid_corner_lat(grid_size, grid_corners) ;
    double grid_corner_lon(grid_size, grid_corners) ;
```

## Notes

1. The reader automatically detects and categorizes variables based on their
   dimensions
2. Variables with dimensions not matching the expected patterns are ignored
3. The reader caches geometry and special variables for performance
4. Time interpolation is handled automatically when requesting specific time
   steps

from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from paraview.util.vtkAlgorithm import smproxy, smproperty
from vtkmodules.numpy_interface import dataset_adapter as dsa
from vtkmodules.vtkCommonCore import vtkPoints, vtkDataArraySelection
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkCellArray
from vtkmodules.util import vtkConstants, numpy_support
from paraview import print_error, print_warning

try:
    import netCDF4
    import numpy as np
    import json

    _has_deps = True
except ImportError as ie:
    print_error(
        "Missing required Python modules/packages. Algorithms in this module may "
        "not work as expected! \n {0}".format(ie)
    )
    _has_deps = False

try:
    from e3sm_quickview.utils import perf as _perf
except ImportError:
    # Plugin may be loaded by paraview with quickview not on sys.path; fall
    # back to a no-op shim so the reader still works.
    from contextlib import contextmanager

    class _perf:  # type: ignore[no-redef]
        @staticmethod
        def is_enabled():
            return False

        @staticmethod
        @contextmanager
        def timed(label):
            yield

# Dimensions will be dynamically determined from connectivity and data files


class EAMConstants:
    LEV = "lev"
    HYAM = "hyam"
    HYBM = "hybm"
    ILEV = "ilev"
    HYAI = "hyai"
    HYBI = "hybi"
    P0 = float(1e5)
    PS0 = float(1e5)


class DimMeta:
    """Simple class to store dimension metadata."""

    def __init__(self, name, size, data=None):
        self.name = name
        self.size = size
        self.long_name = None
        self.units = None
        self.data = data  # Store the actual dimension coordinate values

    def __getitem__(self, key):
        """Dict-like access to attributes."""
        return getattr(self, key, None)

    def __setitem__(self, key, value):
        """Dict-like setting of attributes."""
        setattr(self, key, value)

    def update_from_variable(self, var_info):
        """Update metadata from netCDF variable info - only long_name and units."""
        try:
            self.long_name = var_info.getncattr("long_name")
        except AttributeError:
            pass

        try:
            self.units = var_info.getncattr("units")
        except AttributeError:
            pass

    def __repr__(self):
        return f"DimMeta(name='{self.name}', size={self.size}, long_name='{self.long_name}')"


class VarMeta:
    """Simple class to store variable metadata."""

    def __init__(self, name, info, horizontal_dim=None):
        self.name = name
        self.dimensions = info.dimensions  # Store dimensions for slicing
        self.fillval = np.nan
        self.long_name = None

        # Extract metadata from info
        self._extract_metadata(info)

    def _extract_metadata(self, info):
        """Helper to extract metadata attributes from netCDF variable."""
        # Try to get fill value from either _FillValue or missing_value
        for fillattr in ["_FillValue", "missing_value"]:
            value = self._get_attr(info, fillattr)
            if value is not None:
                self.fillval = value
                break

        # Get long_name if available
        long_name = self._get_attr(info, "long_name")
        if long_name is not None:
            self.long_name = long_name

    def _get_attr(self, info, attr_name):
        """Safely get an attribute from netCDF variable info."""
        try:
            return info.getncattr(attr_name)
        except (AttributeError, KeyError):
            return None

    def __getitem__(self, key):
        """Dict-like access to attributes."""
        return getattr(self, key, None)

    def __setitem__(self, key, value):
        """Dict-like setting of attributes."""
        setattr(self, key, value)

    def __repr__(self):
        return f"VarMeta(name='{self.name}', dimensions={self.dimensions})"


def compare(data, arrays, dim):
    ref = data[arrays[0]][:].flatten()
    if len(ref) != dim:
        raise Exception(
            "Length of hya_/hyb_ variable does not match the corresponding dimension"
        )
    for array in arrays[1:]:
        comp = data[array][:].flatten()
        if not np.array_equal(ref, comp):
            return None
    return ref


def FindSpecialVariable(data, lev, hya, hyb):
    dim = data.dimensions.get(lev, None)
    if dim is None:
        raise Exception(f"{lev} not found in dimensions")
    dim = dim.size
    var = np.array(list(data.variables.keys()))

    if lev in var:
        lev = data[lev][:].flatten()
        return lev

    _hyai = [v for v in var if hya in v]
    _hybi = [v for v in var if hyb in v]
    if len(_hyai) != len(_hybi):
        raise Exception("Unmatched pair of hya and hyb variables found")

    p0 = data["P0"][:].item() if "P0" in var else EAMConstants.P0
    ps0 = EAMConstants.PS0

    if len(_hyai) == 1:
        hyai = data[_hyai[0]][:].flatten()
        hybi = data[_hyai[1]][:].flatten()
        if not (len(hyai) == dim and len(hybi) == dim):
            raise Exception(
                "Lengths of arrays for hya_ and hyb_ variables do not match"
            )
        ldata = ((hyai * p0) + (hybi * ps0)) / 100.0
        return ldata
    else:
        hyai = compare(data, _hyai, dim)
        hybi = compare(data, _hybi, dim)
        if hyai is None or hybi is None:
            raise Exception("Values within hya_ and hyb_ arrays do not match")
        else:
            ldata = ((hyai * p0) + (hybi * ps0)) / 100.0
            return ldata


# ------------------------------------------------------------------------------
# A reader example.
# ------------------------------------------------------------------------------
def createModifiedCallback(anobject):
    import weakref

    weakref_obj = weakref.ref(anobject)
    anobject = None

    def _markmodified(*args, **kwars):
        o = weakref_obj()
        if o is not None:
            o.Modified()

    return _markmodified


@smproxy.reader(
    name="EAMSliceSource",
    label="EAM Slice Data Reader",
    extensions="nc",
    file_description="NETCDF files for EAM",
)
@smproperty.xml("""<OutputPort name="Mesh"  index="0" />""")
@smproperty.xml(
    """
                <StringVectorProperty command="SetDataFileName"
                      name="FileName1"
                      label="Data File"
                      number_of_elements="1">
                    <FileListDomain name="files" />
                    <Documentation>Specify the NetCDF data file name.</Documentation>
                </StringVectorProperty>
                """
)
@smproperty.xml(
    """
                <StringVectorProperty command="SetConnFileName"
                      name="FileName2"
                      label="Connectivity File"
                      number_of_elements="1">
                    <FileListDomain name="files" />
                    <Documentation>Specify the NetCDF connecticity file name.</Documentation>
                </StringVectorProperty>
                """
)
@smproperty.xml(
    """
                <StringVectorProperty command="SetSlicing"
                      name="Slicing"
                      label="Slicing"
                      number_of_elements="1"
                      animateable="0"
                      default_values="">
                    <Documentation>JSON representing dimension slices (e.g. {"lev": 0, "ilev": 1})</Documentation>
                </StringVectorProperty>
                """
)
@smproperty.xml(
    """
<IntVectorProperty command="SetForceFloatPoints"
                         name="ForceFloatPoints"
                         default_values="1"
                         number_of_elements="1">
        <BooleanDomain name="bool" />
        <Documentation>
           If True, the points of the dataset will be float, otherwise they will be float or double depending
           on the type of corner_lat and corner_lon variables in the connectivity file.
        </Documentation>
      </IntVectorProperty>
                """
)
class EAMSliceSource(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(
            self, nInputPorts=0, nOutputPorts=1, outputType="vtkUnstructuredGrid"
        )
        self._output = vtkUnstructuredGrid()

        self._DataFileName = None
        self._ConnFileName = None
        self._ForceFloatPoints = True
        self._dirty = False

        # Variables for dimension sliders
        self._time = 0
        # Dictionaries to store metadata objects
        self._variables = {}  # Will store VarMeta objects by name
        self._dimensions = {}  # Will store DimMeta objects by name
        self._timeSteps = []
        # Dictionary to store dimension slices
        self._slices = {}
        self._changed_dims = set()

        # vtkDataArraySelection to allow users choice for fields
        # to fetch from the netCDF data set
        self._variable_selection = vtkDataArraySelection()
        # Add observers for the selection arrays
        self._variable_selection.AddObserver(
            "ModifiedEvent", createModifiedCallback(self)
        )
        # Flag for area var to calculate averages
        self._areavar = None

        # NetCDF file handle caching
        self._mesh_dataset = None
        self._var_dataset = None
        self._cached_mesh_filename = None
        self._cached_var_filename = None

        # Geometry caching
        self._cached_points = None
        self._cached_cells = None
        self._cached_cell_types = None
        self._cached_offsets = None
        self._cached_ncells2D = None

        # Special variable caching
        # self._cached_lev = None
        # self._cached_ilev = None
        self._cached_area = None

        # Dynamic dimension detection
        self._horizontal_dim = None
        self._data_horizontal_dim = None  # Matched in data file

    def __del__(self):
        """Clean up NetCDF file handles on deletion."""
        self._close_datasets()

    def _close_datasets(self):
        """Close any open NetCDF datasets."""
        if self._mesh_dataset is not None:
            try:
                self._mesh_dataset.close()
            except Exception:
                pass
            self._mesh_dataset = None
        if self._var_dataset is not None:
            try:
                self._var_dataset.close()
            except Exception:
                pass
            self._var_dataset = None

    def _get_mesh_dataset(self):
        """Get cached mesh dataset or open a new one."""
        if (
            self._ConnFileName != self._cached_mesh_filename
            or self._mesh_dataset is None
        ):
            if self._mesh_dataset is not None:
                try:
                    self._mesh_dataset.close()
                except Exception:
                    pass
            self._mesh_dataset = netCDF4.Dataset(self._ConnFileName, "r")
            self._cached_mesh_filename = self._ConnFileName
        return self._mesh_dataset

    def _get_var_dataset(self):
        """Get cached variable dataset or open a new one."""
        if self._DataFileName != self._cached_var_filename or self._var_dataset is None:
            if self._var_dataset is not None:
                try:
                    self._var_dataset.close()
                except Exception:
                    pass
            self._var_dataset = netCDF4.Dataset(self._DataFileName, "r")
            self._cached_var_filename = self._DataFileName
        return self._var_dataset

    # Method to clear all the variable names
    def _clear(self):
        self._variables.clear()

        # Clear special variable cache when metadata changes
        self._cached_area = None

        # Clear dimension detection
        self._data_horizontal_dim = None

    def _identify_horizontal_dimension(self, meshdata, vardata):
        """Identify horizontal dimension from connectivity and match with data file."""
        if self._horizontal_dim and self._data_horizontal_dim:
            return  # Already identified

        # Get first dimension from connectivity file
        conn_dims = list(meshdata.dimensions.keys())
        if not conn_dims:
            print_error("No dimensions found in connectivity file")
            return

        self._horizontal_dim = conn_dims[0]
        conn_size = meshdata.dimensions[self._horizontal_dim].size

        # Match dimension in data file by size
        for dim_name, dim_obj in vardata.dimensions.items():
            if dim_obj.size == conn_size:
                self._data_horizontal_dim = dim_name
                return

        print_error(
            f"Could not match horizontal dimension size {conn_size} in data file"
        )

    def _clear_geometry_cache(self):
        """Clear cached geometry data."""
        self._cached_points = None
        self._cached_cells = None
        self._cached_cell_types = None
        self._cached_offsets = None
        self._cached_ncells2D = None

    '''
    Disable the derivation of lev/ilev for the new approach -- the new approach
    relies on the identified dimensions from the data file and connectivity files.
    We could reintroduce this later if required.

    def _get_cached_lev(self, vardata):
        """Get cached lev array or compute and cache it."""
        if self._cached_lev is None:
            self._cached_lev = FindSpecialVariable(
                vardata, EAMConstants.LEV, EAMConstants.HYAM, EAMConstants.HYBM
            )
        return self._cached_lev

    def _get_cached_ilev(self, vardata):
        """Get cached ilev array or compute and cache it."""
        if self._cached_ilev is None:
            self._cached_ilev = FindSpecialVariable(
                vardata, EAMConstants.ILEV, EAMConstants.HYAI, EAMConstants.HYBI
            )
        return self._cached_ilev
    '''

    def _get_cached_area(self, vardata):
        """Get cached area array or load and cache it."""
        if self._cached_area is None and self._areavar:
            data = vardata[self._areavar.name][:].data
            # Use reshape instead of flatten to avoid copy
            self._cached_area = data.reshape(-1)
            # Apply fill value replacement in-place
            mask = self._cached_area == self._areavar.fillval
            self._cached_area[mask] = np.nan
        return self._cached_area

    def _load_variable(self, vardata, varmeta):
        """Load variable data with dimension-based slicing."""
        try:
            # Build slice tuple based on variable's dimensions and user-selected slices
            slice_tuple = []
            for dim in varmeta.dimensions:
                if dim == self._data_horizontal_dim:
                    slice_tuple.append(slice(None))
                else:
                    # Use all data for unspecified dimensions
                    slice_tuple.append(self._slices.get(dim, 0))

            with _perf.timed(f"reader.netcdf_read.{varmeta.name}"):
                # Get data with proper slicing
                data = vardata[varmeta.name][tuple(slice_tuple)].data.reshape(-1)
            if not np.isnan(varmeta.fillval):
                with _perf.timed(f"reader.fill_value_scan.{varmeta.name}"):
                    data = data.copy()
                    data[data == varmeta.fillval] = np.nan
            return data
        except Exception as e:
            print_error(f"Error loading variable {varmeta.name}: {e}")
            # Return empty array on error
            return np.array([])

    def _get_enabled_arrays(self, var_list, selection_obj):
        """Get list of enabled variable names from selection object."""
        enabled = []
        for varmeta in var_list:
            if selection_obj.ArrayIsEnabled(varmeta.name):
                enabled.append(varmeta)
        return enabled

    def _build_geometry(self, meshdata):
        """Build and cache geometry data from mesh dataset."""
        if self._cached_points is not None:
            # Geometry already cached
            return

        dims = meshdata.dimensions
        mvars = np.array(list(meshdata.variables.keys()))

        # Use the identified horizontal dimension
        if not self._horizontal_dim:
            print_error("Horizontal dimension not identified in connectivity file")
            return

        ncells2D = dims[self._horizontal_dim].size
        self._cached_ncells2D = ncells2D

        # Find lat/lon dimensions
        latdim = mvars[np.where(np.char.find(mvars, "corner_lat") > -1)][0]
        londim = mvars[np.where(np.char.find(mvars, "corner_lon") > -1)][0]

        # Build coordinates
        lat = meshdata[latdim][:].data.reshape(-1)
        lon = meshdata[londim][:].data.reshape(-1)

        if self._ForceFloatPoints:
            points_type = np.float32
        else:
            points_type = np.float64 if lat.dtype == np.float64 else np.float32
        coords = np.empty((len(lat), 3), dtype=points_type)
        coords[:, 0] = lon
        coords[:, 1] = lat
        coords[:, 2] = 0.0

        # Create VTK points
        _coords = dsa.numpyTovtkDataArray(coords)
        vtk_coords = vtkPoints()
        vtk_coords.SetData(_coords)
        self._cached_points = vtk_coords

        # Build cell arrays
        cellTypes = np.empty(ncells2D, dtype=np.uint8)
        cellTypes.fill(vtkConstants.VTK_QUAD)
        self._cached_cell_types = numpy_support.numpy_to_vtk(
            num_array=cellTypes.ravel(),
            deep=True,
            array_type=vtkConstants.VTK_UNSIGNED_CHAR,
        )

        offsets = np.arange(0, (4 * ncells2D) + 1, 4, dtype=np.int64)
        self._cached_offsets = numpy_support.numpy_to_vtk(
            num_array=offsets.ravel(),
            deep=True,
            array_type=vtkConstants.VTK_ID_TYPE,
        )

        cells = np.arange(ncells2D * 4, dtype=np.int64)
        self._cached_cells = numpy_support.numpy_to_vtk(
            num_array=cells.ravel(), deep=True, array_type=vtkConstants.VTK_ID_TYPE
        )

    def _populate_variable_metadata(self):
        if self._DataFileName is None or self._ConnFileName is None:
            return

        meshdata = self._get_mesh_dataset()
        vardata = self._get_var_dataset()

        # Identify horizontal dimensions first
        self._identify_horizontal_dimension(meshdata, vardata)

        if not self._data_horizontal_dim:
            print_error("Could not detect horizontal dimension in data file")
            return

        # Clear existing selection arrays BEFORE adding new ones
        self._variable_selection.RemoveAllArrays()

        # First pass: collect dimensions used by valid variables
        all_dimensions = set()
        for name, info in vardata.variables.items():
            dims = set(info.dimensions)
            if self._data_horizontal_dim not in dims:
                continue
            varmeta = VarMeta(name, info, self._data_horizontal_dim)
            if len(dims) == 1 and "area" in name.lower():
                self._areavar = varmeta
            if len(dims) > 1:
                all_dimensions.update(dims)
            self._variables[name] = varmeta
            self._variable_selection.AddArray(name)

        # Remove the horizontal dimension from sliceable dimensions
        all_dimensions.discard(self._data_horizontal_dim)

        # Second pass: only populate _dimensions for dimensions that are:
        # 1. Used by at least one valid variable
        # 2. Have arity > 1
        self._dimensions.clear()
        for dim_name in all_dimensions:
            if dim_name in vardata.dimensions:
                dim_obj = vardata.dimensions[dim_name]
                if dim_obj.size > 1:
                    dim_meta = DimMeta(dim_name, dim_obj.size)
                    if dim_name in vardata.variables:
                        dim_var = vardata.variables[dim_name]
                        try:
                            dim_meta.data = vardata[dim_name][:].data
                        except Exception:
                            pass
                        dim_meta.update_from_variable(dim_var)
                    self._dimensions[dim_name] = dim_meta

        # Initialize slices for relevant dimensions
        for dim in self._dimensions:
            if dim not in self._slices:
                self._slices[dim] = 0

        self._variable_selection.DisableAllArrays()

        # Clear old timestamps before adding new ones
        self._timeSteps.clear()
        if "time" in vardata.variables:
            timesteps = vardata["time"][:].data.reshape(-1)
            self._timeSteps.extend(timesteps)

    def SetDataFileName(self, fname):
        if fname is not None and fname != "None":
            if fname != self._DataFileName:
                self._DataFileName = fname
                self._dirty = True
                self._clear()
                # Close old dataset if filename changed
                if self._cached_var_filename != fname and self._var_dataset is not None:
                    try:
                        self._var_dataset.close()
                    except Exception:
                        pass
                    self._var_dataset = None
                self._populate_variable_metadata()
                self.Modified()

    def SetConnFileName(self, fname):
        if fname != self._ConnFileName:
            self._ConnFileName = fname
            self._dirty = True
            self._clear()  # Clear dimension cache
            # Close old dataset if filename changed
            if self._cached_mesh_filename != fname and self._mesh_dataset is not None:
                try:
                    self._mesh_dataset.close()
                except Exception:
                    pass
                self._mesh_dataset = None
            self._clear_geometry_cache()
            # Re-populate metadata if data file is already set
            if self._DataFileName:
                self._populate_variable_metadata()
            self.Modified()

    def SetForceFloatPoints(self, forceFloatPoints):
        if self._ForceFloatPoints != forceFloatPoints:
            self._ForceFloatPoints = forceFloatPoints
            self.Modified()

    def SetSlicing(self, slice_str):
        # Parse JSON string containing dimension slices and update self._slices

        if slice_str and slice_str.strip():  # Check for non-empty string
            try:
                slice_dict = json.loads(slice_str)
                # Validate and update slices for provided dimensions
                invalid_slices = []
                for dim, slice_val in slice_dict.items():
                    # Check if dimension exists
                    if dim in self._dimensions:
                        dim_meta = self._dimensions[dim]
                        dim_size = dim_meta.size
                        # Validate slice index
                        if isinstance(slice_val, int):
                            if slice_val < 0 or slice_val >= dim_size:
                                # Include dimension long name if available
                                dim_display = f"{dim}"
                                if dim_meta.long_name:
                                    dim_display += f" ({dim_meta.long_name})"
                                invalid_slices.append(
                                    f"{dim_display}={slice_val} (valid range: 0-{dim_size - 1})"
                                )
                            else:
                                if self._slices.get(dim) != slice_val:
                                    self._changed_dims.add(dim)
                                self._slices[dim] = slice_val
                        else:
                            print_error(
                                f"Slice value for '{dim}' must be an integer, got {type(slice_val).__name__}"
                            )
                    else:
                        # Store the slice anyway for dimensions we haven't seen yet
                        # (might be populated later)
                        self._slices[dim] = slice_val
                        if self._dimensions:  # Only warn if we have dimension info
                            print_warning(f"Dimension '{dim}' not found in data file")

                if invalid_slices:
                    print_error(f"Invalid slice indices: {', '.join(invalid_slices)}")
                else:
                    self.Modified()

            except (json.JSONDecodeError, ValueError) as e:
                print_error(f"Invalid JSON for slicing: {e}")
            except Exception as e:
                print_error(f"Error setting slices: {e}")

    def SetCalculateAverages(self, calcavg):
        if self._avg != calcavg:
            self._avg = calcavg
            self.Modified()

    def GetVariables(self):
        return self._variables

    def GetDimensions(self):
        return self._dimensions

    @smproperty.doublevector(
        name="TimestepValues", information_only="1", si_class="vtkSITimeStepsProperty"
    )
    def GetTimestepValues(self):
        return self._timeSteps

    # Array selection API is typical with readers in VTK
    # This is intended to allow ability for users to choose which arrays to
    # load. To expose that in ParaView, simply use the
    # smproperty.dataarrayselection().
    # This method **must** return a `vtkDataArraySelection` instance.
    @smproperty.dataarrayselection(name="Variables")
    def GetSurfaceVariables(self):
        return self._variable_selection

    def RequestInformation(self, request, inInfo, outInfo):
        executive = self.GetExecutive()
        port = outInfo.GetInformationObject(0)
        port.Remove(executive.TIME_STEPS())
        port.Remove(executive.TIME_RANGE())
        if self._timeSteps is not None and len(self._timeSteps) > 0:
            for t in self._timeSteps:
                port.Append(executive.TIME_STEPS(), t)
            port.Append(executive.TIME_RANGE(), self._timeSteps[0])
            port.Append(executive.TIME_RANGE(), self._timeSteps[-1])
        return 1

    # TODO : implement request extents
    def RequestUpdateExtent(self, request, inInfo, outInfo):
        return super().RequestUpdateExtent(request, inInfo, outInfo)

    def get_time_index(self, outInfo, executive, from_port):
        timeInfo = outInfo.GetInformationObject(from_port)
        timeInd = 0
        if timeInfo.Has(executive.UPDATE_TIME_STEP()) and len(self._timeSteps) > 1:
            time = timeInfo.Get(executive.UPDATE_TIME_STEP())
            for t in self._timeSteps:
                if time <= t:
                    break
                else:
                    timeInd = timeInd + 1
            return timeInd
        return timeInd

    def RequestData(self, request, inInfo, outInfo):
        with _perf.timed("reader.RequestData"):
            return self._RequestDataImpl(request, inInfo, outInfo)

    def _RequestDataImpl(self, request, inInfo, outInfo):
        if (
            self._ConnFileName is None
            or self._ConnFileName == "None"
            or self._DataFileName is None
            or self._DataFileName == "None"
        ):
            print_error(
                "Either one or both, the data file or connectivity file, are not provided!"
            )
            return 0
        global _has_deps
        if not _has_deps:
            print_error("Required Python module 'netCDF4' or 'numpy' missing!")
            return 0

        meshdata = self._get_mesh_dataset()
        vardata = self._get_var_dataset()

        # Ensure dimensions are identified
        self._identify_horizontal_dimension(meshdata, vardata)

        if not self._horizontal_dim or not self._data_horizontal_dim:
            print_error("Could not identify required dimensions from files")
            return 0

        # Build geometry if not cached
        self._build_geometry(meshdata)

        if self._cached_points is None:
            print_error("Could not build geometry from connectivity file")
            return 0

        output_mesh = dsa.WrapDataObject(self._output)

        if self._dirty:
            self._output = vtkUnstructuredGrid()
            output_mesh = dsa.WrapDataObject(self._output)

            # Use cached geometry
            output_mesh.SetPoints(self._cached_points)

            # Create cell array from cached data
            cellArray = vtkCellArray()
            cellArray.SetData(self._cached_offsets, self._cached_cells)
            output_mesh.VTKObject.SetCells(self._cached_cell_types, cellArray)

            self._dirty = False

        # Needed to drop arrays from cached VTK Object
        to_remove = set()
        last_num_arrays = output_mesh.CellData.GetNumberOfArrays()
        for i in range(last_num_arrays):
            to_remove.add(output_mesh.CellData.GetArrayName(i))

        changed_dims = self._changed_dims
        for name, varmeta in self._variables.items():
            if self._variable_selection.ArrayIsEnabled(name):
                if output_mesh.CellData.HasArray(name):
                    to_remove.remove(name)
                    if changed_dims and not changed_dims.intersection(
                        varmeta.dimensions
                    ):
                        continue
                data = self._load_variable(vardata, varmeta)
                output_mesh.CellData.append(data, name)

        self._changed_dims = set()

        area_var_name = "area"
        if self._areavar and not output_mesh.CellData.HasArray(area_var_name):
            data = self._get_cached_area(vardata)
            if data is not None:
                output_mesh.CellData.append(data, area_var_name)
        if area_var_name in to_remove:
            to_remove.remove(area_var_name)

        for var_name in to_remove:
            output_mesh.CellData.RemoveArray(var_name)

        output = vtkUnstructuredGrid.GetData(outInfo, 0)
        output.ShallowCopy(self._output)

        return 1

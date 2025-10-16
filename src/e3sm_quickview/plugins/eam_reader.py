from paraview.util.vtkAlgorithm import *
from vtkmodules.numpy_interface import dataset_adapter as dsa
from vtkmodules.vtkCommonCore import vtkPoints, vtkDataArraySelection
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkCellArray
from vtkmodules.util import vtkConstants, numpy_support
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from paraview import print_error

try:
    import netCDF4
    import numpy as np

    _has_deps = True
except ImportError as ie:
    print_error(
        "Missing required Python modules/packages. Algorithms in this module may "
        "not work as expected! \n {0}".format(ie)
    )
    _has_deps = False

dims1 = set(["ncol"])
dims2 = set(["time", "ncol"])
dims3i = set(["time", "ilev", "ncol"])
dims3m = set(["time", "lev", "ncol"])


class EAMConstants:
    LEV = "lev"
    HYAM = "hyam"
    HYBM = "hybm"
    ILEV = "ilev"
    HYAI = "hyai"
    HYBI = "hybi"
    P0 = float(1e5)
    PS0 = float(1e5)


from enum import Enum  # noqa: E402


class VarType(Enum):
    _1D = 1
    _2D = 2
    _3Dm = 3
    _3Di = 4


class VarMeta:
    def __init__(self, name, info):
        self.name = name
        self.type = None
        self.transpose = False
        self.fillval = np.nan

        dims = info.dimensions

        if len(dims) == 1:
            self.type = VarType._1D
        elif len(dims) == 2:
            self.type = VarType._2D
        elif len(dims) == 3:
            if "lev" in dims:
                self.type = VarType._3Dm
            elif "ilev" in dims:
                self.type = VarType._3Di

            if "ncol" in dims[1]:
                self.transpose = True


def compare(data, arrays, dim):
    ref = data[arrays[0]][:].flatten()
    if len(ref) != dim:
        raise Exception(
            "Length of hya_/hyb_ variable does not match the corresponding dimension"
        )
    for i, array in enumerate(arrays[1:], start=1):
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


import traceback  # noqa: E402


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
                <IntVectorProperty name="Middle Layer"
                    command="SetMiddleLayer"
                    number_of_elements="1"
                    default_values="0">
                </IntVectorProperty>
                """
)
@smproperty.xml(
    """
                <IntVectorProperty name="Interface Layer"
                    command="SetInterfaceLayer"
                    number_of_elements="1"
                    default_values="0">
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
        self._dirty = False
        self._surface_update = True
        self._midpoint_update = True
        self._interface_update = True

        # Variables for dimension sliders
        self._time = 0
        self._lev = 0
        self._ilev = 0
        # Arrays to store field names in netCDF file
        self._info_vars = []  # 1D info variables
        self._surface_vars = []  # 2D surface variables
        self._interface_vars = []  # 3D interface layer variables
        self._midpoint_vars = []  # 3D midpoint layer variables
        self._timeSteps = []

        # vtkDataArraySelection to allow users choice for fields
        # to fetch from the netCDF data set
        self._info_selection = vtkDataArraySelection()
        self._surface_selection = vtkDataArraySelection()
        self._interface_selection = vtkDataArraySelection()
        self._midpoint_selection = vtkDataArraySelection()
        # Cache for non temporal variables
        # Store { names : data }
        self._info_vars_cache = {}
        # Add observers for the selection arrays
        self._info_selection.AddObserver("ModifiedEvent", createModifiedCallback(self))
        self._surface_selection.AddObserver(
            "ModifiedEvent", createModifiedCallback(self)
        )
        self._interface_selection.AddObserver(
            "ModifiedEvent", createModifiedCallback(self)
        )
        self._midpoint_selection.AddObserver(
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
        self._cached_lev = None
        self._cached_ilev = None
        self._cached_area = None

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
        self._info_vars.clear()
        self._surface_vars.clear()
        self._interface_vars.clear()
        self._midpoint_vars.clear()
        # Clear special variable cache when metadata changes
        self._cached_lev = None
        self._cached_ilev = None
        self._cached_area = None

    def _clear_geometry_cache(self):
        """Clear cached geometry data."""
        self._cached_points = None
        self._cached_cells = None
        self._cached_cell_types = None
        self._cached_offsets = None
        self._cached_ncells2D = None

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

    def _load_2d_variable(self, vardata, varmeta, timeInd):
        """Load 2D variable data with optimized operations."""
        # Get data without unnecessary copy
        data = vardata[varmeta.name][:].data[timeInd].flatten()
        data = np.where(data == varmeta.fillval, np.nan, data)
        return data

    def _load_3d_slice(self, vardata, varmeta, timeInd, start_idx, end_idx):
        """Load a slice of 3D variable data with optimized operations."""
        # Load full 3D data for time step
        if not varmeta.transpose:
            data = vardata[varmeta.name][:].data[timeInd].flatten()[start_idx:end_idx]
        else:
            data = (
                vardata[varmeta.name][:]
                .data[timeInd]
                .transpose()
                .flatten()[start_idx:end_idx]
            )
        data = np.where(data == varmeta.fillval, np.nan, data)
        return data

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
        mdims = np.array(list(meshdata.dimensions.keys()))
        mvars = np.array(list(meshdata.variables.keys()))

        # Find ncells2D
        ncells2D = dims[
            mdims[
                np.where(
                    (np.char.find(mdims, "grid_size") > -1)
                    | (np.char.find(mdims, "ncol") > -1)
                )[0][0]
            ]
        ].size
        self._cached_ncells2D = ncells2D

        # Find lat/lon dimensions
        latdim = mvars[np.where(np.char.find(mvars, "corner_lat") > -1)][0]
        londim = mvars[np.where(np.char.find(mvars, "corner_lon") > -1)][0]

        # Build coordinates
        lat = meshdata[latdim][:].data.flatten()
        lon = meshdata[londim][:].data.flatten()

        coords = np.empty((len(lat), 3), dtype=np.float64)
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
        if self._DataFileName is None:
            return
        vardata = self._get_var_dataset()

        # Clear existing selection arrays BEFORE adding new ones
        self._surface_selection.RemoveAllArrays()
        self._midpoint_selection.RemoveAllArrays()
        self._interface_selection.RemoveAllArrays()

        for name, info in vardata.variables.items():
            dims = set(info.dimensions)
            if not (dims == dims1 or dims == dims2 or dims == dims3m or dims == dims3i):
                continue
            varmeta = VarMeta(name, info)
            if varmeta.type == VarType._1D:
                self._info_vars.append(varmeta)
                if "area" in name:
                    self._areavar = varmeta
            elif varmeta.type == VarType._2D:
                self._surface_vars.append(varmeta)
                self._surface_selection.AddArray(name)
            elif varmeta.type == VarType._3Dm:
                self._midpoint_vars.append(varmeta)
                self._midpoint_selection.AddArray(name)
            elif varmeta.type == VarType._3Di:
                self._interface_vars.append(varmeta)
                self._interface_selection.AddArray(name)
            try:
                fillval = info.getncattr("_FillValue")
                varmeta.fillval = fillval
            except Exception:
                try:
                    fillval = info.getncattr("missing_value")
                    varmeta.fillval = fillval
                except Exception:
                    pass
        self._surface_selection.DisableAllArrays()
        self._interface_selection.DisableAllArrays()
        self._midpoint_selection.DisableAllArrays()

        # Clear old timestamps before adding new ones
        self._timeSteps.clear()
        timesteps = vardata["time"][:].data.flatten()
        self._timeSteps.extend(timesteps)

    def SetDataFileName(self, fname):
        if fname is not None and fname != "None":
            if fname != self._DataFileName:
                self._DataFileName = fname
                self._dirty = True
                self._surface_update = True
                self._midpoint_update = True
                self._interface_update = True
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
            self._surface_update = True
            self._midpoint_update = True
            self._interface_update = True
            # Close old dataset if filename changed
            if self._cached_mesh_filename != fname and self._mesh_dataset is not None:
                try:
                    self._mesh_dataset.close()
                except Exception:
                    pass
                self._mesh_dataset = None
            # Clear geometry cache when connectivity file changes
            self._clear_geometry_cache()
            self.Modified()

    def SetMiddleLayer(self, lev):
        if self._lev != lev:
            self._lev = lev
            self._midpoint_update = True
            self.Modified()

    def SetInterfaceLayer(self, ilev):
        if self._ilev != ilev:
            self._ilev = ilev
            self._interface_update = True
            self.Modified()

    def SetCalculateAverages(self, calcavg):
        if self._avg != calcavg:
            self._avg = calcavg
            self.Modified()

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
    @smproperty.dataarrayselection(name="Surface Variables")
    def GetSurfaceVariables(self):
        return self._surface_selection

    @smproperty.dataarrayselection(name="Midpoint Variables")
    def GetMidpointVariables(self):
        return self._midpoint_selection

    @smproperty.dataarrayselection(name="Interface Variables")
    def GetInterfaceVariables(self):
        return self._interface_selection

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

        # Getting the correct time index
        executive = self.GetExecutive()
        from_port = request.Get(executive.FROM_OUTPUT_PORT())
        timeInd = self.get_time_index(outInfo, executive, from_port)
        if self._time != timeInd:
            self._time = timeInd
            self._surface_update = True
            self._midpoint_update = True
            self._interface_update = True

        meshdata = self._get_mesh_dataset()
        vardata = self._get_var_dataset()

        # Build geometry if not cached
        self._build_geometry(meshdata)

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

        # Use cached ncells2D
        ncells2D = self._cached_ncells2D

        # Needed to drop arrays from cached VTK Object
        to_remove = set()
        last_num_arrays = output_mesh.CellData.GetNumberOfArrays()
        for i in range(last_num_arrays):
            to_remove.add(output_mesh.CellData.GetArrayName(i))

        for varmeta in self._surface_vars:
            if self._surface_selection.ArrayIsEnabled(varmeta.name):
                if output_mesh.CellData.HasArray(varmeta.name):
                    to_remove.remove(varmeta.name)
                if (
                    not output_mesh.CellData.HasArray(varmeta.name)
                    or self._surface_update
                ):
                    data = self._load_2d_variable(vardata, varmeta, timeInd)
                    output_mesh.CellData.append(data, varmeta.name)
        self._surface_update = False

        try:
            lev_field_name = "lev"
            has_lev_field = output_mesh.FieldData.HasArray(lev_field_name)
            lev = self._get_cached_lev(vardata)
            if lev is not None:
                if not has_lev_field:
                    output_mesh.FieldData.append(lev, lev_field_name)
                if self._lev >= vardata.dimensions[lev_field_name].size:
                    print_error(
                        f"User provided input for middle layer {self._lev} larger than actual data {len(lev) - 1}"
                    )
                lstart = self._lev * ncells2D
                lend = lstart + ncells2D

                for varmeta in self._midpoint_vars:
                    if self._midpoint_selection.ArrayIsEnabled(varmeta.name):
                        if output_mesh.CellData.HasArray(varmeta.name):
                            to_remove.remove(varmeta.name)
                        if (
                            not output_mesh.CellData.HasArray(varmeta.name)
                            or self._midpoint_update
                        ):
                            data = self._load_3d_slice(
                                vardata, varmeta, timeInd, lstart, lend
                            )
                            output_mesh.CellData.append(data, varmeta.name)
            self._midpoint_update = False
        except Exception as e:
            print_error("Error occurred while processing middle layer variables :", e)
            traceback.print_exc()

        try:
            ilev_field_name = "ilev"
            has_ilev_field = output_mesh.FieldData.HasArray(ilev_field_name)
            ilev = self._get_cached_ilev(vardata)
            if ilev is not None:
                if not has_ilev_field:
                    output_mesh.FieldData.append(ilev, ilev_field_name)
                if self._ilev >= vardata.dimensions[ilev_field_name].size:
                    print_error(
                        f"User provided input for middle layer {self._ilev} larger than actual data {len(ilev) - 1}"
                    )
                ilstart = self._ilev * ncells2D
                ilend = ilstart + ncells2D
                for varmeta in self._interface_vars:
                    if self._interface_selection.ArrayIsEnabled(varmeta.name):
                        if output_mesh.CellData.HasArray(varmeta.name):
                            to_remove.remove(varmeta.name)
                        if (
                            not output_mesh.CellData.HasArray(varmeta.name)
                            or self._interface_update
                        ):
                            data = self._load_3d_slice(
                                vardata, varmeta, timeInd, ilstart, ilend
                            )
                            output_mesh.CellData.append(data, varmeta.name)
            self._interface_update = False
        except Exception as e:
            print_error(
                "Error occurred while processing interface layer variables :", e
            )
            traceback.print_exc()

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

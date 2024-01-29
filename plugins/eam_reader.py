from paraview.util.vtkAlgorithm import *
from vtkmodules.numpy_interface import dataset_adapter as dsa
from vtkmodules.vtkCommonCore import vtkPoints, vtkIdTypeArray
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkCellArray
from vtkmodules.util import vtkConstants, numpy_support
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkIOLegacy import vtkUnstructuredGridWriter
from paraview import servermanager
from paraview import print_error

try:
    import netCDF4
    import numpy as np
    _has_deps = True
except ImportError as ie:
    print_error(
        "Missing required Python modules/packages. Algorithms in this module may "
        "not work as expected! \n {0}".format(ie))
    _has_deps = False

dims2   = ('time', 'ncol')
dims3i  = ('time', 'ilev', 'ncol')
dims3m  = ('time', 'lev' , 'ncol')

timeDim = 0
ilevDim = 0
levDim  = 0

#------------------------------------------------------------------------------
# A reader example.
#------------------------------------------------------------------------------
def createModifiedCallback(anobject):
    import weakref
    weakref_obj = weakref.ref(anobject)
    anobject = None
    def _markmodified(*args, **kwars):
        o = weakref_obj()
        if o is not None:
            o.Modified()
    return _markmodified

@smproxy.reader(name="EAMSource", label="EAM Data Reader",
                extensions="nc", file_description="NETCDF files for EAM")
@smproperty.xml("""<OutputPort name="2D"  index="0" />""")
@smproperty.xml("""<OutputPort name="3D middle layer"  index="1" />""")
@smproperty.xml("""<OutputPort name="3D interface layer"  index="2" />""")
@smproperty.xml("""
                <StringVectorProperty command="SetDataFileName"
                      name="FileName1"
                      label="Data File"
                      number_of_elements="1">
                    <FileListDomain name="files" />
                    <Documentation>Specify the NetCDF data file name.</Documentation>
                </StringVectorProperty>
                """)
@smproperty.xml("""
                <StringVectorProperty command="SetConnFileName"
                      name="FileName2"
                      label="Connectivity File"
                      number_of_elements="1">
                    <FileListDomain name="files" />
                    <Documentation>Specify the NetCDF connecticity file name.</Documentation>
                </StringVectorProperty>
                """)
class EAMSource(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=0,
            nOutputPorts=3,
            outputType='vtkUnstructuredGrid')
        self.__DataFileName = None
        self.__ConnFileName = None
        # Variables for dimension sliders
        self.__time         = 0
        self.__lev          = 0
        self.__ilev         = 0
        # Arrays to store field names in netCDF file
        self.__vars1D       = []
        self.__vars2D       = []
        self.__vars3Di      = []
        self.__vars3Dm      = []
        self.__timeSteps    = []
        from vtkmodules.vtkCommonCore import vtkDataArraySelection
        # vtkDataArraySelection to allow users choice for fields
        # to fetch from the netCDF data set
        self.__vars1Darr    = vtkDataArraySelection()
        self.__vars2Darr    = vtkDataArraySelection()
        self.__vars3Diarr   = vtkDataArraySelection()
        self.__vars3Dmarr   = vtkDataArraySelection()
        # Cache for non temporal variables
        # Store { names : data }
        self.__vars1DCacahe = {}
        # Add observers for the selection arrays
        self.__vars1Darr.AddObserver("ModifiedEvent", createModifiedCallback(self))
        self.__vars2Darr.AddObserver("ModifiedEvent", createModifiedCallback(self))
        self.__vars3Diarr.AddObserver("ModifiedEvent", createModifiedCallback(self))
        self.__vars3Dmarr.AddObserver("ModifiedEvent", createModifiedCallback(self))

    # Method to clear all the variable names
    def __clear(self):
        self.__vars1D.clear()
        self.__vars2D.clear()
        self.__vars3Di.clear()
        self.__vars3Dm.clear()

    def __populate_variable_metadata(self):
        if self.__DataFileName is None:
            return
        vardata     = netCDF4.Dataset(self.__DataFileName, "r")
        for name, info in vardata.variables.items():
            if info.dimensions == dims2:
                self.__vars2D.append(name)
                self.__vars2Darr.AddArray(name)
            elif info.dimensions == dims3i:
                self.__vars3Di.append(name)
                self.__vars3Diarr.AddArray(name)
            elif info.dimensions == dims3m:
                self.__vars3Dm.append(name)
                self.__vars3Dmarr.AddArray(name)
            elif len(info.dimensions) == 1:
                self.__vars1D.append(name)
        self.__vars2Darr.DisableAllArrays()
        self.__vars3Diarr.DisableAllArrays()
        self.__vars3Dmarr.DisableAllArrays()
        timesteps = vardata['time'][:].data.flatten()
        self.__timeSteps.extend(timesteps)
        global timeDim, ilevDim, levDim
        timeDim  = vardata.dimensions["time"].size
        ilevDim  = vardata.dimensions["ilev"].size
        levDim   = vardata.dimensions["lev"].size

    def SetDataFileName(self, fname):
        if fname is not None and fname != "None":
            if fname != self.__DataFileName:
                self.__DataFileName = fname
                self.__clear()
                self.__populate_variable_metadata()
                self.Modified()

    def SetConnFileName(self, fname):
        if fname != self.__ConnFileName:
            self.__ConnFileName = fname
            self.Modified()

    @smproperty.doublevector(name="TimestepValues", information_only="1", si_class="vtkSITimeStepsProperty")
    def GetTimestepValues(self):
            return self.__timeSteps

    # Array selection API is typical with readers in VTK
    # This is intended to allow ability for users to choose which arrays to
    # load. To expose that in ParaView, simply use the
    # smproperty.dataarrayselection().
    # This method **must** return a `vtkDataArraySelection` instance.
    @smproperty.dataarrayselection(name="2D Variables")
    def Get2DDataArrays(self):
        return self.__vars2Darr

    @smproperty.dataarrayselection(name="3D Middle Layer Variables")
    def Get3DmDataArrays(self):
        return self.__vars3Dmarr

    @smproperty.dataarrayselection(name="3D Interface Layer Variables")
    def Get3DiDataArrays(self):
        return self.__vars3Diarr

    def RequestInformation(self, request, inInfo, outInfo):
        executive = self.GetExecutive()
        for i in range(3):
            port = outInfo.GetInformationObject(i)
            port.Remove(executive.TIME_STEPS())
            port.Remove(executive.TIME_RANGE())
            if self.__timeSteps is not None and len(self.__timeSteps) > 0:
                for t in self.__timeSteps:
                    port.Append(executive.TIME_STEPS(), t)
                port.Append(executive.TIME_RANGE(), self.__timeSteps[0])
                port.Append(executive.TIME_RANGE(), self.__timeSteps[-1])
        return 1

    # TODO : implement request extents
    def RequestUpdateExtent(self, request, inInfo, outInfo):
        return super().RequestUpdateExtent(request, inInfo, outInfo)

    def GetTimeIndex(self, time):
        if self.__timeSteps is not None and len(self.__timeSteps) > 0:
            timeInd = 0
            for t in self.__timeSteps:
                if time == t:
                    break
                else:
                    timeInd = timeInd + 1
            return timeInd
        return 0

    def RequestData(self, request, inInfo, outInfo):
        if  self.__ConnFileName is None   or \
            self.__ConnFileName == 'None' or \
            self.__DataFileName is None   or \
            self.__DataFileName == 'None' :
            print_error("Either one or both, the data file or connectivity file, are not provided!")
            return 0
        global _has_deps
        if not _has_deps:
            print_error("Required Python module 'netCDF4' or 'numpy' missing!")
            return 0

        executive = self.GetExecutive()
        from_port = request.Get(executive.FROM_OUTPUT_PORT())
        timeInfo  = outInfo.GetInformationObject(from_port)
        timeInd = 0
        if timeInfo.Has(executive.UPDATE_TIME_STEP()) and len(self.__timeSteps) > 0:
            time = timeInfo.Get(executive.UPDATE_TIME_STEP())
            timeInd = self.GetTimeIndex(time)
            print("Getting ", time, " at index ", timeInd)

        output2D    = dsa.WrapDataObject(vtkUnstructuredGrid.GetData(outInfo, 0))

        meshdata    = netCDF4.Dataset(self.__ConnFileName, "r")
        vardata     = netCDF4.Dataset(self.__DataFileName, "r")

        lat = meshdata['cell_corner_lat'][:].data.flatten()
        lon = meshdata['cell_corner_lon'][:].data.flatten()

        coords = np.empty((len(lat), 3), dtype=np.float64)
        coords[:, 0] = lon
        coords[:, 1] = lat
        coords[:, 2] = 0.0
        _coords = dsa.numpyTovtkDataArray(coords)
        vtk_coords = vtkPoints()
        vtk_coords.SetData(_coords)
        output2D.SetPoints(vtk_coords)

        ncells2D    = meshdata['cell_corner_lat'][:].data.shape[0]
        cellTypes   = np.empty(ncells2D,                  dtype=np.uint8)
        offsets     = np.arange(0, (4 * ncells2D) + 1, 4, dtype=np.int64)
        cells       = np.arange(ncells2D*4,               dtype=np.int64)
        cellTypes.fill(vtkConstants.VTK_QUAD)
        cellTypes   = numpy_support.numpy_to_vtk(num_array=cellTypes.ravel(), \
                                                 deep=True, array_type=vtkConstants.VTK_UNSIGNED_CHAR)
        offsets     = numpy_support.numpy_to_vtk(num_array=offsets.ravel(),   \
                                                 deep=True, array_type=vtkConstants.VTK_ID_TYPE)
        cells       = numpy_support.numpy_to_vtk(num_array=cells.ravel(),     \
                                                 deep=True, array_type=vtkConstants.VTK_ID_TYPE)
        cellArray = vtkCellArray()
        cellArray.SetData(offsets, cells)
        output2D.VTKObject.SetCells(cellTypes, cellArray)
        gridAdapter2D = dsa.WrapDataObject(output2D)
        for var in self.__vars2D:
            if self.__vars2Darr.ArrayIsEnabled(var):
                data = vardata[var][:].data[timeInd].flatten()
                gridAdapter2D.CellData.append(data, var)

        lev         = vardata['lev'][:].flatten()
        output3Dm   = dsa.WrapDataObject(vtkUnstructuredGrid.GetData(outInfo, 1))
        coords3Dm   = np.empty((levDim, len(lat), 3), dtype=np.float64)
        levInd      = 0
        for z in lev:
            coords = np.empty((len(lat), 3), dtype=np.float64)
            coords[:, 0] = lon
            coords[:, 1] = lat
            coords[:, 2] = z
            coords3Dm[levInd] = coords
            levInd = levInd + 1
        coords3Dm = coords3Dm.flatten().reshape(levDim*len(lat), 3)
        _coords = dsa.numpyTovtkDataArray(coords3Dm)
        vtk_coords = vtkPoints()
        vtk_coords.SetData(_coords)
        output3Dm.SetPoints(vtk_coords)
        cellTypesm   = np.empty(ncells2D*levDim,                  dtype=np.uint8)
        offsetsm     = np.arange(0, (4 * ncells2D*levDim) + 1, 4, dtype=np.int64)
        cellsm       = np.arange(ncells2D*levDim*4,               dtype=np.int64)
        cellTypesm.fill(vtkConstants.VTK_QUAD)
        cellTypesm   = numpy_support.numpy_to_vtk(num_array=cellTypesm.ravel(), \
                                                  deep=True, array_type=vtkConstants.VTK_UNSIGNED_CHAR)
        offsetsm     = numpy_support.numpy_to_vtk(num_array=offsetsm.ravel(),   \
                                                  deep=True, array_type=vtkConstants.VTK_ID_TYPE)
        cellsm       = numpy_support.numpy_to_vtk(num_array=cellsm.ravel(),     \
                                                  deep=True, array_type=vtkConstants.VTK_ID_TYPE)
        cellArraym = vtkCellArray()
        cellArraym.SetData(offsetsm, cellsm)
        output3Dm.VTKObject.SetCells(cellTypesm, cellArraym)
        gridAdapter3Dm = dsa.WrapDataObject(output3Dm)
        for var in self.__vars3Dm:
            if self.__vars3Dmarr.ArrayIsEnabled(var):
                data = vardata[var][:].data[timeInd].flatten()
                gridAdapter3Dm.CellData.append(data, var)
        gridAdapter3Dm.FieldData.append(levDim, "numlev")
        gridAdapter3Dm.FieldData.append(lev,    "lev"   )

        ilev        = vardata['ilev'][:].flatten()
        output3Di   = dsa.WrapDataObject(vtkUnstructuredGrid.GetData(outInfo, 2))
        coords3Di   = np.empty((ilevDim, len(lat), 3), dtype=np.float64)
        ilevInd     = 0
        for z in ilev:
            coords = np.empty((len(lat), 3), dtype=np.float64)
            coords[:, 0] = lon
            coords[:, 1] = lat
            coords[:, 2] = z
            coords3Di[ilevInd] = coords
            ilevInd = ilevInd + 1
        coords3Di = coords3Di.flatten().reshape(ilevDim*len(lat), 3)
        _coords = dsa.numpyTovtkDataArray(coords3Di)
        vtk_coords = vtkPoints()
        vtk_coords.SetData(_coords)
        output3Di.SetPoints(vtk_coords)
        cellTypesi   = np.empty(ncells2D*ilevDim,                  dtype=np.uint8)
        offsetsi     = np.arange(0, (4 * ncells2D*ilevDim) + 1, 4, dtype=np.int64)
        cellsi       = np.arange(ncells2D*ilevDim*4,               dtype=np.int64)
        cellTypesi.fill(vtkConstants.VTK_QUAD)
        cellTypesi   = numpy_support.numpy_to_vtk(num_array=cellTypesi.ravel(),     \
                                                  deep=True, array_type=vtkConstants.VTK_UNSIGNED_CHAR)
        offsetsi     = numpy_support.numpy_to_vtk(num_array=offsetsi.ravel(),       \
                                                  deep=True, array_type=vtkConstants.VTK_ID_TYPE)
        cellsi       = numpy_support.numpy_to_vtk(num_array=cellsi.ravel(),         \
                                                  deep=True, array_type=vtkConstants.VTK_ID_TYPE)
        cellArrayi = vtkCellArray()
        cellArrayi.SetData(offsetsi, cellsi)
        output3Di.VTKObject.SetCells(cellTypesi, cellArrayi)
        gridAdapter3Di = dsa.WrapDataObject(output3Di)
        for var in self.__vars3Di:
            if self.__vars3Diarr.ArrayIsEnabled(var):
                data = vardata[var][:].data[timeInd].flatten()
                gridAdapter3Di.CellData.append(data, var)
        gridAdapter3Di.FieldData.append(ilevDim, "numlev")
        gridAdapter3Di.FieldData.append(ilev,    "lev"   )

        #renderView = servermanager.GetRenderView()
        #renderView.OrientationAxesXLabelText = 'long'
        #renderView.OrientationAxesYLabelText = 'lat'
        #renderView.OrientationAxesZLabelText = 'lev'

        return 1

from paraview.util.vtkAlgorithm import *
from vtkmodules.numpy_interface import dataset_adapter as dsa
from vtkmodules.vtkCommonDataModel import (
    vtkCellArray,
)
from vtkmodules.util import vtkConstants, numpy_support
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from paraview import print_error

try:
    from vtkmodules.vtkFiltersGeneral import vtkCleanUnstructuredGrid as uGridFilter
except ImportError:
    from paraview.modules.vtkPVVTKExtensionsFiltersGeneral import (
        vtkCleanUnstructuredGrid as uGridFilter,
    )

    pass
try:
    import numpy as np

    _has_deps = True
except ImportError as ie:
    print_error(
        "Missing required Python modules/packages. Algorithms in this module may "
        "not work as expected! \n {0}".format(ie)
    )
    _has_deps = False


@smproxy.filter()
@smproperty.input(name="Input")
@smdomain.datatype(dataTypes=["vtkUnstructuredGrid"], composite_data_supported=False)
class EAMVolumize(VTKPythonAlgorithmBase):
    def __init__(self):
        super().__init__(
            nInputPorts=1, nOutputPorts=1, outputType="vtkUnstructuredGrid"
        )
        self.__Dims = -1

    def RequestDataObject(self, request, inInfo, outInfo):
        inData = self.GetInputData(inInfo, 0, 0)
        outData = self.GetOutputData(outInfo, 0)
        assert inData is not None
        if outData is None or (not outData.IsA(inData.GetClassName())):
            outData = inData.NewInstance()
            outInfo.GetInformationObject(0).Set(outData.DATA_OBJECT(), outData)
        return super().RequestDataObject(request, inInfo, outInfo)

    def RequestData(self, request, inInfo, outInfo):
        global _has_deps
        if not _has_deps:
            print_error("Required Python module 'netCDF4' or 'nunpy' missing!")
            return 0

        inData = self.GetInputData(inInfo, 0, 0)
        outData = self.GetOutputData(outInfo, 0)
        assert outData.IsA(inData.GetClassName())

        input = dsa.WrapDataObject(inData)
        output = dsa.WrapDataObject(outData)

        numpoints = input.GetNumberOfPoints()
        numcells_i = input.GetNumberOfCells()

        gridAdapterIn = dsa.WrapDataObject(inData)
        zCoords = gridAdapterIn.FieldData.GetArray("lev")
        numLevs = len(zCoords)
        numpoints2D = np.int64(numpoints / numLevs)
        numcells2D = np.int64(numcells_i / numLevs)
        hexstacksize = numLevs - 1
        numhexes = np.int64(numcells2D * hexstacksize)
        hexconn = np.empty((hexstacksize, numcells2D * 8), dtype=np.int64)
        # Hexes occupy one layer less than quads
        for i in range(0, hexstacksize):
            # Start populating from the bottom
            lower = (
                np.arange(i * numpoints2D, (i + 1) * numpoints2D, dtype=np.int64)
                .reshape(numcells2D, 4)
                .transpose()
            )
            upper = (
                np.arange((i + 1) * numpoints2D, (i + 2) * numpoints2D, dtype=np.int64)
                .reshape(numcells2D, 4)
                .transpose()
            )
            conn = np.append(lower, upper, axis=0).flatten("F")
            hexconn[i] = conn
        hexconn = hexconn.flatten()

        output.SetPoints(input.GetPoints())
        cellTypes = np.empty(numhexes, dtype=np.uint8)
        offsets = np.arange(0, (8 * numhexes) + 1, 8, dtype=np.int64)
        cellTypes.fill(vtkConstants.VTK_HEXAHEDRON)
        cellTypes = numpy_support.numpy_to_vtk(
            num_array=cellTypes.ravel(),
            deep=True,
            array_type=vtkConstants.VTK_UNSIGNED_CHAR,
        )
        offsets = numpy_support.numpy_to_vtk(
            num_array=offsets.ravel(), deep=True, array_type=vtkConstants.VTK_ID_TYPE
        )
        cells = numpy_support.numpy_to_vtk(
            num_array=hexconn.ravel(), deep=True, array_type=vtkConstants.VTK_ID_TYPE
        )
        cellArray = vtkCellArray()
        cellArray.SetData(offsets, cells)
        output.VTKObject.SetCells(cellTypes, cellArray)

        numVars = input.VTKObject.GetCellData().GetNumberOfArrays()
        for i in range(numVars):
            varname = input.VTKObject.GetCellData().GetArray(i).GetName()
            vardata = np.array(input.VTKObject.GetCellData().GetArray(i))
            outvardata = np.empty((hexstacksize, numcells2D))
            for i in range(0, hexstacksize):
                # Start populating from the bottom
                lower = vardata[(i + 0) * numcells2D : (i + 1) * numcells2D]
                upper = vardata[(i + 1) * numcells2D : (i + 2) * numcells2D]
                averaged = (upper + lower) / 2
                outvardata[i] = averaged
            output.CellData.append(outvardata.flatten(), varname)

        numVars = input.VTKObject.GetPointData().GetNumberOfArrays()
        for i in range(numVars):
            varname = input.VTKObject.GetPointData().GetArray(i).GetName()
            vardata = np.array(input.VTKObject.GetPointData().GetArray(i))
            output.PointData.append(vardata, varname)

        cleaner = uGridFilter()
        cleaner.SetInputData(output.VTKObject)
        cleaner.Update()
        outData.ShallowCopy(cleaner.GetOutput())

        return 1


@smproxy.filter()
@smproperty.input(name="Input")
@smdomain.datatype(dataTypes=["vtkUnstructuredGrid"], composite_data_supported=False)
class EAMExtractSlices(VTKPythonAlgorithmBase):
    def __init__(self):
        super().__init__(
            nInputPorts=1, nOutputPorts=1, outputType="vtkUnstructuredGrid"
        )
        self.__Min = -1
        self.__Max = -1

    def RequestDataObject(self, request, inInfo, outInfo):
        inData = self.GetInputData(inInfo, 0, 0)
        outData = self.GetOutputData(outInfo, 0)
        assert inData is not None
        if outData is None or (not outData.IsA(inData.GetClassName())):
            outData = inData.NewInstance()
            outInfo.GetInformationObject(0).Set(outData.DATA_OBJECT(), outData)
        return super().RequestDataObject(request, inInfo, outInfo)

    @smproperty.intvector(
        name="MinMaxPlanes", label="Planes (Min - Max)", default_values=[0, 0]
    )
    @smdomain.intrange(min=0, max=100)
    def SetMaxPlane(self, min, max):
        if min > max:
            print_error("Plane min cannot exceed plane max")
            return 0
        if self.__Max != max:
            self.__Max = max
            self.Modified()
        if self.__Min != min:
            self.__Min = min
            self.Modified()

    def RequestData(self, request, inInfo, outInfo):
        global _has_deps
        if not _has_deps:
            print_error("Required Python module 'netCDF4' or 'numpy' missing!")
            return 0

        inData = self.GetInputData(inInfo, 0, 0)
        outData = self.GetOutputData(outInfo, 0)
        assert outData.IsA(inData.GetClassName())

        input = dsa.WrapDataObject(inData)
        output = dsa.WrapDataObject(outData)

        numPoints = input.GetNumberOfPoints()
        numCells = input.GetNumberOfCells()

        gridAdapterIn = dsa.WrapDataObject(inData)
        zCoords = gridAdapterIn.FieldData.GetArray("lev")
        numLevs = len(zCoords)
        numPoints2D = np.int64(numPoints / numLevs)
        numCells2D = np.int64(numCells / numLevs)

        pMin = max(self.__Min, 0)
        pMax = min(self.__Max, numLevs - 1)
        pStart = pMin * numPoints2D
        pEnd = (pMax + 1) * numPoints2D
        cStart = pMin * numCells2D
        cEnd = (pMax + 1) * numCells2D
        numPlanes = (pMax - pMin) + 1
        if pMin > pMax:
            print_error("Error in interpreting min and max planes")
            return 0

        inpPoints = input.GetPoints()
        outPoints = inpPoints[pStart:pEnd]
        output.SetPoints(outPoints)

        cellTypes = np.empty(numCells2D * numPlanes, dtype=np.uint8)
        offsets = np.arange(0, (4 * numCells2D * numPlanes) + 1, 4, dtype=np.int64)
        cells = np.arange(numCells2D * numPlanes * 4, dtype=np.int64)
        cellTypes.fill(vtkConstants.VTK_QUAD)
        cellTypes = numpy_support.numpy_to_vtk(
            num_array=cellTypes.ravel(),
            deep=True,
            array_type=vtkConstants.VTK_UNSIGNED_CHAR,
        )
        offsets = numpy_support.numpy_to_vtk(
            num_array=offsets.ravel(), deep=True, array_type=vtkConstants.VTK_ID_TYPE
        )
        cells = numpy_support.numpy_to_vtk(
            num_array=cells.ravel(), deep=True, array_type=vtkConstants.VTK_ID_TYPE
        )
        cellArray = vtkCellArray()
        cellArray.SetData(offsets, cells)
        output.VTKObject.SetCells(cellTypes, cellArray)

        numVars = input.VTKObject.GetCellData().GetNumberOfArrays()
        for i in range(numVars):
            varname = input.VTKObject.GetCellData().GetArray(i).GetName()
            if varname.startswith("vtk"):
                continue
            inpVardata = np.array(input.VTKObject.GetCellData().GetArray(i))
            outVardata = inpVardata[cStart:cEnd]
            output.CellData.append(outVardata, varname)

        numVars = input.VTKObject.GetPointData().GetNumberOfArrays()
        for i in range(numVars):
            varname = input.VTKObject.GetPointData().GetArray(i).GetName()
            if varname.startswith("vtk"):
                continue
            inpVardata = np.array(input.VTKObject.GetPointData().GetArray(i))
            outVardata = inpVardata[pStart:pEnd]
            output.PointData.append(outVardata, varname)

        gridAdapter = dsa.WrapDataObject(output)
        gridAdapter.FieldData.append(numPlanes, "numlev")
        gridAdapter.FieldData.append(zCoords[pMin : pMax + 1], "lev")

        return 1


@smproxy.filter()
@smproperty.input(name="Input")
@smdomain.datatype(
    dataTypes=["vtkImageData", "vtkUniformGrid", "vtkRectilinearGrid"],
    composite_data_supported=False,
)
@smproperty.xml(
    """
                <IntVectorProperty name="Checkbox 1"
                      command="SetZonalAverage"
                      number_of_elements="1"
                      default_values="1">
                    <BooleanDomain name="bool"/>
                 </IntVectorProperty>
                """
)
class EAMAverage(VTKPythonAlgorithmBase):
    def __init__(self):
        super().__init__(nInputPorts=1, nOutputPorts=1, outputType="vtkImageData")
        self.__Dims = -1

    def SetZonalAverage(self, zonal):
        pass

    def RequestData(self, request, inInfo, outInfo):
        global _has_deps
        if not _has_deps:
            print_error("Required Python module 'netCDF4' or 'numpy' missing!")
            return 0

        inData = self.GetInputData(inInfo, 0, 0)
        outData = self.GetOutputData(outInfo, 0)
        assert outData.IsA("vtkImageData")

        dims = inData.GetDimensions()
        origin = inData.GetOrigin()
        bounds = inData.GetBounds()
        inData.GetExtent()
        outData.SetOrigin(0, origin[1], origin[2])
        outData.SetSpacing(
            0,
            (bounds[3] - bounds[2]) / (dims[1] - 1),
            (bounds[5] - bounds[4]) / (dims[2] - 1),
        )
        outData.SetExtent(0, 0, 0, dims[1] - 1, 0, dims[2] - 1)

        output = dsa.WrapDataObject(outData)

        numVars = inData.GetPointData().GetNumberOfArrays()
        for i in range(numVars):
            varname = inData.GetPointData().GetArray(i).GetName()
            if varname.startswith("vtk"):
                continue
            vardata = np.array(inData.GetPointData().GetArray(i))
            newdata = vardata.reshape((dims[2], dims[1], dims[0]))
            newdata = newdata.transpose((2, 0, 1))
            newdata = newdata.mean(axis=0, keepdims=True)
            newdata = newdata.flatten()
            output.PointData.append(newdata, varname)
        return 1

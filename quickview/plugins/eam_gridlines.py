from paraview.util.vtkAlgorithm import *
from vtkmodules.numpy_interface import dataset_adapter as dsa
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkCellArray

from vtkmodules.util import numpy_support, vtkConstants
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
import numpy as np

# Optional import that may be used in future versions
# try:
#     from vtkmodules.vtkFiltersGeneral import vtkCleanUnstructuredGrid as uGridFilter
# except ImportError:
#     pass


@smproxy.source(name="EAMGridLines")
class EAMGridLines(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(
            self, nInputPorts=0, nOutputPorts=1, outputType="vtkUnstructuredGrid"
        )
        self.llat = -90.0
        self.hlat = 90.0
        self.llon = -180.0
        self.hlon = 180.0
        self.interval = 30

    @smproperty.xml(
        """
        <DoubleVectorProperty name="Longitude Range"
            number_of_elements="2"
            default_values="-180 180"
            command="SetLongRange">
            <DoubleRangeDomain name="Longitude Range" />
            <Documentation>Set the minimum and maximin for the Longitude Lines</Documentation>
        </DoubleVectorProperty>"""
    )
    def SetLongRange(self, llon, hlon):
        if self.llon != llon or self.hlon != hlon:
            self.llon = llon
            self.hlon = hlon
            self.Modified()

    @smproperty.xml(
        """
        <DoubleVectorProperty name="Latitude Range"
            number_of_elements="2"
            default_values="-90 90"
            command="SetLatRange">
            <DoubleRangeDomain name="Latitude Range" />
            <Documentation>Set the minimum and maximin for the Latitude Lines</Documentation>
        </DoubleVectorProperty>"""
    )
    def SetLatRange(self, llat, hlat):
        if self.llat != llat or self.hlat != hlat:
            self.llat = llat
            self.hlat = hlat
            self.Modified()

    @smproperty.xml(
        """
                  <IntVectorProperty name="Interval"
                    command="SetInterval"
                    number_of_elements="1"
                    default_values="30">
                </IntVectorProperty>
                """
    )
    def SetInterval(self, interval):
        if self.interval != interval:
            self.interval = interval
            self.Modified()

    def RequestInformation(self, request, inInfo, outInfo):
        return super().RequestInformation(request, inInfo, outInfo)

    def RequestUpdateExtent(self, request, inInfo, outInfo):
        return super().RequestUpdateExtent(request, inInfo, outInfo)

    def RequestData(self, request, inInfo, outInfo):
        interval = self.interval
        llon = self.llon
        hlon = self.hlon
        llat = self.llat
        hlat = self.hlat

        import math

        llon = math.floor(llon / interval) * interval
        hlon = math.ceil(hlon / interval) * interval
        xextent = hlon - llon
        llat = math.floor(llat / interval) * interval
        hlat = math.ceil(hlat / interval) * interval
        yextent = hlat - llat

        output = dsa.WrapDataObject(vtkUnstructuredGrid.GetData(outInfo, 0))

        # Getting Longitude lines
        longs = int(xextent / interval) + 1
        lonpoints = 100 * longs  # 100 points per longitude line

        # Getting Latitude lines
        lats = int(yextent / interval) + 1
        latpoints = 10 * lats  # 10 points per latitude line

        shape = (lonpoints + latpoints, 3)
        coords = np.empty(shape, dtype=np.float64)

        # Generate longitude line x-coordinates (longitude values)
        lonx = np.linspace(llon, hlon, longs)
        lonx = np.repeat(lonx, 100)  # Each longitude line has 100 points

        # Generate longitude line y-coordinates (latitude values)
        lony = np.linspace(llat, hlat, 100)
        lony = np.tile(lony, longs)  # Repeat for each longitude line

        # Generate latitude line x-coordinates (longitude values)
        latx = np.linspace(llon, hlon, 10)  # 10 points per latitude line
        latx = np.tile(latx, lats)  # Repeat for each latitude line

        # Generate latitude line y-coordinates (latitude values)
        laty = np.linspace(llat, hlat, lats)
        laty = np.repeat(laty, 10)  # Each latitude line has 10 points

        # Verify array sizes before assignment
        assert len(lonx) == lonpoints, f"lonx size {len(lonx)} != expected {lonpoints}"
        assert len(lony) == lonpoints, f"lony size {len(lony)} != expected {lonpoints}"
        assert len(latx) == latpoints, f"latx size {len(latx)} != expected {latpoints}"
        assert len(laty) == latpoints, f"laty size {len(laty)} != expected {latpoints}"

        coords[:lonpoints, 0] = lonx
        coords[:lonpoints, 1] = lony
        coords[:lonpoints, 2] = 1.0
        coords[lonpoints:, 0] = latx
        coords[lonpoints:, 1] = laty
        coords[lonpoints:, 2] = 1.0
        _coords = dsa.numpyTovtkDataArray(coords)

        vtk_coords = vtkPoints()
        vtk_coords.SetData(_coords)
        output.SetPoints(vtk_coords)
        ncells = longs + lats
        cellTypes = np.empty(ncells, dtype=np.uint8)

        # Build cell offsets array
        offsets = np.empty(ncells + 1, dtype=np.int64)

        # Longitude line offsets (each line has 100 points)
        for i in range(longs):
            offsets[i] = i * 100

        # Latitude line offsets (each line has 10 points)
        for i in range(lats):
            offsets[longs + i] = lonpoints + i * 10

        # Final offset
        offsets[-1] = lonpoints + latpoints

        # Build connectivity array for polylines
        cells = np.arange(lonpoints + latpoints, dtype=np.int64)

        cellTypes.fill(vtkConstants.VTK_POLY_LINE)
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
        return 1

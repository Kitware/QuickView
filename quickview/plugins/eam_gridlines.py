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
        xspc = xextent / 9.0

        llat = math.floor(llat / interval) * interval
        hlat = math.ceil(hlat / interval) * interval
        yextent = hlat - llat
        yspc = yextent / 99.0

        output = dsa.WrapDataObject(vtkUnstructuredGrid.GetData(outInfo, 0))

        # Getting Longitude lines
        longs = int(xextent / interval) + 1
        lonpoints = 100 * longs

        lats = int(yextent / interval) + 1
        latpoints = 10 * lats

        shape = (lonpoints + latpoints, 3)
        coords = np.empty(shape, dtype=np.float64)

        lonx = np.arange(llon, hlon + interval, interval)
        lonx = np.hstack((lonx,) * 100).reshape((100, longs)).transpose().flatten()
        lony = np.arange(llat, hlat + yspc, yspc)
        lony = np.hstack((lony,) * longs)

        latx = np.arange(llon, hlon + xspc, xspc)
        latx = np.hstack((latx,) * lats)
        laty = np.arange(llat, hlat + interval, interval)
        laty = np.hstack((laty,) * 10).reshape((10, lats)).transpose().flatten()

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

        offsets = np.empty(ncells + 1, dtype=np.int64)
        off1 = np.arange(0, (100 * longs) + 1, 100, dtype=np.int64)
        off2 = np.arange(lonpoints, lonpoints + (10 * lats) + 1, 10, dtype=np.int64)

        offsets[:longs] = off1[:-1]
        offsets[longs:] = off2

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

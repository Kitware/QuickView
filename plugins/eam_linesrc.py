from paraview.util.vtkAlgorithm import *
from vtkmodules.vtkCommonCore import vtkPoints, vtkIdTypeArray
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkPolyData, vtkCellArray
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.numpy_interface import dataset_adapter as dsa
from vtkmodules.util import vtkConstants, numpy_support

import numpy as np

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

@smproxy.source(name="EAMLineSource")
@smproperty.xml("""
                <IntVectorProperty name="longitude"
                    number_of_elements="1"
                    command="SetLongitude"
                    default_values="0">
                </IntVectorProperty>
                """)
class EAMLineSource(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=0,
            nOutputPorts=1,
            outputType='vtkPolyData')
        self.longitude = 0

    def RequestInformation(self, request, inInfo, outInfo):
        return super().RequestInformation(request, inInfo, outInfo)
        
    def RequestUpdateExtent(self, request, inInfo, outInfo):
        return super().RequestUpdateExtent(request, inInfo, outInfo)

    def SetLongitude(self, long_):
        self.longitude = long_
        self.Modified()

    def RequestData(self, request, inInfo, outInfo):
        x = self.longitude
        y = list(range(-90, 91, 1))
        points = vtkPoints()
        for i in y:
            # Add points to the vtkPoints object
            points.InsertNextPoint(x, i, 0)
        # Create a vtkCellArray to define the connectivity of the polyline
        line = vtkCellArray()
        line.InsertNextCell(len(y))  # 4 is the number of points in the polyline
        index = 0
        for i in range(len(y)):
            line.InsertCellPoint(i)
        # Create a vtkPolyData object to hold the points and the polyline
        polyData = vtkPolyData.GetData(outInfo, 0)
        polyData.SetPoints(points)
        polyData.SetLines(line)
        '''
        outdata = dsa.WrapDataObject(vtkUnstructuredGrid.GetData(outInfo, 0))

        x = self.longitude
        y = np.array(list(range(-90, 91, 1)))

        coords = np.empty((len(y), 3), dtype=np.float64)
        coords[:, 0] = x
        coords[:, 1] = y
        coords[:, 2] = 0.0

        ncells      = 1
        cellTypes   = np.empty(ncells,          dtype=np.uint8)
        offsets     = np.arange(0, ncells + 1,  dtype=np.int64)
        cells       = np.arange(ncells,         dtype=np.int64)

        cellTypes.fill(vtkConstants.VTK_POLY_LINE)
        cellTypes   = numpy_support.numpy_to_vtk(num_array=cellTypes.ravel(), deep=True, array_type=vtkConstants.VTK_UNSIGNED_CHAR)
        offsets     = numpy_support.numpy_to_vtk(num_array=offsets.ravel(),   deep=True, array_type=vtkConstants.VTK_ID_TYPE)
        cells       = numpy_support.numpy_to_vtk(num_array=cells.ravel(),     deep=True, array_type=vtkConstants.VTK_ID_TYPE)

        cellArray = vtkCellArray()
        cellArray.SetData(offsets, cells)

        outdata.SetPoints(coords)
        print(dir(outdata.VTKObject))
        outdata.VTKObject.SetCells(cellTypes, cellArray)
        '''
        return 1

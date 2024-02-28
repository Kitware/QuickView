from paraview.simple import *
from paraview.util.vtkAlgorithm import *
from vtkmodules.numpy_interface import dataset_adapter as dsa
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkPolyData, vtkCellArray
from vtkmodules.vtkFiltersCore import vtkAppendFilter
from vtkmodules.util import vtkConstants, numpy_support
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from paraview import print_error

import math
import time

try:
    import numpy as np
except:
    print("The numpy library is not installed. Install the numpy library to be able to put the data set on a sphere.")

def ProcessPoint(point, radius):
    #theta = math.radians(point[0] - 180.)
    #phi   = math.radians(point[1])
    #rho   = 1.0
    theta   = point[0]
    phi     = 90 - point[1]
    rho     = (1000 - point[2]) + radius if not point[2] == 0 else radius
    x = rho * math.sin(math.radians(phi)) * math.cos(math.radians(theta))
    y = rho * math.sin(math.radians(phi)) * math.sin(math.radians(theta))
    z = rho * math.cos(math.radians(phi))
    return [x, y, z]

@smproxy.filter()
@smproperty.input(name="Input")
@smdomain.datatype(dataTypes=["vtkUnstructuredGrid","vtkPolyData"], composite_data_supported=False)
class EAMSphere(VTKPythonAlgorithmBase):
    def __init__(self):
        super().__init__(nInputPorts=1, nOutputPorts=1, outputType="vtkUnstructuredGrid")
        self.__Dims = -1
        self.isData = False
        self.radius = 2000

    @smproperty.intvector(name="Data Layer", default_values=[0])
    @smdomain.xml(\
        """<BooleanDomain name="bool"/>
        """)
    def SetDataLayer(self, isData_):
        if not self.isData == isData_: 
            self.isData = isData_
            self.Modified()

    def RequestDataObject(self, request, inInfo, outInfo):
        inData = self.GetInputData(inInfo, 0, 0)
        outData = self.GetOutputData(outInfo, 0)
        assert inData is not None
        if outData is None or (not outData.IsA(inData.GetClassName())):
            outData = inData.NewInstance()
            outInfo.GetInformationObject(0).Set(outData.DATA_OBJECT(), outData)
        return super().RequestDataObject(request, inInfo, outInfo)

    def RequestData(self, request, inInfo, outInfo):
        inData = self.GetInputData(inInfo, 0, 0)
        outData = self.GetOutputData(outInfo, 0)
        outData.DeepCopy(inData)

        inWrap     = dsa.WrapDataObject(inData)
        outWrap    = dsa.WrapDataObject(outData)

        inPoints    = np.array(inWrap.Points)
        pRadius     = (self.radius + 1) if self.isData else self.radius
        outPoints   = np.array(list(map(lambda x: ProcessPoint( x , pRadius), inPoints)))
        
        _coords = numpy_support.numpy_to_vtk(outPoints, deep=True, array_type=vtkConstants.VTK_FLOAT)
        vtk_coords = vtkPoints()
        vtk_coords.SetData(_coords)
        outWrap.SetPoints(vtk_coords)

        return 1

@smproxy.filter()
@smproperty.input(name="Input")
@smdomain.datatype(dataTypes=["vtkUnstructuredGrid","vtkPolyData"], composite_data_supported=False)
class EAMVTSSphere(VTKPythonAlgorithmBase):
    def __init__(self):
        super().__init__(nInputPorts=1, nOutputPorts=1)
        self.__Dims = -1
        self.isData = False
        self.radius = 2000

    @smproperty.intvector(name="Data Layer", default_values=[0])
    @smdomain.xml(\
        """<BooleanDomain name="bool"/>
        """)
    def SetDataLayer(self, isData_):
        if not self.isData == isData_: 
            self.isData = isData_
            self.Modified()

    def RequestDataObject(self, request, inInfo, outInfo):
        inData = self.GetInputData(inInfo, 0, 0)
        outData = self.GetOutputData(outInfo, 0)
        assert inData is not None
        if outData is None or (not outData.IsA(inData.GetClassName())):
            outData = inData.NewInstance()
            outInfo.GetInformationObject(0).Set(outData.DATA_OBJECT(), outData)
        return super().RequestDataObject(request, inInfo, outInfo)

    def RequestData(self, request, inInfo, outInfo):
        inData = self.GetInputData(inInfo, 0, 0)
        outData = self.GetOutputData(outInfo, 0)
        outData.DeepCopy(inData)

        inWrap     = dsa.WrapDataObject(inData)
        outWrap    = dsa.WrapDataObject(outData)

        inPoints    = np.array(inWrap.Points)
        pRadius     = (self.radius + 1) if self.isData else self.radius
        outPoints   = np.array(list(map(lambda x: ProcessPoint( x , pRadius), inPoints)))
        #outPoints   = np.array(list(map(ProcessPoint,inPoints)))
        
        _coords = numpy_support.numpy_to_vtk(outPoints, deep=True, array_type=vtkConstants.VTK_FLOAT)
        vtk_coords = vtkPoints()
        vtk_coords.SetData(_coords)
        outWrap.SetPoints(vtk_coords)

        return 1

@smproxy.source(name="EAMLineSource")
@smproperty.xml("""
                <IntVectorProperty name="longitude"
                    command="SetLongitude"
                    number_of_elements="1"
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
        return 1

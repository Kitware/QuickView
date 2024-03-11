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

try:
    import numpy as np
    import pandas as pd
    from pyproj import Proj, Transformer
    _has_deps = True
except ImportError as ie:
    print_error(
        "Missing required Python modules/packages. Algorithms in this module may "
        "not work as expected! \n {0}".format(ie))
    _has_deps = False

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
        
        if inData.IsA('vtkPolyData'):
            afilter = vtkAppendFilter()
            afilter.AddInputData(inData)
            afilter.Update() 
            out = afilter.GetOutput()
            outData.DeepCopy(afilter.GetOutput())
        else:
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

@smproxy.filter()
@smproperty.input(name="Input")
@smdomain.datatype(dataTypes=["vtkPolyData","vtkUnstructuredGrid"], composite_data_supported=False)
@smproperty.xml("""
                <IntVectorProperty name="Translate"
                      command="SetTranslation"
                      number_of_elements="1"
                      default_values="0">
                    <BooleanDomain name="bool"/>
                 </IntVectorProperty>
                 <IntVectorProperty
                    name="Projection"
                    command="SetProjection"
                    number_of_elements="1"
                    default_values="0">
                    <EnumerationDomain name="enum">
                        <Entry value="0" text="Robinson"/>
                        <Entry value="1" text="Mollweide"/>
                    </EnumerationDomain>
                </IntVectorProperty>
                """)
class EAMProject(VTKPythonAlgorithmBase):
    def __init__(self):
        super().__init__(nInputPorts=1, nOutputPorts=1, outputType="vtkUnstructuredGrid")
        self.__Dims = -1
        self.project = 0
        self.translate = False

    def SetTranslation(self, translate):
        if self.translate != translate:
            self.translate = translate
            self.Modified()

    def SetProjection(self, project):
        if self.project != int(project):
            self.project = int(project)
            self.Modified()

    def RequestData(self, request, inInfo, outInfo):
        inData = self.GetInputData(inInfo, 0, 0)
        outData = self.GetOutputData(outInfo, 0)
        if inData.IsA('vtkPolyData'):
            afilter = vtkAppendFilter()
            afilter.AddInputData(inData)
            afilter.Update()
            out = afilter.GetOutput()
            outData.DeepCopy(afilter.GetOutput())
        else:
            outData.DeepCopy(inData)

        inWrap     = dsa.WrapDataObject(inData)
        outWrap     = dsa.WrapDataObject(outData)
        inPoints    = np.array(inWrap.Points)

        flat = inPoints.flatten()
        x = flat[0::3] - 180. if self.translate else flat[0::3]
        y = flat[1::3]

        latlon  = Proj(init="epsg:4326")
        if self.project == 0:
            proj = Proj(proj="robin")
        elif self.project == 1:
            proj = Proj(proj="moll")

        xformer = Transformer.from_proj(latlon, proj)
        res = xformer.transform(x, y)
        flat[0::3] = np.array(res[0])
        flat[1::3] = np.array(res[1])

        outPoints = flat.reshape(inPoints.shape)
        _coords = numpy_support.numpy_to_vtk(outPoints, deep=True, array_type=vtkConstants.VTK_FLOAT)
        vtk_coords = vtkPoints()
        vtk_coords.SetData(_coords)
        outWrap.SetPoints(vtk_coords)

        return 1
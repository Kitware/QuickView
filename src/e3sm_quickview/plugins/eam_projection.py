from paraview.simple import *
from paraview.util.vtkAlgorithm import *
from vtkmodules.numpy_interface import dataset_adapter as dsa
from vtkmodules.vtkCommonCore import (
    vtkPoints,
)
from vtkmodules.vtkCommonDataModel import (
    vtkCellArray,
    vtkDataSetAttributes,
    vtkPlane,
    vtkPolyData,
)
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkFiltersCore import (
    vtkAppendFilter,
    vtkCellCenters,
    vtkGenerateIds,
    vtkPolyDataToUnstructuredGrid,
)
from vtkmodules.vtkFiltersGeneral import (
    vtkTableBasedClipDataSet,
    vtkTransformFilter,
)
from vtkmodules.vtkFiltersPoints import (
    vtkExtractSurface
)
from vtkmodules.vtkFiltersGeometry import (
    vtkGeometryFilter
)

try:
    from paraview.modules.vtkPVVTKExtensionsFiltersGeneral import vtkPVClipDataSet
    from paraview.modules.vtkPVVTKExtensionsMisc import vtkPVBox
except Exception as e:
    print(e)
from vtkmodules.util import vtkConstants, numpy_support
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from paraview import print_error

import math

try:
    import numpy as np
    import warnings
    from pyproj import Proj, Transformer

    warnings.filterwarnings("ignore", category=FutureWarning, module="pyproj")
    _has_deps = True
except ImportError as ie:
    print_error(
        "Missing required Python modules/packages. Algorithms in this module may "
        "not work as expected! \n {0}".format(ie)
    )
    _has_deps = False


def ProcessPoint(point, radius):
    # theta = math.radians(point[0] - 180.)
    # phi   = math.radians(point[1])
    # rho   = 1.0
    theta = point[0]
    phi = 90 - point[1]
    rho = (1000 - point[2]) + radius if not point[2] == 0 else radius
    x = rho * math.sin(math.radians(phi)) * math.cos(math.radians(theta))
    y = rho * math.sin(math.radians(phi)) * math.sin(math.radians(theta))
    z = rho * math.cos(math.radians(phi))
    return [x, y, z]


@smproxy.filter()
@smproperty.input(name="Input")
@smdomain.datatype(
    dataTypes=["vtkUnstructuredGrid", "vtkPolyData"], composite_data_supported=False
)
class EAMSphere(VTKPythonAlgorithmBase):
    def __init__(self):
        super().__init__(
            nInputPorts=1, nOutputPorts=1, outputType="vtkUnstructuredGrid"
        )
        self.__Dims = -1
        self.isData = False
        self.radius = 2000

    @smproperty.intvector(name="Data Layer", default_values=[0])
    @smdomain.xml(
        """<BooleanDomain name="bool"/>
        """
    )
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

        if inData.IsA("vtkPolyData"):
            afilter = vtkAppendFilter()
            afilter.AddInputData(inData)
            afilter.Update()
            afilter.GetOutput()
            outData.DeepCopy(afilter.GetOutput())
        else:
            outData.DeepCopy(inData)

        inWrap = dsa.WrapDataObject(inData)
        outWrap = dsa.WrapDataObject(outData)

        inPoints = np.array(inWrap.Points)
        pRadius = (self.radius + 1) if self.isData else self.radius
        outPoints = np.array(list(map(lambda x: ProcessPoint(x, pRadius), inPoints)))

        _coords = numpy_support.numpy_to_vtk(
            outPoints, deep=True, array_type=vtkConstants.VTK_FLOAT
        )
        vtk_coords = vtkPoints()
        vtk_coords.SetData(_coords)
        outWrap.SetPoints(vtk_coords)

        return 1


@smproxy.filter()
@smproperty.input(name="Input")
@smdomain.datatype(
    dataTypes=["vtkUnstructuredGrid", "vtkPolyData"], composite_data_supported=False
)
class EAMVTSSphere(VTKPythonAlgorithmBase):
    def __init__(self):
        super().__init__(nInputPorts=1, nOutputPorts=1)
        self.__Dims = -1
        self.isData = False
        self.radius = 2000

    @smproperty.intvector(name="Data Layer", default_values=[0])
    @smdomain.xml(
        """<BooleanDomain name="bool"/>
        """
    )
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

        inWrap = dsa.WrapDataObject(inData)
        outWrap = dsa.WrapDataObject(outData)

        inPoints = np.array(inWrap.Points)
        pRadius = (self.radius + 1) if self.isData else self.radius
        outPoints = np.array(list(map(lambda x: ProcessPoint(x, pRadius), inPoints)))
        # outPoints   = np.array(list(map(ProcessPoint,inPoints)))

        _coords = numpy_support.numpy_to_vtk(
            outPoints, deep=True, array_type=vtkConstants.VTK_FLOAT
        )
        vtk_coords = vtkPoints()
        vtk_coords.SetData(_coords)
        outWrap.SetPoints(vtk_coords)

        return 1


@smproxy.source(name="EAMLineSource")
@smproperty.xml(
    """
                <IntVectorProperty name="longitude"
                    command="SetLongitude"
                    number_of_elements="1"
                    default_values="0">
                </IntVectorProperty>
                """
)
class EAMLineSource(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(
            self, nInputPorts=0, nOutputPorts=1, outputType="vtkPolyData"
        )
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
        for i in range(len(y)):
            line.InsertCellPoint(i)
        # Create a vtkPolyData object to hold the points and the polyline
        polyData = vtkPolyData.GetData(outInfo, 0)
        polyData.SetPoints(points)
        polyData.SetLines(line)
        return 1


@smproxy.filter()
@smproperty.input(name="Input")
@smdomain.datatype(
    dataTypes=["vtkPolyData", "vtkUnstructuredGrid"], composite_data_supported=False
)
@smproperty.xml(
    """
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
                        <Entry value="0" text="Cyl. Equidistant"/>
                        <Entry value="1" text="Robinson"/>
                        <Entry value="2" text="Mollweide"/>
                    </EnumerationDomain>
                </IntVectorProperty>
                """
)
class EAMProject(VTKPythonAlgorithmBase):
    def __init__(self):
        super().__init__(
            nInputPorts=1, nOutputPorts=1, outputType="vtkUnstructuredGrid"
        )
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
        if inData.IsA("vtkPolyData"):
            afilter = vtkAppendFilter()
            afilter.AddInputData(inData)
            afilter.Update()
            outData.DeepCopy(afilter.GetOutput())
        else:
            outData.DeepCopy(inData)

        if self.project == 0:
            return 1

        inWrap = dsa.WrapDataObject(inData)
        outWrap = dsa.WrapDataObject(outData)
        inPoints = np.array(inWrap.Points)

        flat = inPoints.flatten()
        x = flat[0::3] - 180.0 if self.translate else flat[0::3]
        y = flat[1::3]

        try:
            # Use proj4 string for WGS84 instead of EPSG code to avoid database dependency
            latlon = Proj(proj="latlong", datum="WGS84")
            if self.project == 1:
                proj = Proj(proj="robin")
            elif self.project == 2:
                proj = Proj(proj="moll")
            else:
                # Should not reach here, but return without transformation
                return 1

            xformer = Transformer.from_proj(latlon, proj, always_xy=True)
            res = xformer.transform(x, y)
        except Exception as e:
            print(f"Projection error: {e}")
            # If projection fails, return without modifying coordinates
            return 1
        flat[0::3] = np.array(res[0])
        flat[1::3] = np.array(res[1])

        outPoints = flat.reshape(inPoints.shape)
        _coords = numpy_support.numpy_to_vtk(
            outPoints, deep=True, array_type=vtkConstants.VTK_FLOAT
        )
        vtk_coords = vtkPoints()
        vtk_coords.SetData(_coords)
        outWrap.SetPoints(vtk_coords)

        return 1


@smproxy.filter()
@smproperty.input(name="Input")
@smdomain.datatype(
    dataTypes=["vtkPolyData", "vtkUnstructuredGrid"], composite_data_supported=False
)
@smproperty.xml(
    """
                <DoubleVectorProperty name="Longitude Range"
                      command="SetLongitudeRange"
                      number_of_elements="2"
                      default_values="-180 180">
                 </DoubleVectorProperty>
                <DoubleVectorProperty name="Latitude Range"
                      command="SetLatitudeRange"
                      number_of_elements="2"
                      default_values="-90 90">
                 </DoubleVectorProperty>
                """
)
class EAMTransformAndExtract(VTKPythonAlgorithmBase):
    def __init__(self):
        super().__init__(
            nInputPorts=1, nOutputPorts=1, outputType="vtkUnstructuredGrid"
        )
        self.project = 0
        self.longrange = [-180.0, 180.0]
        self.latrange = [-90.0, 90.0]

    def SetLongitudeRange(self, min, max):
        if self.longrange[0] != min or self.longrange[1] != max:
            self.longrange = [min, max]
            self.Modified()

    def SetLatitudeRange(self, min, max):
        if self.latrange[0] != min or self.latrange[1] != max:
            self.latrange = [min, max]
            self.Modified()

    def RequestData(self, request, inInfo, outInfo):
        inData = self.GetInputData(inInfo, 0, 0)
        outData = self.GetOutputData(outInfo, 0)

        planeL = vtkPlane()
        planeL.SetOrigin([180.0, 0.0, 0.0])
        planeL.SetNormal([-1, 0, 0])
        clipL = vtkTableBasedClipDataSet()
        clipL.SetClipFunction(planeL)
        clipL.SetInputData(inData)
        clipL.Update()

        planeR = vtkPlane()
        planeR.SetOrigin([180.0, 0.0, 0.0])
        planeR.SetNormal([1, 0, 0])
        clipR = vtkTableBasedClipDataSet()
        clipR.SetClipFunction(planeR)
        clipR.SetInputData(inData)
        clipR.Update()

        transFunc = vtkTransform()
        transFunc.Translate(-360, 0, 0)
        transform = vtkTransformFilter()
        transform.SetInputData(clipR.GetOutput())
        transform.SetTransform(transFunc)
        transform.Update()

        append = vtkAppendFilter()
        append.AddInputData(clipL.GetOutput())
        append.AddInputData(transform.GetOutput())
        append.Update()

        box = vtkPVBox()
        box.SetReferenceBounds(
            self.longrange[0],
            self.longrange[1],
            self.latrange[0],
            self.latrange[1],
            -1.0,
            1.0,
        )
        box.SetUseReferenceBounds(True)
        extract = vtkPVClipDataSet()
        extract.SetClipFunction(box)
        extract.InsideOutOn()
        extract.ExactBoxClipOn()
        extract.SetInputData(append.GetOutput())
        extract.Update()

        outData.ShallowCopy(extract.GetOutput())
        return 1


@smproxy.filter()
@smproperty.input(name="Input")
@smdomain.datatype(dataTypes=["vtkPolyData"], composite_data_supported=False)
@smproperty.xml(
    """
                <DoubleVectorProperty name="Trim Longitude"
                      command="SetTrimLongitude"
                      number_of_elements="2"
                      default_values="0 0">
                 </DoubleVectorProperty>
                <DoubleVectorProperty name="Trim Latitude"
                      command="SetTrimLatitude"
                      number_of_elements="2"
                      default_values="0 0">
                 </DoubleVectorProperty>
                """
)
class EAMExtract(VTKPythonAlgorithmBase):
    def __init__(self):
        super().__init__(
            nInputPorts=1, nOutputPorts=1, outputType="vtkUnstructuredGrid"
        )
        self.trim_lon = [0, 0]
        self.trim_lat = [0, 0]

    def SetTrimLongitude(self, min, max):
        if self.trim_lon[0] != min or self.trim_lon[1] != max:
            self.trim_lon = [min, max]
            self.Modified()

    def SetTrimLatitude(self, min, max):
        if self.trim_lat[0] != min or self.trim_lat[1] != max:
            self.trim_lat = [min, max]
            self.Modified()

    def RequestData(self, request, inInfo, outInfo):
        inData = self.GetInputData(inInfo, 0, 0)
        outData = self.GetOutputData(outInfo, 0)
        if self.trim_lon == [0, 0] and self.trim_lat == [0, 0]:
            outData.ShallowCopy(inData)
            return 1
        # convert to polydata
        to_poly = vtkGeometryFilter()
        to_poly.SetInputData(inData)

        # get cell centers
        compute_centers = vtkCellCenters()
        compute_centers.SetInputConnection(to_poly.GetOutputPort())
        compute_centers.Update()

        # compute the new bounds by trimming the inData bounds
        bounds = list(inData.GetBounds())
        bounds[0] = bounds[0] + self.trim_lon[0]
        bounds[1] = bounds[1] - self.trim_lon[1]
        bounds[2] = bounds[2] + self.trim_lat[0]
        bounds[3] = bounds[3] - self.trim_lat[1]

        # add the cell centers as cell data array
        outData.ShallowCopy(inData)
        #import pdb;pdb.set_trace()
        cell_centers = compute_centers.GetOutput().GetPoints().GetData()
        cell_centers.SetName("CellCenters")
        outData.GetCellData().AddArray(cell_centers)

        # get the numpy array for cell centers
        cc = numpy_support.vtk_to_numpy(cell_centers)


        # add hidden cells based on bounds
        outside_mask = (
            (cc[:,0] < bounds[0]) | (cc[:,0] > bounds[1]) |
            (cc[:,1] < bounds[2]) | (cc[:,1] > bounds[3])
        )

        # Create ghost array (0 = visible, HIDDENCELL = invisible)
        ghost = np.where(outside_mask, vtkDataSetAttributes.HIDDENCELL, 0).astype(np.uint8)

        # Convert to VTK and add to output
        ghost_vtk = numpy_support.numpy_to_vtk(ghost)
        ghost_vtk.SetName(vtkDataSetAttributes.GhostArrayName())
        outData.GetCellData().AddArray(ghost_vtk)

        return 1


@smproxy.filter()
@smproperty.input(name="Input")
@smproperty.xml(
    """
                <IntVectorProperty name="Meridian"
                    command="SetMeridian"
                    number_of_elements="1"
                    default_values="0">
                <IntRangeDomain min="-180" max="180" name="range" />
                <Documentation>
    Sets the central meridian.
    Commonly used central meridians (longitudes) (- represents West, + represents East,
     0 is Greenwitch prime meridian):
    - 0 (Prime Meridian): Standard "Western" view.
    - -90/-100: Centered on North America.
    - 100/110: Centered on Asia.
    - -150/-160: Centered on the Pacific Ocean.
    - 20: Often used to center Europe and Africa.
                </Documentation>
                </IntVectorProperty>
                """
)
@smdomain.datatype(
    dataTypes=["vtkPolyData", "vtkUnstructuredGrid"], composite_data_supported=False
)
class EAMCenterMeridian(VTKPythonAlgorithmBase):
    """Cuts an unstructured grid and re-arranges the pieces such that
    the specified meridian is in the middle.  Note that the mesh is
    specified with bounds [0, 360], but the meridian is specified in the more
    common bounds [-180, 180].
    """

    def __init__(self):
        super().__init__(
            nInputPorts=1, nOutputPorts=1, outputType="vtkUnstructuredGrid"
        )
        # common values:
        self._center_meridian = 0
        self._cached_output = None

    def __del__(self):
        if self._cached_output:
            self._cached_output.Unregister(self)

    def SetMeridian(self, meridian_):
        """
        Specifies the central meridian (longitude in the middle of the map)
        """
        if meridian_ < -180 or meridian_ > 180:
            print_error(
                "SetMeridian called with parameter outside [-180, 180]: {}".format(
                    meridian_
                )
            )
            return
        self._center_meridian = meridian_
        self.Modified()

    def GetMeridian(self):
        """
        Returns the central meridian
        """
        return self._center_meridian

    def RequestData(self, request, inInfo, outInfo):
        inData = self.GetInputData(inInfo, 0, 0)

        outData = self.GetOutputData(outInfo, 0)
        if (
            self._cached_output
            and self._cached_output.GetPoints().GetMTime() >= inData.GetPoints().GetMTime()
            and self._cached_output.GetCells().GetMTime() >= inData.GetCells().GetMTime()
        ):
            # only scalars have been added or removed
            cached_cell_data = self._cached_output.GetCellData()

            in_cell_data = inData.GetCellData()

            outData.ShallowCopy(self._cached_output)
            out_cell_data = outData.GetCellData()

            out_cell_data.Initialize()
            for i in range(in_cell_data.GetNumberOfArrays()):
                in_array = in_cell_data.GetArray(i)
                cached_array = cached_cell_data.GetArray(in_array.GetName())
                if cached_array and cached_array.GetMTime() >= in_array.GetMTime():
                    # this scalar has been seen before
                    # simply add a reference in the outData
                    out_cell_data.AddArray(cached_array)
                else:
                    # this scalar is new
                    # we have to fill in the additional cells resulted from the clip
                    out_array = in_array.NewInstance()
                    array0 = cached_cell_data.GetArray(0)
                    out_array.SetNumberOfComponents(array0.GetNumberOfComponents())
                    out_array.SetNumberOfTuples(array0.GetNumberOfTuples())
                    out_array.SetName(in_array.GetName())
                    out_cell_data.AddArray(out_array)
                    outData.cell_data[out_array.GetName()] = inData.cell_data[i][
                        self._cached_output.cell_data["PedigreeIds"]
                    ]
        else:
            generate_ids = vtkGenerateIds()
            generate_ids.SetInputData(inData)
            generate_ids.PointIdsOff()
            generate_ids.SetCellIdsArrayName("PedigreeIds")

            cut_meridian = self._center_meridian + 180
            plane = vtkPlane()
            plane.SetOrigin([cut_meridian, 0.0, 0.0])
            plane.SetNormal([-1, 0, 0])
            # vtkClipPolyData hangs
            clipL = vtkTableBasedClipDataSet()
            clipL.SetClipFunction(plane)
            clipL.SetInputConnection(generate_ids.GetOutputPort())
            clipL.Update()

            plane.SetNormal([1, 0, 0])
            clipR = vtkTableBasedClipDataSet()
            clipR.SetClipFunction(plane)
            clipR.SetInputConnection(generate_ids.GetOutputPort())
            clipR.Update()

            transFunc = vtkTransform()
            transFunc.Translate(-360, 0, 0)
            transform = vtkTransformFilter()
            transform.SetInputData(clipR.GetOutput())
            transform.SetTransform(transFunc)
            transform.Update()

            append = vtkAppendFilter()
            append.AddInputData(clipL.GetOutput())
            append.AddInputData(transform.GetOutput())
            append.Update()
            outData.ShallowCopy(append.GetOutput())
            if self._cached_output:
                self._cached_output.Unregister(self)
            self._cached_output = outData.NewInstance()
            self._cached_output.ShallowCopy(outData)
            self._cached_output.Register(self)
        return 1

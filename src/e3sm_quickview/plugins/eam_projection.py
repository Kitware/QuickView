from paraview.simple import *
from paraview.util.vtkAlgorithm import *
from vtkmodules.vtkCommonCore import (
    vtkPoints,
    vtkUnsignedCharArray,
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
)
from vtkmodules.vtkFiltersGeneral import (
    vtkTableBasedClipDataSet,
    vtkTransformFilter,
)
from vtkmodules.vtkFiltersGeometry import vtkGeometryFilter

try:
    from paraview.modules.vtkPVVTKExtensionsFiltersGeneral import vtkPVClipDataSet
    from paraview.modules.vtkPVVTKExtensionsMisc import vtkPVBox
except Exception as e:
    print(e)
import math
import os
from concurrent.futures import ThreadPoolExecutor

from paraview import print_error
from vtkmodules.util import numpy_support, vtkConstants
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase


# Number of threads for the projection fan-out. pyproj releases the GIL
# inside Transformer.transform, so chunking the input across threads
# scales nearly linearly (7.4x on 8 threads in our bench). Default is
# max(1, cpu_count - 1) to leave one core for the UI/IO thread; override
# via QV_PROJECTION_THREADS for HPC machines or to pin down for testing.
def _default_projection_threads():
    env = os.environ.get("QV_PROJECTION_THREADS")
    if env:
        try:
            return max(1, int(env))
        except ValueError:
            pass
    return max(1, (os.cpu_count() or 2) - 1)


_PROJECTION_THREADS = _default_projection_threads()
# Below this point count the thread-pool overhead outweighs the speedup.
_PROJECTION_THREADING_MIN = 1_000_000


def _threaded_transform(xformer, x, y):
    """Apply xformer.transform over x, y by chunking across threads."""
    n = len(x)
    if _PROJECTION_THREADS <= 1 or n < _PROJECTION_THREADING_MIN:
        return xformer.transform(x, y)

    chunk = n // _PROJECTION_THREADS

    def work(i):
        lo = i * chunk
        hi = n if i == _PROJECTION_THREADS - 1 else lo + chunk
        return xformer.transform(x[lo:hi], y[lo:hi])

    with ThreadPoolExecutor(max_workers=_PROJECTION_THREADS) as ex:
        results = list(ex.map(work, range(_PROJECTION_THREADS)))

    x_out = np.concatenate([r[0] for r in results])
    y_out = np.concatenate([r[1] for r in results])
    return x_out, y_out


try:
    import warnings

    import numpy as np
    from pyproj import Proj, Transformer

    warnings.filterwarnings("ignore", category=FutureWarning, module="pyproj")
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
    # back to a no-op shim so the filter still works.
    from contextlib import contextmanager

    class _perf:  # type: ignore[no-redef]
        @staticmethod
        def is_enabled():
            return False

        @staticmethod
        @contextmanager
        def timed(label):
            yield


def _cell_types_array(grid):
    """Per-cell type array, across VTK versions.

    VTK 9.7 dropped `GetCellTypesArray()`; `GetCellTypes()` now returns that
    array, where it used to fill a vtkCellTypes passed in by the caller.
    """
    getter = getattr(grid, "GetCellTypesArray", None)
    return getter() if getter is not None else grid.GetCellTypes()


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


def _translated(dataset, shift):
    """dataset moved `shift` degrees in longitude (returned as-is when shift is 0)."""
    if shift == 0.0:
        return dataset
    transform = vtkTransform()
    transform.Translate(shift, 0, 0)
    transform_filter = vtkTransformFilter()
    transform_filter.SetInputData(dataset)
    transform_filter.SetTransform(transform)
    transform_filter.Update()
    return transform_filter.GetOutput()


def _longitude_window(origin, input_origin=0.0):
    """Cut meridian and the two shifts that move [input_origin, +360) to [origin, +360).

    Everything below the cut is translated by one turn relative to everything
    above it, and a whole-turn offset then places the seam exactly at `origin`.
    With an input running [0, 360) and origin = -180 this reduces to the
    historical behaviour: cut at 180, right half shifted by -360.
    """
    cut = input_origin + (origin - input_origin) % 360.0
    return cut, origin + 360.0 - cut, origin - cut


def _remap_arrays(in_attrs, cached_attrs, out_attrs, pedigree_vtk, label):
    """Rebuild out_attrs from in_attrs, permuted through a pedigree map.

    The number of values in a freshly read array differs from the number that
    came out of the pipeline, so values are gathered through the pedigree
    permutation recorded when the geometry was last built.

    A single fancy-index gather does this. An earlier version walked the
    permutation as a list of monotonic run slices, assuming the runs were
    thousands of entries long. Measured against the permutations this pipeline
    actually produces — mean run 13 for point ids, 55-110 for cell ids — that
    loop is 8-66x *slower* than one numpy gather, because the per-run Python
    overhead dominates.
    """
    pid_np = numpy_support.vtk_to_numpy(pedigree_vtk)
    n_tuples = pedigree_vtk.GetNumberOfTuples()
    out_attrs.Initialize()
    for i in range(in_attrs.GetNumberOfArrays()):
        in_array = in_attrs.GetArray(i)
        cached_array = cached_attrs.GetArray(in_array.GetName())
        if cached_array and cached_array.GetMTime() >= in_array.GetMTime():
            # This scalar has been seen before — reuse cached copy.
            out_attrs.AddArray(cached_array)
        else:
            with _perf.timed(f"{label}.pedigree_copy.{in_array.GetName()}"):
                out_array = in_array.NewInstance()
                out_array.SetNumberOfComponents(in_array.GetNumberOfComponents())
                out_array.SetNumberOfTuples(n_tuples)
                out_array.SetName(in_array.GetName())
                out_attrs.AddArray(out_array)

                in_np = numpy_support.vtk_to_numpy(in_array)
                out_np = numpy_support.vtk_to_numpy(out_array)
                out_np[...] = in_np[pid_np]
                out_array.Modified()


def add_cell_arrays(inData, outData, cached_output):
    """Refresh cell arrays only — for filters that interpolate point data.

    A clip creates new points by interpolation, so an output point has no
    single source point to gather from and the pedigree trick cannot work
    for point data. Cells are only ever kept or dropped, so they can.
    """
    pedigree_vtk = cached_output.GetCellData().GetArray("PedigreeIds")
    if pedigree_vtk is None:
        print_error("Error: no PedigreeIds array")
        return

    outData.ShallowCopy(cached_output)
    _remap_arrays(
        inData.GetCellData(),
        cached_output.GetCellData(),
        outData.GetCellData(),
        pedigree_vtk,
        "add_cell_arrays",
    )


def add_cell_and_point_arrays(inData, outData, cached_output):
    """Refresh cell *and* point arrays through their respective pedigree maps.

    Usable only where the filter subsets whole cells and never interpolates —
    then every output point is a copy of an input point, so its pedigree id is
    an exact gather index. EAMExtract qualifies; a clip does not.
    """
    outData.ShallowCopy(cached_output)

    cell_pedigree = cached_output.GetCellData().GetArray("PedigreeIds")
    if cell_pedigree is not None and inData.GetCellData().GetNumberOfArrays():
        _remap_arrays(
            inData.GetCellData(),
            cached_output.GetCellData(),
            outData.GetCellData(),
            cell_pedigree,
            "add_cell_arrays",
        )

    point_pedigree = cached_output.GetPointData().GetArray("PointPedigreeIds")
    if point_pedigree is not None and inData.GetPointData().GetNumberOfArrays():
        _remap_arrays(
            inData.GetPointData(),
            cached_output.GetPointData(),
            outData.GetPointData(),
            point_pedigree,
            "add_point_arrays",
        )


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

        inPoints = inData.points
        pRadius = (self.radius + 1) if self.isData else self.radius
        outPoints = np.array(list(map(lambda x: ProcessPoint(x, pRadius), inPoints)))
        outData.points = outPoints

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

        inPoints = inData.points
        pRadius = (self.radius + 1) if self.isData else self.radius
        outPoints = np.array(list(map(lambda x: ProcessPoint(x, pRadius), inPoints)))
        # outPoints   = np.array(list(map(ProcessPoint,inPoints)))

        _coords = numpy_support.numpy_to_vtk(
            outPoints, deep=True, array_type=vtkConstants.VTK_FLOAT
        )
        vtk_coords = vtkPoints()
        vtk_coords.SetData(_coords)
        outData.points = vtk_coords

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
                        <Entry value="3" text="Spherical"/>
                    </EnumerationDomain>
                </IntVectorProperty>
                <DoubleVectorProperty name="Longitude Origin"
                      command="SetLongitudeOrigin"
                      number_of_elements="1"
                      default_values="-180">
                    <Documentation>Left edge of the map; the projection is centred half a turn east of it.</Documentation>
                 </DoubleVectorProperty>
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
        self.cached_points = None
        # Cache keyed on input-points identity + projection params. Immune to
        # spurious upstream Modified() on the shared points.
        self._cached_input_points = None
        self._cached_key = None

        self.longitude_origin = -180.0

    def _invalidate_cache(self):
        self.cached_points = None
        self._cached_input_points = None
        self._cached_key = None

    def SetTranslation(self, translate):
        if self.translate != translate:
            self.translate = translate
            self._invalidate_cache()
            self.Modified()

    def SetProjection(self, project):
        if self.project != int(project):
            self.project = int(project)
            self._invalidate_cache()
            self.Modified()

    def SetLongitudeOrigin(self, origin):
        """Left edge of the map. The projection is centred half a turn east of
        it, so a rotated window still maps onto the middle of the figure."""
        if self.longitude_origin != origin:
            self.longitude_origin = origin
            self._invalidate_cache()
            self.Modified()

    def RequestData(self, request, inInfo, outInfo):
        with _perf.timed("project.RequestData"):
            inData = self.GetInputData(inInfo, 0, 0)
            outData = self.GetOutputData(outInfo, 0)
            if inData.IsA("vtkPolyData"):
                afilter = vtkAppendFilter()
                afilter.AddInputData(inData)
                afilter.Update()
                outData.ShallowCopy(afilter.GetOutput())
            else:
                outData.ShallowCopy(inData)

            in_points = inData.GetPoints()
            cache_key = (id(in_points), self.project, self.translate)
            if self.cached_points is not None and self._cached_key == cache_key:
                with _perf.timed("project.cache_hit"):
                    outData.SetPoints(self.cached_points)
            else:
                with _perf.timed("project.cache_miss"):
                    # we modify the points, so copy them
                    with _perf.timed("project.deep_copy_points"):
                        out_points_vtk = vtkPoints()
                        out_points_vtk.DeepCopy(outData.GetPoints())
                        outData.SetPoints(out_points_vtk)
                    # Go through numpy_support rather than the pythonic
                    # `.points`: VTK 9.7 returns a vtkPoints subclass there,
                    # where earlier versions handed back a numpy array.
                    out_points_np = numpy_support.vtk_to_numpy(
                        outData.GetPoints().GetData()
                    )

                    flat = out_points_np.flatten()
                    x = flat[0::3] - 180.0 if self.translate else flat[0::3]
                    y = flat[1::3]

                    if self.project == 3:
                        # Spherical
                        to_rad = np.pi / 180
                        x_rad = x * to_rad
                        y_rad = y * to_rad
                        cos_y_rad = np.cos(y_rad)
                        zs = np.cos(x_rad) * cos_y_rad
                        xs = np.sin(x_rad) * cos_y_rad
                        ys = np.sin(y_rad)
                        flat[0::3] = xs
                        flat[1::3] = ys
                        flat[2::3] = zs
                    else:
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

                            # Re-centre on the middle of the window here rather
                            # than through PROJ's lon_0. PROJ normalises its
                            # input into [-180, 180) *before* subtracting lon_0,
                            # which sends the window's right edge to the left
                            # rim -- drawing coastlines and cells straight
                            # across the map. The data is already confined to
                            # the window, so the offset lands in range on its
                            # own and PROJ never has to wrap anything.
                            x = np.clip(
                                x - (self.longitude_origin + 180.0), -180.0, 180.0
                            )

                            xformer = Transformer.from_proj(
                                latlon, proj, always_xy=True
                            )
                            with _perf.timed("project.pyproj_transform"):
                                res = _threaded_transform(xformer, x, y)
                        except Exception as e:
                            print(f"Projection error: {e}")
                            # If projection fails, return without modifying coordinates
                            return 1

                        flat[0::3] = np.array(res[0])
                        flat[1::3] = np.array(res[1])

                    outPoints = flat.reshape(out_points_np.shape)
                    _coords = numpy_support.numpy_to_vtk(outPoints, deep=True)
                    outData.GetPoints().SetData(_coords)
                    # the previous cached_points, if any, is available for
                    # garbage collection after this assignment
                    self.cached_points = out_points_vtk
                    self._cached_input_points = (
                        in_points  # hold ref so id() stays valid
                    )
                    self._cached_key = cache_key

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
                <DoubleVectorProperty name="Longitude Origin"
                      command="SetLongitudeOrigin"
                      number_of_elements="1"
                      default_values="-180">
                    <Documentation>Left edge of the map; the right edge is 360 degrees east of it.</Documentation>
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
        self.longitude_origin = -180.0

    def SetLongitudeOrigin(self, origin):
        """Left edge of the map, so the overlay follows the data's window."""
        if self.longitude_origin != origin:
            self.longitude_origin = origin
            self.Modified()

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

        cut, shift_low, shift_high = _longitude_window(self.longitude_origin)

        planeL = vtkPlane()
        planeL.SetOrigin([cut, 0.0, 0.0])
        planeL.SetNormal([-1, 0, 0])
        clipL = vtkTableBasedClipDataSet()
        clipL.SetClipFunction(planeL)
        clipL.SetInputData(inData)
        clipL.Update()

        planeR = vtkPlane()
        planeR.SetOrigin([cut, 0.0, 0.0])
        planeR.SetNormal([1, 0, 0])
        clipR = vtkTableBasedClipDataSet()
        clipR.SetClipFunction(planeR)
        clipR.SetInputData(inData)
        clipR.Update()

        append = vtkAppendFilter()
        append.AddInputData(_translated(clipL.GetOutput(), shift_low))
        append.AddInputData(_translated(clipR.GetOutput(), shift_high))
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
class EAMExtract(VTKPythonAlgorithmBase):
    def __init__(self):
        super().__init__(
            nInputPorts=1, nOutputPorts=1, outputType="vtkUnstructuredGrid"
        )
        self.lon_range = [-180.0, 180.0]
        self.lat_range = [-90.0, 90.0]
        self.cached_cell_centers = None
        self._cached_geometry_key = None
        #: Strong ref to the geometry the caches were built from, so nothing
        #: else can be allocated at the same address while its id() is a key.
        self._cached_geometry = None
        self._cached_output = None
        self._cached_crop_key = None
        self._last_was_cropped = False

    def SetLongitudeRange(self, min, max):
        # Ranges arrive in whichever 360-degree window the map is using, so
        # only the ordering and the width are meaningful here.
        if min > max or (max - min) > 360.0:
            print_error(
                f"SetLongitudeRange called with invalid parameters: {min=}, {max=}"
            )
            return
        if self.lon_range[0] != min or self.lon_range[1] != max:
            self.lon_range = [min, max]
            self.Modified()

    def SetLatitudeRange(self, min, max):
        if min < -90 or max > 90 or min > max:
            print_error(
                f"SetLatitudeRange called with invalid parameters: {min=}, {max=}"
            )
            return
        if self.lat_range[0] != min or self.lat_range[1] != max:
            self.lat_range = [min, max]
            self.Modified()

    def RequestData(self, request, inInfo, outInfo):
        with _perf.timed("extract.RequestData"):
            inData = self.GetInputData(inInfo, 0, 0)
            outData = self.GetOutputData(outInfo, 0)
            spans_full_turn = (self.lon_range[1] - self.lon_range[0]) >= 359.999
            if spans_full_turn and self.lat_range == [-90.0, 90.0]:
                outData.ShallowCopy(inData)
                # Only invalidate the shared points when transitioning *out* of a
                # cropped state — the original code did it unconditionally, which
                # defeated EAMProject's cache on every pipeline update.
                if self._last_was_cropped:
                    outData.GetPoints().Modified()
                    self._last_was_cropped = False
                return 1

            # Name the incoming geometry by identity as well as by modified
            # time. Modified times only order events within one object, and
            # upstream can legitimately hand back an *older* object than the
            # one these caches were built from: EAMCenterMeridian passes the
            # reader's own points straight through whenever the map already
            # sits in the reader's window. Comparing times alone then made a
            # cache built from a rotated mesh look fresh, and the cell centres
            # of one mesh were used to mask the cells of another.
            in_points = inData.GetPoints()
            in_cells = inData.GetCells()
            geometry_key = (
                id(in_points),
                in_points.GetMTime(),
                id(in_cells),
                in_cells.GetMTime(),
            )
            if (
                self.cached_cell_centers is not None
                and self._cached_geometry_key == geometry_key
            ):
                cell_centers = self.cached_cell_centers
            else:
                with _perf.timed("extract.cell_centers"):
                    # convert to polydata, as vtkCellCenters only works on polydata
                    to_poly = vtkGeometryFilter()
                    to_poly.SetInputData(inData)

                    # get cell centers
                    compute_centers = vtkCellCenters()
                    compute_centers.SetInputConnection(to_poly.GetOutputPort())
                    compute_centers.Update()
                    cell_centers = compute_centers.GetOutput().GetPoints().GetData()
                    # previous cached_cell_centers, if any,
                    # is available for garbage collection after this assignment
                    self.cached_cell_centers = cell_centers
                    self._cached_geometry_key = geometry_key
                    self._cached_geometry = (in_points, in_cells)

            # get the numpy array for cell centers
            cc = numpy_support.vtk_to_numpy(cell_centers)

            crop_key = (geometry_key, tuple(self.lon_range), tuple(self.lat_range))
            if self._cached_output is not None and self._cached_crop_key == crop_key:
                with _perf.timed("extract.cache_hit"):
                    add_cell_and_point_arrays(inData, outData, self._cached_output)
            else:
                with _perf.timed("extract.rebuild_trim"):
                    # add PedigreeIds
                    generate_ids = vtkGenerateIds()
                    generate_ids.SetInputData(inData)
                    # Point ids as well: RemoveGhostCells only ever drops whole
                    # cells, so a surviving point keeps an exact source index
                    # and nodal formats can be refreshed from the cache too.
                    generate_ids.PointIdsOn()
                    generate_ids.SetPointIdsArrayName("PointPedigreeIds")
                    generate_ids.SetCellIdsArrayName("PedigreeIds")
                    generate_ids.Update()
                    outData.ShallowCopy(generate_ids.GetOutput())
                    # we have to deep copy the cell array because we modify it
                    # with RemoveGhostCells
                    with _perf.timed("extract.deep_copy_cells"):
                        cells = vtkCellArray()
                        cell_types = vtkUnsignedCharArray()
                        cells.DeepCopy(outData.GetCells())
                        cell_types.DeepCopy(_cell_types_array(outData))
                        outData.SetCells(cell_types, cells)

                    # Crop against absolute lon/lat ranges, in the same
                    # [-180, 180] x [-90, 90] frame as EAMTransformAndExtract,
                    # so the result is independent of the data's own extent
                    # (regional meshes no longer get mis-cropped).
                    lon_min, lon_max = self.lon_range
                    lat_min, lat_max = self.lat_range

                    # add HIDDENCELL based on ranges
                    with _perf.timed("extract.ghost_mask"):
                        # Compare longitudes as offsets from lon_min taken
                        # modulo a turn, so the test is independent of which
                        # 360-degree window the data happens to live in and
                        # still works for a range that spans the seam.
                        lon_offset = (cc[:, 0] - lon_min) % 360.0
                        outside_mask = (
                            (lon_offset > ((lon_max - lon_min) % 360.0 or 360.0))
                            | (cc[:, 1] < lat_min)
                            | (cc[:, 1] > lat_max)
                        )
                        # Create ghost array (0 = visible, HIDDENCELL = invisible)
                        ghost_np = np.where(
                            outside_mask, vtkDataSetAttributes.HIDDENCELL, 0
                        ).astype(np.uint8)

                        # Convert to VTK and add to output
                        ghost = numpy_support.numpy_to_vtk(ghost_np)
                        ghost.SetName(vtkDataSetAttributes.GhostArrayName())
                        outData.GetCellData().AddArray(ghost)
                    with _perf.timed("extract.remove_ghost_cells"):
                        outData.RemoveGhostCells()

                    self._cached_output = outData.NewInstance()
                    self._cached_output.ShallowCopy(outData)
                    self._cached_crop_key = crop_key
            self._last_was_cropped = True
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

                <DoubleVectorProperty name="Longitude Origin"
                      command="SetLongitudeOrigin"
                      number_of_elements="1"
                      default_values="-180">
                    <Documentation>Left edge of the map; the right edge is 360 degrees east of it.</Documentation>
                 </DoubleVectorProperty>
                <DoubleVectorProperty name="Input Longitude Origin"
                      command="SetInputLongitudeOrigin"
                      number_of_elements="1"
                      default_values="0">
                    <Documentation>Left edge of the window the input already uses.</Documentation>
                 </DoubleVectorProperty>
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
        self._input_origin = 0.0
        self._cached_output = None

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
        if self._center_meridian != meridian_:
            self._center_meridian = meridian_
            self._cached_output = None
            self.Modified()

    def SetLongitudeOrigin(self, origin):
        """Left edge of the map; the right edge is 360 degrees further east."""
        if origin < -180 or origin > 180:
            print_error(
                f"SetLongitudeOrigin called with parameter outside [-180, 180]: {origin}"
            )
            return
        meridian = origin + 180.0
        if self._center_meridian != meridian:
            self._center_meridian = meridian
            self._cached_output = None
            self.Modified()

    def GetLongitudeOrigin(self):
        return self._center_meridian - 180.0

    def SetInputLongitudeOrigin(self, origin):
        """Left edge of the window the *input* already uses.

        The pg2 reader emits [0, 360); the dycore reader emits [-180, 180).
        Without this the cut lands outside the data and the rotation silently
        does nothing.
        """
        if self._input_origin != origin:
            self._input_origin = origin
            self._cached_output = None
            self.Modified()

    def GetMeridian(self):
        """
        Returns the central meridian
        """
        return self._center_meridian

    def RequestData(self, request, inInfo, outInfo):
        with _perf.timed("center_meridian.RequestData"):
            inData = self.GetInputData(inInfo, 0, 0)

            outData = self.GetOutputData(outInfo, 0)

            # Nothing to do when the input already sits in the requested
            # window -- the dycore reader's default case. Clipping here would
            # be a no-op that still rebuilds the points every pass, which also
            # costs EAMProject its cache downstream. The two origins have to
            # agree exactly: a window a whole turn away covers the same
            # meridians but names them 360 degrees apart, and everything
            # downstream -- the crop ranges, the projection's re-centring --
            # reads coordinates, not residues.
            origin = self._center_meridian - 180.0
            if origin == self._input_origin:
                with _perf.timed("center_meridian.passthrough"):
                    outData.ShallowCopy(inData)
                return 1
            # A clip makes new points by interpolation, so an output point has
            # no single source to gather from and the pedigree cache cannot
            # refresh point data. Nodal formats therefore re-clip every pass;
            # it costs a few milliseconds and is always correct.
            has_point_arrays = inData.GetPointData().GetNumberOfArrays() > 0
            geometry_cached = bool(
                self._cached_output
                and self._cached_output.GetPoints().GetMTime()
                >= inData.GetPoints().GetMTime()
                and self._cached_output.GetCells().GetMTime()
                >= inData.GetCells().GetMTime()
            )
            if geometry_cached and not has_point_arrays:
                with _perf.timed("center_meridian.cache_hit"):
                    add_cell_arrays(inData, outData, self._cached_output)
            else:
                with _perf.timed("center_meridian.rebuild"):
                    generate_ids = vtkGenerateIds()
                    generate_ids.SetInputData(inData)
                    generate_ids.PointIdsOff()
                    generate_ids.SetCellIdsArrayName("PedigreeIds")

                    cut, shift_low, shift_high = _longitude_window(
                        origin, self._input_origin
                    )
                    if (origin - self._input_origin) % 360.0 == 0.0:
                        # A whole turn away: the cut falls on the window's own
                        # edge, so one side comes back empty and there is
                        # nothing to rearrange. Sliding the whole mesh over is
                        # cheaper than clipping it and keeps every cell intact.
                        generate_ids.Update()
                        with _perf.timed("center_meridian.transform"):
                            halves = [_translated(generate_ids.GetOutput(), shift_high)]
                    else:
                        plane = vtkPlane()
                        plane.SetOrigin([cut, 0.0, 0.0])
                        plane.SetNormal([-1, 0, 0])
                        # vtkClipPolyData hangs
                        clipL = vtkTableBasedClipDataSet()
                        clipL.SetClipFunction(plane)
                        clipL.SetInputConnection(generate_ids.GetOutputPort())
                        with _perf.timed("center_meridian.clip_left"):
                            clipL.Update()

                        plane.SetNormal([1, 0, 0])
                        clipR = vtkTableBasedClipDataSet()
                        clipR.SetClipFunction(plane)
                        clipR.SetInputConnection(generate_ids.GetOutputPort())
                        with _perf.timed("center_meridian.clip_right"):
                            clipR.Update()

                        with _perf.timed("center_meridian.transform"):
                            halves = [
                                _translated(clipL.GetOutput(), shift_low),
                                _translated(clipR.GetOutput(), shift_high),
                            ]

                    append = vtkAppendFilter()
                    for half in halves:
                        append.AddInputData(half)
                    with _perf.timed("center_meridian.append"):
                        append.Update()
                    outData.ShallowCopy(append.GetOutput())

                    # The clip is deterministic, so when only the values
                    # changed the geometry it just produced is identical to the
                    # cached one. Hand the *same* points and cells objects
                    # downstream: EAMProject keys its cache on the identity of
                    # the incoming points, and EAMExtract on their modified
                    # time, so fresh copies would make both rebuild for nothing.
                    if (
                        geometry_cached
                        and self._cached_output.GetNumberOfPoints()
                        == outData.GetNumberOfPoints()
                        and self._cached_output.GetNumberOfCells()
                        == outData.GetNumberOfCells()
                    ):
                        with _perf.timed("center_meridian.reuse_geometry"):
                            outData.SetPoints(self._cached_output.GetPoints())
                            outData.SetCells(
                                _cell_types_array(self._cached_output),
                                self._cached_output.GetCells(),
                            )
                    else:
                        # previous _cached_output is available for garbage collection
                        self._cached_output = outData.NewInstance()
                        self._cached_output.ShallowCopy(outData)
            return 1

import json
from collections import defaultdict
from pathlib import Path

from paraview import simple
from vtkmodules.vtkCommonCore import vtkLogger
from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper


def longitude_window(lon_range, origin):
    """Express a geographic longitude range inside the window [origin, origin+360).

    Everything downstream -- the data, the continents, the graticule -- has to
    agree on which 360-degree window it is working in, or the overlays drift off
    the map when the origin is rotated.
    """
    low, high = lon_range
    width = (high - low) % 360.0
    if width == 0.0:
        # A full turn has no meaningful left edge of its own -- it is the window.
        return [origin, origin + 360.0]
    low_in_window = origin + (low - origin) % 360.0
    # A selection may not run off the end of its own window: the box crop behind
    # the continents and the graticule cannot wrap, so it would silently lose
    # whatever fell past the seam.
    return [low_in_window, min(low_in_window + width, origin + 360.0)]


def load_plugins():
    try:
        plugin_dir = Path(__file__).with_name("plugins")
        for plugin in plugin_dir.glob("*.py"):
            if plugin.is_file():
                print("Loading plugin : ", plugin)
                simple.LoadPlugin(str(plugin.resolve()), ns=globals())

        vtkLogger.SetStderrVerbosity(vtkLogger.VERBOSITY_OFF)
    except Exception as e:
        print("Error loading plugin :", e)


class ErrorObserver:
    def __init__(self):
        self.error_occurred = False
        self.error_message = ""

    def __call__(self, obj, event):
        self.error_occurred = True

    def clear(self):
        self.error_occurred = False


class Continent:
    def __init__(self, projection="Mollweide"):
        self._projection = projection
        input_file = Path(__file__).with_name("data") / "globe.vtk"
        self.reader = simple.LegacyVTKReader(FileNames=[str(input_file.resolve())])
        self.contour = simple.Contour(
            Input=self.reader,
            ContourBy=["POINTS", "cstar"],
            Isosurfaces=[0.5],
            PointMergeMethod="Uniform Binning",
        )
        self._crop = simple.EAMTransformAndExtract(
            Input=self.contour,
            LongitudeRange=[-180.0, 180.0],
            LatitudeRange=[-90.0, 90.0],
        )
        self._longitude_origin = -180.0
        self.proj = simple.EAMProject(
            Input=self._crop,
            Projection=projection,
            Translate=0,
        )
        # Representation
        self.geometry = simple.ExtractSurface(Input=self.proj)
        self.mapper = vtkPolyDataMapper(
            input_connection=self.geometry.GetClientSideObject().output_port,
            scalar_visibility=0,
        )
        self.actor = vtkActor(mapper=self.mapper)
        self.actor.property.SetRepresentationToWireframe()
        self.actor.property.render_lines_as_tubes = 1
        self.actor.property.line_width = 1.0
        self.actor.property.ambient_color = (0.67, 0.67, 0.67)
        self.actor.property.diffuse_color = (0.67, 0.67, 0.67)

    def crop(self, longitude_min_max, latitude_min_max):
        self._crop.LongitudeRange = longitude_min_max
        self._crop.LatitudeRange = latitude_min_max

    @property
    def longitude_origin(self):
        return self._longitude_origin

    @longitude_origin.setter
    def longitude_origin(self, origin):
        self._longitude_origin = origin
        self._crop.LongitudeOrigin = origin
        self.proj.LongitudeOrigin = origin

    @property
    def projection(self):
        return self._projection

    @projection.setter
    def projection(self, value):
        self._projection = value
        self.proj.Projection = value

    def update(self):
        self.geometry.UpdatePipeline()


class GridLines:
    def __init__(self, projection="Mollweide"):
        self._projection = projection
        self.grid_lines = simple.EAMGridLines()
        self._longitude_origin = -180.0
        self.proj = simple.EAMProject(
            Input=self.grid_lines,
            Projection=projection,
            Translate=0,
        )
        self.geometry = simple.ExtractSurface(Input=self.proj)
        # representation
        self.mapper = vtkPolyDataMapper(
            input_connection=self.geometry.GetClientSideObject().output_port,
        )
        self.actor = vtkActor(mapper=self.mapper)
        self.actor.property.SetRepresentationToWireframe()
        self.actor.property.ambient_color = (0.67, 0.67, 0.67)
        self.actor.property.diffuse_color = (0.67, 0.67, 0.67)
        self.actor.property.opacity = 0.4

    def set_interval(self, interval):
        self.grid_lines.Interval = interval

    def crop(self, longitude_min_max, latitude_min_max):
        self.grid_lines.LongitudeRange = longitude_min_max
        self.grid_lines.LatitudeRange = latitude_min_max

    @property
    def longitude_origin(self):
        return self._longitude_origin

    @longitude_origin.setter
    def longitude_origin(self, origin):
        self._longitude_origin = origin
        self.proj.LongitudeOrigin = origin

    @property
    def projection(self):
        return self._projection

    @projection.setter
    def projection(self, value):
        self._projection = value
        self.proj.Projection = value

    def update(self):
        self.geometry.UpdatePipeline()
        self.mapper.Update()


def connectivity_kind(conn_file):
    """Sniff a connectivity file and name the format it describes.

    Returns "dycore" for a HOMME np4/GLL grid file (nodal values on shared
    spectral-element nodes), "pg2" for a SCRIP physics grid (cell values on
    unshared corners), or None if neither signature is present.
    """
    try:
        import netCDF4

        with netCDF4.Dataset(conn_file) as ds:
            names = set(ds.variables)
            if "element_corners" in names:
                return "dycore"
            if any("corner_lat" in name for name in names):
                return "pg2"
    except Exception as e:
        print(f"Could not inspect connectivity file {conn_file}: {e}")

    return None


class DataPath:
    """One format's pipeline, from its reader to the surface the views render.

    Each format brings its own chain of filters and its own attribute
    association, so the rest of the application can stay format-agnostic: it
    talks to whichever path is active through this interface and reads
    ``association`` when it needs to know where the variables live.

    Subclasses provide ``_build_pipeline``, which must set ``reader``, ``proj``
    and ``geometry``.
    """

    kind = None
    label = None
    #: Where this format's variables land -- "cell" or "point".
    association = "cell"

    def __init__(self, projection="Mollweide"):
        self._file_connection = None
        self._file_mesh = None
        self._projection = projection
        self._observer = ErrorObserver()
        self._valid = False
        self._time_values = None
        self._variables = None
        self._dimensions = None
        self._slicing = defaultdict(int)

        self._build_pipeline(projection)
        self.vtk_geometry = self.geometry.GetClientSideObject()

        # Add observer to
        vtk_obj = self.reader.GetClientSideObject()
        vtk_obj.AddObserver("ErrorEvent", self._observer)
        vtk_obj.GetExecutive().AddObserver("ErrorEvent", self._observer)

    def _build_pipeline(self, projection):
        raise NotImplementedError

    @property
    def valid(self):
        return self._valid and not self._observer.error_occurred

    @property
    def time_values(self):
        if self._time_values is None and self.valid:
            timestep_values = self.reader.TimestepValues
            if timestep_values is None or isinstance(timestep_values, float):
                self._time_values = [] if timestep_values is None else [timestep_values]
            else:
                self._time_values = list(timestep_values)

        return self._time_values

    def load(self, file_mesh, file_connection):
        if self._file_mesh == file_mesh and self._file_connection == file_connection:
            return self.valid

        # Reset internal state
        self._valid = False
        self._time_values = None
        self._observer.clear()

        # Update files
        self.reader.DataFile = self._file_mesh = file_mesh
        self.reader.ConnectivityFile = self._file_connection = file_connection

        try:
            self.reader.UpdatePipeline()
            if self._observer.error_occurred:
                raise RuntimeError(
                    "Error occurred in UpdatePipeline. "
                    "Please check if the data and connectivity files exist "
                    "and are compatible"
                )

            # update internal state
            self._valid = True
            self.time_values
            self._variables = self.reader.GetClientSideObject().GetVariables()
            self._dimensions = self.reader.GetClientSideObject().GetDimensions()
            self._slicing = {k: 0 for k in self._dimensions}

        except Exception as e:
            print(e)

        return self.valid

    @property
    def variables(self):
        return self._variables

    @property
    def dimensions(self):
        return self._dimensions

    @property
    def projection(self):
        return self._projection

    @projection.setter
    def projection(self, value):
        self._projection = value
        self.proj.Projection = value

    def set_variables(self, names):
        self.reader.Variables = list(set([*names, "lat", "lon"]))

    def update_slicing(self, dimension, value):
        current_value = self._slicing.get(dimension, 0)

        if current_value == value:
            return False

        self._slicing[dimension] = value
        self.reader.Slicing = json.dumps(self._slicing)
        return True

    def update(self, time=0.0):
        if not self.valid:
            return

        self.geometry.UpdatePipeline(time)

    def crop(self, longitude_min_max, latitude_min_max):
        """Restrict the rendered region. Formats that cannot crop ignore this."""

    def set_longitude_origin(self, origin):
        """Place the left edge of the map; the right edge is a turn further east."""
        self.proj.LongitudeOrigin = origin


class Pg2Path(DataPath):
    """ne*pg2 physics grid: cell values on a SCRIP corner mesh.

    Cells are cut at the central meridian, so coverage stays exact, and the
    per-tick cost of re-cutting is avoided by remapping cell values through
    the clip's PedigreeIds.
    """

    kind = "pg2"
    label = "EAM physics grid (pg2)"
    association = "cell"

    def _build_pipeline(self, projection):
        self.reader = simple.EAMSliceDataReader()
        self.center_meridian = simple.EAMCenterMeridian(
            Input=self.reader,
            Meridian=0,
        )
        self._crop = simple.EAMExtract(
            Input=self.center_meridian,
            LongitudeRange=[-180, 180],
            LatitudeRange=[-90, 90],
        )
        self.proj = simple.EAMProject(  # noqa: F821
            Input=self._crop,
            Projection=projection,
            Translate=0,
        )
        self.geometry = simple.ExtractSurface(Input=self.proj)

    def crop(self, longitude_min_max, latitude_min_max):
        self._crop.LongitudeRange = longitude_min_max
        self._crop.LatitudeRange = latitude_min_max

    def set_longitude_origin(self, origin):
        # The clip already rearranges the halves; it just needs the new seam.
        super().set_longitude_origin(origin)
        self.center_meridian.LongitudeOrigin = origin


class DycorePath(DataPath):
    """ne*np4 dynamical core grid: nodal values on shared GLL nodes.

    The reader lays the sphere flat itself, duplicating nodes at the date line
    and the poles instead of clipping, so cells stay whole and no value is
    interpolated. That leaves nothing for EAMCenterMeridian to do -- the mesh
    already tiles [-180, 180] exactly -- so the path goes straight to the
    projection.
    """

    kind = "dycore"
    label = "EAM dynamical core (np4)"
    association = "point"

    def _build_pipeline(self, projection):
        # The reader stays in its natural [-180, 180) window, where the GLL
        # nodes land exactly on the seam and its node-duplication split tiles
        # the map with no overhang and no gap. Rotating to any other origin is
        # left to the clip: shifting whole cells would throw a polar cell --
        # up to 90 degrees wide -- past the edge, and a projection wraps that
        # onto the far side of the map.
        self.reader = simple.EAMDycoreReader()  # noqa: F821
        self.center_meridian = simple.EAMCenterMeridian(  # noqa: F821
            Input=self.reader,
            Meridian=0,
            InputLongitudeOrigin=-180,
        )
        # EAMExtract is not a clip -- it hides whole cells and removes them --
        # so it never interpolates and the nodal values survive untouched.
        self._crop = simple.EAMExtract(  # noqa: F821
            Input=self.center_meridian,
            LongitudeRange=[-180, 180],
            LatitudeRange=[-90, 90],
        )
        self.proj = simple.EAMProject(  # noqa: F821
            Input=self._crop,
            Projection=projection,
            Translate=0,
        )
        self.geometry = simple.ExtractSurface(Input=self.proj)

    def crop(self, longitude_min_max, latitude_min_max):
        self._crop.LongitudeRange = longitude_min_max
        self._crop.LatitudeRange = latitude_min_max

    def set_longitude_origin(self, origin):
        # The reader keeps its exact window; the clip does the rotation.
        super().set_longitude_origin(origin)
        self.center_meridian.LongitudeOrigin = origin


#: Every format the application can open, in detection order.
DATA_PATHS = (Pg2Path, DycorePath)

#: Kept so existing callers that expect the pg2 pipeline keep working.
DataReader = Pg2Path


class EAMVisSource:
    def __init__(self):
        self.projection = "Mollweide"

        load_plugins()
        self._paths = {}
        # pg2 is the default so that opening a physics-grid file behaves
        # exactly as it did before formats became selectable.
        self.data_reader = self._path_for(Pg2Path)
        self.continent = Continent(self.projection)
        self.grid_lines = GridLines(self.projection)
        self.views = {}
        #: True when the last Update() switched to a different format.
        self.path_changed = False
        #: Left edge of the map; the right edge sits 360 degrees east of it.
        self.longitude_origin = -180.0
        self._crop_lon = [-180.0, 180.0]
        self._crop_lat = [-90.0, 90.0]

    def _path_for(self, path_cls):
        """Return this format's pipeline, building it the first time it is used."""
        path = self._paths.get(path_cls.kind)
        if path is None:
            path = path_cls(self.projection)
            self._paths[path_cls.kind] = path
        return path

    @property
    def association(self):
        """Where the active format's variables live -- "cell" or "point"."""
        return self.data_reader.association

    @property
    def valid(self):
        return self.data_reader.valid

    @property
    def variables(self):
        return self.data_reader.variables

    @property
    def dimensions(self):
        return self.data_reader.dimensions

    def UpdateGridInterval(self, interval):
        self.grid_lines.set_interval(interval)

    def ApplyClipping(self, cliplong, cliplat):
        if not self.valid:
            return

        self._crop_lon = list(cliplong)
        self._crop_lat = list(cliplat)
        # The crop arrives in geographic longitude; everything downstream works
        # in the current window, so move it there once, here.
        window = longitude_window(cliplong, self.longitude_origin)
        self.data_reader.crop(window, cliplat)
        self.continent.crop(window, cliplat)
        self.grid_lines.crop(window, cliplat)

    def SetLongitudeOrigin(self, origin):
        """Rotate the map so its left edge is at `origin` degrees longitude."""
        if self.longitude_origin == origin:
            return

        self.longitude_origin = origin
        # Every format keeps its own pipeline, so they all have to be told --
        # not just the active one, or switching format would lose the window.
        for path in self._paths.values():
            path.set_longitude_origin(origin)
        self.continent.longitude_origin = origin
        self.grid_lines.longitude_origin = origin

        # Re-express the crop in the new window and refresh the overlays.
        self.ApplyClipping(self._crop_lon, self._crop_lat)
        self.UpdatePipeline()
        self.continent.update()
        self.grid_lines.update()

    def UpdateProjection(self, proj):
        if not self.valid:
            return

        if self.projection != proj:
            self.projection = proj
            self.data_reader.projection = proj
            self.grid_lines.projection = proj
            self.continent.projection = proj
            self.data_reader.update()
            self.grid_lines.update()
            self.continent.update()

    def UpdatePipeline(self, time=0.0):
        self.data_reader.update(time)

    def UpdateSlicing(self, dimension, slice):
        self.data_reader.update_slicing(dimension, slice)

    def Update(self, data_file, conn_file):  # force_reload
        kind = connectivity_kind(conn_file)
        path_cls = next(
            (cls for cls in DATA_PATHS if cls.kind == kind),
            Pg2Path,
        )
        path = self._path_for(path_cls)

        # Views bind to the tail of a specific pipeline, so a format switch has
        # to be visible to the caller -- it invalidates every existing view.
        self.path_changed = path is not self.data_reader
        if self.path_changed:
            self.data_reader = path
            path.projection = self.projection

        if self.data_reader.load(data_file, conn_file):
            self.views["atmosphere_data"] = self.data_reader.vtk_geometry
            self.views["continents"] = self.continent.proj
            self.views["grid_lines"] = self.grid_lines.proj
            return True

        return False

    def LoadVariables(self, vars):
        if not self.valid:
            return

        self.data_reader.set_variables(vars)

    def Clip(self, plane=None):
        self.grid_lines.mapper.RemoveAllClippingPlanes()
        self.continent.mapper.RemoveAllClippingPlanes()

        if plane:
            self.grid_lines.mapper.AddClippingPlane(plane)
            self.continent.mapper.AddClippingPlane(plane)


if __name__ == "__main__":
    e = EAMVisSource()

import json
from collections import defaultdict
from pathlib import Path

from paraview import simple
from vtkmodules.vtkCommonCore import vtkLogger
from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper


def range_to_trim(range, max):
    """
    Convert an range interval contained in [-180, 180] (such as [-170, 160])
    into an interval specifying how much to trim (for our example: [10, 20]).
    'max' is 180 for longitude or 90 for latitude
    """
    (min_range, max_range) = range
    return [min_range + max, max - max_range]


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
    def projection(self):
        return self._projection

    @projection.setter
    def projection(self, value):
        self._projection = value
        self.proj.Projection = value


class GridLines:
    def __init__(self, projection="Mollweide"):
        self._projection = projection
        self.grid_lines = simple.EAMGridLines()
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

    def crop(self, longitude_min_max, latitude_min_max):
        self.grid_lines.LongitudeRange = longitude_min_max
        self.grid_lines.LatitudeRange = latitude_min_max

    @property
    def projection(self):
        return self._projection

    @projection.setter
    def projection(self, value):
        self._projection = value
        self.proj.Projection = value


class DataReader:
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

        # Pipeline
        self.reader = simple.EAMSliceDataReader()
        self.center_meridian = simple.EAMCenterMeridian(
            Input=self.reader,
            Meridian=0,
        )
        self._crop = simple.EAMExtract(
            Input=self.center_meridian,
            TrimLongitude=[0, 0],
            TrimLatitude=[0, 0],
        )
        self.proj = simple.EAMProject(  # noqa: F821
            Input=self._crop,
            Projection=projection,
            Translate=0,
        )
        self.geometry = simple.ExtractSurface(Input=self.proj)
        self.vtk_geometry = self.geometry.GetClientSideObject()

        # Add observer to
        vtk_obj = self.reader.GetClientSideObject()
        vtk_obj.AddObserver("ErrorEvent", self._observer)
        vtk_obj.GetExecutive().AddObserver("ErrorEvent", self._observer)

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
        self._crop.TrimLongitude = range_to_trim(longitude_min_max, 180)
        self._crop.TrimLatitude = range_to_trim(latitude_min_max, 90)


class EAMVisSource:
    def __init__(self):
        self.projection = "Mollweide"

        load_plugins()
        self.data_reader = DataReader(self.projection)
        self.continent = Continent(self.projection)
        self.grid_lines = GridLines(self.projection)
        self.views = {}

    @property
    def valid(self):
        return self.data_reader.valid

    @property
    def variables(self):
        return self.data_reader.variables

    @property
    def dimensions(self):
        return self.data_reader.dimensions

    def ApplyClipping(self, cliplong, cliplat):
        if not self.valid:
            return

        self.data_reader.crop(cliplong, cliplat)
        self.continent.crop(cliplong, cliplat)
        self.grid_lines.crop(cliplong, cliplat)

    def UpdateProjection(self, proj):
        if not self.valid:
            return

        if self.projection != proj:
            self.projection = proj
            self.data_reader.projection = proj
            self.grid_lines.projection = proj
            self.continent.projection = proj

    def UpdatePipeline(self, time=0.0):
        self.data_reader.update(time)

    def UpdateSlicing(self, dimension, slice):
        self.data_reader.update_slicing(dimension, slice)

    def Update(self, data_file, conn_file):  # force_reload
        if self.data_reader.load(data_file, conn_file):
            self.views["atmosphere_data"] = self.data_reader.geometry
            self.views["continents"] = self.continent.proj
            self.views["grid_lines"] = self.grid_lines.proj
            return True

        return False

    def LoadVariables(self, vars):
        if not self.valid:
            return
        self.data_reader.reader.Variables = vars


if __name__ == "__main__":
    e = EAMVisSource()

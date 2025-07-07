import fnmatch
import numpy as np
import os


from paraview.simple import (
    FindSource,
    GetTimeKeeper,
    LoadPlugin,
    OutputPort,
    Contour,
    LegacyVTKReader,
)

from paraview import servermanager as sm
from paraview.vtk.numpy_interface import dataset_adapter as dsa
from vtkmodules.vtkCommonCore import vtkLogger


# Define a VTK error observer
class ErrorObserver:
    def __init__(self):
        self.error_occurred = False
        self.error_message = ""

    def __call__(self, obj, event):
        self.error_occurred = True

    def clear(self):
        self.error_occurred = False


class EAMVisSource:
    def __init__(self):
        # flag to check if the pipeline is valid
        # this is set to true when the pipeline is updated
        # and the data is available
        self.valid = False

        self.data_file = None
        self.conn_file = None

        self.lev = 0
        self.ilev = 0

        # List of all available variables
        self.vars2D = []
        self.vars3Dm = []
        self.vars3Di = []
        # List of selected variables
        self.vars2D_sel = []
        self.vars3Di_sel = []
        self.vars3Dm_sel = []

        self.data = None
        self.globe = None
        self.projection = "Cyl. Equidistant"
        self.timestamps = []
        self.center = 0.0

        self.extents = [-180.0, 180.0, -90.0, 90.0]
        self.moveextents = [-180.0, 180.0, -90.0, 90.0]

        self.views = {}
        self.vars = {}

        self.observer = ErrorObserver()
        try:
            plugin_dir = os.path.join(os.path.dirname(__file__), "plugins")
            plugins = fnmatch.filter(os.listdir(path=plugin_dir), "*.py")
            for plugin in plugins:
                print("Loading plugin : ", plugin)
                plugpath = os.path.abspath(os.path.join(plugin_dir, plugin))
                if os.path.isfile(plugpath):
                    LoadPlugin(plugpath, ns=globals())

            vtkLogger.SetStderrVerbosity(vtkLogger.VERBOSITY_OFF)
        except Exception as e:
            print("Error loading plugin :", e)

    def UpdateLev(self, lev, ilev):
        if not self.valid:
            return

        if self.data is None:
            return
        if self.lev != lev or self.ilev != ilev:
            self.lev = lev
            self.ilev = ilev
            self.data.MiddleLayer = lev
            self.data.InterfaceLayer = ilev

    def ApplyClipping(self, cliplong, cliplat):
        if not self.valid:
            return

        extract = FindSource("DataExtract")
        extract.LongitudeRange = cliplong
        extract.LatitudeRange = cliplat

        gextract = FindSource("GExtract")
        gextract.LongitudeRange = cliplong
        gextract.LatitudeRange = cliplat

    def UpdateCenter(self, center):
        """
        if self.center != int(center):
            self.center = int(center)

            meridian = FindSource("CenterMeridian")
            meridian.CenterMeridian = self.center

            gmeridian = FindSource("GCMeridian")
            gmeridian.CenterMeridian = self.center
        """
        pass

    def UpdateProjection(self, proj):
        if not self.valid:
            return

        eamproj2D = FindSource("2DProj")
        eamprojG = FindSource("GProj")
        projA = FindSource("GLines")
        if self.projection != proj:
            self.projection = proj
            eamproj2D.Projection = proj
            eamprojG.Projection = proj
            projA.Projection = proj

    def UpdateTimeStep(self, t_index):
        if not self.valid:
            return

        time = self.timestamps[t_index]
        tk = GetTimeKeeper()
        tk.Time = time

    def UpdatePipeline(self):
        if not self.valid:
            return

        eamproj2D = FindSource("2DProj")
        if eamproj2D:
            eamproj2D.UpdatePipeline()
        self.moveextents = eamproj2D.GetDataInformation().GetBounds()

        eamprojG = FindSource("GProj")
        if eamprojG:
            eamprojG.UpdatePipeline()

        extract = FindSource("DataExtract")
        bounds = extract.GetDataInformation().GetBounds()

        grid = FindSource("OGLines")
        if grid:
            grid.LongitudeRange = [bounds[0], bounds[1]]
            grid.LatitudeRange = [bounds[2], bounds[3]]
        projA = FindSource("GLines")
        if projA:
            projA.UpdatePipeline()

        self.views["2DProj"] = OutputPort(eamproj2D, 0)
        self.views["GProj"] = OutputPort(eamprojG, 0)
        self.views["GLines"] = OutputPort(projA, 0)

    def Update(self, data_file, conn_file, lev=0, ilev=0):
        if self.data_file == data_file and self.conn_file == conn_file:
            return

        self.data_file = data_file
        self.conn_file = conn_file

        if self.data is None:
            data = EAMSliceDataReader(
                registrationName="eamdata",
                ConnectivityFile=conn_file,
                DataFile=data_file,
            )
            data.MiddleLayer = lev
            data.InterfaceLayer = ilev
            self.data = data
            vtk_obj = data.GetClientSideObject()
            vtk_obj.AddObserver("ErrorEvent", self.observer)
            vtk_obj.GetExecutive().AddObserver("ErrorEvent", self.observer)
            self.observer.clear()
        else:
            self.data.DataFile = data_file
            self.data.ConnectivityFile = conn_file
            self.observer.clear()

        try:
            self.data.UpdatePipeline()
            if self.observer.error_occurred:
                raise RuntimeError(
                    "Error occurred in UpdatePipeline. "
                    "Please check if the data and connectivity files exist "
                    "and are compatible"
                )

            data_wrapped = dsa.WrapDataObject(sm.Fetch(self.data))
            self.lev = data_wrapped.FieldData["lev"].tolist()
            self.ilev = data_wrapped.FieldData["ilev"].tolist()

            self.vars2D = list(
                np.asarray(self.data.GetProperty("a2DVariablesInfo"))[::2]
            )
            self.vars3Dm = list(
                np.asarray(self.data.GetProperty("a3DMiddleLayerVariablesInfo"))[::2]
            )
            self.vars3Di = list(
                np.asarray(self.data.GetProperty("a3DInterfaceLayerVariablesInfo"))[::2]
            )

            tk = GetTimeKeeper()
            self.timestamps = np.array(tk.TimestepValues).tolist()
            tk.Time = tk.TimestepValues[0]

            extract = EAMTransformAndExtract(
                registrationName="DataExtract", Input=self.data
            )
            extract.LongitudeRange = [-180.0, 180.0]
            extract.LatitudeRange = [-90.0, 90.0]
            # meridian = EAMCenterMeridian(
            #    registrationName="CenterMeridian", Input=OutputPort(extract, 0)
            # )
            # meridian.CenterMeridian = 0
            extract.UpdatePipeline()
            self.extents = extract.GetDataInformation().GetBounds()
            proj2D = EAMProject(registrationName="2DProj", Input=OutputPort(extract, 0))
            proj2D.Projection = self.projection
            proj2D.Translate = 0
            proj2D.UpdatePipeline()
            self.moveextents = proj2D.GetDataInformation().GetBounds()

            if self.globe is None:
                globe_file = os.path.join(
                    os.path.dirname(__file__), "data", "globe.vtk"
                )
                gdata = LegacyVTKReader(
                    registrationName="globe", FileNames=[globe_file]
                )
                cgdata = Contour(registrationName="gcontour", Input=gdata)
                cgdata.ContourBy = ["POINTS", "cstar"]
                cgdata.Isosurfaces = [0.5]
                cgdata.PointMergeMethod = "Uniform Binning"
                self.globe = cgdata

            gextract = EAMTransformAndExtract(
                registrationName="GExtract", Input=self.globe
            )
            gextract.LongitudeRange = [-180.0, 180.0]
            gextract.LatitudeRange = [-90.0, 90.0]
            # gmeridian = EAMCenterMeridian(
            #    registrationName="GCMeridian", Input=OutputPort(gextract, 0)
            # )
            # gmeridian.CenterMeridian = 0
            # gmeridian.UpdatePipeline()
            projG = EAMProject(registrationName="GProj", Input=OutputPort(gextract, 0))
            projG.Projection = self.projection
            projG.Translate = 0
            projG.UpdatePipeline()

            glines = EAMGridLines(registrationName="OGLines")
            glines.UpdatePipeline()
            # self.annot = glines
            projA = EAMProject(registrationName="GLines", Input=OutputPort(glines, 0))
            projA.Projection = self.projection
            projA.Translate = 0
            projA.UpdatePipeline()

            self.views["2DProj"] = OutputPort(proj2D, 0)
            self.views["GProj"] = OutputPort(projG, 0)
            self.views["GLines"] = OutputPort(projA, 0)

            self.valid = True
            self.observer.clear()
        except Exception as e:
            # print("Error in UpdatePipeline :", e)
            # traceback.print_stack()
            print(e)
            self.valid = False
            return

    def LoadVariables(self, v2d, v3dm, v3di):
        if not self.valid:
            return
        self.data.a2DVariables = v2d
        self.data.a3DMiddleLayerVariables = v3dm
        self.data.a3DInterfaceLayerVariables = v3di
        self.vars["2D"] = v2d
        self.vars["3Dm"] = v3dm
        self.vars["3Di"] = v3di


if __name__ == "__main__":
    e = EAMVisSource()

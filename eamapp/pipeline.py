import os

import numpy as np

from paraview.simple import (
    FindSource,
    GetTimeKeeper,
    LoadPlugin,
    OutputPort,
    Clip,
    Contour,
    Transform,
    AppendDatasets,
)


class EAMVisSource:
    def __init__(self):
        self.DataFile = None
        self.ConnFile = None

        self.views = {}
        self.vars = {}

        self.lev = 0
        self.ilev = 0
        self.vars2D_sel = []
        self.vars3Di_sel = []
        self.vars3Dm_sel = []

        self.data = None
        self.globe = None
        self.projection = "Cyl. Equidistant"
        self.timestamps = []
        self.lev = 0
        self.center = 0.0

        currdir = os.path.dirname(__file__)
        try:
            plugdir = os.path.join(currdir, "plugins")
            import fnmatch

            plugins = fnmatch.filter(os.listdir(path=plugdir), "*.py")
            for plugin in plugins:
                print("Loading plugin : ", plugin)
                plugpath = os.path.abspath(os.path.join(plugdir, plugin))
                if os.path.isfile(plugpath):
                    LoadPlugin(plugpath, ns=globals())
        except Exception as e:
            print("Error loading plugin :", e)

    def UpdateLev(self, lev, ilev):
        eamproj2D = FindSource("2DProj")
        if self.data == None:
            return
        if self.lev != lev or self.ilev != ilev:
            self.lev = lev
            self.ilev = ilev
            self.data.MiddleLayer = lev
            self.data.InterfaceLayer = ilev
            # eamproj2D.UpdatePipeline()
            # self.views["2DProj"]  = OutputPort(eamproj2D,  0)
            # self.UpdateProjection(self.projection)

    def ApplyClipping(self, cliplong, cliplat):
        extract = FindSource("DataExtract")
        extract.LongitudeRange = cliplong
        extract.LatitudeRange = cliplat

        gextract = FindSource("GExtract")
        gextract.LongitudeRange = cliplong
        gextract.LatitudeRange = cliplat

    def UpdateCenter(self, center):
        if self.center != int(center):
            self.center = int(center)

            meridian = FindSource("CenterMeridian")
            meridian.CenterMeridian = self.center

            gmeridian = FindSource("GCMeridian")
            gmeridian.CenterMeridian = self.center

    def UpdateProjection(self, proj):
        eamproj2D = FindSource("2DProj")
        eamprojG = FindSource("GProj")
        projA = FindSource("GLines")
        if self.projection != proj:
            self.projection = proj
            eamproj2D.Projection = proj
            eamprojG.Projection = proj
            projA.Projection = proj

    def UpdateTimeStep(self, t_index):
        time = self.timestamps[t_index]
        print("Setting time to ", time)
        tk = GetTimeKeeper()
        tk.Time = time

    def UpdatePipeline(self):
        eamproj2D = FindSource("2DProj")
        if eamproj2D:
            eamproj2D.UpdatePipeline()
        self.moveextents = eamproj2D.GetDataInformation().GetBounds()
        eamprojG = FindSource("GProj")
        if eamprojG:
            eamprojG.UpdatePipeline()

        meridian = FindSource("CenterMeridian")
        bounds = meridian.GetDataInformation().GetBounds()
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

    def Update(self, datafile, connfile, globefile, lev):
        self.DataFile = datafile
        self.ConnFile = connfile
        if self.data == None:
            data = EAMSliceDataReader(
                registrationName="eamdata", ConnectivityFile=connfile, DataFile=datafile
            )
            data.MiddleLayer = lev
            data.InterfaceLayer = 0
            data.UpdatePipeline()
            self.data = data
        else:
            self.data.SetDataFileName(datafile)
            self.data.SetConnFileName(connfile)

        if self.globe == None:
            gdata = LegacyVTKReader(registrationName="globe", FileNames=[globefile])
            gdata.UpdatePipeline()
            cgdata = Contour(registrationName="gcontour", Input=gdata)
            cgdata.ContourBy = ["POINTS", "cstar"]
            cgdata.Isosurfaces = [0.5]
            cgdata.PointMergeMethod = "Uniform Binning"
            cgdata.UpdatePipeline()
            self.globe = cgdata

        self.vars2D = list(np.asarray(self.data.GetProperty("a2DVariablesInfo"))[::2])
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
        meridian = EAMCenterMeridian(
            registrationName="CenterMeridian", Input=OutputPort(extract, 0)
        )
        meridian.CenterMeridian = 0
        meridian.UpdatePipeline()
        self.extents = meridian.GetDataInformation().GetBounds()
        proj2D = EAMProject(registrationName="2DProj", Input=OutputPort(meridian, 0))
        proj2D.Projection = self.projection
        proj2D.Translate = 0
        proj2D.UpdatePipeline()
        self.moveextents = proj2D.GetDataInformation().GetBounds()

        gextract = EAMTransformAndExtract(registrationName="GExtract", Input=self.globe)
        gextract.LongitudeRange = [-180.0, 180.0]
        gextract.LatitudeRange = [-90.0, 90.0]
        gmeridian = EAMCenterMeridian(
            registrationName="GCMeridian", Input=OutputPort(gextract, 0)
        )
        gmeridian.CenterMeridian = 0
        gmeridian.UpdatePipeline()
        projG = EAMProject(registrationName="GProj", Input=OutputPort(gmeridian, 0))
        projG.Projection = self.projection
        projG.Translate = 1
        projG.UpdatePipeline()

        glines = EAMGridLines(registrationName="OGLines")
        glines.UpdatePipeline()
        self.annot = glines
        projA = EAMProject(registrationName="GLines", Input=OutputPort(glines, 0))
        projA.Projection = self.projection
        projA.Translate = 0
        projA.UpdatePipeline()

        self.views["2DProj"] = OutputPort(proj2D, 0)
        self.views["GProj"] = OutputPort(projG, 0)
        self.views["GLines"] = OutputPort(projA, 0)

        from paraview import servermanager as sm
        from paraview.vtk.numpy_interface import dataset_adapter as dsa

        data1 = sm.Fetch(data)
        data1 = dsa.WrapDataObject(data1)
        self.lev = data1.FieldData["lev"].tolist()
        self.ilev = data1.FieldData["ilev"].tolist()

    def LoadVariables(self, v2d, v3dm, v3di):
        self.data.a2DVariables = v2d
        self.data.a3DMiddleLayerVariables = v3dm
        self.data.a3DInterfaceLayerVariables = v3di

        self.vars["2D"] = v2d
        self.vars["3Dm"] = v3dm
        self.vars["3Di"] = v3di

        # self.data.UpdatePipeline()
        pass


if __name__ == "__main__":
    e = EAMVisSource()

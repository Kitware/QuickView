import os

import numpy as np

from vissource.viewmanager import ViewManager

from paraview.simple import (
    FindSource,
    GetTimeKeeper,
    LoadPlugin,
    OutputPort,
    Contour,
    Clip,
)

from paraview.simple import servermanager as sm

# -----------------------------------------------------------------------------
# ParaView code
# -----------------------------------------------------------------------------

class EAMVisSource:
    def __init__(self):
        self.DataFile   = None
        self.ConnFile   = None

        self.views    = {}
        self.vars     = {}

        self.lev      = 0
        self.ilev     = 0
        self.vars2D_sel     = []
        self.vars3Di_sel    = []
        self.vars3Dm_sel    = []

        self.data       = None
        self.globe      = None
        self.projection = 'Cyl. Equidistant'
        self.timestamps = []
        self.lev        = 0

        file       = os.path.abspath(__file__)
        currdir    = os.path.dirname(file)
        root       = os.path.dirname(currdir)
        try:
            plugdir    = os.path.join(root, 'plugins')
            plugins         = os.listdir(path=plugdir)
            for plugin in plugins:
                plugpath = os.path.abspath(os.path.join(plugdir, plugin))
                if os.path.isfile(plugpath):
                    LoadPlugin(plugpath, ns=globals())
        except Exception as e:
            print("Error loading plugin :", e)

    def UpdateProjection(self, proj):
        eamproj2D  = FindSource('2DProj')
        eamprojG   = FindSource('GProj')
        projA      = FindSource('GLines')
        if self.projection != proj:
            self.projection = proj
            eamproj2D.Projection  = proj
            eamprojG.Projection   = proj
            projA.Projection      = proj
        eamproj2D.UpdatePipeline()
        eamprojG.UpdatePipeline()
        projA.UpdatePipeline()
        self.views["2DProj"]  = OutputPort(eamproj2D,  0)
        self.views["GProj"]   = OutputPort(eamprojG, 0)                  
        self.views["GLines"]   = OutputPort(projA, 0)                  

    def UpdateLev(self, lev, ilev):
        eamproj2D  = FindSource('2DProj')
        if self.data == None:
            return
        if self.lev != lev or self.ilev != ilev:
            self.lev = lev
            self.ilev = ilev
            self.data.MiddleLayer = lev
            self.data.InterfaceLayer = ilev
            eamproj2D.UpdatePipeline()
            self.views["2DProj"]  = OutputPort(eamproj2D,  0)
            self.UpdateProjection(self.projection)         

    def ApplyClipping(self, cliplong, cliplat):
        pos = [cliplong[0], cliplat[0], -5.0]
        len = [cliplong[1] - cliplong[0], cliplat[1] - cliplat[0], 10.0]
        clip  = FindSource('Clip')
        clip.ClipType = 'Box'
        clip.ClipType.Position = pos 
        clip.ClipType.Length   = len 
        clip.UpdatePipeline()
        clip  = FindSource('GClip')
        clip.ClipType = 'Box'
        clip.ClipType.Position = pos 
        clip.ClipType.Length   = len 
        clip.UpdatePipeline()
        grid = FindSource("OGLines")
        grid.LatitudeRange = cliplat
        grid.LongitudeRange = cliplong
        grid.UpdatePipeline()

    def Update(self, datafile, connfile, globefile, lev):
        if self.data == None:
            data = EAMSliceDataReader(registrationName='eamdata',
                                        ConnectivityFile=connfile,
                                        DataFile=datafile)
            data.MiddleLayer = lev
            data.InterfaceLayer = 0
            data.UpdatePipeline()
            self.data = data
            self.extents = data.GetDataInformation().GetBounds()
        else:
            self.data.SetDataFileName(datafile)
            self.data.SetConnFileName(connfile)

        if self.globe == None:
            gdata = LegacyVTKReader(registrationName='globe', FileNames=[globefile])
            gdata.UpdatePipeline()
            cgdata = Contour(registrationName='gcontour', Input=gdata)
            cgdata.ContourBy = ['POINTS', 'cstar']
            cgdata.Isosurfaces = [0.5]
            cgdata.PointMergeMethod = 'Uniform Binning'
            cgdata.UpdatePipeline()
            self.globe = cgdata
                             
        glines = EAMGridLines(registrationName='OGLines')
        glines.UpdatePipeline()
        self.annot = glines

        self.vars2D  = list(np.asarray(self.data.GetProperty('a2DVariablesInfo'))[::2])
        self.vars3Dm = list(np.asarray(self.data.GetProperty('a3DMiddleLayerVariablesInfo'))[::2])
        self.vars3Di = list(np.asarray(self.data.GetProperty('a3DInterfaceLayerVariablesInfo'))[::2])

        tk = GetTimeKeeper()
        self.timestamps = np.array(tk.TimestepValues).tolist()
        tk.Time = tk.TimestepValues[0]

        dclip = Clip(registrationName='Clip', Input=OutputPort(self.data, 0))
        dclip.ClipType = 'Box'
        dclip.ClipType.Position = [self.extents[0], self.extents[2], -5] 
        dclip.ClipType.Length   = [self.extents[1] - self.extents[0], self.extents[3] - self.extents[2], 10]
        dclip.UpdatePipeline()
        gclip = Clip(registrationName='GClip', Input=OutputPort(self.globe, 0))
        gclip.ClipType = 'Box'
        gclip.ClipType.Position = [self.extents[0], self.extents[2], -5] 
        gclip.ClipType.Length   = [self.extents[1] - self.extents[0], self.extents[3] - self.extents[2], 10]
        gclip.UpdatePipeline()

        proj2D            = EAMProject(registrationName='2DProj', Input=OutputPort(dclip, 0))
        proj2D.Projection = self.projection
        proj2D.Translate  = 1
        proj2D.UpdatePipeline()

        projG            = EAMProject(registrationName='GProj', Input=OutputPort(gclip, 0))
        projG.Projection = self.projection
        projG.Translate  = 1
        projG.UpdatePipeline()

        projA            = EAMProject(registrationName='GLines', Input=OutputPort(glines, 0))
        projA.Projection = self.projection
        projA.Translate  = 1
        projA.UpdatePipeline()

        self.views["2DProj"]    = OutputPort(proj2D,  0)
        self.views["GProj"]     = OutputPort(projG, 0) 
        self.views["GLines"]    = OutputPort(projA, 0) 

        from paraview import servermanager as sm
        from paraview.vtk.numpy_interface import dataset_adapter as dsa
        data1 = sm.Fetch(data)
        data1 = dsa.WrapDataObject(data1)
        self.lev    = data1.FieldData['lev'].tolist()
        self.ilev   = data1.FieldData['ilev'].tolist()

    def UpdateTimeStep(self, timeprop):
        time = self.timestamps[0] + (self.timestamps[-1:][0] - self.timestamps[0]) * (timeprop / 100.)
        tk = GetTimeKeeper()
        tk.Time = time

    def LoadVariables(self, v2d, v3dm, v3di):
        self.data.a2DVariables = v2d
        self.data.a3DMiddleLayerVariables = v3dm
        self.data.a3DInterfaceLayerVariables = v3di

        self.vars["2D"]    = v2d 
        self.vars["3Dm"]   = v3dm
        self.vars["3Di"]   = v3di

        self.data.UpdatePipeline()
        pass

if __name__ == "__main__":
    e = EAMVisSource()

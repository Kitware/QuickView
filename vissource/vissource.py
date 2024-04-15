import os

import numpy as np

from vissource.viewmanager import ViewManager

from paraview.simple import (
    FindSource,
    GetTimeKeeper,
    LoadPlugin,
    OutputPort,
    SetActiveSource,
    XMLRectilinearGridReader,
    Contour,
)

# -----------------------------------------------------------------------------
# ParaView code
# -----------------------------------------------------------------------------

class EAMVisSource:
    def __init__(self):
        self.DataFile   = None
        self.ConnFile   = None

        self.views    = {}
        self.vars     = {}

        self.lev = []
        self.ilev = []
        self.vars2D_sel     = []
        self.vars3Di_sel    = []
        self.vars3Dm_sel    = []

        self.data       = None
        self.globe      = None
        self.projection = 'Robinson'
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

        if self.projection != proj:
            self.projection = proj
            eamproj2D.Projection  = proj
            eamprojG.Projection   = proj

        eamproj2D.UpdatePipeline()
        eamprojG.UpdatePipeline()
        self.views["2DProj"]  = OutputPort(eamproj2D,  0)
        self.views["GProj"]   = OutputPort(eamprojG, 0)                  

    def UpdateLev(self, lev):
        eamproj2D  = FindSource('2DProj')
        if self.data == None:
            return
        if self.lev != lev:
            self.lev = lev
            self.data.MiddleLayer = lev
            eamproj2D.UpdatePipeline()
            self.views["2DProj"]  = OutputPort(eamproj2D,  0)
        #    self.UpdateProjection(self.projection)         

    def Update(self, datafile, connfile, globefile, lev):
        if self.data == None:
            data = EAMSliceDataReader(registrationName='eamdata',
                                        ConnectivityFile=connfile,
                                        DataFile=datafile)
            data.MiddleLayer = lev
            data.InterfaceLayer = 0
            data.UpdatePipeline()
            self.data = data
        else:
            self.data.SetDataFileName(datafile)
            self.data.SetConnFileName(connfile)

        if self.globe == None:
            gdata = XMLRectilinearGridReader(registrationName='globe', FileName=[globefile])
            gdata.PointArrayStatus = ['cstar']             
            cgdata = Contour(registrationName='gcontour', Input=gdata)
            cgdata.ContourBy = ['POINTS', 'cstar']
            cgdata.Isosurfaces = [0.5]
            cgdata.PointMergeMethod = 'Uniform Binning'
            self.globe = cgdata
                             
        self.vars2D  = list(np.asarray(self.data.GetProperty('a2DVariablesInfo'))[::2])
        self.vars3Dm = list(np.asarray(self.data.GetProperty('a3DMiddleLayerVariablesInfo'))[::2])
        self.vars3Di = list(np.asarray(self.data.GetProperty('a3DInterfaceLayerVariablesInfo'))[::2])

        tk = GetTimeKeeper()
        self.timestamps = np.array(tk.TimestepValues).tolist()
        tk.Time = tk.TimestepValues[0]

        eamproj2D            = EAMProject(registrationName='2DProj', Input=OutputPort(self.data, 0))
        eamproj2D.Projection = self.projection
        eamproj2D.Translate  = 1
        eamproj2D.UpdatePipeline()

        eamprojG            = EAMProject(registrationName='GProj', Input=OutputPort(cgdata, 0))
        eamprojG.Projection = self.projection
        eamprojG.Translate  = 1
        eamprojG.UpdatePipeline()

        self.views["2DProj"]    = OutputPort(eamproj2D,  0)
        self.views["GProj"]     = OutputPort(eamprojG, 0) 

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
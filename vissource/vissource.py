import os

import numpy as np

from vissource.viewmanager import ViewManager

from paraview.simple import (
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

        self.vars2D_sel     = []
        self.vars3Di_sel    = []
        self.vars3Dm_sel    = []

        self.data       = None
        self.globe      = None
        self.slice3Dm   = None
        self.timestamps = []
        self.lev      = -1

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

    def UpdateLev(self, lev):
        if self.data == None:
            return
        src1 = OutputPort(self.data, 1)
        slice = EAMExtractSlices(registrationName='eamslice3Dm', Input=src1)                
        slice.PlanesMinMax = [lev, lev] 
        eamproj3Dm = EAMProject(registrationName='3DmProj', Input=OutputPort(slice, 0))
        eamproj3Dm.Translate = 1
        eamproj3Dm.UpdatePipeline()
        self.views["3Dm"] = OutputPort(eamproj3Dm, 0)

    def Update(self, datafile, connfile, globefile, lev):
        if self.data == None:
            self.data = EAMDataReader(registrationName='eamdata',
                                        ConnectivityFile=connfile,
                                        DataFile=datafile)
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
            eamprojG  = EAMProject(registrationName='Gproj', Input=OutputPort(cgdata, 0))
            eamprojG.Translate = 1
            eamprojG.UpdatePipeline()
            self.views["globe"] = OutputPort(eamprojG, 0)                  

        self.vars2D  = list(np.asarray(self.data.GetProperty('a2DVariablesInfo'))[::2])
        self.vars3Dm = list(np.asarray(self.data.GetProperty('a3DMiddleLayerVariablesInfo'))[::2])
        self.vars3Di = list(np.asarray(self.data.GetProperty('a3DInterfaceLayerVariablesInfo'))[::2])

        tk = GetTimeKeeper()
        self.timestamps = tk.TimestepValues
        tk.Time = tk.TimestepValues[0]

        slice = EAMExtractSlices(registrationName='eamslice3Dm', Input=OutputPort(self.data, 1))                
        slice.PlanesMinMax = [lev, lev]
        slice.UpdatePipeline()

        eamproj2D  = EAMProject(registrationName='2DProj', Input=OutputPort(self.data, 0))
        eamproj2D.Translate = 1
        eamproj2D.UpdatePipeline()
        eamproj3Dm = EAMProject(registrationName='3DmProj', Input=OutputPort(slice, 0))
        eamproj3Dm.Translate = 1
        eamproj3Dm.UpdatePipeline()

        self.views["2D"]  = OutputPort(eamproj2D,  0)
        self.views["3Dm"] = OutputPort(eamproj3Dm, 0)

    def UpdateTimeStep(self, timeprop):
        time = self.timestamps[0] + (self.timestamps[-1:][0] - self.timestamps[0]) * (timeprop / 100.)
        print(f"Updating to time {time}")
        tk = GetTimeKeeper()
        tk.Time = time

    def LoadVariables(self, v2d, v3dm, v3di):
        print(v2d, v3dm, v3di)

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

import os

import numpy as np

from vissource.viewmanager import ViewManager

from paraview.simple import (
    Show,
    CreateRenderView,
    GetTimeKeeper,
    LoadPlugin,
    OutputPort,
    SetActiveSource,
    AddCameraLink,
    RemoveCameraLink
)

# -----------------------------------------------------------------------------
# ParaView code
# -----------------------------------------------------------------------------

class EAMVisSource:
    def __init__(self):
        self.DataFile   = None
        self.ConnFile   = None
        self.views      = []
        self.vars2D     = []
        self.vars3Di    = []
        self.vars3Dm    = []
        self.data       = None
        self.timestamps = []

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

    def Update(self, datafile, connfile):
        self.data = EAMDataReader(registrationName='eamdata',
                                    ConnectivityFile=connfile,
                                    DataFile=datafile)

        self.vars2D  = list(np.asarray(self.data.GetProperty('a2DVariablesInfo'))[::2])
        self.vars3Dm = list(np.asarray(self.data.GetProperty('a3DMiddleLayerVariablesInfo'))[::2])
        self.vars3Di = list(np.asarray(self.data.GetProperty('a3DInterfaceLayerVariablesInfo'))[::2])

        tk = GetTimeKeeper()
        self.timestamps = tk.TimestepValues
        tk.Time = tk.TimestepValues[0]

        SetActiveSource(self.data)

        self.views  = []

        view0 = CreateRenderView('port0')
        rep0 = Show(OutputPort(self.data, 0), view0)
        vmgr0 = ViewManager(rep0, view0)
        self.views.append(vmgr0)

        view1 = CreateRenderView('port1')
        rep1 = Show(OutputPort(self.data, 1), view1)
        vmgr1 = ViewManager(rep1, view1)
        self.views.append(vmgr1)

    def UpdateViews2D(self, varaible, colormap):
        if varaible is None:
            return
        view = self.views[0]
        view.ApplyColorMap(varaible, colormap)
        pass

    def UpdateViews3D(self, varaible, colormap):
        if varaible is None:
            return
        view = self.views[1]
        view.ApplyColorMap(varaible, colormap)
        pass

    def UpdateTimeStep(self, timeprop):
        time = self.timestamps[0] + (self.timestamps[-1:][0] - self.timestamps[0]) * (timeprop / 100.)
        print(f"Updating to time {time}")
        tk = GetTimeKeeper()
        tk.Time = time
        #self.data.UpdatePipeline()

    def LoadVariables(self, v2d, v3dm, v3di):
        self.data.a2DVariables = v2d
        self.data.a3DMiddleLayerVariables = v3dm
        self.data.a3DInterfaceLayerVariables = v3di
        self.data.UpdatePipeline()
        pass

    def AddCameraLink(self, enable):
        if enable:
            AddCameraLink(self.views[0].view, self.views[1].view, 'viewlink')
        else:
            RemoveCameraLink('viewlink')

if __name__ == "__main__":
    e = EAMVisSource()

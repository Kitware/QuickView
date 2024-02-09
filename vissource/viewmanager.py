from paraview.simple import (
    Show,
    ColorBy,
    GetColorTransferFunction
)

class ViewManager():
    def __init__(self, rep, view):
        self.rep  = rep
        self.view = view

    def __str__(self):
        return f"View {self.view}, Rep {self.rep}"

    def ApplyColorMap(self, variable, colormap):
        ColorBy(self.rep, ("CELLS", variable))
        coltrfunc = GetColorTransferFunction(variable)
        # Apply a preset using its name. Note this may not work as expected when presets have duplicate names.
        coltrfunc.ApplyPreset(colormap, True)
        pass

    def GetView(self):
        return self.view

from trame.widgets import html
from trame.widgets import vuetify2 as v2
import base64

from vtkmodules.vtkCommonCore import vtkUnsignedCharArray
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkIOImage import vtkPNGWriter
from vtkmodules.vtkCommonCore import vtkLookupTable


def paraview_to_vtk_lut(paraview_lut, num_colors=256):
    """
    Convert a ParaView color transfer function to a VTK lookup table.

    Parameters:
    -----------
    paraview_lut : paraview.servermanager.PVLookupTable
        The ParaView color transfer function from GetColorTransferFunction()
    num_colors : int, optional
        Number of colors in the VTK lookup table (default: 256)

    Returns:
    --------
    vtk.vtkLookupTable
        A VTK lookup table with interpolated colors from the ParaView LUT
    """
    import vtk
    import numpy as np

    # Get RGB points from ParaView LUT
    rgb_points = paraview_lut.RGBPoints

    if len(rgb_points) < 8:
        raise ValueError("ParaView LUT must have at least 2 color points")

    # Create VTK lookup table
    vtk_lut = vtk.vtkLookupTable()

    # Extract scalars and colors from the flat RGB points array
    scalars = np.array([rgb_points[i] for i in range(0, len(rgb_points), 4)])
    colors = np.array(
        [
            [rgb_points[i + 1], rgb_points[i + 2], rgb_points[i + 3]]
            for i in range(0, len(rgb_points), 4)
        ]
    )

    # Get range
    min_val = scalars[0]
    max_val = scalars[-1]

    # Generate all scalar values for the lookup table
    table_scalars = np.linspace(min_val, max_val, num_colors)

    # Vectorized interpolation for all colors at once
    r_values = np.interp(table_scalars, scalars, colors[:, 0])
    g_values = np.interp(table_scalars, scalars, colors[:, 1])
    b_values = np.interp(table_scalars, scalars, colors[:, 2])

    # Set up the VTK lookup table
    vtk_lut.SetRange(min_val, max_val)
    vtk_lut.SetNumberOfTableValues(num_colors)
    vtk_lut.Build()

    # Set all colors at once
    for i in range(num_colors):
        vtk_lut.SetTableValue(i, r_values[i], g_values[i], b_values[i], 1.0)

    return vtk_lut


def to_image(lut, samples=255):
    colorArray = vtkUnsignedCharArray()
    colorArray.SetNumberOfComponents(3)
    colorArray.SetNumberOfTuples(samples)

    dataRange = lut.GetRange()
    delta = (dataRange[1] - dataRange[0]) / float(samples)

    # Add the color array to an image data
    imgData = vtkImageData()
    imgData.SetDimensions(samples, 1, 1)
    imgData.GetPointData().SetScalars(colorArray)

    # Loop over all presets
    rgb = [0, 0, 0]
    for i in range(samples):
        lut.GetColor(dataRange[0] + float(i) * delta, rgb)
        r = int(round(rgb[0] * 255))
        g = int(round(rgb[1] * 255))
        b = int(round(rgb[2] * 255))
        colorArray.SetTuple3(i, r, g, b)

    writer = vtkPNGWriter()
    writer.WriteToMemoryOn()
    writer.SetInputData(imgData)
    writer.SetCompressionLevel(6)
    writer.Write()

    writer.GetResult()

    base64_img = base64.standard_b64encode(writer.GetResult()).decode("utf-8")
    return f"data:image/png;base64,{base64_img}"


class ScalarBar(v2.VTooltip):
    """
    Scalar bar for the XArray Explorers.
    """

    _next_id = 0

    @classmethod
    def next_id(cls):
        """Get the next unique ID for the scalar bar."""
        cls._next_id += 1
        return f"pan3d_scalarbar{cls._next_id}"

    def __init__(
        self,
        preset="Fast",
        color_min=0.0,
        color_max=1.0,
        ctx_name=None,
        paraview_lut=None,
        **kwargs,
    ):
        """Scalar bar for the XArray Explorers.

        Parameters:
        -----------
        preset : str, optional
            Color preset name (default: "Fast")
        color_min : float, optional
            Minimum color value (default: 0.0)
        color_max : float, optional
            Maximum color value (default: 1.0)
        ctx_name : str, optional
            Context name for trame
        paraview_lut : paraview.servermanager.PVLookupTable, optional
            ParaView color transfer function to initialize from
        **kwargs : dict
            Additional keyword arguments
        """
        # Initialize VTK lookup table
        if paraview_lut is not None:
            self._lut = paraview_to_vtk_lut(paraview_lut)
            # Get range from the converted LUT
            lut_range = self._lut.GetRange()
            color_min = lut_range[0]
            color_max = lut_range[1]
        else:
            self._lut = vtkLookupTable()

        super().__init__(location="top", ctx_name=ctx_name)

        ns = self.next_id()
        self.__preset_image = f"{ns}_preset"
        self.__color_min = f"{ns}_color_min"
        self.__color_max = f"{ns}_color_max"
        # Probe enables mouse events for scalar bar
        self.__probe_location = f"{ns}_probe_location"
        self.__probe_enabled = f"{ns}_probe_enabled"

        # Initialize state
        self.preset = preset
        self.set_color_range(color_min, color_max)
        self.state[self.__probe_location] = []
        self.state[self.__probe_enabled] = 0
        self.state.client_only(
            self.__probe_location,
            self.__probe_enabled,
        )

        # Generate initial scalar bar image
        self._update_preset_image()

        with self:
            # Content
            with html.Template(v_slot_activator="{ props }"):
                with html.Div(
                    classes="scalarbar",
                    rounded="pill",
                    v_bind="props",
                    **kwargs,
                ):
                    html.Div(
                        f"{{{{{self.__color_min}.toFixed(6) }}}}",
                        classes="scalarbar-left",
                    )
                    html.Img(
                        src=(self.__preset_image, None),
                        style="height: 100%; width: 100%;",
                        classes="rounded-lg border-thin",
                        mousemove=f"{self.__probe_location} = [$event.x, $event.target.getBoundingClientRect()]",
                        mouseenter=f"{self.__probe_enabled} = 1",
                        mouseleave=f"{self.__probe_enabled} = 0",
                        __events=["mousemove", "mouseenter", "mouseleave"],
                    )
                    html.Div(
                        v_show=(self.__probe_enabled, False),
                        classes="scalar-cursor",
                        style=(
                            f"`left: ${{{self.__probe_location}?.[0] - {self.__probe_location}?.[1]?.left}}px`",
                        ),
                    )
                    html.Div(
                        f"{{{{ {self.__color_max}.toFixed(6) }}}}",
                        classes="scalarbar-right",
                    )
            html.Span(
                f"{{{{ (({self.__color_max} - {self.__color_min}) * ({self.__probe_location}?.[0] - {self.__probe_location}?.[1]?.left) / {self.__probe_location}?.[1]?.width + {self.__color_min}).toFixed(6) }}}}"
            )

    def set_color_range(self, color_min, color_max):
        """Set the color range for the scalar bar."""
        self.state[self.__color_min] = color_min
        self.state[self.__color_max] = color_max

    def update_from_paraview_lut(self, paraview_lut, num_colors=256):
        """Update the internal VTK lookup table from a ParaView color transfer function.

        Parameters:
        -----------
        paraview_lut : paraview.servermanager.PVLookupTable
            ParaView color transfer function to update from
        num_colors : int, optional
            Number of colors in the VTK lookup table (default: 256)
        """
        # Convert ParaView LUT to VTK LUT
        self._lut = paraview_to_vtk_lut(paraview_lut, num_colors)

        # Update color range from the new LUT
        lut_range = self._lut.GetRange()
        self.set_color_range(lut_range[0], lut_range[1])

        # Update the scalar bar image
        self._update_preset_image()

    def _update_preset_image(self):
        """Generate and update the scalar bar image from the current lookup table."""
        if self._lut is not None:
            image_data = to_image(self._lut)
            self.state[self.__preset_image] = image_data

    def update_preset(self, preset_name):
        """Update the color preset and regenerate the scalar bar image.

        Parameters:
        -----------
        preset_name : str
            Name of the color preset to apply
        """
        self.preset = preset_name
        # If you have a method to apply presets to VTK LUT, call it here
        # For now, just update the image with current LUT
        self._update_preset_image()

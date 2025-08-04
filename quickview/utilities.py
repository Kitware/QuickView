import os
import base64
import numpy as np

from vtkmodules.vtkCommonCore import vtkUnsignedCharArray, vtkLookupTable
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkIOImage import vtkPNGWriter


def ValidateArguments(conn_file, data_file, state_file, work_dir):
    if (conn_file is None or data_file is None) and state_file is None:
        print(
            "Error : either both the data and connectivity files are not specified and the state file is not provided too"
        )
        exit()
    if state_file is None:
        if not os.path.exists(conn_file) or not os.path.exists(data_file):
            print("Either the data file or the connectivity file does not exist")
            exit()
    elif not os.path.exists(state_file):
        print("Provided state file does not exist")
        exit()
    if work_dir is None:
        print("No working directory is provided, using current directory as default")
    return True


def get_lut_from_color_transfer_function(paraview_lut, num_colors=256):
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
    vtkLookupTable
        A VTK lookup table with interpolated colors from the ParaView LUT
    """
    # Get RGB points from ParaView LUT
    rgb_points = paraview_lut.RGBPoints

    if len(rgb_points) < 8:
        raise ValueError("ParaView LUT must have at least 2 color points")

    # Create VTK lookup table
    vtk_lut = vtkLookupTable()

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


def vtk_lut_to_image(lut, samples=255):
    """
    Convert a VTK lookup table to a base64-encoded PNG image.

    Parameters:
    -----------
    lut : vtkLookupTable
        The VTK lookup table to convert
    samples : int, optional
        Number of samples for the color bar (default: 255)

    Returns:
    --------
    str
        Base64-encoded PNG image as a data URI
    """
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


def build_colorbar_image(paraview_lut, log_scale=False, invert=False):
    """
    Build a colorbar image from a ParaView color transfer function.

    Parameters:
    -----------
    paraview_lut : paraview.servermanager.PVLookupTable
        The ParaView color transfer function
    log_scale : bool, optional
        Whether to apply log scale (affects data mapping, not image)
    invert : bool, optional
        Whether to invert colors (will affect the image)

    Returns:
    --------
    str
        Base64-encoded PNG image as a data URI
    """
    # Convert to VTK LUT - this will get the current state from ParaView
    # including any inversions already applied by InvertTransferFunction
    vtk_lut = get_lut_from_color_transfer_function(paraview_lut)

    # Convert to image
    return vtk_lut_to_image(vtk_lut)


def get_cached_colorbar_image(colormap_name, inverted=False):
    """
    Get a cached colorbar image for a given colormap.

    Parameters:
    -----------
    colormap_name : str
        Name of the colormap (e.g., "Cool to Warm", "Rainbow Desaturated")
    inverted : bool
        Whether to get the inverted version

    Returns:
    --------
    str
        Base64-encoded PNG image as a data URI, or empty string if not found
    """
    # Import the cache (will be added after running generate_colorbar_cache.py)
    from quickview.colorbar_cache import COLORBAR_CACHE

    if colormap_name in COLORBAR_CACHE:
        variant = "inverted" if inverted else "normal"
        return COLORBAR_CACHE[colormap_name].get(variant, "")

    return ""

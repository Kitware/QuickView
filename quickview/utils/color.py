"""
Color and colormap operations for visualization.

This module contains utilities for color transfer functions, lookup tables,
and colorbar generation.
"""

import base64
import io
import numpy as np
from PIL import Image
from vtkmodules.vtkCommonCore import vtkUnsignedCharArray, vtkLookupTable
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkIOImage import vtkPNGWriter
from vtkmodules.vtkRenderingCore import (
    vtkRenderer,
    vtkRenderWindow,
    vtkWindowToImageFilter,
)
from vtkmodules.vtkRenderingAnnotation import vtkScalarBarActor


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
    writer.SetCompressionLevel(1)
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
    if colormap_name in COLORBAR_CACHE:
        variant = "inverted" if inverted else "normal"
        return COLORBAR_CACHE[colormap_name].get(variant, "")

    return ""


def create_vertical_scalar_bar(vtk_lut, width, height, config):
    """Create a vertical scalar bar image using VTK's ScalarBarActor.

    Parameters:
    -----------
    vtk_lut : vtkLookupTable
        The VTK lookup table for colors
    width : int
        Width of the scalar bar image
    height : int
        Height of the scalar bar image (should match main image height)
    config : object
        Configuration object with scalar bar settings

    Returns:
    --------
    PIL.Image
        Vertical scalar bar image with gradient background
    """
    # Create a renderer and render window
    renderer = vtkRenderer()
    # Set gradient background from (0, 0, 42) at top to (84, 89, 109) at bottom
    # Note: VTK uses bottom color first for gradient
    renderer.SetBackground(84 / 255.0, 89 / 255.0, 109 / 255.0)  # Bottom color
    renderer.SetBackground2(0 / 255.0, 0 / 255.0, 42 / 255.0)  # Top color
    renderer.SetGradientBackground(True)

    # Use actual panel dimensions for render window
    window_width = width
    window_height = height

    render_window = vtkRenderWindow()
    render_window.SetSize(window_width, window_height)
    render_window.SetOffScreenRendering(1)
    render_window.AddRenderer(renderer)

    # Create scalar bar actor
    scalar_bar = vtkScalarBarActor()
    scalar_bar.SetLookupTable(vtk_lut)
    scalar_bar.SetNumberOfLabels(config.scalar_bar_num_labels)

    # Set orientation to vertical
    scalar_bar.SetOrientationToVertical()

    # Set title if provided
    if config.scalar_bar_title:
        scalar_bar.SetTitle(config.scalar_bar_title)

    # Configure title text properties
    title_prop = scalar_bar.GetTitleTextProperty()
    title_prop.SetFontFamilyToArial()
    title_prop.SetBold(True)
    title_prop.SetFontSize(config.scalar_bar_title_font_size)
    title_prop.SetColor(1, 1, 1)  # white title text for visibility on dark background

    # Configure label text properties
    label_prop = scalar_bar.GetLabelTextProperty()
    label_prop.SetFontFamilyToArial()
    label_prop.SetBold(False)
    label_prop.SetFontSize(config.scalar_bar_label_font_size)
    label_prop.SetColor(1, 1, 1)  # white label text for visibility on dark background

    # Enable absolute font sizing
    scalar_bar.UnconstrainedFontSizeOn()

    # Set the label format
    scalar_bar.SetLabelFormat(config.scalar_bar_label_format)
    # Configure scalar bar dimensions and position
    # Make the color bar 30% of panel width with room for labels
    # Leave more margin at top and bottom to prevent bleeding
    scalar_bar.SetPosition(0.1, 0.1)  # Start at 10% from left, 5% from bottom
    scalar_bar.SetPosition2(
        0.9, 0.80
    )  # Use 90% of window width, 90% height (leaving 10% top margin)

    # Set the width of the color bar itself to be 30% of the actor width
    # This gives the color bar proper visual presence
    scalar_bar.SetBarRatio(0.3)  # Color bar takes 30% of actor width

    # Add to renderer
    renderer.AddActor(scalar_bar)

    # Render the scene
    render_window.Render()

    # Convert to image
    window_to_image = vtkWindowToImageFilter()
    window_to_image.SetInput(render_window)
    window_to_image.SetInputBufferTypeToRGBA()
    window_to_image.Update()

    # Write to PNG in memory
    writer = vtkPNGWriter()
    writer.WriteToMemoryOn()
    writer.SetInputConnection(window_to_image.GetOutputPort())
    writer.Write()

    # Convert to PIL Image
    png_data = writer.GetResult()
    img = Image.open(io.BytesIO(bytes(png_data)))

    # Keep the image as is with the gradient background
    # No need to make anything transparent or crop
    return img


def add_metadata_annotations(image, metadata, font_size=14):
    """
    Add metadata annotations to an image (e.g., timestep, average, level).

    Parameters:
    -----------
    image : PIL.Image
        The image to annotate
    metadata : dict
        Metadata dictionary containing:
        - variable_name: str
        - average: float
        - timestep: int
        - level: int or None (for midpoint/interface variables)
        - level_type: str ('midpoint' or 'interface') or None
    font_size : int
        Font size for the annotations

    Returns:
    --------
    PIL.Image
        Annotated image
    """
    from PIL import Image, ImageDraw, ImageFont

    # Create a copy to avoid modifying the original
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)

    # Try to load a good font, fall back to default if not available
    try:
        # Try to load a monospace font for better alignment
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf", font_size
        )
    except (OSError, IOError):
        try:
            # Try DejaVu Sans Mono as alternative
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", font_size
            )
        except (OSError, IOError):
            # Fall back to default font
            font = ImageFont.load_default()

    # Prepare metadata text lines
    lines = []

    # Variable name
    if "variable_name" in metadata and metadata["variable_name"]:
        lines.append(metadata["variable_name"])

    # Average value
    if "average" in metadata and metadata["average"] is not None:
        if isinstance(metadata["average"], (int, float)):
            # Format in scientific notation
            lines.append(f"(avg: {metadata['average']:.2e})")
        else:
            lines.append("(avg: N/A)")

    # Time step
    if "timestep" in metadata:
        lines.append(f"t = {metadata['timestep']}")

    # Level (for midpoint/interface variables)
    if "level" in metadata and metadata["level"] is not None:
        if "level_type" in metadata:
            if metadata["level_type"] == "midpoint":
                lines.append(f"k = {metadata['level']} (midpoint)")
            elif metadata["level_type"] == "interface":
                lines.append(f"k = {metadata['level']} (interface)")
            else:
                lines.append(f"k = {metadata['level']}")
        else:
            lines.append(f"k = {metadata['level']}")

    # Calculate text positioning
    x_offset = 10
    y_offset = 10
    line_height = font_size + 4

    # Draw semi-transparent background for better text visibility
    if lines:
        # Calculate background size
        max_width = 0
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            max_width = max(max_width, text_width)

        background_width = max_width + 20
        background_height = len(lines) * line_height + 10

        # Draw semi-transparent background rectangle
        background = Image.new("RGBA", annotated.size, (0, 0, 0, 0))
        background_draw = ImageDraw.Draw(background)
        background_draw.rectangle(
            [
                (x_offset - 5, y_offset - 5),
                (x_offset + background_width, y_offset + background_height),
            ],
            fill=(0, 0, 0, 128),  # Semi-transparent black
        )

        # Composite the background onto the image
        annotated = Image.alpha_composite(
            annotated.convert("RGBA"), background
        ).convert("RGB")

        # Redraw on the composited image
        draw = ImageDraw.Draw(annotated)

    # Draw text lines
    for i, line in enumerate(lines):
        y_position = y_offset + i * line_height
        draw.text((x_offset, y_position), line, fill=(255, 255, 255), font=font)

    return annotated


# Auto-generated colorbar cache
# This dictionary contains pre-generated base64-encoded colorbar images
COLORBAR_CACHE = {
    "Inferno (matplotlib)": {
        "normal": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAtElEQVQokY2SQW7EMAzEyLH6/x+velC8TorFooAhkKNJLrZQIgqRYAYccA1f8+jSZBcyCcnoMJGVO3QmHw5KgpsNXuAwm/E24+QIe8tW/qVX2M+wp3kBaIdTG32G/Ul7/7xzoM/np7bZ9l4b/Qqm48uHtpPkhPr6qNxXafL6DuTB5GWakzfBNELm+H5KRAzn8p+vIOumb17trNZ0+uI/s8jqmRYpUp1isxb50cIypaUVS5fWL+AwbZqLAs4pAAAAAElFTkSuQmCC",
        "inverted": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAwUlEQVQokY2SUWpDMRDEZnP/Y/SWXUv9WPvlhYS2YIxGjI0xW+0XLG1d2M6iY2uHb+3QoWMXm8sOq+iwQhcrrE87GXCAQB0InM61fIITDUqCISExUiGhpELFgUcorfAYf/HvIKX77PD2n2PpgyeXFrcO/gFY5jVa3E1y1bAwA5pnLeGleYtb5k2GFObck/nUqU18lf+M7hjZl3jtqJGEeFhyoCAaDp8JqIF1zDqTsQy4HOkMxyIoZnnMgR1zeD9kgz+NE+IXkDSoZwAAAABJRU5ErkJggg==",
    },
    "Viridis (matplotlib)": {
        "normal": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAsklEQVQokXWQ2w0DMQgEZ5fWUkL6L8XkA/xI4pNOaBgWn4ReeiPLWhULSTYSXaXpt2wuOKZTpoRZ8mwXp4RAym4rQAWyeY3ADaf8Yl+nP3U9ew/slkvmaXcDT4H8f6ElSybH6JQ6p5Q5Kyj7otP3GereDZvrwM2zmgnr49qOk6N5WBkLlKZMtcNkaFijMrN2ZgcY0VsjqMdHVJKMWmyTvdtQfydIQ4hAhpCMAhmFZGwU8gd7+IgHAybGAwAAAABJRU5ErkJggg==",
        "inverted": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAsklEQVQokXWQ0W3FMAzEKO/S/cfqFDr2I3acF78CgXDiUQjg6t+fkDbBkNZgY7A10NgSaCrSVFOxmmrGDI4wVqhmTOLljGa0lcmrHev2amvPJaz2uqp4O5XpVLyEBXde3+fqIvqchJ31nQUt5nrlUnBzBApB7harVljVA0I9qmVuWCfnNN/rF/7/1QH9KswnuHIO8srxgPOJ2dAKzN/JFo78XPOEYg6Yu9XMKkHNLcc1/wAGJ3utf9Ck5gAAAABJRU5ErkJggg==",
    },
    "oslo": {
        "normal": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAmUlEQVQokXWRWQ7EMAxCedz/zp2PeiEZVa0QEJzEDoAwtjAYiggGAUGjASkcWVB/c4RovzkR0ByhU3Yedof201xe99Th36t/ye70DmTXaRLml/QrXWSxHNzfFNwbeaQc5B2DUUgZ1QP0+NFwTimkTapMF3k+A8EjP2exS1cVeTG6EPezmMRu09PvORwH5pR8jXt4b2Z75AYKf0CgA/rlIrMBAAAAAElFTkSuQmCC",
        "inverted": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAmElEQVQokW2RUQ7EQAhC6f3vzNuPjoqdTRMDQo2DD2ADviperLU0UB8lYTid7qeEqq9S1RXrAGQVQIxHIKTB7xwFDbyc0kw7nmf5/xjkwWzazlnMszBB93sjlk84GeeOeYJfWWKuYR+qoNrNltRNLamrxoYuZ/YPXmoYRP6l925JQe89w38mNFaP7TWoUb32ucH1FlcCxv4BzjllJjnD7IwAAAAASUVORK5CYII=",
    },
    "batlow": {
        "normal": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAArklEQVQokW2RwZEEMQjEWk0UG9rmHwj3AGzmZj+ULBqbKsPniwVggTAgvVjFCEswICFASC4uyeKVYWeuBEntf9TV4so8x8VZYTckyN3NBqWvT1ThnKrFPVLJU1deXn515ecl77DZmWZ3prbVGF3uIyNlYckwsoACBgyW3V/qYxDGFpZ5gOmAza3TMgooMMQ/EEHvFf2UYnaJ2Tdqdy0/fPxPWRxH5ls+Z/PymYrEfz0jPL9tQdmmAAAAAElFTkSuQmCC",
        "inverted": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAArklEQVQokW2RQQ4DIQzEnP9/rS+qxLgHCLDqXkaOGciB+n6+mDIwMBgcGEjZhpZrXFzr6CG55X33VR4/vLwGhgajA+LsEI0vEBmazJHkTqLOo5DghhgxZC6wIQe0IQfokR5pSZhjtVzsMjsrIrU5lIvL06nd2dIrd/nUHsn9iNfSTk7Tsq/oBtwrZPYVRRpEis2ymAUvyWLE9e4xt7y8h/O8mFUw3Y8KQfGP57/+AEbyxodkWlsHAAAAAElFTkSuQmCC",
    },
    "vik": {
        "normal": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAuUlEQVQokXWOUXIGIQyCAfcEvWHvf4ZAH4xbbf1nMuwHQVfi65siSCz9Y1uv4U35qfxut7/MMklKFKWFIiWJWnZMu2CcsOlmx2X73O3H5Nlv5r9EHNIjDi77CxjkEAZ7BIgZgBDCSggzPbARw9Xqig1XXLCTysue7FTFhWzJ0blaJ0cCO7nbrsXrJb2CnX6Su7a4m/Gy5ZWnmr3Ytue3smzK201OGX4nJwTJYW0kcNjbGb4wt2YfDH4AjnNMdUGwXfEAAAAASUVORK5CYII=",
        "inverted": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAwUlEQVQokXWOQZbDMAxCAW3minP/a1TQha20btM8P/xBODb/8SdCBAkRUkhIEEFhjxYI4mt66RwcfQehBInayhJV1PoW1HasksRhXqzNpHCxRBbeeO4oct1X6wh11Yqczp3F/OdIVL8sVaComtfW0dnPq/USqKACNapwFmQykMEGHBrozDI66aCddjq54OG0va3T9mOP/JlM7fHq3ydfBbfTfdpz6hN8ghM7GZtt1xY4cZDEwQUJxn5o7sKf+hXmDJ8lOkiIWk7JIwAAAABJRU5ErkJggg==",
    },
    "roma": {
        "normal": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAxUlEQVQokW2PQQ7DIAwEd80j+tv+nJ0eDCRpK1nWMF6I4/dLHl5V9pCrWS67XBtcl9T96C+W7tKd1za2T+Bn6n/J/ZqOP+b6UFftTO2+QNU/c+RYcrNr6MHjGNWwjxnyv+5iM67uaNBehSsuVDSrUHefHjkNOPK9T/QANGnWXEclmg1o5jIJE82058hEExIlZJtcZgEhiJAISOAJ3AGRBQoAEUGsjHamzckICOrRuX5iPY0I65Etl1+B5w7Zu4UAWTsndH0AoR4v4nBAd8IAAAAASUVORK5CYII=",
        "inverted": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAA0ElEQVQokWWPQY4gIRDD4vCi+e18lmQPTQM9K6GScQUoGD+/Nnth2WAMGCzMWQijxejtCrBkALz8kssA0gqfLjy3rdjKXAdPBt0zPJkN/oItjBHrXzI3yMboMeM1A9kaxmhYg0uiYRkNtI3RoK+skelAVm/41li1aoVPjRUaHm5opNBJgyaNuqoy6dTL/9dmKrOHs0xmF2dzEyU9Jk3bLdsPVO27bdO2emFL9Rilra6w2otXTOueP8ndPQ+9x093sfZI0Z4kh9XZpp1q2tnO/gOZg0urikp4YQAAAABJRU5ErkJggg==",
    },
    "vanimo": {
        "normal": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAv0lEQVQokW2NUXLFMAwCAeX+N+uRBP2wZee9diaRlyWKmZ92O22308M+xv6Kh/2qPudu7fQ6p/VOA39M1sjtvj59xX7JTttet3V62u4sOfBt2vEF7F917PiYCzvGsOEsSIIENpLNfx8ACQLgTgKLB0AAAAOAPHF4gCQI6sbF1PUUKWhVAsUrtYHkYS1ztz6ktG7hf7u33Sscz7P+kmfyM0rDUu24X0m1DnFAVTNLJamGS3pUG+rGR3pUm0uP6vkFRqZfaI03/wEAAAAASUVORK5CYII=",
        "inverted": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAxklEQVQokW2NwXHEMAwDAbD/MtJGKjOBPCRa9uVmNNRiSUr87R/35b7al/tyt/vyzb66215+wD3Vw97Vzr7ttu3skNju2I6zozOcJK/oJBiG8yExK8jeQrK9P7tnxTPzkp+7a32Pze+3BHI4CYLjJyI4gGEA4YoAAHIAAUHgWUmA4JdDCiREUKQgkoIEiRQXqCDxDVSxblOs4gNURRUlDjyN9qS0WvspLS9tvuFb5FzP8h48hjW+Rtbxz6ra3SPr0ar/rVrmD0AJPNOWINzbAAAAAElFTkSuQmCC",
    },
    "tokyo": {
        "normal": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAoUlEQVQokW2Syw3DMAxD+eh7J+gY3X+2HiRZih0EEEjq+R++nx/IwsgCyWDxCDlD2C2MzJPhWZ08IwfhEGVDxBSZSNXVsGqbcCd6dCXuVjNHIilm0+jedVheAN6BS/Tq99JcQ/pERU5s3M/J+4DBewgg+RbQ5K4onyyf8NQpnLU+XMZhQrnUGnZFXdtie5kKqXAKhTVqi8hEgC2QHdvtX89/EjgCyIkUtH0AAAAASUVORK5CYII=",
        "inverted": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAq0lEQVQokXWSQQ6DMAwEp/9/Y9/QD5SdHuIEJ6gCWbvLYISd1+f7FiVRsekENakkYkxKJ2bZmHh1ca0kV4WZYVaNmcBto9M5WtZloqtqVIllm0aMqOGuQlRQwikEGSSOEITs1tmq3c0KnDw7xkbWIzayC5c9XuQfwAE8+nvw/vtu6X0CbH/nPi7bfGx2JpqRr9Om4jx8qby2Z2iLnZV723PJU4x9doZHyB3+APLS0HEVvfePAAAAAElFTkSuQmCC",
    },
    "davos": {
        "normal": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAApklEQVQokYWSUa7DIAwEd0Z6l+v975N+2CbQNnqRsGbXGKMY8veKRqJABAxQEpEADRbWqhIAzQCQL6iqrfxMdV9WdjZwf9MhG5dqcMkVG3I4HxySQ36bCVynf0Gy+Amyqi5IPv1/5Hn+c5e6WwKXDxeWzWmZ+eu3Y4+ix95ynoAiOIA3qz8jKi6nti9gM7eDnSey2Jl6X2rAlN9RUilSZixIVWWZzW/flBj7cleqDQAAAABJRU5ErkJggg==",
        "inverted": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAnElEQVQokX2SQRLDMAgDlf//ebcHQ0xdTy/MSgGiTHiAxMSEqFkSNYvFDV2DkvhWQ8S1QRSXX4yWpM0FgPryAEtuvlbH/F5dmVBTaViZUimNQ05Ho0/JbGcxg/Xpnhu0zPaPtrvMlJe2E3KG+Qrs+SF/TCfnNN2VlwesW2h2s8PvGRwN3U1v5/fRhnol9Kq+rq9x6jCXW+P07yf4AfjdPHOVKVO9AAAAAElFTkSuQmCC",
    },
    "acton": {
        "normal": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAi0lEQVQokYWRyREDIQwEu+fvNByH84/KD/CuhKGWD6O5isP36+NYmTtqfsPCFwldPJWhBDfSKfKM2fJnI+FiUMOQEISAOvAcoai3tKj55y+/lWkgLW56bZrTxoyTi5h5OzIvvX8t2oeq8yWIFEMhU8kbGOMhm41/re2gNTuaWf3sVFhTXD2r4RkDfgEEQgLT9KY7/QAAAABJRU5ErkJggg==",
        "inverted": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAjUlEQVQokZWSOxJDMQgDlfvfNFXqFNpXYByDPZ5JtyAJf1+f9xeQEBKIqPiHRxZzNrg2HZFdRZ4DF1tCMRQwR78R3v2AcBu7rWUyMg2zKhzLDxAC5LgPCQXLYnB2SqlhHtmUOowUTfoxvb/6D2puMlVi5/MvWHlebQe/3Mi5f2XfPOtbtEg327Vch7j1H1G+JZaGOgELAAAAAElFTkSuQmCC",
    },
    "grayC": {
        "normal": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAASUlEQVQokbWSOw4AMAhCgfsfukOTxrRWTT8MBh6MEoAkSSRlRLITngrAq2U82LUuX2FK6rFY3fg0BjDgn+T+zwonYqPr68aN4zZHpwL88xPUcgAAAABJRU5ErkJggg==",
        "inverted": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAR0lEQVQokbWSSQoAIAwD6///nHgQROxiEM2hZKY9tpEkCSCcGYql6B5Dk8l/MTPdb7LAV11fHVE0mSy8slUOLi591recGdgB5Ri1JqWVr6UAAAAASUVORK5CYII=",
    },
    "navia": {
        "normal": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAr0lEQVQokXWS0Q3EIAxD/ZwRbojbf0LuwyGlrQ6h6OE4CVWhPl9sYYGwMOS4t+/HePzXw6PE05BhsMzotA62yIqh18mA2tVRzQLUoCcosEBS9LVFoRWQxrCECOhIjfmdOmqvJjr67ynTIXd4zVpM9qqK8yqBu/+hv5Qz+r/ijjrZ+XuzHSCxHKbApsBgXK24sKGwCb9ANuWt3I5qEdWGI+IM31dgsvvd5Emdyv4++AEbhyvIyFxhOAAAAABJRU5ErkJggg==",
        "inverted": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAr0lEQVQokXWSQY7EIBADzf9fuP/Y41I1h24IzMxGqFU2dkgkxt/vj0E1LtgTorIdNgsdQNvfEzGzgOXgPLjlXPINpqBTgKlTaUcoKTrreNck2MslNTj0Yh0YF//n9Ex05MMpTi4/xbuSoUlXjnySs1KywzFHN7v1QHrrCew3xHzfeutex/VnP6f0L1TxE1xc0DMU99M35WE6V9dKCiJKBRafPnEt0EvmkN7ye+ZhIy9nOgFitgzqrgAAAABJRU5ErkJggg==",
    },
    "bam": {
        "normal": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAvUlEQVQokW2Q0W3FMAwDSXm8ztH9F6jIfkhWlNcmgnFHEXAQfsdXnHMi4tQ0xon1vAPuVZBrwbUnm/kIWzjtYU4tyEoW7/Clp8LRP7AYh0/5kEGsQnOQh8MfgCBZAAZxuYEVAiQCLCD+GQwYhDFgwKWXawTYtiFDBXKxml1JyrJTlpwqUF7O4VRr+kdqTVWSnXywJGVaD0uS5AtSSvIVe4WexC91e2084vt207fZ3bXSbffdfa/v4fVh8zv0CzRYXG5OJkEEAAAAAElFTkSuQmCC",
        "inverted": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAvUlEQVQokW2QQY7DMAwDSarX/dn+/zcme7DsCG2DQJ6RaMcI//4hsqQSJUkUVdLlBkl8Apwdsol8pmd0suQM8x4+k5pnnjvc72pcTCWJ1aDqysEqqYr1g3k7L11lqX/DZB0Vd0X1lSlCpIjLJBqAzSQ274rmoDXA1gBbf7xJAAMJgvjWwA1xcxJ4a/INaza9tQMrsXvaMd/84AG9cYPt2X/Un03bSRynyV+8/YHed3hgr+c5uj5W2+vIWl6tb9Q4Uct7Ls3FAAAAAElFTkSuQmCC",
    },
    "lisbon": {
        "normal": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAv0lEQVQokXWN240DMQwDSar/MpMuTN6HX9pFTjDs0YiQ+f1k2CMZtp1hN4jtBjNzoGVyM/8lnV+yJZ33j21hT9q57anxeu3sHfPN+mSZxLngZDE8pkFGbCx2PJAZ8ILFY3GCBeeEMBJgcgAzASaHBBECYAiQIENABEkSJERQJCGShESS0mx52wXUlBtEUk8vipKe05MXJb1H2zzaw+zy3nVZElVqRWmLurir+qyZarIkqaqtri5vq1LNTPMlqf4AXTRc4dgYTmkAAAAASUVORK5CYII=",
        "inverted": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAt0lEQVQokW2MQZLEIAwD1eL/D9zHYO0hOHFmhgKX1JIh+avaVbt2HVFVtfOQwffL5hOO+ey2eJEatZtmJsNmP+l75rYZ0cUfmy/Sdkap1CENnzRvflaU22ZaVZIolYpybiqKlJAokkKkiEQSERIByRECyYLIAuH3RRgsluzWlo/AS5grssXiirzA2DTBpqG9sI3xsg+xDR5nnfeB7rW2renOIBw+miwPyA/Y4szF/PZ3c/m70wL+AVF/dNRI9cmXAAAAAElFTkSuQmCC",
    },
    "managua": {
        "normal": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAsElEQVQokXWNUW4FMQwCGS7b4/ZGph+2k129VymKAA2Y/P6kklJVWqRSK1KpFcPkbZvMA4tua+EaoeRjJw97unnMZvPLqBa49RVruztkZU+/k5q10beSJtvqq01UIVotEiWUlM5Fi4h51zpwcxyhI3BAcrAgWJuLDufF6GHlf4Qt4GVNd22wjDCNDdP8+x/s/GxlNCADyAf4sFt/JTa948eaZ+3k59y2NvzEvjI3MeYPUfEsdP/GMIoAAAAASUVORK5CYII=",
        "inverted": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAqklEQVQokXWM2w0DMRACYTtPtemCycf6ebpI1mrAgD9fSL9oAAokE94cXjIE8RqDRHD7OSoNl6MEnlIBjrWLs2+APK7IDEfbzypq+IEIlhR/gIi4u80LxJSYSDG0byLR4AZhsFrKZvuSTW2Qja0StsqyVJ583D/Stqpauiw/ecDpdMUD9j3AI1my5eru+Brdmtz+uVPecoXXyMxc3Tpmy6P42Fmx9qv9q/IDYtw/QqfIVtUAAAAASUVORK5CYII=",
    },
    "berlin": {
        "normal": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAwElEQVQokW2Q0Q3EIAxDbbP/CjfDLYh9Hwm09Iqq6OXFRBX8fGPEiJN5gUvOxMhE3OCOZfOtZrNn7Nhe0DxtO46n00N7JjvYO2zHxl16Jo6P9Thke2TBurWniM+Lvn7f3knsnWVutTZgcZsYDmLGSOoVyyBBwhgIY66WqyVC5AJEABEyBNhcAHEZQEB5VYwPoPaU98rNIkkIFCmCLDg/aTRQlMRBSVQXShpLXOfRStI45TiT4230Jv9gNDz86/Qpf7dSTmRawDOQAAAAAElFTkSuQmCC",
        "inverted": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAvElEQVQokX2QUQ7DMAhDbXP/o+yIsfdRaNqtW1Shh3mhUpjXy7a9bC8v91n/w9/TR7DzFB4cP/kfpu9mt+ukzG9ytnGyEttOPr4kDpwYSQMSGMiNYSCAg6DzADe4aAFH7vxIAiQM6HYYMLwAFTAU2C2mBQkKIii0oCNhw64c5ndVtSBxQ0FiO0X1Bqou5jizYU9V14tjFmfDmEVJErlDqUhpWBRV6kFJ0kXd63BuYeG7srmBAqufqR2hNYFvAulCW3Q7HqMAAAAASUVORK5CYII=",
    },
    "lajolla": {
        "normal": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAArElEQVQokXWRUY5EIQgEq5pTzP0vuh+Co+/tJMY01YgKfj6ogrQAFVmw9QW9LJ/WkaNC8N8wAxfJT60SjIrxEFfIDjOud3i4bFgaePGLVPO9MznrnWxLiUbcbvcIQ6ZB04juhYEDdtE9g6zxLCEPuIb3zV93D7+TOcZwHX+m+So7K8ctd+X+dn/EGzqPl57o6k6mRyHRkGD87kVKQwrLFMYUFpYWv3SvjM6b/AE3AwLH88Pa5AAAAABJRU5ErkJggg==",
        "inverted": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAqklEQVQokW2RWw7DMAzDuPsfbWeKuI84TrMGKAqZVl7yx3xhYHBoCbwQiw9y12ZgTPOQyYOZfxINRURNUKJKwAmnwIggRKd4QjEsrcIuKX9a+1pC70kOz8WWxynHtq9r5IBuXTdsMt/acH7R1aIScgawQpJgKq0S0fBsOR56df0jo8jJD6hn2WZPc5cusxJq+RrpRe/Z1rtXxq+yRrEFlZk94d3ir7XhnuEPk2frRoSfIrIAAAAASUVORK5CYII=",
    },
    "Rainbow Desaturated": {
        "normal": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAf0lEQVQokb2MSwrDMAxExxkV52a5/7oncSxZXfSD6rgkIVAQjydpmLQs99asNR3SfXzfpbuNCwnkG7Kc43wy/6QkaIEVWHnJT67HYl3bGl+SLAsy8eEc/Aq3PQJAAQXqP0Qb1KC2I/VAppO6uTiSTBPfIyTjGpzk1xq/ZBcevh6R9SSE4xjKlAAAAABJRU5ErkJggg==",
        "inverted": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAgUlEQVQokb2MwRLCIAxENyHI1/X/r35GM02CB2WYYq3Ug5c3L7sLdF8Wj/AIi/AId9+d36rX2aqDdl8RqiRIgjCekpvItOTpMTIggPxDDFCDeufqY/Ib3/+xmiAFqTTeuvfwlMOrs1mBVegGtWtcL+7VoBs5mBOzDCQ6CGdI9LF9AEoJAHMyopBpAAAAAElFTkSuQmCC",
    },
    "Yellow - Gray - Blue": {
        "normal": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAABAklEQVQokW2NTVJAMQiDSQKMju49lfc/iW5eCy76fqojw6RfSUrx+f6RVtGVVtmV6MTSTnZ4pzq9wy3ULgs/NdTh5mq5yZeaByKXQgE6FGCADnNgtQinOSGYC05I5oTL3OFu7g/r1oAHFOZhSihtNQNKYxgTDGMYAwyD26MBhCGBMEuzbEuz/P56m/MY4xjjmPMYY4xxzDHGGHOMueqG31WzrsDGt7llatacVbOqLl51Q3VVdfd1WbDu/SfwT6yfJdukz0z3pc/WqZerX40OkiRBnOfOeoaPJWq9OV1Sp6vTuIdXcJtfrJu18C9fg32HpP0RpV9hEttXD0vUGUaIIYTzB37sE9oBp0aLAAAAAElFTkSuQmCC",
        "inverted": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAABCElEQVQokW2OQW7FIAxEbUM27f1P2Cu0amXPeLqA0OirFhoe9iPEPz6rqEIXVWxSZLOb7FVkd+uF15TkDTvJ1T53+ZSP+nLt1h+vHvM+PPt6NHWmbDVb+19P6mjPkTZYY/B78GetiAj3iPCIcPfwnbHPsfkoN9z9LbkfZ1v/aX9fG/c+Fo8Ym8dYvOrA2P354H9rzgNzzjHnnNecc4xrzmvOa4zr7f3LLN3SLM1SKtPKsi4TVqrLuqxLXdZpXWJalzGNKaYxDSWWUEIZIWAnINDw5BYptIGiDC202IIEGdRQl1hqiKVKoVTrBRhhhBMGesGKXnDQdtILlvCkFzzbU2tFytMjLcrjF8c3wYUVNTbdAAAAAElFTkSuQmCC",
    },
    "Blue Orange (divergent)": {
        "normal": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAABLUlEQVQokWXQUW5bMQxE0TuknmtnAVlV97+SFmn8RE4+JNsNAhCDwxEECNK7fkuHOKRjgRfCCiI3lOWY5HROZys9glwZGskIjQUpVykylEGK0M4n9souQ47vTcopQs7lIPHzbsrJwo+BIacYIvEQKQ0p0YaUaEgh5U6CkbqF34JbshG6JbfQNXSVD/lQX/4HPqQh1ide0JW4Er/QQQw00CCSSEUSiRYuyjeNq9T1x/0X38WJT/wPPvAHnmbiEyY+3Sc+6XO7d+Oe9Ome7pMq99xT09XuclVXu5puV7vb7dda7bIfR7Rd7TZtyi4oU7hM491s7LXtwo/cp22vi23Xc/B8uddjy13uSZd7PaHczQOuotpVfqTK+paOaSYqa1oLBc884Y7v+BPf7c+HvwARUEha3E6gQgAAAABJRU5ErkJggg==",
        "inverted": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAABMElEQVQokWWQQW5cMQxDHyU7bdCuepLe/2CZ6XxL7MKeSYoCBPFICQZk/ebXG/qGjuvwG5qQcn7xgYf8BFKdcob/8VSGnk6EIhVBBE9QpGIQuUGRUqKUUhpfOKUQO4aUIlFITydey5zphjiRlBJSxH4hCClCGYpQShnK4DRntGPsM2JfMhRHZCqmYrBdUzGJqZhoEvM0mjDQFAMN9A7v6DuaZqI3xY/In3f7w+vhKrrchZ/Qi1544Yv+g+/0nX7gy77MMpd9oYd1OS5/wt26t2/tW3FrfzS31q3YsMo0Lrt9fNmFa4NdeJmylilYVpnN5f+lV99WmULVlPXZmN6CtvoVT3MWXmvP6GqqvUy1q1n2Kq9mtVdRrdVUaXW4hmqoBpVqXHLjpg+c3/K1wb7M9RffkB57mVnKkwAAAABJRU5ErkJggg==",
    },
    "Cool to Warm (Extended)": {
        "normal": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAA7UlEQVQokW2QS25FIQxDbYdx99f9j7qFitgd8Hn3tQVknZiQKBD4pCiR5zyZIvgvi0WKWLzM0lLtWx2HlLThpP3pJYH87b8SSJV2HUkSxdVIN6y//m59/bWqpDq7JFWVRqnEKg2pSgfOKK/5thY5tOGld+LzMXtoYpBFDmKQgyhykB/fX0gjvhpPdMMb0hOe6cM9s2DOdO9wTrTjTjfsdKcNd9rHN7rTvn66M1fmgbkT4o5tL/Zid7vdbXc/dJ3Ydsdtn9fZTxPbSXaZPPxzuyBwYCCBQ2cBAjoM+M4MaMhgIJOGHg6uvgFx1WSAH/EtJrKFrcGEAAAAAElFTkSuQmCC",
        "inverted": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAA+ElEQVQokWWQQVbEMAxDLSm8suYw3IX77zkAjCUWSdrO0PSpX2qcxMHXxycTVDFhBalTWUE9wbZGhWUmKF8JctN6YhRRRIBi1UoIEiBJgNh2AkEQ6+/OSYEENYHUZEqkdFNSWpUktFehIELEECQMQndg7QklQQRV065cRUJa+RiQSgNSjQGddpQEjeJmjqImhG/NwzzMo3m8/37/Fuf7Ey0oduCkEyd2Tm6nnc6ljw2+aSeeeedhd7vbC5xHu9t2d9u9R/t84sxvprPTufI+JzzlOUvayTx67FdIYlf+51cDM/TV87nRvU8ndq3CfU1O5Vrwzi972fkDNhKObqnUqaEAAAAASUVORK5CYII=",
    },
    "Black-Body Radiation": {
        "normal": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAAKElEQVQokWNkYGBgYmBgZmBggqFBxR5wB2BlD7wLhl6QsTIysg42EgCSowL6mmk4BgAAAABJRU5ErkJggg==",
        "inverted": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAAALElEQVQokWP8//8/A8Pv//9/D0KS4R8Dw18Ghn8wNKjYA+4AbOyBtn+IBRgAiJwwE57a+5gAAAAASUVORK5CYII=",
    },
    "Blue - Green - Orange": {
        "normal": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAABHElEQVQokWWSXZLcMBCCG9r25P5nyyFyhR0JyINkz26ioqgP9KKfxu8/76/p98yXPJQpT2UowxkfqA3OdIZraIGnMu0pD2fKczV63HJky7E325YsSVLk+CNnrw1WpLISVxy77MjerFhlwYaFCCVE8IRVEWJEyERmZSKqR1CgoqpHjndxGA4cZDsTppiwiilWiKLDWZyFAK4KkP84haBSCFlAEQUUWEQRaIBkA9+5Hye5I5tokOSze4D3Fps8PuoFvdX9jU/2q49ffb76ePX56uPq6zquq8/ruM4+mTDpKu57hwmS2OWsNy+v6LKzyvs7Ipc2bNmRfpaJbGVBnH8bxbK1xkOWpUX2Atm6Cz1TlJ/RnzjvMZv27b5PsvQX57DrjJTIH+EAAAAASUVORK5CYII=",
        "inverted": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAP8AAAABCAIAAACe8u/0AAABC0lEQVQokWWSUW7lMAwDxaHTHngv3/cSi/thp013A4IY0YJjw9IfSuYhYbA9ttu28QCwt38DYOt3aVbDghUZjHcHGFn37zaI/5L7VGVki+c5V4hMgViu4rvUWiokiNQPzaoF5zzf1/u9/f2a12uer3l9zfM1r7Pn7Dm7b22+tuYNd0N6dl9ZnNndO8xa6uTuzPJenjy5U+lKqlNJdVdFKVWU3F5K+Ierh3pUo071uuR91ZYiheWE6kPXR82j2oorLm1FLo1sOaLk4DAip5xdUli4sAA9nkNIFJbXiwrtD0nwI68Z+zUdrBkBo2GGGdZ2GOZYOQzrgIEO66AGOpasw3XDTtYmh/VpPob+Aq7u3qtK6nECAAAAAElFTkSuQmCC",
    },
}

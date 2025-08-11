#!/usr/bin/env python3
"""
Standalone script to generate colorbar cache for QuickView.
This script generates base64-encoded PNG images for all supported colormaps
in both normal and inverted forms.

Usage:
    python generate_colorbar_cache.py > colorbar_cache_output.py
"""

import os
import sys
import xml.etree.ElementTree as ET

# Add quickview to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from paraview.simple import GetColorTransferFunction, ImportPresets, GetLookupTableNames
from quickview.utilities import build_colorbar_image

# Define the colormaps to cache (matching interface.py)
noncvd = [
    {
        "text": "Rainbow Desat.",
        "value": "Rainbow Desaturated",
    },
    {
        "text": "Cool to Warm",
        "value": "Cool to Warm",
    },
    {
        "text": "Jet",
        "value": "Jet",
    },
    {
        "text": "Yellow-Gray-Blue",
        "value": "Yellow - Gray - Blue",
    },
]

# CVD-friendly colormaps will be loaded from XML files
cvd = []

# Load CVD presets from XML files
try:
    existing = GetLookupTableNames()
    presdir = os.path.join(os.path.dirname(__file__), "quickview", "presets")
    presets = os.listdir(path=presdir)
    for preset in presets:
        prespath = os.path.abspath(os.path.join(presdir, preset))
        if os.path.isfile(prespath):
            name = ET.parse(prespath).getroot()[0].attrib["name"]
            if name not in existing:
                ImportPresets(prespath)
            cvd.append({"text": name.title(), "value": name})
except Exception as e:
    print(f"# Error loading presets: {e}", file=sys.stderr)

# Combine all colormaps
all_colormaps = cvd + noncvd

print("# Auto-generated colorbar cache")
print("# Generated using generate_colorbar_cache.py")
print()
print("COLORBAR_CACHE = {")

for colormap in all_colormaps:
    colormap_name = colormap["value"]
    print(f'    "{colormap_name}": {{')

    try:
        # Get the color transfer function
        lut = GetColorTransferFunction("dummy_var")
        lut.ApplyPreset(colormap_name, True)

        # Generate normal colorbar
        normal_image = build_colorbar_image(lut, log_scale=False, invert=False)
        print(f'        "normal": "{normal_image}",')

        # Invert the transfer function
        lut.InvertTransferFunction()

        # Generate inverted colorbar
        inverted_image = build_colorbar_image(lut, log_scale=False, invert=False)
        print(f'        "inverted": "{inverted_image}",')

        # Reset for next iteration
        lut.InvertTransferFunction()  # Revert back to normal

    except Exception as e:
        print(f"# Error processing {colormap_name}: {e}", file=sys.stderr)
        print('        "normal": "",')
        print('        "inverted": "",')

    print("    },")

print("}")

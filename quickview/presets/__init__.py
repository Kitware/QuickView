from pathlib import Path

from paraview import simple

ALL_PRESETS = set(simple.GetLookupTableNames())
CUSTOM_PRESETS = set()

# Import any missing preset
for preset_file in Path(__file__).parent.glob("*_PARAVIEW.xml"):
    preset_name = preset_file.name[:-13]  # remove _PARAVIEW.xml
    if preset_name not in ALL_PRESETS:
        try:
            simple.ImportPresets(str(preset_file.resolve()))
            ALL_PRESETS.add(preset_name)
            CUSTOM_PRESETS.add(preset_name)
        except Exception as e:
            print("Error importing color preset to ParaView", e)

PARAVIEW_PRESETS = ALL_PRESETS - CUSTOM_PRESETS

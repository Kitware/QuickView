from pathlib import Path

from paraview import simple

ALL_PRESETS = set(simple.GetLookupTableNames())
COLOR_BLIND_SAFE = set()

# Import any missing preset
for preset_file in Path(__file__).parent.glob("*_PARAVIEW.xml"):
    preset_name = preset_file.name[:-13]  # remove _PARAVIEW.xml
    COLOR_BLIND_SAFE.add(preset_name)
    if preset_name not in ALL_PRESETS:
        ALL_PRESETS.add(preset_name)
        try:
            simple.ImportPresets(str(preset_file.resolve()))
        except Exception as e:
            print("Error importing color preset to ParaView", e)


PARAVIEW_PRESETS = ALL_PRESETS - COLOR_BLIND_SAFE

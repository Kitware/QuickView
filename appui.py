from trame.widgets import html,vuetify, vtk, trame

def ui_card(title, ui_name):
    with vuetify.VCard(v_show=f"active_ui == '{ui_name}'"):
        vuetify.VCardTitle(
            title,
            classes="grey lighten-1 py-1 grey--text text--darken-3",
            style="user-select: none; cursor: pointer",
            hide_details=True,
            dense=True,
        )
        content = vuetify.VCardText(classes="py-2")
    return content

class LookupTable:
    Rainbow = 0
    Inverted_Rainbow = 1
    Greyscale = 2
    Inverted_Greyscale = 3

def properties2D():
    with ui_card(title="2D Vars", ui_name="prop2D"):
        with vuetify.VRow(classes="pt-2", dense=True):
            with vuetify.VCol(cols="6"):
                vuetify.VSelect(
                    # Color By
                    style="max-height: 400px",
                    label="Color By",
                    v_model=("colorby2D", None),
                    items=("color2D", []),
                    hide_details=True,
                    dense=True,
                    outlined=True,
                    classes="pt-1",
                )
            with vuetify.VCol(cols="6"):
                vuetify.VSelect(
                    v_model=("colormap2D", "Rainbow"),
                    items=(
                        "colormaps",
                        ["Rainbow", "Inv Rainbow", "Greyscale", "Inv Greyscale"],
                    ),
                    # Color Map
                )

def properties3Dm():
    with ui_card(title="3D Vars", ui_name="prop3D"):
        with vuetify.VRow(classes="pt-2", dense=True):
            with vuetify.VCol(cols="6"):
                vuetify.VSelect(
                    # Color By
                    style="max-height: 400px",
                    label="Color By",
                    v_model=("colorby3D", None),
                    items=("color3D", []),
                    hide_details=True,
                    dense=True,
                    outlined=True,
                    classes="pt-1",
                )
            with vuetify.VCol(cols="6"):
                vuetify.VSelect(
                    # Color Map
                    label="Colormap",
                    v_model=("colormap3D", "Rainbow"),
                    items=(
                        "colormaps",
                        ["Rainbow", "Inv Rainbow", "Greyscale", "Inv Greyscale"],
                    ),
                )

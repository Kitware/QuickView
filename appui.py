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

def properties2D():
    with ui_card(title="Mesh", ui_name="mesh"):
        vuetify.VSelect(
            # Representation
        )
        with vuetify.VRow(classes="pt-2", dense=True):
            with vuetify.VCol(cols="6"):
                vuetify.VSelect(
                    # Color By
                )
            with vuetify.VCol(cols="6"):
                vuetify.VSelect(
                    # Color Map
                )
        vuetify.VSlider(
            # Opacity
        )

def properties3Dm():
    with ui_card(title="Contour", ui_name="contour"):
        vuetify.VSelect(
            # Contour By
        )
        vuetify.VSlider(
            # Contour Value
        )
        vuetify.VSelect(
            # Representation
        )
        with vuetify.VRow(classes="pt-2", dense=True):
            with vuetify.VCol(cols="6"):
                vuetify.VSelect(
                    # Color By
                )
            with vuetify.VCol(cols="6"):
                vuetify.VSelect(
                    # Color Map
                )
        vuetify.VSlider(
            # Opacity
        )

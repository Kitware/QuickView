from trame.widgets import vuetify

class UICard(vuetify.VCard):
    def __init__(self, title, varname):
        super().__init__(
            v_show=f"{varname} == true"
        )
        with self:
            vuetify.VCardTitle(
                title,
                classes="lighten-1 py-1 grey--text text--darken-3",
                #style="user-select: none; cursor: pointer",
                hide_details=True,
                dense=True,
            )
            self.content = vuetify.VCardText(classes="py-2")

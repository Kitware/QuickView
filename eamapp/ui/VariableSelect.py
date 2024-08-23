from trame.widgets import vuetify

class VariableSelect(vuetify.VContainer):
    def __init__(self, variables, state):
        super().__init__(
            fluid=True, 
            style="max-height: 200px",
            classes="overflow-y-auto"
        )
        with self:
            with vuetify.VListItemGroup(dense=True):
                vuetify.VCheckbox(
                    v_for=f"v, i in {variables}",
                    key="i",
                    label=(f"{variables}[i]",),
                    v_model=(f"{state}[i]",),
                    change=f"flushState('{state}')",
                    style="max-height: 20px",
                    dense=True
                )
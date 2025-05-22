from trame.decorators import TrameApp, change
from trame.widgets import html, vuetify2 as v2

from quickview.ui.collapsible import CollapsableSection

style = dict(density="compact", hide_details=True)


class SelectionList(v2.VContainer):
    def __init__(self, variables, state, update=None):
        super().__init__(
            fluid=True, style="max-height: 200px", classes="overflow-y-auto py-0"
        )
        with self:
            with v2.VListItemGroup(dense=True, **style):
                v2.VCheckbox(
                    v_for=f"v, i in {variables}",
                    key="i",
                    label=(f"{variables}[i]",),
                    v_model=(f"{state}[i]",),
                    change=(update, "[i, $event]"),
                    style="max-height: 20px",
                    dense=True,
                )


@TrameApp()
class VariableSelection(CollapsableSection):
    def __init__(
        self,
        title=None,
        panel_name=None,
        var_list=None,
        var_list_state=None,
        on_search=None,
        on_clear=None,
        on_update=None,
    ):
        super().__init__(title=title, var_name=panel_name)
        with self.content:
            with v2.VRow(classes="px-5 pt-2"):
                with v2.VCol(cols=9):
                    v2.VTextField(
                        prepend_inner_icon="mdi-magnify",
                        label="variable search",
                        change=(on_search, "[$event]"),
                        classes="py-0",
                        **style,
                    )
                with v2.VCol(cols=3):
                    with v2.VTooltip(bottom=True):
                        with html.Template(v_slot_activator="{ on, attrs }"):
                            with v2.VBtn(
                                icon=True,
                                click=(on_clear),
                                color="primary",
                                v_bind="attrs",
                                v_on="on",
                                **style,
                            ):
                                v2.VIcon("mdi-sim-off")
                        html.Span("Clear Selection")
                SelectionList(var_list, var_list_state, on_update)

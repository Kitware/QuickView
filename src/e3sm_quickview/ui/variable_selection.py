from trame.decorators import TrameApp
from trame.widgets import html, vuetify2 as v2

from e3sm_quickview.ui.collapsible import CollapsableSection

style = dict(dense=True, hide_details=True)


class SelectionList(v2.VContainer):
    def __init__(self, variables, state, update=None):
        super().__init__(
            fluid=True,
            style="max-height: 180px; background: #f5f5f5; border-radius: 4px;",
            classes="overflow-y-auto pa-1 mt-1",
        )
        with self:
            with v2.VListItemGroup(**style):
                with v2.VHover(v_for=f"v, i in {variables}", key="i"):
                    with html.Template(v_slot_default="{ hover }"):
                        with v2.VCard(
                            flat=True,
                            color=("hover ? 'grey lighten-4' : 'transparent'",),
                            classes="px-1 mb-0",
                            style="transition: all 0.2s;",
                        ):
                            v2.VCheckbox(
                                label=(f"{variables}[i]",),
                                v_model=(f"{state}[i]",),
                                change=(update, "[i, $event]"),
                                color="primary",
                                classes="ma-0 pa-0",
                                style="height: 24px;",
                                dense=True,
                                hide_details=True,
                            )


@TrameApp()
class VariableSelection(CollapsableSection):
    _next_id = 0

    @classmethod
    def next_id(cls):
        """Get the next unique ID for the scalar bar."""
        cls._next_id += 1
        return f"var_select_{cls._next_id}"

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

        ns = self.next_id()
        self.__search_var = f"{ns}_search"

        with self.content:
            # Search and controls section
            with v2.VCard(flat=True, elevation=0, classes="pa-2 mb-1"):
                with v2.VRow(classes="align-center", no_gutters=True):
                    with v2.VCol(cols=9, classes="pr-1"):
                        v2.VTextField(
                            v_model=(self.__search_var, ""),
                            prepend_inner_icon="mdi-magnify",
                            label="Search variables",
                            placeholder="Type to filter...",
                            change=(on_search, "[$event]"),
                            clearable=True,
                            outlined=True,
                            dense=True,
                            hide_details=True,
                            classes="elevation-0",
                        )
                    with v2.VCol(cols=3):
                        with v2.VTooltip(bottom=True):
                            with html.Template(v_slot_activator="{ on, attrs }"):
                                with v2.VBtn(
                                    click=(on_clear, f"['{self.__search_var}']"),
                                    depressed=True,
                                    small=True,
                                    v_bind="attrs",
                                    v_on="on",
                                    classes="elevation-1",
                                    style="width: 100%;",
                                ):
                                    v2.VIcon(
                                        "mdi-close-box-multiple", left=True, small=True
                                    )
                                    html.Span("Clear", classes="text-caption")
                            html.Span("Clear all selections")

            # Variables list
            with v2.VCard(flat=True, elevation=0, classes="px-2"):
                html.Div(
                    "Variables",
                    classes="text-caption font-weight-medium mb-0",
                    style="color: #616161;",
                )
                SelectionList(var_list, var_list_state, on_update)

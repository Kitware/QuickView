from trame.decorators import change
from trame.widgets import html, vuetify3 as v3

from e3sm_quickview import __version__ as quickview_version
from e3sm_quickview.components import css, tools
from e3sm_quickview.utils import js, constants


class Tools(v3.VNavigationDrawer):
    def __init__(self, reset_camera=None):
        super().__init__(
            permanent=True,
            rail=("compact_drawer", True),
            width=220,
            style="transform: none;",
        )

        with self:
            with html.Div(style=css.NAV_BAR_TOP):
                with v3.VList(
                    density="compact",
                    nav=True,
                    select_strategy="independent",
                    v_model_selected=("active_tools", ["load-data"]),
                ):
                    tools.AppLogo()
                    tools.OpenFile()
                    tools.FieldSelection()
                    tools.MapProjection()
                    tools.ResetCamera(click=reset_camera)

                    v3.VDivider(classes="my-1")  # ---------------------

                    tools.LayoutManagement()
                    tools.Cropping()
                    tools.DataSelection()
                    tools.Animation()

                    v3.VDivider(classes="my-1")  # ---------------------

                    tools.StateImportExport()

                    # dev add-on ui reload
                    if self.server.hot_reload:
                        tools.ActionButton(
                            compact="compact_drawer",
                            title="Refresh UI",
                            icon="mdi-database-refresh-outline",
                            click=self.ctrl.on_server_reload,
                        )

            with html.Div(style=css.NAV_BAR_BOTTOM):
                v3.VDivider()
                v3.VLabel(
                    f"{quickview_version}",
                    classes="text-center text-caption d-block text-wrap",
                )


class FieldSelection(v3.VNavigationDrawer):
    def __init__(self, load_variables=None):
        super().__init__(
            model_value=(js.is_active("select-fields"),),
            width=500,
            permanent=True,
            style=(f"{js.is_active('select-fields')} ? 'transform: none;' : ''",),
        )

        with self:
            with html.Div(style="position:fixed;top:0;width: 500px;"):
                with v3.VCardActions(key="variables_selected.length"):
                    for name, color in [
                        ("surfaces", "success"),
                        ("interfaces", "info"),
                        ("midpoints", "warning"),
                    ]:
                        v3.VChip(
                            js.var_title(name),
                            color=color,
                            v_show=js.var_count(name),
                            size="small",
                            closable=True,
                            click_close=js.var_remove(name),
                        )

                    v3.VSpacer()
                    v3.VBtn(
                        classes="text-none",
                        color="primary",
                        prepend_icon="mdi-database",
                        text=(
                            "`Load ${variables_selected.length} variable${variables_selected.length > 1 ? 's' :''}`",
                        ),
                        variant="flat",
                        disabled=(
                            "variables_selected.length === 0 || variables_loaded",
                        ),
                        click=load_variables,
                    )

                v3.VTextField(
                    v_model=("variables_filter", ""),
                    hide_details=True,
                    color="primary",
                    placeholder="Filter",
                    density="compact",
                    variant="outlined",
                    classes="mx-2",
                    prepend_inner_icon="mdi-magnify",
                    clearable=True,
                )
                with html.Div(style="margin:1px;"):
                    v3.VDataTable(
                        v_model=("variables_selected", []),
                        show_select=True,
                        item_value="id",
                        density="compact",
                        fixed_header=True,
                        headers=(
                            "variables_headers",
                            constants.VAR_HEADERS,
                        ),
                        items=("variables_listing", []),
                        height="calc(100vh - 6rem)",
                        style="user-select: none; cursor: pointer;",
                        hover=True,
                        search=("variables_filter", ""),
                        items_per_page=-1,
                        hide_default_footer=True,
                    )

    @change("variables_selected")
    def _on_dirty_variable_selection(self, **_):
        self.state.variables_loaded = False

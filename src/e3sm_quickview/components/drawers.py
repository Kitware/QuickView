from trame.decorators import change
from trame.widgets import client, html
from trame.widgets import vuetify3 as v3

from e3sm_quickview import __version__ as quickview_version
from e3sm_quickview.components import css, tools
from e3sm_quickview.utils import constants, js


class Tools(v3.VNavigationDrawer):
    def __init__(self, reset_camera=None):
        super().__init__(
            permanent=True,
            rail=("compact_drawer", True),
            width=253,
            style="transform: none;",
        )

        with self:
            with html.Div(style=css.NAV_BAR_TOP):
                with v3.VList(
                    density="compact",
                    nav=True,
                    select_strategy="independent",
                    v_model_selected=(
                        "active_tools",
                        ["load-data", "select-slice-time", "animation-controls"],
                    ),
                ):
                    tools.AppLogo()
                    tools.ResetCamera(click=reset_camera)

                    v3.VDivider(classes="my-1")  # ---------------------

                    tools.StateImportExport()
                    tools.OpenFile()

                    v3.VDivider(classes="my-1")  # ---------------------

                    tools.FieldSelection()
                    tools.DataSelection()
                    tools.Animation()

                    v3.VDivider(classes="my-1")  # ---------------------

                    tools.LayoutManagement()
                    tools.MapProjection()
                    tools.Cropping()

                    # dev add-on ui reload
                    if self.server.hot_reload:
                        v3.VDivider(classes="my-1")  # ---------------------
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

        self.state.setdefault("loading_time", 0)

        with self:
            with html.Div(
                style="position:fixed;top:0;width: 500px;height:100vh;",
                classes="d-flex flex-column",
            ):
                with v3.VCardActions(classes="pb-0", style="min-height: 0;"):
                    v3.VBtn(
                        classes="text-none",
                        color="primary",
                        prepend_icon="mdi-database",
                        text=(
                            "`Load ${variables_selected.length} variable${variables_selected.length > 1 ? 's' :''} ${ loading_time ? ('(' + loading_time.toFixed(1) + ' s)') : ''}`",
                        ),
                        variant="flat",
                        disabled=(
                            "variables_selected.length === 0 || variables_loaded || loading",
                        ),
                        loading=("loading", False),
                        click=load_variables,
                        block=True,
                    )
                with v3.VCardActions(
                    key="variables_selected.length",
                    classes="flex-wrap py-1 flex-0-0 ga-1",
                    style="overflow-y: auto; max-height: 40vh; min-height: 64px;",
                ):
                    with v3.VChip(
                        "{{ vtype.name }}",
                        v_for="(vtype, idx) in variable_types",
                        key="idx",
                        color=("vtype.color",),
                        v_show=(
                            "variables_selected.filter(id => variables_listing.find(v => v.id === id)?.type === vtype.name).length",
                        ),
                        size="small",
                        closable=True,
                        click_close=(
                            "variables_selected = variables_selected.filter(id => variables_listing.find(v => v.id === id)?.type !== vtype.name)"
                        ),
                        classes="mx-1",
                    ):
                        with v3.Template(v_slot_prepend=True):
                            v3.VAvatar(
                                "{{ variables_selected.filter(id => variables_listing.find(v => v.id === id)?.type === vtype.name).length }}",
                                border=True,
                                classes="mr-1 ml-n1",
                                variant="plain",
                            )

                v3.VTextField(
                    v_model=("variables_filter", ""),
                    hide_details=True,
                    color="primary",
                    placeholder="Filter",
                    density="compact",
                    variant="outlined",
                    classes="mx-2 flex-0-0",
                    prepend_inner_icon="mdi-magnify",
                    clearable=True,
                )
                with html.Div(style="margin:1px;padding:1px;", classes="flex-fill"):
                    with client.SizeObserver("var_selection_size"):
                        with v3.VDataTable(
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
                            height=["var_selection_size?.size.height || '30vh'"],
                            style="user-select: none; cursor: pointer;top:0;left:0;",
                            classes="position-absolute show-scrollbar",
                            hover=True,
                            search=("variables_filter", ""),
                            items_per_page=-1,
                            hide_default_footer=True,
                        ):
                            with v3.Template(raw_attrs=['#item.name="{ value }"']):
                                html.Div(
                                    "{{ value }}",
                                    classes="text-break",
                                    title=["`${value}`"],
                                )
                            with v3.Template(raw_attrs=['#item.type="{ value }"']):
                                html.Div(
                                    "{{ value }}",
                                    classes="text-break text-caption",
                                )

    @change("variables_selected")
    def _on_dirty_variable_selection(self, **_):
        self.state.variables_loaded = False

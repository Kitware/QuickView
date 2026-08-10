from trame.decorators import controller
from trame.widgets import client, colormaps, dataclass, html
from trame.widgets import vuetify3 as v3

from e3sm_quickview.components import css
from e3sm_quickview.utils import js


class FileOpen(html.Div):
    def __init__(self, file_browser):
        super().__init__(style=css.FULLSCREEN_OVERLAY)
        with self:
            with v3.VDialog(
                model_value=(js.is_active("load-data"),),
                **css.DIALOG_STYLES,
                v_on_keyup_enter=file_browser.on_enter,
            ):
                file_browser.ui()


class ColorMapEditor(html.Div):
    def __init__(self):
        super().__init__(style=css.FULLSCREEN_OVERLAY)
        self.state.setdefault("color_map_editor_field_name", None)
        self.state.setdefault("color_map_editor_field_label", None)
        with self:
            with (
                v3.VDialog(
                    model_value=("color_map_editor", None),
                    contained=True,
                    persistent=True,
                ),
                dataclass.Provider(
                    name="colormap", instance=("color_map_editor", None)
                ),
            ):
                with v3.VCard(
                    rounded="lg",
                    style="--tcmap-editor-size: 100%;--tcmap-editor-search-width: 250px;width: 100%; height: 100%;",
                ):
                    with v3.VCardItem(
                        density="compact",
                        title=(
                            "`Adjust color map for ${ color_map_editor_field_label }`",
                        ),
                    ):
                        with v3.Template(v_slot_append=True):
                            v3.VBtn(
                                icon="mdi-close",
                                click=self.edit_lookup_table,
                                variant="plain",
                                density="compact",
                            )
                    v3.VDivider()
                    with v3.VRow(
                        classes="pa-0 ma-0",
                        style="height: calc(100vh - 115px);",
                    ):
                        with v3.VCol(classes="pa-0 border-e-thin h-100"):
                            colormaps.ColorMapEditor(
                                name="colormap",
                                show_close_button=False,
                                variant="flat",
                                style="height: 100%;",
                            )
                        with v3.VCol(align_self="center", classes="pa-2 "):
                            client.ServerTemplate(
                                name=("`view_${color_map_editor_field_name}`",)
                            )

    @controller.set("edit_lookup_table")
    def edit_lookup_table(self, colormap_id=None, field_name=None, field_label=None):
        self.state.color_map_editor = colormap_id
        self.state.color_map_editor_field_name = field_name
        self.state.color_map_editor_field_label = field_label or field_name


class StateDownload(html.Div):
    def __init__(self):
        super().__init__(style=css.FULLSCREEN_OVERLAY)
        with self:
            with v3.VDialog(
                model_value=("show_export_dialog", False),
                **css.DIALOG_STYLES,
                v_on_keyup_enter="utils.quickview.saveState(download_name)",
            ):
                with v3.VCard(title="Save QuickView State file", rounded="lg"):
                    v3.VDivider()
                    with v3.VCardText():
                        with v3.VRow(dense=True):
                            with v3.VCol(cols=12):
                                html.Label(
                                    "Filename",
                                    classes="text-subtitle-1 font-weight-medium mb-2 d-block",
                                )
                                v3.VTextField(
                                    v_model=(
                                        "download_name",
                                        "quickview-state.json",
                                    ),
                                    density="comfortable",
                                    placeholder="Enter a filename (not a path)",
                                    hint="Name only — save location is chosen via dialog or defaults to ~/Downloads",
                                    persistent_hint=True,
                                    variant="outlined",
                                )
                        with v3.VRow(dense=True):
                            with v3.VCol(cols=12):
                                html.Label(
                                    "Comments",
                                    classes="text-subtitle-1 font-weight-medium mb-2 d-block",
                                )
                                v3.VTextarea(
                                    v_model=("export_comment", ""),
                                    density="comfortable",
                                    placeholder="Remind yourself what that state captures",
                                    rows="4",
                                    variant="outlined",
                                )
                    with v3.VCardActions():
                        v3.VSpacer()
                        v3.VBtn(
                            text="Cancel",
                            click="show_export_dialog=false",
                            classes="text-none",
                            variant="flat",
                            color="surface",
                        )
                        v3.VBtn(
                            text="Save",
                            classes="text-none",
                            variant="flat",
                            color="primary",
                            click="utils.quickview.saveState(download_name)",
                        )

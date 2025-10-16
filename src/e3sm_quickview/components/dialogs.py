from trame.widgets import html, vuetify3 as v3

from e3sm_quickview.components import css
from e3sm_quickview.utils import js


class FileOpen(html.Div):
    def __init__(self, file_browser):
        super().__init__(style=css.FULLSCREEN_OVERLAY)
        with self:
            with v3.VDialog(
                model_value=(js.is_active("load-data"),),
                **css.DIALOG_STYLES,
            ):
                file_browser.ui()


class StateDownload(html.Div):
    def __init__(self):
        super().__init__(style=css.FULLSCREEN_OVERLAY)
        with self:
            with v3.VDialog(
                model_value=("show_export_dialog", False),
                **css.DIALOG_STYLES,
            ):
                with v3.VCard(title="Download QuickView State file", rounded="lg"):
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
                                    placeholder="Enter the filename to download",
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
                            text="Download",
                            classes="text-none",
                            variant="flat",
                            color="primary",
                            click="show_export_dialog=false;utils.download(download_name, trigger('download_state'), 'application/json')",
                        )

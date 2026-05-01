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
                            click="""
                                show_export_dialog=false;
                                const fname = download_name.split('/').pop() || 'quickview-state.json';
                                if (window.showSaveFilePicker) {
                                    (async () => {
                                        try {
                                            const content = await trigger('download_state');
                                            const handle = await window.showSaveFilePicker({
                                                suggestedName: fname,
                                                types: [{
                                                    description: 'JSON State File',
                                                    accept: {'application/json': ['.json']},
                                                }],
                                            });
                                            const writable = await handle.createWritable();
                                            await writable.write({type: 'write', data: content});
                                            await writable.close();
                                        } catch(e) {
                                            if (e.name !== 'AbortError') console.error(e);
                                        }
                                    })();
                                } else {
                                    trigger('download_state').then((content) => {
                                        utils.download(fname, content, 'application/json');
                                    });
                                }
                            """,
                        )

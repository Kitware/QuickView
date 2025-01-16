from trame.widgets import html, vuetify as vuetify
from trame.app import get_server

server = get_server()


class FileSelect(vuetify.VCard):
    def __init__(
        self,
        display_var="export_config",
        exported_state_var="exported_state",
        export_completed="export_completed",
        state_save_file_var="state_save_file",
    ):
        super().__init__()
        with self:
            with vuetify.VCardText():
                vuetify.VCardTitle(
                    "Export Completed Successfully.",
                    v_show=(export_completed,),
                )
                with html.Div(
                    v_show=(f"!{export_completed}",),
                ):
                    vuetify.VCardTitle("Export File Select")
                    vuetify.VTextField(
                        v_model=(f"{state_save_file_var}",),
                        v_show=(f"{state_save_file_var} != false",),
                        label="Download Location",
                        prepend_icon="mdi-paperclip",
                        # FileSystem API is only available on some browsers:
                        # https://caniuse.com/native-filesystem-api
                        click="""
                            if ($event){
                                try {
                                    window.showSaveFilePicker({
                                        suggestedName: 'pan3d_state.json',
                                        types: [{
                                            accept: {
                                                'application/json': ['.json']
                                            }
                                        }]
                                    }).then((handle) => {
                                        handle.createWritable().then((writable) => {
                                            writable.write(JSON.stringify(%s, null, 4));
                                            writable.close();
                                        })
                                        %s = true;
                                    });
                                } catch {
                                    window.alert('Your browser does not support selecting a download location. Your download will be made to the default location, saved as pan3d_state.json.')
                                }
                            }
                        """
                        % (exported_state_var, export_completed),
                    )
                    '''
                    vuetify.VBtn(
                        v_show=(
                            "state_save_file === false",
                        ),
                        variant="tonal",
                        text="Download pan3d_state.json",
                        click=f"""
                            var content = JSON.stringify({exported_state_var}, null, 4);
                            var a = window.document.createElement('a');
                            a.href = 'data:application/json;charset=utf-8,'  + encodeURIComponent(content);
                            a.download = 'pan3d_state.json';
                            a.style.display = 'none';
                            window.document.body.appendChild(a);
                            a.click()
                            window.document.body.removeChild(a);
                            {export_complete_message_var} = 'Export complete.'
                        """,
                        style="width: 100%",
                    )
                    '''

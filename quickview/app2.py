import json

from pathlib import Path

from trame.app import TrameApp
from trame.ui.vuetify3 import VAppLayout
from trame.widgets import vuetify3 as v3, paraview as pvw, client

from quickview.pipeline import EAMVisSource
from quickview.assets import ASSETS


class EAMApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(server)

        # CLI
        cli = self.server.cli
        cli.add_argument(
            "-cf",
            "--conn",
            nargs="?",
            help="the nc file with connnectivity information",
        )
        cli.add_argument(
            "-df",
            "--data",
            help="the nc file with data/variables",
        )
        cli.add_argument(
            "-sf",
            "--state",
            nargs="?",
            help="state file to be loaded",
        )
        cli.add_argument(
            "-wd",
            "--workdir",
            default=str(Path.cwd().resolve()),
            help="working directory (to store session data)",
        )
        args, _ = cli.parse_known_args()

        # Data input
        self.source = EAMVisSource()
        self.app_state = {}
        if args.state is not None:
            self.app_state = json.loads(Path(args.state).read_text())
            self.source.Update(**{k: state[k] for k in ("data_file", "conn_file")})

        # GUI
        self._build_ui()

    def _build_ui(self, **_):
        with VAppLayout(self.server, fill_height=True) as self.ui:
            with v3.VLayout():
                with v3.VNavigationDrawer(permanent=True, rail=True):
                    with v3.VListItem(loading=True):
                        v3.VAvatar(image=ASSETS.icon)
                        v3.VProgressCircular(
                            color="primary",
                            indeterminate=True,
                            v_show="trame__busy",
                            style="position: absolute !important;left: 50%;top: 50%;transform: translate(-50%, -50%);",
                        )
                    with v3.VList(density="compact", nav=True, v_model=("active_drawer", "load-data")):
                        v3.VListItem(
                            prepend_icon="mdi-file-document-outline",
                            value="load-data",
                        )
                        v3.VListItem(
                            prepend_icon="mdi-database-check-outline",
                            value="select-fields",
                            disabled=True,
                        )
                        v3.VListItem(
                            prepend_icon="mdi-collage",
                            value="adjust-layout",
                            disabled=True,
                        )
                        v3.VListItem(
                            prepend_icon="mdi-compass-rose",
                            value="reset-camera",
                            disabled=True,
                        )
                        v3.VListItem(
                            prepend_icon="mdi-compass-rose",
                            value="reset-camera",
                            disabled=True,
                        )
                        v3.VListItem(
                            prepend_icon="mdi-cog",
                            value="settings",
                            disabled=True,
                        )
                        v3.VListItem(
                            prepend_icon="mdi-earth",
                            value="projection-sphere",
                            disabled=True,
                        )
                        v3.VListItem(
                            prepend_icon="mdi-earth-box",
                            value="projection-box",
                            disabled=True,
                        )
                        v3.VListItem(
                            prepend_icon="mdi-folder-arrow-left-right-outline",
                            value="import-export",
                            disabled=True,
                        )

                with v3.VMain(classes="bg-red"):
                    v3.VLabel("Hello")



def main():
    app = EAMApp()
    app.server.start()


if __name__ == "__main__":
    main()

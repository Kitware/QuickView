from trame.widgets import html
from trame.widgets import vuetify3 as v3


def create_size_menu(name, config):
    with v3.VBtn(
        icon=True,
        density="compact",
        variant="plain",
        classes="mx-1",
        size="small",
    ):
        v3.VIcon(
            "mdi-arrow-expand",
            size="x-small",
            style="transform: scale(-1, 1);",
        )
        with v3.VMenu(activator="parent"):
            with config.provide_as("config"):
                with v3.VList(density="compact"):
                    v3.VListItem(
                        subtitle="Full Screen",
                        click=f"active_layout = '{name}'",
                    )
                    v3.VDivider()
                    with v3.VListItem(
                        subtitle="Line Break",
                        click="config.break_row = !config.break_row",
                    ):
                        with v3.Template(v_slot_append=True):
                            v3.VSwitch(
                                v_model="config.break_row",
                                hide_details=True,
                                density="compact",
                                color="primary",
                            )
                    with v3.VListItem(subtitle="Offset"):
                        v3.VBtn(
                            "0",
                            classes="text-none ml-2",
                            size="small",
                            variant="outined",
                            click="config.offset = 0",
                            active=("config.offset === 0",),
                        )
                        v3.VBtn(
                            "1",
                            classes="text-none ml-2",
                            size="small",
                            variant="outined",
                            click="config.offset = 1",
                            active=("config.offset === 1",),
                        )
                        v3.VBtn(
                            "2",
                            classes="text-none ml-2",
                            size="small",
                            variant="outined",
                            click="config.offset = 2",
                            active=("config.offset === 2",),
                        )
                        v3.VBtn(
                            "3",
                            classes="text-none ml-2",
                            size="small",
                            variant="outined",
                            click="config.offset = 3",
                            active=("config.offset === 3",),
                        )
                        v3.VBtn(
                            "4",
                            classes="text-none ml-2",
                            size="small",
                            variant="outined",
                            click="config.offset = 4",
                            active=("config.offset === 4",),
                        )
                        v3.VBtn(
                            "5",
                            classes="text-none ml-2",
                            size="small",
                            variant="outined",
                            click="config.offset = 5",
                            active=("config.offset === 5",),
                        )
                    v3.VDivider()

                    v3.VListItem(
                        subtitle="Full width",
                        click="active_layout = 'auto_layout';config.size = 12",
                    )
                    v3.VListItem(
                        subtitle="1/2 width",
                        click="active_layout = 'auto_layout';config.size = 6",
                    )
                    v3.VListItem(
                        subtitle="1/3 width",
                        click="active_layout = 'auto_layout';config.size = 4",
                    )
                    v3.VListItem(
                        subtitle="1/4 width",
                        click="active_layout = 'auto_layout';config.size = 3",
                    )
                    v3.VListItem(
                        subtitle="1/6 width",
                        click="active_layout = 'auto_layout';config.size = 2",
                    )



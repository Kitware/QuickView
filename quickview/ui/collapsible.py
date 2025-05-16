from trame.widgets import vuetify2 as v2
from trame_client.widgets.core import AbstractElement


class CollapsableSection(AbstractElement):
    id_count = 0

    def __init__(self, title, var_name=None, expended=False):
        super().__init__(None)
        CollapsableSection.id_count += 1
        show = var_name or f"show_section_{CollapsableSection.id_count}"
        with v2.VCardSubtitle(
            classes="pa-0 d-flex align-center font-weight-bold pointer",
            click=f"{show} = !{show}",
        ) as container:
            v2.VIcon(
                f"{{{{ {show} ? 'mdi-menu-down' : 'mdi-menu-right' }}}}",
                size="sm",
                classes="pa-0 ma-0",
            )
            container.add_child(title)
        self.content = v2.VSheet(
            classes="overflow-hidden mx-2 mb-3",
            rounded="lg",
            style="border: 2px solid #ccc;",
            v_show=(show, expended),
        )

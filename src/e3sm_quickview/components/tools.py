from trame.widgets import vuetify3 as v3

from e3sm_quickview import __version__ as quickview_version
from e3sm_quickview.assets import ASSETS


# -----------------------------------------------------------------------------
# Logo / Help
# -----------------------------------------------------------------------------
class AppLogo(v3.VTooltip):
    def __init__(self, compact="compact_drawer"):
        super().__init__(
            text=f"QuickView {quickview_version}",
            disabled=(f"!{compact}",),
        )
        with self:
            with v3.Template(v_slot_activator="{ props }"):
                with v3.VListItem(
                    v_bind="props",
                    title=(f"{compact} ? null : 'QuickView {quickview_version}'",),
                    classes="text-h6",
                    click=f"{compact} = !{compact}",
                ):
                    with v3.Template(raw_attrs=["#prepend"]):
                        v3.VAvatar(
                            image=ASSETS.icon,
                            size=24,
                            classes="me-4",
                        )
                    v3.VProgressCircular(
                        color="primary",
                        indeterminate=True,
                        v_show="trame__busy",
                        v_if=compact,
                        style="position: absolute !important;left: 50%;top: 50%; transform: translate(-50%, -50%);",
                    )
                    v3.VProgressLinear(
                        v_else=True,
                        color="primary",
                        indeterminate=True,
                        v_show="trame__busy",
                        absolute=True,
                        style="top:90%;width:100%;",
                    )


# -----------------------------------------------------------------------------
# Clickable tools
# -----------------------------------------------------------------------------
class ActionButton(v3.VTooltip):
    def __init__(self, compact, title, icon, click):
        super().__init__(text=title, disabled=(f"!{compact}",))
        with self:
            with v3.Template(v_slot_activator="{ props }"):
                v3.VListItem(
                    v_bind="props",
                    prepend_icon=icon,
                    title=(f"{compact} ? null : '{title}'",),
                    click=click,
                )


class ResetCamera(ActionButton):
    def __init__(self, compact="compact_drawer", click=None):
        super().__init__(
            compact=compact,
            title="Reset camera",
            icon="mdi-crop-free",
            click=click,
        )


class ToggleHelp(ActionButton):
    def __init__(self, compact="compact_drawer"):
        super().__init__(
            compact=compact,
            title="Toggle Help",
            icon="mdi-lifebuoy",
            click=f"{compact} = !{compact}",
        )


# -----------------------------------------------------------------------------
# Toggle toolbar tools
# -----------------------------------------------------------------------------
class ToggleButton(v3.VTooltip):
    def __init__(self, compact, title, icon, value, disabled=None):
        super().__init__(text=title, disabled=(f"!{compact}",))

        add_on = {}
        if disabled:
            add_on["disabled"] = (disabled,)

        with self:
            with v3.Template(v_slot_activator="{ props }"):
                v3.VListItem(
                    v_bind="props",
                    prepend_icon=icon,
                    value=value,
                    title=(f"{compact} ? null : '{title}'",),
                    **add_on,
                )


class LayoutManagement(ToggleButton):
    def __init__(self):
        super().__init__(
            compact="compact_drawer",
            title="Layout management",
            icon="mdi-collage",
            value="adjust-layout",
        )


class OpenFile(ToggleButton):
    def __init__(self):
        super().__init__(
            compact="compact_drawer",
            title="File loading",
            icon="mdi-file-document-outline",
            value="load-data",
        )


class FieldSelection(ToggleButton):
    def __init__(self):
        super().__init__(
            compact="compact_drawer",
            title="Fields selection",
            icon="mdi-list-status",
            value="select-fields",
            disabled="variables_listing.length === 0",
        )


class Cropping(ToggleButton):
    def __init__(self):
        super().__init__(
            compact="compact_drawer",
            title="Lat/Long cropping",
            icon="mdi-crop",
            value="adjust-databounds",
        )


class DataSelection(ToggleButton):
    def __init__(self):
        super().__init__(
            compact="compact_drawer",
            title="Slice selection",
            icon="mdi-tune-variant",
            value="select-slice-time",
        )


class Animation(ToggleButton):
    def __init__(self):
        super().__init__(
            compact="compact_drawer",
            title="Animation controls",
            icon="mdi-movie-open-cog-outline",
            value="animation-controls",
        )


# -----------------------------------------------------------------------------
# Menu tools
# -----------------------------------------------------------------------------
class MapProjection(v3.VTooltip):
    def __init__(self, compact="compact_drawer", title="Map Projection"):
        super().__init__(
            text=title,
            disabled=(f"!{compact}",),
        )
        with self:
            with v3.Template(v_slot_activator="{ props }"):
                with v3.VListItem(
                    v_bind="props",
                    prepend_icon="mdi-earth",
                    title=(f"{compact} ? null : '{title}'",),
                ):
                    with v3.VMenu(
                        activator="parent",
                        location="end",
                        offset=10,
                    ):
                        v3.VList(
                            mandatory=True,
                            v_model_selected=(
                                "projection",
                                ["Cyl. Equidistant"],
                            ),
                            density="compact",
                            items=("projections", self.options),
                        )

    @property
    def options(self):
        return [
            {
                "title": "Cylindrical Equidistant",
                "value": "Cyl. Equidistant",
            },
            {
                "title": "Robinson",
                "value": "Robinson",
            },
            {
                "title": "Mollweide",
                "value": "Mollweide",
            },
        ]


class StateImportExport(v3.VTooltip):
    def __init__(self, compact="compact_drawer", title="State Import/Export"):
        super().__init__(
            text=title,
            disabled=(f"!{compact}",),
        )
        with self:
            with v3.Template(v_slot_activator="{ props }"):
                with v3.VListItem(
                    v_bind="props",
                    prepend_icon="mdi-folder-arrow-left-right-outline",
                    title=(f"{compact} ? null : '{title}'",),
                ):
                    with v3.VMenu(
                        activator="parent",
                        location="end",
                        offset=10,
                    ):
                        with v3.VList(density="compact"):
                            v3.VListItem(
                                title="Download state file",
                                prepend_icon="mdi-file-download-outline",
                                click="show_export_dialog=true",
                                disabled=("!variables_loaded",),
                            )
                            v3.VListItem(
                                title="Upload state file",
                                prepend_icon="mdi-file-upload-outline",
                                click="utils.get('document').querySelector('#fileUpload').click()",
                            )

                    v3.VFileInput(
                        id="fileUpload",
                        v_show=False,
                        v_model=("upload_state_file", None),
                        density="compact",
                        prepend_icon=False,
                        style="position: absolute;left:-1000px;width:1px;",
                    )

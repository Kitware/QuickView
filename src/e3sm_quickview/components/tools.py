from pathlib import Path
from trame.widgets import vuetify3 as v3
from trame.app import asynchronous

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
    def __init__(self, compact, title, icon, click, keybinding=None):
        super().__init__(text=title, disabled=(f"!{compact}",))
        with self:
            with v3.Template(v_slot_activator="{ props }"):
                with v3.VListItem(
                    v_bind="props",
                    prepend_icon=icon,
                    title=(f"{compact} ? null : '{title}'",),
                    click=click,
                ):
                    if keybinding:
                        with v3.Template(v_slot_append=True):
                            v3.VHotkey(
                                keys=keybinding,
                                variant="contained",
                                inline=True,
                                classes="mt-n2",
                            )


class ResetCamera(ActionButton):
    def __init__(self, compact="compact_drawer", click=None):
        super().__init__(
            compact=compact,
            title="Reset camera",
            icon="mdi-crop-free",
            click=click,
            keybinding="r",
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
    def __init__(self, compact, title, icon, value, disabled=None, keybinding=None):
        super().__init__(text=title, disabled=(f"!{compact}",))

        add_on = {}
        if disabled:
            add_on["disabled"] = (disabled,)

        with self:
            with v3.Template(v_slot_activator="{ props }"):
                with v3.VListItem(
                    v_bind="props",
                    prepend_icon=icon,
                    value=value,
                    title=(f"{compact} ? null : '{title}'",),
                    **add_on,
                ):
                    if keybinding:
                        with v3.Template(v_slot_append=True):
                            v3.VHotkey(
                                keys=keybinding,
                                variant="contained",
                                inline=True,
                                classes="mt-n2",
                            )


class LayoutManagement(ToggleButton):
    def __init__(self):
        super().__init__(
            compact="compact_drawer",
            title="Layout management",
            icon="mdi-collage",
            value="adjust-layout",
            keybinding="l",
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
            keybinding="v",
        )


class Cropping(ToggleButton):
    def __init__(self):
        super().__init__(
            compact="compact_drawer",
            title="Lat/Long cropping",
            icon="mdi-crop",
            value="adjust-databounds",
            keybinding="c",
        )


class DataSelection(ToggleButton):
    def __init__(self):
        super().__init__(
            compact="compact_drawer",
            title="Slice selection",
            icon="mdi-tune-variant",
            value="select-slice-time",
            keybinding="s",
        )


class Animation(ToggleButton):
    def __init__(self):
        super().__init__(
            compact="compact_drawer",
            title="Animation controls",
            icon="mdi-movie-open-cog-outline",
            value="animation-controls",
            keybinding="a",
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
                        with v3.VList(
                            mandatory=True,
                            v_model_selected=(
                                "projection",
                                ["Cyl. Equidistant"],
                            ),
                            density="compact",
                            # items=("projections", self.options),
                        ):
                            for entry in self.options:
                                with (
                                    v3.VListItem(
                                        title=entry.get("title"),
                                        value=entry.get("value"),
                                    ),
                                    v3.Template(v_slot_append=True),
                                ):
                                    v3.VHotkey(
                                        keys=entry.get("key"),
                                        variant="contained",
                                        inline=True,
                                        classes="ml-4 mn-2",
                                    )

    @property
    def options(self):
        return [
            {
                "title": "Cylindrical Equidistant",
                "value": "Cyl. Equidistant",
                "key": "e",
            },
            {
                "title": "Robinson",
                "value": "Robinson",
                "key": "b",
            },
            {
                "title": "Mollweide",
                "value": "Mollweide",
                "key": "m",
            },
        ]


class StateImportExport(v3.VTooltip):
    def __init__(self, compact="compact_drawer", title="State Import/Export"):
        super().__init__(
            text=title,
            disabled=(f"!{compact}",),
        )
        self._pending_task = None
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
                                title=(
                                    "is_tauri ? 'Save state file' : 'Download state file'",
                                ),
                                prepend_icon="mdi-file-download-outline",
                                click=self.download_state,
                                disabled=("!variables_loaded",),
                            )
                            v3.VListItem(
                                title=(
                                    "is_tauri ? 'Load state file' : 'Upload state file'",
                                ),
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

    def download_state(self):
        if not self.state.is_tauri:
            self.state.show_export_dialog = True
            return

        self._pending_task = asynchronous.create_task(self._tauri_save())

    async def _tauri_save(self):
        export_path = await self.ctrl.save("Export State")
        txt_content = self.ctrl.download_state()
        Path(export_path).write_text(txt_content)
        self._pending_task = None

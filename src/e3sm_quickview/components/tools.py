from pathlib import Path

from trame.app import asynchronous
from trame.decorators import trigger
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
                                classes="mt-n2 border-md border-grey-darken-1 border-opacity-100 rounded-lg",
                            )


class ResetCamera(ActionButton):
    def __init__(self, compact="compact_drawer", click=None):
        super().__init__(
            compact=compact,
            title="Auto zoom",
            icon="mdi-fit-to-page-outline",
            click=click,
            keybinding="z",
        )


class CaptureFullPanel(ActionButton):
    def __init__(self, compact="compact_drawer", click=None):
        super().__init__(
            compact=compact,
            title="Capture full grid as png",
            icon="mdi-camera-outline",
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
                    active_class="border-primary border-md border-primary border-opacity-100",
                    **add_on,
                ):
                    if keybinding:
                        with v3.Template(v_slot_append=True):
                            v3.VHotkey(
                                keys=keybinding,
                                variant="contained",
                                inline=True,
                                classes="mt-n2 border-md border-grey-darken-1 border-opacity-100 rounded-lg",
                            )


class LayoutManagement(ToggleButton):
    def __init__(self):
        super().__init__(
            compact="compact_drawer",
            title="Viewport layout",
            icon="mdi-view-module",
            value="adjust-layout",
            keybinding="p",
        )


class OpenFile(ToggleButton):
    def __init__(self):
        super().__init__(
            compact="compact_drawer",
            title="File loading",
            icon="mdi-file-upload-outline",
            value="load-data",
        )


class FieldSelection(ToggleButton):
    def __init__(self):
        super().__init__(
            compact="compact_drawer",
            title="Variable selection",
            icon="mdi-list-status",
            value="select-fields",
            disabled="variables_listing.length === 0",
            keybinding="v",
        )


class Cropping(ToggleButton):
    def __init__(self):
        super().__init__(
            compact="compact_drawer",
            title="Lat/Lon cropping",
            icon="mdi-web",
            value="adjust-databounds",
            keybinding="l",
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
            icon="mdi-video",
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
                                ["Mollweide"],
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
                "key": "c",
            },
            {
                "title": "Robinson",
                "value": "Robinson",
                "key": "r",
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
                                click=self.download_state_dialog,
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

    @trigger("download_state_dialog")
    def download_state_dialog(self):
        if not self.state.is_tauri:
            self.state.show_export_dialog = True
            return

        self._pending_task = asynchronous.create_task(self._tauri_save())

    async def _tauri_save(self):
        export_path = await self.ctrl.save("Export State")
        txt_content = self.ctrl.download_state()
        Path(export_path).write_text(txt_content)
        self._pending_task = None

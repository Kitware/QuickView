NAV_BAR_TOP = ("`position:fixed;top:0;width:${compact_drawer ? '55' : '250'}px;`",)
NAV_BAR_BOTTOM = (
    "`position:fixed;bottom:0;width:${compact_drawer ? '55' : '250'}px;`",
)

TOOLBARS_FIXED_OVERLAY = (
    "position:relative;width:100%;z-index:1;background:rgb(var(--v-theme-surface));"
)


FULLSCREEN_OVERLAY = "position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:1000;"

DIALOG_STYLES = {
    "contained": True,
    "max_width": "80vw",
    "persistent": True,
}

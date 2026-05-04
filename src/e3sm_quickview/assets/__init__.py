from trame.assets.local import LocalFileManager

ASSETS = LocalFileManager(__file__)
ASSETS.url("icon", "app-icon.png")
ASSETS.url("banner", "banner.jpg")

from trame.assets.local import LocalFileManager

ASSETS = LocalFileManager(__file__)
ASSETS.url("icon", "small-icon.png")
ASSETS.url("banner", "banner.jpg")

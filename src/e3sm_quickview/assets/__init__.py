from trame.assets.local import LocalFileManager

ASSETS = LocalFileManager(__file__)
ASSETS.url("icon", "icon-192.png")
ASSETS.url("banner", "banner.jpg")

from pathlib import Path

from e3sm_quickview import __version__

__all__ = ["serve", "scripts", "styles"]

BASE_URL = f"quick_view_{__version__}"

serve = {
    BASE_URL: str(Path(__file__).with_name("serve").resolve()),
}
scripts = [
    f"{BASE_URL}/html2canvas.js",
    f"{BASE_URL}/utils.js",
]
styles = [
    f"{BASE_URL}/style.css",
]

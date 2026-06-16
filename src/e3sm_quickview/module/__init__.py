from pathlib import Path

from e3sm_quickview import __version__

__all__ = ["serve", "scripts"]

serve = {f"quick_view_{__version__}": str(Path(__file__).with_name("serve").resolve())}
scripts = [
    f"quick_view_{__version__}/html2canvas.js",
    f"quick_view_{__version__}/utils.js",
]
styles = [f"quick_view_{__version__}/style.css"]

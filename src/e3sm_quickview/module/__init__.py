from pathlib import Path

__all__ = ["serve", "scripts"]

serve = {"quick_view": str(Path(__file__).with_name("serve").resolve())}
scripts = [
    "quick_view/html2canvas.js",
    "quick_view/utils.js",
]
styles = ["quick_view/style.css"]

#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.40", "pillow>=10.1", "pyyaml>=6"]
# ///
"""Regenerate the QuickView documentation screenshots from recipes.

Each recipe in ../recipes.yaml describes one image: the state file to load,
the UI steps to perform, the region to capture, the elements to highlight,
and optionally several panels combined side by side. For every capture, a
fresh QuickView server is started (with --state when the recipe has one) and
driven with Playwright through the locally installed Chrome.

Run with uv (dependencies are declared above):

    uv run .claude/skills/screenshots/scripts/capture.py --help
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import shlex
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

SKILL_DIR = Path(__file__).resolve().parent.parent
REPO = SKILL_DIR.parent.parent.parent
SCREENSHOTS = REPO / "docs" / "guides" / "quickview" / "screenshots"
RECIPES = SKILL_DIR / "recipes.yaml"

HIGHLIGHT_COLOR = "#ff350f"
HIGHLIGHT_WIDTH = 5  # CSS pixels
COMPACT_TOOLBAR_STYLE = """
.qv-main-toolbar.v-navigation-drawer--rail
.qv-main-toolbar-buttons .v-list-item__prepend:has(> .v-icon) {
    position: absolute;
    inset: 0;
    grid-area: auto;
    justify-content: center;
    pointer-events: none;
}
.qv-main-toolbar.v-navigation-drawer--rail
.qv-main-toolbar-buttons .v-list-item__prepend:has(> .v-icon) > .v-list-item__spacer,
.qv-main-toolbar.v-navigation-drawer--rail
.qv-main-toolbar-buttons .v-list-item:has(.v-list-item__prepend > .v-icon)
> .v-list-item__append {
    display: none;
}
"""


class Skip(Exception):
    """Raised when a recipe cannot run (e.g., missing data); the image is kept."""


# -----------------------------------------------------------------------------
# Data files
# -----------------------------------------------------------------------------


@dataclass
class DataIndex:
    roots: list[Path]
    _cache: dict[str, Path | None] = field(default_factory=dict)

    def find_dir(self, name: str) -> Path | None:
        """A directory given relative to a data root ("." for the root itself)."""
        if Path(name).is_absolute():
            return Path(name) if Path(name).is_dir() else None
        for root in self.roots:
            if (root / name).is_dir():
                return root / name
        return None

    def find(self, name: str) -> Path | None:
        if name not in self._cache:
            found = None
            for root in self.roots:
                hits = sorted(root.rglob(name))
                if hits:
                    found = hits[0]
                    break
            self._cache[name] = found
        return self._cache[name]


def localize_state(state_file: Path, data: DataIndex) -> Path:
    """Copy a state file, pointing its data files to local copies found by name."""
    content = json.loads(state_file.read_text())
    missing = []
    for key in ("simulation", "connectivity"):
        original = content["files"][key]
        local = data.find(Path(original).name)
        if local is None:
            missing.append(Path(original).name)
        else:
            content["files"][key] = str(local)
    if missing:
        raise Skip(f"data not found: {', '.join(missing)}")
    tmp = tempfile.NamedTemporaryFile(
        "w", suffix=".json", prefix="qv-state-", delete=False
    )
    json.dump(content, tmp)
    tmp.close()
    return Path(tmp.name)


# -----------------------------------------------------------------------------
# QuickView server
# -----------------------------------------------------------------------------


def clean_env() -> dict:
    """Environment for child processes, without uv's virtualenv markers.

    conda resolves environments by name incorrectly when VIRTUAL_ENV is set.
    """
    return {k: v for k, v in os.environ.items() if k not in ("VIRTUAL_ENV",)}


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextlib.contextmanager
def quickview_server(python: list[str], args: list[str], log_dir: Path):
    port = free_port()
    cmd = [
        *python,
        "-m",
        "e3sm_quickview.app",
        "--server",
        "--port",
        str(port),
        "--timeout",
        "0",
        *args,
    ]
    log = open(log_dir / f"server-{port}.log", "w")
    proc = subprocess.Popen(
        cmd,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        env=clean_env(),
    )
    url = f"http://localhost:{port}/"
    try:
        deadline = time.time() + 120
        while time.time() < deadline:
            if proc.poll() is not None:
                raise RuntimeError(f"server exited, see {log.name}")
            try:
                urllib.request.urlopen(url, timeout=1)
                break
            except OSError:
                time.sleep(0.5)
        else:
            raise RuntimeError("server did not start within 120 s")
        yield url
    finally:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(proc.pid, 15)
        with contextlib.suppress(subprocess.TimeoutExpired):
            proc.wait(10)
        log.close()


# -----------------------------------------------------------------------------
# Browser steps
# -----------------------------------------------------------------------------


def wait_ready(page, needs_data: bool, wait_files=False, timeout: float = 180):
    page.wait_for_function("() => window.trame && window.trame.state", timeout=60000)
    if wait_files:
        # --data/--conn: files are opened, variables are listed but not loaded
        page.wait_for_function(
            "() => (trame.state.get('variables_listing') || []).length > 0",
            timeout=timeout * 1000,
        )
    if needs_data:
        page.wait_for_function(
            "() => trame.state.get('variables_loaded') && !trame.state.get('loading')",
            timeout=timeout * 1000,
        )


def locate(page, selector: str):
    loc = page.locator(selector)
    if loc.count() == 0:
        raise RuntimeError(f"selector matched nothing: {selector}")
    return loc.first


def run_steps(page, steps: list[dict]):
    for step in steps or []:
        (kind, value), *_ = step.items()
        if kind == "click":
            locate(page, value).click()
        elif kind == "dblclick":
            locate(page, value).dblclick()
        elif kind == "hover":
            locate(page, value).hover()
        elif kind == "press":
            page.keyboard.press(value)
        elif kind == "type":
            locate(page, value["selector"]).fill(value["text"])
        elif kind == "set":
            # Change trame state, e.g. {"show_pan_controls": true}
            page.evaluate("(s) => trame.state.update(s)", value)
        elif kind == "eval":
            page.evaluate(value)
        elif kind == "wait":
            page.wait_for_timeout(float(value) * 1000)
        elif kind == "wait_for":
            page.wait_for_selector(value, state="visible", timeout=60000)
        elif kind == "mouse":
            # [x, y] in CSS px, or {selector, x, y} with x/y as fractions of
            # the element box (moved in a few steps so mousemove events fire)
            if isinstance(value, dict):
                box = locate(page, value["selector"]).bounding_box()
                x = box["x"] + box["width"] * value.get("x", 0.5)
                y = box["y"] + box["height"] * value.get("y", 0.5)
            else:
                x, y = value
            page.mouse.move(x, y, steps=5)
        else:
            raise ValueError(f"unknown step: {kind}")
        page.wait_for_timeout(250)


def union_box(page, selectors):
    boxes = []
    for sel in selectors:
        loc = page.locator(sel)
        for i in range(loc.count()):
            box = loc.nth(i).bounding_box()
            if box and box["width"] and box["height"]:
                boxes.append(box)
    if not boxes:
        raise RuntimeError(f"no visible element for {selectors}")
    x0 = min(b["x"] for b in boxes)
    y0 = min(b["y"] for b in boxes)
    x1 = max(b["x"] + b["width"] for b in boxes)
    y1 = max(b["y"] + b["height"] for b in boxes)
    return x0, y0, x1, y1


def as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def compute_clip(page, clip, viewport):
    """Return (x0, y0, x1, y1) in CSS pixels."""
    vw, vh = viewport
    if not clip or clip == "viewport":
        return 0, 0, vw, vh
    if "rect" in clip:
        x, y, w, h = clip["rect"]
        return x, y, x + w, y + h
    x0, y0, x1, y1 = union_box(page, as_list(clip["selector"]))
    pad = clip.get("pad", 8)
    x0, y0, x1, y1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
    if clip.get("extend"):
        # extra CSS px on each side: [left, top, right, bottom]
        el, et, er, eb = clip["extend"]
        x0, y0, x1, y1 = x0 - el, y0 - et, x1 + er, y1 + eb
    if clip.get("full_height"):
        y0, y1 = 0, vh
    if clip.get("full_width"):
        x0, x1 = 0, vw
    if clip.get("from_left"):
        x0 = 0
    if clip.get("from_top"):
        y0 = 0
    return max(0, x0), max(0, y0), min(vw, x1), min(vh, y1)


def capture_panel(browser, python, data, spec, defaults, tmp_dir) -> Image.Image:
    viewport = spec.get("viewport", defaults["viewport"])
    scale = spec.get("scale", defaults["scale"])
    settle = spec.get("settle", defaults["settle"])

    args = list(spec.get("args", []))
    state = spec.get("state")
    if state:
        args += ["--state", str(localize_state(SCREENSHOTS / state, data))]
    for key, flag in (("simulation", "--data"), ("connectivity", "--conn")):
        name = (spec.get("data") or {}).get(key)
        if name:
            local = data.find(name)
            if local is None:
                raise Skip(f"data not found: {name}")
            args += [flag, str(local)]
    if spec.get("workdir"):
        workdir = data.find_dir(spec["workdir"])
        if workdir is None:
            raise Skip(f"workdir not found: {spec['workdir']}")
        args += ["--workdir", str(workdir)]

    with quickview_server(python, args, tmp_dir) as url:
        page = browser.new_page(
            viewport={"width": viewport[0], "height": viewport[1]},
            device_scale_factor=scale,
        )
        try:
            page.goto(url)
            page.add_style_tag(content=COMPACT_TOOLBAR_STYLE)
            try:
                wait_ready(
                    page, needs_data=bool(state), wait_files=bool(spec.get("data"))
                )
            except Exception:
                page.screenshot(path=str(tmp_dir / f"fail-{spec['name']}.png"))
                raise
            page.wait_for_timeout(settle * 1000)
            try:
                run_steps(page, spec.get("steps"))
            except Exception:
                page.screenshot(path=str(tmp_dir / f"fail-{spec['name']}.png"))
                raise
            page.wait_for_timeout(spec.get("settle_after", 1.0) * 1000)

            page.screenshot(
                path=str(tmp_dir / f"full-{spec['name']}-{time.time_ns()}.png")
            )
            x0, y0, x1, y1 = compute_clip(page, spec.get("clip"), viewport)
            highlights = []
            for sel in as_list(spec.get("highlight")):
                hx0, hy0, hx1, hy1 = union_box(page, as_list(sel))
                highlights.append((hx0 - x0, hy0 - y0, hx1 - x0, hy1 - y0))

            png = tmp_dir / f"panel-{time.time_ns()}.png"
            page.screenshot(
                path=str(png),
                clip={"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0},
            )
        finally:
            page.close()

    image = Image.open(png).convert("RGB")
    pad = spec.get("highlight_pad", 3)
    line = max(3, int(spec.get("highlight_width", HIGHLIGHT_WIDTH) * scale))
    # Keep the extra clearance for strokes wider than the original 2.5 CSS px.
    baseline_line = max(3, int(2.5 * scale))
    bleed = max(0, line - baseline_line) * 2 if highlights else 0
    if bleed:
        image = ImageOps.expand(image, border=bleed, fill="white")
    draw = ImageDraw.Draw(image)
    for hx0, hy0, hx1, hy1 in highlights:
        # Keep the whole outline inside the image (e.g., full-width toolbars)
        box = [
            max(line / 2, (hx0 - pad) * scale + bleed),
            max(line / 2, (hy0 - pad) * scale + bleed),
            min(image.width - 1 - line / 2, (hx1 + pad) * scale + bleed),
            min(image.height - 1 - line / 2, (hy1 + pad) * scale + bleed),
        ]
        draw.rounded_rectangle(
            box,
            radius=3 * scale,
            outline=spec.get("highlight_color", HIGHLIGHT_COLOR),
            width=line,
        )
    label = spec.get("label")
    frame = spec.get("frame")
    if label or frame:
        return frame_panel(
            image, scale, label=label, raised=frame is True or frame == "raised"
        )
    return image


def render_icons(browser, python, spec, defaults, tmp_dir) -> Image.Image:
    """Render Material Design Icons (as used in the UI) large, side by side."""
    icons = spec["icons"]
    size = spec.get("icon_size", 160)
    with quickview_server(python, [], tmp_dir) as url:
        page = browser.new_page(viewport={"width": 1600, "height": 800})
        try:
            page.goto(url)
            wait_ready(page, needs_data=False)
            html = "".join(
                f'<i class="mdi {name}" style="font-size:{size}px;'
                f'line-height:1;margin:0 {size // 4}px;color:#000"></i>'
                for name in icons
            )
            page.evaluate(
                """(html) => {
                    const div = document.createElement('div');
                    div.id = 'qv-icon-sheet';
                    div.style.cssText = 'position:fixed;inset:0;z-index:99999;'
                      + 'background:white;display:flex;align-items:center;'
                      + 'justify-content:center;padding:40px';
                    const row = document.createElement('div');
                    row.id = 'qv-icon-row';
                    row.style.cssText = 'display:flex;align-items:center;padding:20px';
                    row.innerHTML = html;
                    div.appendChild(row);
                    document.body.appendChild(div);
                }""",
                html,
            )
            page.wait_for_timeout(500)
            png = tmp_dir / f"icons-{time.time_ns()}.png"
            page.locator("#qv-icon-row").screenshot(path=str(png))
        finally:
            page.close()
    return Image.open(png).convert("RGB")


def with_retry(fn, name, attempts=2):
    """Run a capture, retrying once with a fresh server (startup can be racy)."""
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Skip:
            raise
        except Exception as e:
            if attempt == attempts:
                raise
            print(f"(retrying after: {str(e).splitlines()[0]}) ", end="", flush=True)


def frame_panel(
    image: Image.Image, scale: int, *, label: str | None = None, raised: bool = False
) -> Image.Image:
    """Frame a capture with a soft shadow and an optional label above it."""
    inset = round((8 if label or raised else 4) * scale)
    label_height = label_width = 0
    if label:
        font = ImageFont.load_default(size=round(16 * scale))
        lines = label.splitlines()
        label_height = round((26 + 21 * (len(lines) - 1)) * scale)
        label_width = max(round(font.getlength(line)) for line in lines)

    border = max(1, round(scale))
    width = max(image.width, label_width) + 2 * inset
    frame_height = image.height + 2 * inset
    radius = round((18 if raised else 6) * scale)
    margin = round((48 if raised else 10) * scale)
    offset = round((17 if raised else 2) * scale)
    blur = (13 if raised else 3) * scale
    frame_top = margin + (label_height + inset if label else 0)
    size = (width + 2 * margin, frame_top + frame_height + margin)

    shadow = Image.new("L", size)
    ImageDraw.Draw(shadow).rounded_rectangle(
        (
            margin,
            frame_top + offset,
            margin + width - 1,
            frame_top + frame_height + offset - 1,
        ),
        radius=radius,
        fill=180 if raised else 60,
    )
    out = Image.new("RGBA", size)
    out.putalpha(shadow.filter(ImageFilter.GaussianBlur(blur)))

    card = Image.new("RGBA", (width, frame_height))
    draw = ImageDraw.Draw(card)
    draw.rounded_rectangle(
        (0, 0, width - 1, frame_height - 1),
        radius=radius,
        fill="white",
        outline="#b8c0c9",
        width=border,
    )
    card.paste(image, ((width - image.width) // 2, inset))
    out.alpha_composite(card, (margin, frame_top))

    if not label:
        return out

    draw = ImageDraw.Draw(out)
    draw.rounded_rectangle(
        (margin, margin, margin + width - 1, margin + label_height - 1),
        radius=radius,
        fill="#eaf1f9",
    )
    draw.multiline_text(
        (margin + width / 2, margin + label_height / 2),
        label,
        font=font,
        fill="#244b73",
        anchor="mm",
        align="center",
        spacing=round(4 * scale),
    )
    return out


def combine(images, gap=24, vertical=False):
    transparent = any(im.mode == "RGBA" for im in images)
    mode = "RGBA" if transparent else "RGB"
    background = (0, 0, 0, 0) if transparent else "white"
    if vertical:
        width = max(im.width for im in images)
        height = sum(im.height for im in images) + gap * (len(images) - 1)
        out = Image.new(mode, (width, height), background)
        y = 0
        for im in images:
            out.paste(im, (0, y))
            y += im.height + gap
        return out
    height = max(im.height for im in images)
    width = sum(im.width for im in images) + gap * (len(images) - 1)
    out = Image.new(mode, (width, height), background)
    x = 0
    for im in images:
        out.paste(im, (x, (height - im.height) // 2))
        x += im.width + gap
    return out


def finalize(image: Image.Image, max_width: int) -> Image.Image:
    if image.width > max_width:
        ratio = max_width / image.width
        image = image.resize(
            (max_width, round(image.height * ratio)), Image.Resampling.LANCZOS
        )
    return image


# -----------------------------------------------------------------------------
# Review sheet
# -----------------------------------------------------------------------------


def review_sheet(pairs, path: Path, width=700):
    rows = []
    for name, before, after in pairs:
        cells = []
        for img_path in (before, after):
            if img_path and img_path.exists():
                im = Image.open(img_path).convert("RGBA")
                im.thumbnail((width, width))
                background = Image.new("RGB", im.size, "white")
                background.paste(im, mask=im.getchannel("A"))
                im = background
            else:
                im = Image.new("RGB", (width, 80), "white")
            cells.append(im)
        h = max(c.height for c in cells) + 30
        row = Image.new("RGB", (2 * width + 30, h), "white")
        d = ImageDraw.Draw(row)
        d.text((5, 5), f"{name}   (left: before, right: after)", fill="red")
        row.paste(cells[0], (5, 25))
        row.paste(cells[1], (width + 25, 25))
        rows.append(row)
    if not rows:
        return
    sheet = Image.new("RGB", (rows[0].width, sum(r.height for r in rows)), "white")
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.height
    sheet.save(path)


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


def default_python() -> list[str]:
    env = os.environ.get("QUICKVIEW_PYTHON")
    if env:
        return shlex.split(env)
    # Locate the "quickview" conda environment and use its interpreter directly
    # ("conda run ... python" would pick uv's python first on PATH).
    try:
        listing = subprocess.run(
            ["conda", "env", "list", "--json"],
            capture_output=True,
            text=True,
            check=True,
            env=clean_env(),
        ).stdout
        for prefix in json.loads(listing)["envs"]:
            if Path(prefix).name == "quickview":
                exe = Path(prefix) / ("python.exe" if os.name == "nt" else "bin/python")
                if exe.exists():
                    return [str(exe)]
    except (OSError, subprocess.CalledProcessError, ValueError, KeyError):
        pass
    sys.exit(
        "No Python with QuickView found: pass --python or set QUICKVIEW_PYTHON "
        "(e.g. the python of an environment where `pip install -e .` was run)."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("names", nargs="*", help="only these images (file names)")
    parser.add_argument(
        "--data-dir",
        action="append",
        type=Path,
        help="directory searched (recursively, by file name) for the data files "
        "referenced by state files; repeatable (default: ../Data next to the repo, "
        "or $QUICKVIEW_DATA)",
    )
    parser.add_argument(
        "--python",
        default=None,
        help="Python command with e3sm_quickview and ParaView available "
        "(default: $QUICKVIEW_PYTHON, else the 'quickview' conda env)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="write images here instead of overwriting the docs screenshots",
    )
    parser.add_argument(
        "--recipes",
        type=Path,
        default=RECIPES,
        help="recipe file (default: recipes.yaml next to the skill); state "
        "paths are relative to the docs screenshots folder unless absolute",
    )
    parser.add_argument("--list", action="store_true", help="list recipes and exit")
    args = parser.parse_args()

    recipes = yaml.safe_load(args.recipes.read_text())
    defaults = {
        "viewport": [1600, 1000],
        "scale": 2,
        "settle": 2.0,
        "max_width": 2400,
        **recipes.get("defaults", {}),
    }
    shots = recipes["screenshots"]
    if args.names:
        unknown = set(args.names) - {s["name"] for s in shots}
        if unknown:
            parser.error(f"no recipe for: {', '.join(sorted(unknown))}")
        shots = [s for s in shots if s["name"] in args.names]
    if args.list:
        for s in shots:
            print(f"{s['name']:50s} {s.get('page', '')}")
        return

    roots = (
        args.data_dir
        or [
            Path(p) for p in os.environ.get("QUICKVIEW_DATA", "").split(os.pathsep) if p
        ]
        or [REPO.parent / "Data"]
    )
    data = DataIndex([r.resolve() for r in roots])
    python = shlex.split(args.python) if args.python else default_python()
    out_dir = args.out or SCREENSHOTS
    out_dir.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="qv-screenshots-"))
    print(f"python: {' '.join(python)}\ndata: {', '.join(map(str, data.roots))}")
    print(f"output: {out_dir}\nwork dir (logs, review sheet): {work}\n")

    from playwright.sync_api import sync_playwright

    results = {"updated": [], "skipped": [], "failed": []}
    pairs = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=True)
        for shot in shots:
            name = shot["name"]
            before = SCREENSHOTS / name
            backup = work / f"before-{name}"
            if before.exists():
                backup.write_bytes(before.read_bytes())
            print(f"- {name} ... ", end="", flush=True)
            try:
                if "icons" in shot:
                    image = render_icons(browser, python, shot, defaults, work)
                else:
                    base = {k: v for k, v in shot.items() if k != "panels"}
                    panels = [{**base, **p} for p in shot.get("panels", [{}])]
                    images = [
                        with_retry(
                            lambda p=p: capture_panel(
                                browser, python, data, p, defaults, work
                            ),
                            name,
                        )
                        for p in panels
                    ]
                    image = (
                        images[0]
                        if len(images) == 1
                        else combine(
                            images,
                            gap=shot.get("gap", 24) * defaults["scale"],
                            vertical=shot.get("layout") == "vertical",
                        )
                    )
                image = finalize(image, shot.get("max_width", defaults["max_width"]))
                image.save(out_dir / name, optimize=True)
                results["updated"].append(name)
                pairs.append((name, backup, out_dir / name))
                print("updated", flush=True)
            except Skip as e:
                results["skipped"].append(f"{name}: {e}")
                print(f"skipped ({e})")
            except Exception as e:  # keep going, report at the end
                results["failed"].append(f"{name}: {e}")
                print(f"FAILED ({e})")
        browser.close()

    sheet = work / "review.png"
    review_sheet(pairs, sheet)
    print("\nSummary")
    for key, items in results.items():
        print(f"  {key}: {len(items)}")
        for item in items if key != "updated" else []:
            print(f"    {item}")
    if pairs:
        print(f"\nBefore/after review sheet: {sheet}")
    sys.exit(1 if results["failed"] else 0)


if __name__ == "__main__":
    main()

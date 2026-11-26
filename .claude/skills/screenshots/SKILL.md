---
name: screenshots
description: Regenerate the QuickView documentation screenshots (docs/guides/quickview/screenshots/*.png) from the current code, by replaying per-image recipes (state file, UI steps, crop, red highlight boxes) in a headless browser. Use when the UI changed and the doc images are stale, when the user asks to update/refresh/retake screenshots, or to add a recipe for a new doc image. Accepts optional image file names to limit the run.
---

# Update the QuickView documentation screenshots

Images are produced from **recipes** in `recipes.yaml` (next to this file) by
`scripts/capture.py`. For each image, the script starts a fresh QuickView
server (with `--state` when the recipe has a state file), drives it with
Playwright through the locally installed Chrome, crops the result, draws red
highlight boxes, and writes the PNG into `docs/guides/quickview/screenshots/`.
The capture runner centers icons inside compact toolbar buttons.

Out of scope: `docs/guides/quickcompare/**` and `docs/guides/siteview/**`
(their images come from the sibling tools). QuickCompare pages also embed
`state_export_import.png` from QuickView. Mention it when the image changes.

## Requirements

- `uv` (dependencies are declared inline in the script).
- Google Chrome installed (used through Playwright's `chrome` channel, so no
  browser download is needed).
- A Python environment where QuickView runs (ParaView + `pip install -e .`).
  By default the `quickview` conda env is used; otherwise pass
  `--python /path/to/python` or set `QUICKVIEW_PYTHON`.
- The data files referenced by the recipes. They are searched **by file name**
  (recursively) under `--data-dir` (repeatable), `$QUICKVIEW_DATA`, or by
  default `../Data` next to the repository. State files keep their original
  (e.g., NERSC) paths; the script rewrites them to the local copies.

## Run

From the repository root:

```bash
# All images, written to a scratch folder first for review
uv run .claude/skills/screenshots/scripts/capture.py --out /tmp/qv-shots

# Only some images
uv run .claude/skills/screenshots/scripts/capture.py --out /tmp/qv-shots map_projections.png quickview_ui.png

# List the recipes
uv run .claude/skills/screenshots/scripts/capture.py --list
```

Without `--out`, the images in `docs/guides/quickview/screenshots/` are
overwritten. Prefer `--out` first, review, then rerun without it (or copy).

A recipe whose data (or state file data) is not found is **skipped** and the
existing image is kept. A failing recipe is reported and does not stop the run.
The script exits non-zero if any recipe failed.

## Review (always)

The run prints a work directory containing:

- `review.png`: before/after pairs for every regenerated image.
- `full-<name>-*.png`: the whole browser window before cropping, useful when
  a crop or highlight is wrong.
- `server-*.log`: QuickView output for each capture.

Open `review.png` (Read tool) and check each pair:

1. The crop shows the part of the UI the doc text talks about, and the red
   boxes surround the right elements.
2. Nothing transient is visible (loading spinner, half-rendered views,
   tooltips that are not meant to be there).
3. Labels in the image match the wording of the page that embeds it
   (`page:` in the recipe).

Fix the recipe and rerun only that image until it is right. Report to the
user: updated, skipped (with reason), failed, and anything that changed
meaningfully compared to the old image (e.g., UI labels that differ from the
page text, which means the page needs an update too).

## Recipes

```yaml
- name: map_projections.png        # output file
  page: map_related.md             # page embedding it (informational)
  state: quickview-state_map_projections.json   # in the screenshots folder
  data:                            # or: open files with --data/--conn
    simulation: file.nc
    connectivity: connectivity_file.nc
  workdir: "."                     # file browser start dir, relative to a data dir
  viewport: [1400, 900]            # CSS pixels (default in `defaults`)
  scale: 2                         # device pixel ratio
  settle: 2.0                      # seconds to wait after data is loaded
  steps:                           # run in order
    - set: { active_tools: ["select-fields"] }   # change trame state
    - click: "<selector>"
    - dblclick / hover: "<selector>"
    - press: Escape                # keyboard key
    - type: { selector: "<selector>", text: "abc" }
    - mouse: [x, y]                # move the mouse (CSS px), or
    - mouse: { selector: "<selector>", x: 0.5, y: 0.5 }   # relative to an element
    - eval: "() => { ... }"        # JavaScript in the page (trame.state, ...)
    - wait: 0.5                    # seconds
    - wait_for: "<selector>"       # until visible
  clip: viewport                   # or rect: [x, y, w, h], or:
  # clip: { selector: [..], pad: 8, from_left: true, from_top: true,
  #         full_width: false, full_height: false,
  #         extend: [left, top, right, bottom] }   # extra CSS px
  highlight:                       # red boxes; a nested list = one box around all
    - "<selector>"
    - ["<selector A>", "<selector B>"]
  highlight_pad: 5                  # optional padding around red boxes in CSS px (default: 3)
  highlight_width: 6               # optional outline width in CSS px (default: 5)
  highlight_color: "#dc2626"       # optional outline color (default: "#ff350f")
  frame: true                      # optional raised frame with rounded corners and a deeper shadow
  panels:                          # several captures combined side by side
    - label: Collapsed              # optional title above the framed, shadowed capture
      steps: [...]                  # each panel overrides recipe keys
    - steps: [...]
  gap: 24                          # spacing between panels, scaled by defaults.scale
  layout: vertical                 # stack panels instead
  icons: [mdi-home, mdi-pan]       # instead of a capture: render MDI icons large
```

`anchors:` at the top of the file holds YAML anchors reused by recipes
(`*app_content` crops to the toolbar, open toolbars and views; `*auto_zoom`
clicks the Auto zoom button).

Selectors are Playwright selectors (CSS plus `:has()`, `:has-text()`,
`>> nth=1`). Prefer the stable classes the app sets for this purpose:

| Class | Element |
| ----- | ------- |
| `.qv-main-toolbar`, `.qv-main-toolbar-buttons` | Vertical toolbar / its buttons (pick one with `.v-list-item:has(.mdi-<icon>)`) |
| `.qv-variable-selection` | Variable selection drawer |
| `.qv-toolbar-layout`, `.qv-toolbar-cropping`, `.qv-toolbar-slices`, `.qv-toolbar-animation` | Control panels |
| `.v-card[data-field-name='VAR']` | View of variable `VAR` |
| `.v-overlay--active .v-list` | Open menu |

Useful state keys for `set`: `active_tools` (open panels: `select-fields`,
`select-slice-time`, `animation-controls`, `adjust-layout`,
`adjust-databounds`, `load-data`), `compact_drawer`, `layout_grouped`,
`show_aspect_ratio`, `show_zoom_controls`, `show_pan_controls`,
`expanded_slice_track`, `visible_selection_icon_idx`, `variables_filter`,
`picking_mode`, `spherical_center_lon` / `_lat`, `animation_track`.

### Adding an image

1. Add the image to a doc page, then a recipe with the same `name`.
2. If the scene needs loaded data and settings, save a state file from the app
   as `docs/guides/quickview/screenshots/quickview-state_<topic>.json` and
   reference it with `state:`.
3. Run the script on that image with `--out`, check the `full-*.png` and the
   result, iterate.
4. If no stable selector exists for an element the doc points at, add a
   `qv-*` class to it in the component (and to the table above) rather than
   relying on layout-dependent selectors.

## Commit

Images and recipe changes go in a `docs(quickview): ...` commit; script or
skill changes in a `chore(screenshots): ...` commit; new `qv-*` classes in the
app in their own commit.

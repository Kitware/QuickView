# Keyboard shortcuts in QuickView

<script setup>
import MdiIcon from "../../.vitepress/theme/MdiIcon.vue";
</script>

![QuickView help page showing toolbar icons and keyboard shortcuts](./screenshots/shortcuts.png){ width="55%" align=right style="margin: 0.5rem 0 0rem 1.5rem" }

Most of QuickView's shortcuts use a single key for convenience and to
avoid conflict with the multi-key combinations used by the operating system or other applications.
To use QuickView's shortcuts, *make sure the browser
tab or window showing QuickView is active.*

The viewport displays an in-app help page, shown in the screenshot,
when no variables from the simulation file are loaded, including at startup.
The remainder of this page summarizes the shortcuts and provides links
to more detailed description pages.


## General

| Key | Toolbar icon | Action |
| --- | :----------: | ------ |
| `H` | ![](/public/logos/quickview-icon-only.png){ width="24" height="24" style="display: inline-block; vertical-align: middle" } | Expand or collapse the main toolbar |
| `Z` | <MdiIcon name="mdi-fit-to-page-outline" /> | **Auto zoom** fits each plot to its view |
| `F` | <MdiIcon name="mdi-file-upload-outline" /> | Open the [**File loading**](./file_selection) dialog |
| `E` | <MdiIcon name="mdi-folder-arrow-left-right-outline" /> | [**Save state file**](./file_selection#state-files) |
| `I` | <MdiIcon name="mdi-folder-arrow-left-right-outline" /> | [**Upload state file**](./file_selection#state-files) (**Load state file** in the desktop app) |
| `Esc` |  | Close all control panels and collapse the main toolbar |

## Control panels

| Key | Toolbar icon | Action |
| --- | :----------: | ------ |
| `V` | <MdiIcon name="mdi-list-status" /> | Show or hide the [**Variable selection**](./variable_selection) panel |
| `S` | <MdiIcon name="mdi-tune-variant" /> | Show or hide the [**Slice selection**](./slice_selection#slice-selection-control-panel) panel |
| `A` | <MdiIcon name="mdi-video" /> | Show or hide the [**Animation controls**](./slice_selection#animation-control-panel) panel |
| `P` | <MdiIcon name="mdi-view-module" /> | Show or hide the [**Viewport layout**](./viewport_layout) panel |
| `L` | <MdiIcon name="mdi-web" /> | Show or hide the [**Lat/Lon cropping**](./map_related#geographical-region) panel |

## Map projections

| Key | Projection |
| --- | ---------- |
| `C` | **Cylindrical Equidistant** |
| `R` | **Robinson** |
| `M` | **Mollweide** |
| `N` | **Spherical** |

## Viewport layout

| Key | Action |
| --- | ------ |
| `G` | Toggle between [grouped and ungrouped](./viewport_layout#grouped-or-ungrouped) views |
| `=` | Use the **Auto flow** column layout |
| `0` | Use the **Auto** column layout |
| `1`, `2`, `3`, `4`, `6` | Set the number of columns to 1, 2, 3, 4, or 6 |

You can also hold `Alt` while pressing any of the number keys above, including `0`.

## Zoom and pan

Zoom shortcuts require the [zoom controls](./viewport_layout#zoom) to be expanded
in the viewport layout panel. Pan shortcuts require the
[pan controls](./viewport_layout#pan) to be expanded.

| Key | Action |
| --- | ------ |
| `Shift` + `↑` | Zoom in |
| `Shift` + `↓` | Zoom out |
| `←`, `→`, `↑`, `↓` | Pan the plots inside their views |

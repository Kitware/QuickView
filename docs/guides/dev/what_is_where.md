# Where Things Are in the Code

## Key bindings

- Defined in `src/e3sm_quickview/app.py`. Look for `mt.bind`.
- Hints in the main toolbar: `src/e3sm_quickview/components/tools.py`. Look for `keybinding=`.
- Hints on the help page: `src/e3sm_quickview/components/doc.py`. Look for `keys=`.

## Icons

- Main toolbar buttons and their menus: `src/e3sm_quickview/components/tools.py`. Look for `icon=`.
- Control panels opened by those buttons: `src/e3sm_quickview/components/toolbars.py`.

## State files

- Export and import: `src/e3sm_quickview/app.py`. Look for `download_state` and `_import_state`.
- Round-trip tests: `tests/test_state.py`.

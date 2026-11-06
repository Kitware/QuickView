# Continuous Integration and Deployment

The [QuickView repository on GitHub](https://github.com/Kitware/QuickView)
has 4 workflows in its [Actions tab](https://github.com/Kitware/QuickView/actions):
- __CI (automatic):__
- __Deploy VitePress site to Pages (automatic):__ Update the [QuickView website](https://kitware.github.io/QuickView/) when a new commit in the repository updates `docs/`.
- __test (automatic):__ Validate PR and code based on the current tests implemented.
- __Release (manual):__ Check `git` history to generate a version bump with associated changelog.
  This  will publish a new version to PyPI. Then conda-forge will catchup the new version and will
  automatically publish it the next day or so.
- __Package (automatic):__ Generate desktop bundles and link them to the release on GitHub.

## Web site

The [QuickView website](https://kitware.github.io/QuickView/) contains
online documentation for the tool family.
The site is generated using [VitePress](https://vitepress.dev)
from Markdown files under `docs/`.

While different tools in the family have separate GitHub repositories,
the documentation source codes all live in the `docs/` folder
in the [QuickView repository](https://github.com/Kitware/QuickView)

## Release

This workflow needs to be triggered manually
on [GitHub](https://github.com/Kitware/QuickView/actions/workflows/release.yml)
by clicking on the green __Run workflow__ button.

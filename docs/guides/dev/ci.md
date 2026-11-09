# Continuous Integration (CI) and Deployment


Each tool in the QuickView family has its own GitHub repository for
**source code development and releases**.
Release workflows publish Python packages to [PyPI](https://pypi.org/).
For tools distributed through [conda-forge](https://conda-forge.org/),
a separate feedstock repository contains the recipe and build configuration for
publishing the conda package.

| Tool | Source repository | PyPI package | conda-forge feedstock |
| --- | --- | --- | --- |
| QuickView | [Kitware/QuickView](https://github.com/Kitware/QuickView) | [e3sm-quickview](https://pypi.org/project/e3sm-quickview/) | [e3sm-quickview-feedstock](https://github.com/conda-forge/e3sm-quickview-feedstock) |
| QuickCompare | [Kitware/E3SMQuickCompare](https://github.com/Kitware/E3SMQuickCompare) | [e3sm-compareview](https://pypi.org/project/e3sm-compareview/) | [e3sm_compareview-feedstock](https://github.com/conda-forge/e3sm_compareview-feedstock) |
| SiteView | [Kitware/SiteView](https://github.com/Kitware/SiteView) | [e3sm-siteview](https://pypi.org/project/e3sm-siteview/) | In progress as of November 2026 |

The [QuickView family website](https://kitware.github.io/QuickView/)
contains **documentation** for all available tools in the family.
Its source lives in the QuickView repository's `docs/` folder,
so website builds and deployment are managed in that repository.

The following sections describe how the tools are checked, packaged, and
published, and how the shared documentation website is built and deployed.

[[toc]]

## Tool workflows

Each tool's GitHub repository has an **Actions** tab containing at least two
workflows: **CI** and **Release**. Their definitions live under
`.github/workflows/` in the corresponding repository.

### Continuous integration

The **CI** workflow is defined in `test.yml`; there is no separate
workflow named **test**. The CI workflow runs automatically on pushes and pull requests
targeting `master` or `release` for QuickView, and `main` or `release`
for QuickCompare and SiteView.
The checks differ by tool.
- QuickView and QuickCompare install the package and run the application's
 `--help` command as a basic startup check.
- SiteView also runs tests across multiple Python versions and lint checks.
See each repository's `test.yml` for the current checks.

### Release and PyPI publishing

The **Release** workflow is defined in `release.yml` and is triggered
manually. In the corresponding repository's **Actions** tab, select
**Release**, then **Run workflow**. Use the release branch configured for
the tool: `master` for QuickView and `main` for QuickCompare and SiteView.

The workflow uses Python Semantic Release, configured in `pyproject.toml`,
to examine commit history, determine a version bump, update version metadata
and the changelog, and create a GitHub release. It also builds a Python
source distribution and wheel. When a new release is created, the workflow
publishes those distributions to PyPI using
`pypa/gh-action-pypi-publish` with Trusted Publishing.
Thus, PyPI publishing is part of the source repository's release workflow.

### conda-forge publishing

QuickView's and QuickCompare's feedstock recipes download the source
distributions from PyPI and build conda packages with their dependencies.
Updating and building a feedstock is a separate process from running the
tool's **Release** workflow, but much of this process is automated:

1. After a new version is published to PyPI, the conda-forge bot detects
   the release and opens a PR to update the feedstock recipe.
2. The feedstock's CI checks the proposed update. A maintainer can review
   and merge the PR once the changes are complete and the checks pass.
   QuickView's feedstock also enables bot automerge, allowing eligible
   bot PRs to merge automatically when the checks pass.
3. After the PR is merged, the feedstock builds and publishes the new
   conda package.

The bot's routine version detection can take several hours, so allowing
about a day for a routine update can be useful for planning. This is an
estimate, not a fixed waiting period or a guaranteed publication time.
See the conda-forge documentation on
[automatic version updates](https://conda-forge.org/docs/maintainer/updating_pkgs/#how-does-regro-cf-autotick-bot-create-automatic-version-updates).

To request an earlier version check for QuickView:

1. Confirm that the new release is available on PyPI, then check the
   [feedstock's open PRs](https://github.com/conda-forge/e3sm-quickview-feedstock/pulls)
   for an existing version update.
2. If no update PR exists, open an issue in the
   [feedstock repository](https://github.com/conda-forge/e3sm-quickview-feedstock/issues/new/choose),
   select the **Bot Commands** template, and use this issue title:

   ```text
   @conda-forge-admin, please update version
   ```

3. The bot checks for a new version and opens an update PR if one is
   available. It may initially create a partial PR and add the remaining
   changes a few minutes later. Wait for the completed changes and passing
   CI checks, then review and merge the PR if you have feedstock permissions,
   or ask a feedstock maintainer to do so.
4. Wait for the conda-forge feedstock's builds to finish and the new package
   to be published to the conda-forge channel. On the computer where you
   plan to update the installation (for example, Perlmutter at NERSC), run the following
   command in a terminal to check which versions are available through conda:

   ```bash
   conda search --override-channels -c conda-forge e3sm-quickview
   ```

Using `@conda-forge-admin, please update version` as the issue title in
step 2 requests an earlier version check by the conda-forge bot. This
[request](https://conda-forge.org/docs/maintainer/infrastructure/#conda-forge-admin-please-update-version)
reduces the wait for version detection; it does not bypass CI or package
publication. The process may finish within a couple of hours, but bot and
CI queues, build times, and distribution delays affect availability.
Packages can also appear on Anaconda.org before they are downloadable
through conda; see the
[conda-forge availability FAQ](https://conda-forge.org/docs/maintainer/maintainer_faq/#why-does-my-new-version-appear-on-anaconda-cloud-but-is-not-installable-with-conda).

### Desktop packaging

QuickView and QuickCompare also have a **Package** workflow, defined in
`package.yml`, that builds desktop bundles and attaches them to a GitHub
release. It is triggered when the **Release** workflow completes on the
repository's default branch, and can also be run manually.

## Website

The [central website of the tool family](https://kitware.github.io/QuickView/) is generated with
[VitePress](https://vitepress.dev) from the Markdown files under `docs/` in the
[QuickView repository](https://github.com/Kitware/QuickView).

The workflow
[Deploy VitePress site to Pages](https://github.com/Kitware/QuickView/actions/workflows/website.yml),
defined in `.github/workflows/website.yml` in the QuickView repository,
runs on every push to `master` and can also be triggered manually.
It is not restricted to changes under `docs/`.

This workflow handles both building and deploying the website in two jobs:

1. **build** installs dependencies with `npm ci`, runs `npm run build`,
   and uploads the generated files from `docs/.vitepress/dist` as a
   GitHub Pages artifact.
2. **deploy** waits for **build** to succeed (`needs: build`), then uses
   `actions/deploy-pages` to publish that artifact to GitHub Pages.


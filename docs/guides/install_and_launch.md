# Install and launch

(See [System Requirements](/guides/system_requirements.md) for the prerequisites
for local installation and remote usage.)

Tools of the QuickView family are available as
**Conda** and **PyPI** packages as well as **pre-compiled desktop bundles**
for various OS's including Mac, Windows, and Linux.
The table below summarizes where the different packages
and bundles can be found.

| Tool name    | Desktop bundle | conda package name | Conda  | PyPI  |
| ------------ | -------------- | ------------------ | ------ | ----- |
| QuickView    | [Download page](https://github.com/Kitware/QuickView/releases) | e3sm-quickview   | [![Conda Version](https://img.shields.io/conda/vn/conda-forge/e3sm-quickview.svg)](https://anaconda.org/conda-forge/e3sm-quickview)     | [![PyPI](https://img.shields.io/pypi/v/e3sm-quickview?label=pypi%20package)](https://pypi.org/project/e3sm-quickview/)      |
| QuickCompare | [Download page](https://github.com/Kitware/E3SMQuickCompare/releases) | e3sm_compareview | [![Conda Version](https://img.shields.io/conda/vn/conda-forge/e3sm_compareview.svg)](https://anaconda.org/conda-forge/e3sm_compareview) | [![PyPI](https://img.shields.io/pypi/v/e3sm-compareview?label=pypi%20package)](https://pypi.org/project/e3sm-compareview/)  |

:::tip Note: The contents below were written with desktop and laptop computers in mind.

Users who would like to **use** our tools installed at NERSC can find information in
[a quickstart guide](/hpcsystems/nersc/launching.md).
Users who would like to **install** their own copy at NERSC
can follow [this example](/hpcsystems/nersc/installation_personal.md).
:::

## Desktop bundles {#desktop-bundles}

To deliver pre-compiled standalone desktop applications,
we use [PyInstaller](https://pyinstaller.org/en/stable/) and [Tauri](https://tauri.app/)
to bundle each of our Python-based tools and their dependencies
into a standalone graphical application.
The creation of such a bundle is done by triggering a release using GitHub Actions.
Hence, the bundles are available from the corresponding GitHub repo's Releases page.
The links are given in the summary table above.

:::warning ATTENTION Mac Users!!
The binaries compiled for Macs have not been signed using an Apple Developer ID.
Hence, after downloading a binary for Mac, the user needs to use the following
command to remove quarantine on the binary.

```
xattr -d com.apple.quarantine <your_filename>.dmg
```

Also note that the **first execution of the app will take a while** as macOS
will check and validate the full application file tree.
:::

## Conda installation {#conda}

Our tools are built with [trame](https://www.kitware.com/trame/),
and they rely on [ParaView](https://www.paraview.org/)
or [VTK](https://vtk.org/)
as well as specific features in [Python](https://www.python.org/).
We use conda to facilitate the setup.

### Initial installation

For example, to create a conda environment named `quickview-env`
then install QuickView and QuickCompare, we can use the following commands:

```sh
conda create --name quickview-env python=3.14 typing_extensions
conda activate quickview-env
conda install conda-forge::e3sm-quickview
conda install conda-forge::e3sm_compareview
```

### Updating to new versions

To update the tools to newer versions, first find the most recent version
numbers using the links in the summary table above,
then use the following commands, replacing the version numbers by what you need:

```sh
conda activate quickview-env
conda install conda-forge::"e3sm-quickview>=2.10.5"
conda install conda-forge::"e3sm_compareview>=1.11.3"
```

### Launching a tool installed via conda

To use the tools installed via conda, open a Terminal window and
activate the conda environment using

```
 conda activate quickview-env
```

Then, in the same window, use one of the following depending on
which tool you'd like to use

```
quickview
```

```
quickcompare
```

After some seconds, the Terminal window should indicate that the app has
loaded various plugins, and then provide an URL similar to `http://localhost:50329/`
(your actual number will likely be different).
**Enter the URL into a web browser** to access the graphical UI.


### Launching from JupyterLab {#jupyterlab}

QuickView can also be started from the launcher of a JupyterLab session,
with its UI shown in a JupyterLab tab. This requires installing QuickView
with its `jupyter` extra in the **same environment as the JupyterLab server**:

```sh
pip install "e3sm-quickview[jupyter]"
```

After restarting JupyterLab, an **E3SM QuickView** tile appears in the "Other"
section of the launcher. Clicking it starts QuickView on the server
(through [jupyter-server-proxy](https://jupyter-server-proxy.readthedocs.io/))
and opens it in a new JupyterLab tab.

### Command-line options {#cli}

The `quickview` command accepts options to pre-load data and to choose
where the file browser starts. Use `quickview --help` to list all of them.

| Option | Description |
| ------ | ----------- |
| `-df`, `--data <file>` | Simulation file to open at startup (used together with `--conn`). |
| `-cf`, `--conn <file>` | Connectivity file to open at startup (used together with `--data`). |
| `-sf`, `--state <file>` | [State file](/guides/quickview/file_selection#state-files) to load at startup. The data files it refers to are opened, and the saved variables and settings are restored. When given, `--data` and `--conn` are ignored. |
| `-wd`, `--workdir <dir>` | Start directory of the file browser. Defaults to the directory in which `quickview` was launched. |
| `--user-home` | Start the file browser in the user's home directory instead of `--workdir`. |
| `-p`, `--port <number>` | Port of the web server. By default, a free port is picked. |
| `--host <name>` | Host name or IP address the web server listens on (default `localhost`). |
| `--perf` | Print performance timings (`[PERF]` lines) in the terminal, to diagnose slow interactions. |

For example, to open a pair of files directly:

```sh
quickview --data /path/to/simulation.nc --conn /path/to/connectivity.nc
```

When `--data` and `--conn` are used, the files are opened but no variable is
selected yet; pick the variables to visualize as usual.

To resume an earlier analysis:

```sh
quickview --state my-analysis.json
```

:::tip Tip: First execution on macOS
On macOS, the first execution after installation via conda will also take a while
(e.g., a minute or more),
as the system will validate each Python file for security. But any following
execution should be very quick (a few seconds).
:::

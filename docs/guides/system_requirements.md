# System Requirements

This page describes the prerequisites for **local installation** and **remote usage**
of tools in the QuickView family. See [Install and Launch](/guides/install_and_launch.md)
for available packages, desktop bundles, and installation instructions.

## Local installation using a desktop bundle

Requirements:

- A desktop bundle for the selected tool matching the operating system and processor architecture.
- Sufficient disk space and permission to install and run the application.
- Access to [simulation files](/guides/simulation_data.md) and [connectivity files](/guides/connectivity.md).

The bundle includes the application's runtime dependencies (e.g., Python, ParaView, VTK).
No separate installation of these dependencies or a package manager is required.

On macOS, unsigned bundles require the
[quarantine-removal step](/guides/install_and_launch.md#desktop-bundles).
On Linux, additional system libraries may be required, depending on the distribution.

## Local installation using conda

Requirements:

- A working conda installation, such as Miniconda or Anaconda.
- Internet access to download packages.
- Sufficient disk space and write permission for the conda environment and package cache.
- A web browser.
- Access to [simulation files](/guides/simulation_data.md) and [connectivity files](/guides/connectivity.md).

Conda installs Python and the selected tool's declared dependencies.

## Remote usage

The local computer requires:

- A web browser.
- Network access to the remote system.
- For connections through an SSH tunnel, an SSH client that supports port forwarding.

The remote system requires a working installation of the selected tool and access to
[simulation files](/guides/simulation_data.md) and [connectivity files](/guides/connectivity.md).
An account and permission to run the application on an appropriate node are also required.
For system-specific instructions, see, for example, the
[NERSC launching guide](/hpcsystems/nersc/launching.md) and the
[Chrysalis guide](/hpcsystems/chrysalis/chrysalis.md).

No local installation of the selected tool or its runtime dependencies
(e.g., Python, ParaView, VTK) is required.

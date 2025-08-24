# Install and Launch for End Users


At version 1.0, QuickView is expected to be installed and used from
a personal computer with the data files also being local.
Future versions will support the server-client model allowing access
to remote data files.

Releases so far have focused on macOS. We plan to add support for
more systems in the near [future](../future.md).

---
# Install

For end users, we provide pre-built binaries that can be installed using
just a few clicks.

1. Download the latest binary from the
   [releases page](https://github.com/ayenpure/QuickView/releases/).
   macOS users with Apple Silicon chips should download `QuickView_{version}_aarch64.dmg`,
   and those with Intel chips should download a `*_x64.dmg` file.

2. **Important** for intermediate releases with three-part version numbers
   (e.g., 1.0.1): After the download, use the following command in Terminal to
   unblock the app for macOS:
   ```
   xattr -d com.apple.quarantine <your_filename>.dmg
   ```
   Explanation: in order to facilitate frequent iterations between our
   developers on the software and science sides, only major releases with
   two-part version numbers like 1.0, 1.1 etc. are signed and notarized using
   Kitware's Apple Developer ID.
   Hence the command provided above is needed for intermediate releases,
   so that after download, the macOS Gatekeeper will not block the app.

3. Double-click the downloaded `.dmg` file. In the pop-up window,
   drag the QuickView icon into the Applications folder.


!!! tip "Tip: No Need to Worry about Dependencies"

    The pre-built binaries include all dependencies needed to start the app
    on a local computer. Additional dependencies needed for data processing
    and visualization are downloaded and installed automatically when the app is launched for the first time.

---
# Launch

To launch the EAM QuickView GUI, simply double-click the app icon in your Applications folder.

!!! tip "Tip: Patience with First launch"

    When a new version of the app is launched on a computer for the
    first time, a significant amount of dependencies will be identified,
    downloaded, and installed, which will take about a minute to a few minutes
    and can be affected by the Internet connection.

    Subsequent launches should take just a few seconds.


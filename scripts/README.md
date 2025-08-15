# QuickView Scripts

This directory contains utility scripts for maintaining and developing QuickView.

## Scripts

### generate_colorbar_cache.py

Generates the colorbar image cache for all supported colormaps. This pre-generates base64-encoded PNG images for both normal and inverted versions of each colormap, improving runtime performance.

**Usage:**

```bash
# Requires ParaView's pvpython
export EAMPVIEW=/path/to/paraview/bin/pvpython
$EAMPVIEW scripts/generate_colorbar_cache.py > quickview/colorbar_cache.py
```

This will update the `quickview/colorbar_cache.py` file with all colorbar images.

### release.sh

Automates the release process for QuickView, including version bumping, tagging, and creating GitHub releases with auto-generated changelogs from git history.

**Usage:**

```bash
# Create a patch release (0.1.0 -> 0.1.1)
./scripts/release.sh patch

# Create a minor release (0.1.0 -> 0.2.0)
./scripts/release.sh minor

# Create a major release (0.1.0 -> 1.0.0)
./scripts/release.sh major
```

The script will:
- Bump version using bumpversion
- Create a git tag
- Generate changelog from commits
- Push changes to remote
- Create a GitHub release

### setup_tauri.sh

Prepares the Tauri desktop application for building by packaging the Python application with PyInstaller. This creates platform-specific sidecar executables for the Tauri app.

**Usage:**

```bash
# Run from project root (called by CI/CD workflow)
./scripts/setup_tauri.sh
```

This script:
- Creates a PyInstaller spec file
- Builds the Python application bundle
- Copies the bundle to the Tauri sidecar directory
- Prepares for Tauri desktop app compilation

**Note:** This is primarily used by the GitHub Actions workflow for automated releases.
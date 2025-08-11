# QuickView Scripts

This directory contains utility scripts for maintaining and developing
QuickView.

## Scripts

### generate_colorbar_cache.py

Generates the colorbar image cache for all supported colormaps. This
pre-generates base64-encoded PNG images for both normal and inverted versions of
each colormap, improving runtime performance.

**Usage:**

```bash
# Requires ParaView's pvpython
export EAMPVIEW=/path/to/paraview/bin/pvpython
$EAMPVIEW scripts/generate_colorbar_cache.py > quickview/colorbar_cache.py
```

This will update the `quickview/colorbar_cache.py` file with all colorbar
images.

---
# Identity and display order
id: scream
order: 100
title: Time evolution in a SCREAM simulation

# Filter values
tools:
- QuickView
models:
- SCREAM
gridConfigurations:
- Uniform
gridRepresentations:
- FV
meshDesignations:
- pg2

# Media
images:
- type: video
  src: /gallery/examples/QuickView2.5.0_SCREAM_TOMLWup.mp4
  poster: /gallery/examples/gallery_scream_preview.png
  alt: SCREAM upward longwave flux screen recording
  caption: The video clip is an unedited real-time screen recording of [QuickView](/guides/quickview/index)
    running on an exclusive GPU node at NERSC,
    showing the time evolution of the top-of-model upward longwave flux.
    The simulation was performed by the EAMxx team.
    The output data was provided by Chris Terai (LLNL).
    The visualization was created by Hui Wan (PNNL).

# The Markdown body will be shown on a separate webpage only when showDetails is set to true.
#showDetails: true
---

# Time evolution in a SCREAM simulation

Watch a real-time QuickView recording of top-of-model upward longwave flux.

- **Tool:** QuickView
- **Horizontal mesh:** ne1024pg2 (~3.5 km)
- **Credits:** Simulation performed by the EAMxx team; thanks to Chris Terai (LLNL) for providing the data. Visualization created by Hui Wan (PNNL).

Unedited real-time screen recording of QuickView running on an exclusive GPU node at NERSC, showing the time evolution of top-of-model upward longwave flux.

<script setup>
import recordingUrl from '../examples/QuickView2.5.0_SCREAM_TOMLWup.mp4'
</script>

<video controls playsinline preload="none" :src="recordingUrl" aria-label="SCREAM upward longwave flux screen recording" style="width: 100%">
  Your browser does not support embedded video.
</video>

<a :href="recordingUrl" target="_blank" rel="noopener">Open the recording</a>

[Back to the gallery](/gallery/)

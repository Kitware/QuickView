---
id: scream
order: 50
title: Time evolution in a SCREAM simulation
summary: Watch a real-time QuickView recording of top-of-model upward longwave flux.
models:
- SCREAM
mesh: ne1024pg2 (~3.5 km)
credit: Simulation performed by the EAMxx team; thanks to Chris Terai (LLNL) for providing the data. Visualization
  created by Hui Wan (PNNL).
images:
- type: video
  src: /gallery/QuickView2.5.0_SCREAM_TOMLWup.mp4
  alt: SCREAM upward longwave flux screen recording
  caption: Unedited real-time screen recording of QuickView running on an exclusive GPU node at NERSC,
    showing the time evolution of top-of-model upward longwave flux.
tools:
- QuickView
gridConfigurations:
- Uniform
gridRepresentations:
- FV
meshDesignations:
- pg2
---

# Time evolution in a SCREAM simulation

Watch a real-time QuickView recording of top-of-model upward longwave flux.

- **Tool:** QuickView
- **Horizontal mesh:** ne1024pg2 (~3.5 km)
- **Credits:** Simulation performed by the EAMxx team; thanks to Chris Terai (LLNL) for providing the data. Visualization created by Hui Wan (PNNL).

Unedited real-time screen recording of QuickView running on an exclusive GPU node at NERSC, showing the time evolution of top-of-model upward longwave flux.

<script setup>
import recordingUrl from '../QuickView2.5.0_SCREAM_TOMLWup.mp4'
</script>

<video controls playsinline preload="none" :src="recordingUrl" aria-label="SCREAM upward longwave flux screen recording" style="width: 100%">
  Your browser does not support embedded video.
</video>

<a :href="recordingUrl" target="_blank" rel="noopener">Open the recording</a>

[Back to the gallery](/gallery/)

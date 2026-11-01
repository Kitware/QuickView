---
# Identity and display order
id: narrm
aliases:
- atmosphere-and-land-model-output-from-the-e3smv2-regionally-refined-model-rrm
order: 40
title: E3SMv2 output on the NARRM mesh

# Filter values
tools:
- QuickView
models:
- EAM
- ELM
gridConfigurations:
- Regionally refined
gridRepresentations:
- FV
meshDesignations:
- pg2

# Media
images:
- src: /gallery/examples/gallery_narrm_eamv2.png
  alt: EAMv2 output on the North America regionally refined mesh
  caption: A variable from the atmosphere component of the fully coupled E3SMv2 Regionally Refined Model
    ([Tang et al., 2023](https://gmd.copernicus.org/articles/16/3953/2023/gmd-16-3953-2023.html))
    is displayed in [QuickView](/guides/quickview/index).
    The horizontal resolution is ne30 over most of the globe but with a 4x refinement in North America.
    The simulation data was downloaded from the archive linked in
    [Tang et al. (2023)](https://gmd.copernicus.org/articles/16/3953/2023/gmd-16-3953-2023.html).
- src: /gallery/examples/gallery_narrm_elmv2.png
  alt: ELMv2 output on the North America regionally refined mesh
  caption: A variable from the land component of the fully coupled E3SMv2 Regionally Refined Model
    ([Tang et al., 2023](https://gmd.copernicus.org/articles/16/3953/2023/gmd-16-3953-2023.html))
    is displayed in [QuickView](/guides/quickview/index).
    The horizontal resolution is ne30 over most of the globe but with a 4x refinement in North America.
    The simulation data was downloaded from the archive linked in
    [Tang et al. (2023)](https://gmd.copernicus.org/articles/16/3953/2023/gmd-16-3953-2023.html).

# The Markdown body will be shown on a separate webpage only when showDetails is set to true.
#showDetails: true
---

# Atmosphere and land output on a regionally refined mesh

Explore EAMv2 and ELMv2 output with refinement over North America.

- **Tool:** QuickView
- **Horizontal mesh:** ne30pg2 with 4× refinement in North America
- **Credits:** Visualization created by Hui Wan (PNNL). Simulation data from Tang et al. (2023).

Simulation data and mesh description: [Tang et al. (2023)](https://gmd.copernicus.org/articles/16/3953/2023/gmd-16-3953-2023.html), including Figure 1.

Atmosphere-model output from the E3SMv2 Regionally Refined Model.

![EAMv2 output on the North America regionally refined mesh](/gallery/examples/gallery_narrm_eamv2.png)

Land-model output from the E3SMv2 Regionally Refined Model.

![ELMv2 output on the North America regionally refined mesh](/gallery/examples/gallery_narrm_elmv2.png)

[Back to the gallery](/gallery/)

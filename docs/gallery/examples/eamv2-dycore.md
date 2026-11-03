---
# Identity and display order
id: eamv2-dycore
order: 50
title: EAMv2 dycore output

# Filter values
tools:
- QuickView
models:
- EAM
gridConfigurations:
- Uniform
gridRepresentations:
- GLL 
meshDesignations:
- np4

# Media
images:
- src: /gallery/examples/gallery_eamv2_dycore.png
  alt: EAM dycore output on ne30np4 mesh 
  caption: 
    Four variables written out by EAMv2's spectral element dycore on the `ne30np4` mesh
    are displayed in [QuickView](/guides/quickview/index). Variables defined on the GLL nodes
    are interpreted as point data. The connectivity file for the `np4` mesh was generated
    with `homme_tool`, a piece of software released as a part of E3SM.

# The Markdown body will be shown on a separate webpage only when showDetails is set to true.
#showDetails: true 
---


[Back to the gallery](/gallery/)

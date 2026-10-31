---
id: quickcompare-aerosols
order: 20
title: Aerosol sensitivity experiments
summary: Compare aerosol number mixing ratios and differences across six EAMv2 simulations.
tools:
- QuickCompare
models:
- EAM
mesh: ne30pg2 (~165 km)
images:
- src: /gallery/gallery_quickcompare_multi-sim_value.png
  alt: Accumulation-mode aerosol number mixing ratios from six EAMv2 simulations
  caption: Accumulation-mode aerosol number mixing ratio from six EAMv2 simulations. By default, QuickCompare
    displays all simulations using the same colormap and contour levels, enabling direct visual comparison
    of the values.
- src: /gallery/gallery_quickcompare_multi-sim_diff.png
  alt: Control simulation and differences from five aerosol sensitivity experiments
  caption: Accumulation-mode aerosol number mixing ratio from the control simulation, followed by the
    difference between each of five sensitivity experiments and the control. By default, all difference
    plots use the same colormap and contour levels, with a diverging colormap centered at zero.
gridConfigurations:
- Uniform
gridRepresentations:
- FV
meshDesignations:
- pg2
credit: Simulation performed and visualization created by Hui Wan (PNNL).
---

# Aerosol sensitivity experiments

Compare aerosol number mixing ratios and differences across six EAMv2 simulations.

- **Tool:** QuickCompare
- **Horizontal mesh:** ne30pg2 (~165 km)
- **Credits:** Simulation performed and visualization created by Hui Wan (PNNL).

Accumulation-mode aerosol number mixing ratio from six EAMv2 simulations. By default, QuickCompare displays all simulations using the same colormap and contour levels, enabling direct visual comparison of the values.

![Accumulation-mode aerosol number mixing ratios from six EAMv2 simulations](/gallery/gallery_quickcompare_multi-sim_value.png)

Accumulation-mode aerosol number mixing ratio from the control simulation, followed by the difference between each of five sensitivity experiments and the control. By default, all difference plots use the same colormap and contour levels, with a diverging colormap centered at zero.

![Control simulation and differences from five aerosol sensitivity experiments](/gallery/gallery_quickcompare_multi-sim_diff.png)

[Back to the gallery](/gallery/)

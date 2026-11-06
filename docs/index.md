---
# https://vitepress.dev/reference/default-theme-home-page
layout: home

hero:
  name: "QuickView"
  text: "for Earth System Models"
  tagline:
    Efficient, intuitive, and interactive exploration of simulation data.
  image: /website_banner.png
  actions:
    - theme: brand 
      text: Installation
      link: /guides/install_and_launch
    - theme: brand 
      text: User's Guide 
      link: /guides/reminders
    - theme: brand 
      text: HPC Systems
      link: /hpcsystems/nersc/launching

features:
  - title: Purpose
    icon:
      src: /logos/E3SM_Logo.png
      width: 120px
    details:
      Currently supported are data on cubed-sphere meshes
      consisting of Gauss-Lobatto-Legendre (GLL) nodes
      or finite-volume style grid cells.
    link: https://e3sm.org/
  - title: Engine and UI 
    icon:
      src: /logos/paraview_trame_vtk.png
      width: 180px
    details:
      User Interfaces (UIs) based on the trame platform
      provide customized and intuitive access to
      powerful analysis and visualization
      capabilities without requiring a steep learning curve.
    link: https://www.kitware.com/interactive-visualization-and-analytics/
  - title: Remote Data 
    icon:
      src: /logos/nersc.png
      width: 150px
    details:
      The tools have been deployed to NERSC and other HPC systems
      so that users can
      directly access simulation data on those systems.
      No installation is required on the user's end,
      as the UI shows up in a browser window.
    link: /hpcsystems/nersc/launching
  - title: Funding Source 
    icon:
      src: /logos/SciDAC-logo.png
      width: 170px
    details:
      The QuickView family of tools is developed using funding from the
      U.S. Department of Energy's SciDAC program.
    link: https://www.scidac.gov/
---

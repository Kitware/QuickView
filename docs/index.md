---
# https://vitepress.dev/reference/default-theme-home-page
layout: home

hero:
  name: "QuickView"
  text: "for Earth system models"
  tagline:
    Efficient, intuitive, and interactive exploration of simulation data.
  image: /banner.png
  actions:
    - theme: brand 
      text: Installation
      link: /guides/install_and_launch
    - theme: brand 
      text: User's Guide 
      link: /guides/reminders
    - theme: brand 
      text: Using it at NERSC
      link: /nersc/index

features:
  - title: Purpose
    icon:
      src: /logos/E3SM_Logo.png
      width: 120px
    details:
      Currently supported are simulation input and output files   
      of the Energy Exascale Earth System Model (E3SM)
      on the cubed-sphere "physics" grids.
    link: https://e3sm.org/
  - title: Engine and UI 
    icon:
      src: /logos/paraview_trame_python.png
      width: 180px
    details:
      User Interfaces (UIs) based on Python and trame
      provide intuitive access to ParaView's
      powerful analysis and visualization
      capabilities without requiring a steep learning curve.
    link: https://www.paraview.org/ 
  - title: Remote Data 
    icon:
      src: /logos/nersc.png
      width: 150px
    details:
      The tools have been deployed to NERSC so that users can
      directly access simulation data there.
      No installation is required on the user's end,
      as the UI shows up in a browser window.
    link: /nersc/index
  - title: Funding Source 
    icon:
      src: /logos/SciDAC-logo.png
      width: 170px
    details:
      The QuickView family of tools is developed using funding from the
      U.S. Department of Energy's SciDAC program.
    link: https://www.energy.gov/science/articles/accelerating-scientific-discovery-through-advanced-computing
---

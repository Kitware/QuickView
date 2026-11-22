![E3SM-Unified icon](/public/logos/e3sm_unified_logo_200.png){ width="30%", align=right }

QuickView version 2.11.0 and QuickCompare 1.11.5 are included in
version 1.14.0 of the [E3SM-Unified](https://github.com/E3SM-Project/e3sm-unified) Conda + Spack environment
released on November 22, 2026 by the E3SM Infrastructure Team.
Researchers who would like to use the two tools on Perlmutter through E3SM-Unified
are expected to take the following steps:

1. Connect to Perlmutter using SSH with port forwarding, e.g., via [NERSC's JupyterHub](https://jupyter.nersc.gov/)
   or using [VS Code](/hpcsystems/nersc/login_vscode.md)

2. Activate the E3SM-Unified environment using the following command (for login nodes and CPU nodes):
   ```
   source /global/common/software/e3sm/anaconda_envs/load_latest_e3sm_unified_pm-cpu.sh
   ``` 
3. Launch QuickView or QuickCompare by running the command `quickview` or `quickcompare` in the terminal.
4. Open the URL printed in the terminal to access the graphical interface in a web browser on the local computer.


If a user needs to run QuickView or QuickCompare on a GPU node, please use
a standalone installation by following the steps described [here](/hpcsystems/nersc/launching).

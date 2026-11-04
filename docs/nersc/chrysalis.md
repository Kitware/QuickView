<script setup>
import { withBase } from 'vitepress'
</script>

# The QuickView Family on Chrysalis

## The cluster

[Chrysalis](https://e3sm.org/resources/supported-machines/chrysalis-anl/) is
a computer cluster dedicated to the E3SM project and its team members.
The cluster is owned by the Department of Energy (DOE)
Office of Biological and Environmental Research (BER)
and maintained by Argonne National Laboratory (ANL).

## Public installation

QuickView and QuickCompare are installed under the following `conda` environment:

```
/lcrc/group/e3sm/share/quickview/
```

To test your access, please execute the following commands in your SSH session:

```
module load miniforge3/25.3.1
conda activate /lcrc/group/e3sm/share/quickview
quickview
```
Take a sip of your tea or coffee and wait for some more seconds.
If you then see text like the following in your SSH session, it means you have
the correct permissions to use this public installation of QuickView.
```
Loading plugin :  /lcrc/group/e3sm/share/quickview/lib/python3.14/site-packages/e3sm_quickview/plugins/eam_gridlines.py
Loading plugin :  /lcrc/group/e3sm/share/quickview/lib/python3.14/site-packages/e3sm_quickview/plugins/eam_projection.py
Loading plugin :  /lcrc/group/e3sm/share/quickview/lib/python3.14/site-packages/e3sm_quickview/plugins/eam_reader.py
Loading plugin :  /lcrc/group/e3sm/share/quickview/lib/python3.14/site-packages/e3sm_quickview/plugins/eam_filters.py
tauri-server-port=42757

Use URL below to connect to the application:

  => http://localhost:42757/
```

## One-step launchers

Since tools in the QuickView family use browser-based user interfaces,
information needs to be passed from the server port on Chrysalis
to the local computer. The Python scripts linked below are one-step launchers
that each establishes an SSH connection to Chrysalis with port forwarding and,
after QuickView or QuickCompare is launched on Chrysalis,
open the UI in a browser on the local computer.

- Click to download: <a :href="withBase('/downloads/launchers/launch_quickview_on_chrysalis.py')"    download>launch_quickview_on_chrysalis.py</a>
- Click to download: <a :href="withBase('/downloads/launchers/launch_quickcompare_on_chrysalis.py')" download>launch_quickcompare_on_chrysalis.py</a>

Execute the scripts on the local computer using the following commands, replacing `USERNAME` by your username.
```
python3 launch_quickview_on_chrysalis.py USERNAME@chrysalis.lcrc.anl.gov
```
```
python3 launch_quickcompare_on_chrysalis.py USERNAME@chrysalis.lcrc.anl.gov
```
Enter your authentication information when prompted to do so.

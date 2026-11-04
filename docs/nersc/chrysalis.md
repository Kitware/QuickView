<script setup>
import { withBase } from 'vitepress'
</script>

# The QuickView Family on Chrysalis

## Chrysalis

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


Some [connectivity](/guides/connectivity) files are available under `/lcrc/group/e3sm/share/connectivity/`,
additional files can be downloaded from [Zenodo](/guides/connectivity#connectivity-file-download). 

:::tip Tip: Manage connectivity files
We recommend having a copy or softlink of the connectivity file you need
in the folder of the simulation files, so as to minimize the number of
clicks needed for [file selection](/guides/quickview/file_selection#new-analysis).
:::

:::warning Tip: SSH connection 

If your typical login method does **not** include port forwarding,
skip the rest of this section and jump to [One-step launchers](#one-step-launchers) below.
:::

If your typical login method already supports port forwarding,
you can load the `conda` environment using

```
module load miniforge3/25.3.1
conda activate /lcrc/group/e3sm/share/quickview
```
and then, launch QuickView or QuickCompare using
```
quickview
```

```
quickcompare
```

Take a sip of tea or coffee and wait for some more seconds until
your screen output looks like the following.
Enter the URL in a web browser to start using the tool.
```
Loading plugin :  /lcrc/group/e3sm/share/quickview/lib/python3.14/site-packages/e3sm_quickview/plugins/eam_gridlines.py
Loading plugin :  /lcrc/group/e3sm/share/quickview/lib/python3.14/site-packages/e3sm_quickview/plugins/eam_projection.py
Loading plugin :  /lcrc/group/e3sm/share/quickview/lib/python3.14/site-packages/e3sm_quickview/plugins/eam_reader.py
Loading plugin :  /lcrc/group/e3sm/share/quickview/lib/python3.14/site-packages/e3sm_quickview/plugins/eam_filters.py
tauri-server-port=42757

Use URL below to connect to the application:

  => http://localhost:42757/
```

## One-step launchers {#one-step-launchers}

Since tools in the QuickView family use browser-based user interfaces,
information needs to be passed from the server port on Chrysalis
to the local computer. The Python scripts linked below are one-step launchers
that each establishes an SSH connection to Chrysalis with port forwarding and,
after QuickView or QuickCompare is started on Chrysalis,
open the UI in a browser on the local computer.

- Click to download: <a :href="withBase('/downloads/launchers/launch_quickview_on_chrysalis.py')"    download>launch_quickview_on_chrysalis.py</a>
- Click to download: <a :href="withBase('/downloads/launchers/launch_quickcompare_on_chrysalis.py')"    download>launch_quickcompare_on_chrysalis.py</a>

Execute the scripts on the local computer using one of the following commands,
replacing `USERNAME` by your username.
```
python3 launch_quickview_on_chrysalis.py USERNAME@chrysalis.lcrc.anl.gov
```

```
python3 launch_quickcompare_on_chrysalis.py USERNAME@chrysalis.lcrc.anl.gov
```
Enter your authentication information when prompted to do so.
After a successful login and some more seconds, the SSH session will print out text similar to the screenshot below.
If the tool's graphical user interface does not show up automatically in a web browser,
you will need to manually enter the last URL (that includes "localhost:" but probably with a different number)
in a web browser to start using the tool.

![Chrysalis one-step launcher output](./chrysalis_launch_quickcompare.png)

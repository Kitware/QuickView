![NERSC logo](/logos/nersc.png){width="40%"}

QuickView and other tools in the family can be used to interactively explore data residing on a remote computing system without installing a dedicated QuickView client on the user’s local computer. The tool runs on the remote system, close to the data, while its graphical user interface is displayed in a local web browser. Thus, unlike client–server visualization workflows such as ParaView, QuickView does not require a separate local client; nor does it require an X Window System implementation such as XQuartz. Remote use generally requires no additional local software beyond a web browser and a familiar remote-access environment. Two such workflows are currently supported and tested on NERSC’s Perlmutter: users can launch QuickView from a terminal in NERSC JupyterHub and open the URL provided by the tool in the terminal, or launch it through a VS Code Remote–SSH session and open the resulting URL in either VS Code’s built-in browser or an external browser. Here is the step-by-step recipe:

- Login to Perlmutter via [NERSC's JupyterHub](login_jupyter) or using [VS Code](login_vscode). 

- *Optional but recommended*: in the terminal, use the `cd` command to go to the directory
  where your data files are located or a directory closer to the data files than your home directory.
  While this is optional, it may save you quite some clicks later in the graphical UI.

- **QuickView version 2** can be launched using the following command:
```
/global/common/software/m4359/quickview2
```

- **QuickCompare** can be launched using the following command:
```
/global/common/software/m4359/quickcompare
```

After a few seconds, the terminal window will provide a URL for accessing the UI.

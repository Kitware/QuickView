# QuickCompare @ NERSC

## Log in to NERSC

To use QuickCompare at NERSC to directly access and analyze data files there,
users need to first connect to NERSC using JupyterHub, as described
[on this page](./jupyter_at_nersc.md).

Once connected,

- Start a Terminal from the Launcher in JupyterHub.
  You will likely need to scroll down in the Launcher in order to
  see the "Other" section and the Terminal icon there, as shown in the screenshot below.
  Click on the Terminal icon, and the Launcher window should turn into a shell.
  !["Other" section of JupyterHub Launcher window](./jupyter_launcher_terminal.png)

- *Optional but recommended*: in the shell, use the `cd` command to go to
  the directory where your data files are located (or a directory closer to the data files than your home directory).
  While this step is optional, it may save you quite some clicks later in the graphical UI.

- Starting QuickCompare using the command `/global/common/software/m4359/quickcompare`.

- After some seconds, a URL is provided in the Terminal, similar to the screenshot below.
  A click on the URL will bring up the graphical UI in a separate brower window or tab.
  ![QuickCompare Terminal with URL](./quickcompare/quickcompare-terminal-with-url.png)

- The graphical UI will prompt you to choose connectivity and simulation files, see example below.
  Double click your connectivity file and then some simulation files, then
  click on the blue "Load Files" button in the bottom-right corner
  ![QuickCompare File Loading](./quickcompare/quickcompare-file-loading.png) -->

- Select the variables to load and inspect.
  The [variable search and selection functionalities](/guides/quickview/variable_selection)
  are the same in QuickCompare and QuickView.

A detailed User's Guide for using QuickCompare can be found through [this link](/guides/quickcompare/index).

## Shutting down the server

::: warning ATTENTION: Shut down the server when you are done!
After finishing your analysis, please remember to shut down the connection to your
assigned node to avoid keeping the resource idle and unnecessarily charging
to your project's allocation. This is explained at the end of
[this video](https://docs.nersc.gov/beginner-guide/#keypad-entry-log-in-using-jupyter).
Also see below for a recap of the steps (clicks).
:::

- Go to the JupytherHub window/tab in your browser.
- Click on `File` in the top-left corner.
- Scroll down and choose `Hub Control Panel`.
- In the Control Panel brought up in a new browser tab or window,
  click on the red "stop" button for the server to be shut down.
  An example is shown in the screenshot below.

![](./login/login-04.png)

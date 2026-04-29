# Developers' Installation at NERSC

The QuickView family of tools are Python packages.
They have been installed and are frequently updated at NERSC under project m4359.

NERSC users who would like to **use** the developers' installation
can start a terminal (shell) window through NERSC's JupyterHub
(see step-by-step guide [here](./jupyter_at_nersc))
and then use the following commands to start QuickView and QuickCompare,
respectively.

```
/global/common/software/m4359/quickview2
```

```
/global/common/software/m4359/quickcompare
```

For installing the tools at a location of the user's choice,
an example is provided on [this page](./users_installation.md).
The remainder of this page documents how the developers' installation was done.


## Setting default permissions

To allow any developer in project m4359 to install, uninstall, or update,
and to allow all NERSC users to use the installation, we set the default permission using
```
umask 002
```

## One-time action: creating custom conda environment


```sh
mkdir -p /global/common/software/m4359/conda-envs

module load conda
conda create --prefix /global/common/software/m4359/conda-envs/quickview-family python=3.13
```

## First installation

```
conda activate /global/common/software/m4359/conda-envs/quickview-family
conda install conda-forge::e3sm-quickview 
conda install conda-forge::e3sm_compareview 
```

## Updating to newer versions 

Different members of the QuickView tool family are versioned separately.
The current (newest) version numbers are summarized in the table at the beginning
of [this page](/guides/install_and_launch).
The following commands were used to update QuickView to version 2.1.2
and QuickCompare to version 1.3.5.

```sh
module load conda
conda activate /global/common/software/m4359/conda-envs/quickview-family

conda install "e3sm-quickview>=2.1.2"
conda install "e3sm_compareview>=1.3.5"
```

## Shortcuts to the executables

The commands listed at the beginning of this page are in fact scripts
with the following contents. These scripts were created to allow
the users to start any tool in the QuickView family using a single command.

`/global/common/software/m4359/quickview2` is a script with the following contents

```sh
#!/usr/bin/env bash

module load conda
conda activate /global/common/software/m4359/conda-envs/quickview-family
quickview -p 0
```

Similarly, `/global/common/software/m4359/quickcompare` is a script with the following contents

```sh
#!/usr/bin/env bash

module load conda
conda activate /global/common/software/m4359/conda-envs/quickview-family
quickcompare -p 0
```

## Launching/Using QuickView

To clone this repository use the following commands

```
git clone https://gitlab.kitware.com/ayenpure/eamapp.git
cd eamapp
git lfs install
git lfs pull
```

Alternatively, the code can also be downloaded as a tarball

```
wget https://gitlab.kitware.com/ayenpure/eamapp/-/archive/master/eamapp-master.tar.gz
tar -xvzf eamapp-master.tar.gz
cd eamapp-master
```

To run the app, execute

```
python3 launch.py --data data/aerosol_F2010.eam.h0.2014-12.nc
```

Alternatively, if the path to `pvpython` is known, it can be used to directly execute the main application script on successive scripts.

```
/Applications/ParaView-5.13.1.app/Contents/bin/pvpython --force-offscreen-rendering eamapp.py --venv .pvenv --data aerosol_F2010.eam.h0.2014-12.nc
```

Please ensure that the `python3` is the correct version.
In the above execution the data file is provided as the sample data out of the repository. The repository also contains the connectivity file that it uses by default.
If another connectivity and data files are to be used please specify the paths using the `--conn` and `--data` options.

The above command will start the Trame app server.
On the browser proceed to `http://localhost:8080` to use the app

import os
import json
import argparse
import traceback
from pathlib import Path

import paraview.web.venv

from eamapp.pipeline import EAMVisSource
from eamapp.interface import EAMApp
from eamapp.utilities import ValidateArguments


def serve():
    parser = argparse.ArgumentParser(
        prog="eamapp.py", description="Trame based app for visualizing EAM data"
    )
    parser.add_argument(
        "-cf", "--conn", nargs="?", help="the nc file with connnectivity information"
    )
    parser.add_argument("-df", "--data", help="the nc file with data/variables")
    parser.add_argument("-sf", "--state", nargs="?", help="state file to be loaded")
    parser.add_argument(
        "-wd", "--workdir", help="working directory (to store session data)"
    )
    args, xargs = parser.parse_known_args()

    data_file = args.data
    state_file = args.state
    work_dir = args.workdir
    conn_file = args.conn

    # ValidateArguments(conn_file, data_file, state_file, work_dir)

    if args.conn is None:
        conn_file = os.path.join(
            os.path.dirname(__file__), "eamapp", "data", "connectivity.nc"
        )

    globe_file = os.path.join(os.path.dirname(__file__), "eamapp", "data", "globe.vtk")

    if work_dir is None:
        work_dir = str(os.getcwd())

    source = EAMVisSource()
    state = None
    try:
        if state_file is not None:
            state = json.loads(Path(state_file).read_text())
            data_file = state["DataFile"]
            conn_file = state["ConnFile"]
        source.Update(
            data_file=data_file,
            conn_file=conn_file,
            globefile=globe_file,
            lev=0,
            ilev=0,
        )
        app = EAMApp(source, workdir=work_dir, initstate=state)
        app.start()
    except Exception as e:
        print("Problem : ", e)
        traceback.print_exc()


if __name__ == "__main__":
    serve()

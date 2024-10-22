import traceback, argparse
import paraview.web.venv

def serve():
    parser = argparse.ArgumentParser(prog='eamapp.py',
                                 description='Trame based app for visualizing EAM data')
    parser.add_argument('-cf', '--conn', nargs="?", help='the nc file with connnectivity information')
    parser.add_argument('-df', '--data', help='the nc file with data/variables')
    parser.add_argument('-sf', '--state', nargs='?', help='state file to be loaded')
    parser.add_argument('-wd', '--workdir', help='working directory (to store session data)')
    args, xargs = parser.parse_known_args()

    import os

    ConnFile = args.conn 
    if args.conn is None:
        ConnFile = os.path.join(os.path.dirname(__file__), "eamapp", "data", "connectivity.nc")
    DataFile = args.data
    StateFile = args.state
    WorkDir = args.workdir

    print(f"{DataFile, ConnFile, StateFile, WorkDir}")

    from eamapp.utilities import ValidateArguments
    ValidateArguments(ConnFile, DataFile, StateFile, WorkDir)

    if WorkDir is None:
        WorkDir = str(os.getcwd())
    from eamapp.pipeline import EAMVisSource

    GlobeFile = os.path.join(os.path.dirname(__file__), "eamapp", "data", "globe.vtk")
    
    from eamapp.interface import EAMApp
    source = EAMVisSource()
    import json
    try:
        print(WorkDir)
        if StateFile is not None:
            from pathlib import Path
            path = Path(StateFile)
            state = json.loads(path.read_text())
            DataFile = state['DataFile']
            ConnFile = state['ConnFile']
            source.Update(datafile=DataFile, connfile=ConnFile, globefile=GlobeFile, lev=0)
            app = EAMApp(source, workdir=WorkDir, initstate=state)
            app.start()
        else:
            source.Update(datafile=DataFile, connfile=ConnFile, globefile=GlobeFile, lev=0)
            app = EAMApp(source, workdir=WorkDir) 
            app.start()
    except Exception as e:
        print("Problem : ", e)
        traceback.print_exc()


if __name__ == "__main__":
    serve()

import traceback, argparse

def serve():
    parser = argparse.ArgumentParser(prog='eamapp.py',
                                 description='Trame based app for visualizing EAM data')
    parser.add_argument('-cf', '--conn', nargs="?", help='the nc file with connnectivity information')
    parser.add_argument('-df', '--data', help='the nc file with data/variables')
    parser.add_argument('-sf', '--state', nargs='+', help='state file to be loaded')
    parser.add_argument('-wd', '--workdir', help='working directory (to store session data)')
    args, xargs = parser.parse_known_args()

    import os

    ConnFile = args.conn 
    if args.conn is None:
        ConnFile = os.path.join(os.path.dirname(__file__), "eamapp", "data", "connectivity.nc")
    DataFile = args.data
    StateFile = args.state
    WorkDir = args.workdir
    from eamapp.utilities import ValidateArguments
    ValidateArguments(ConnFile, DataFile, StateFile, WorkDir)

    from eamapp.vissource.vissource import EAMVisSource

    source = EAMVisSource()
    try:
        GlobeFile = os.path.join(os.path.dirname(__file__), "eamapp", "data", "globe.vtk")
        source.Update(datafile=DataFile, connfile=ConnFile, globefile=GlobeFile, lev=0)
        print(source.extents)
    except Exception as e:
        print("Problem : ", e)
        traceback.print_exc()

    from eamapp.eamapp import EAMApp
    app = EAMApp(source)
    
    app.start()

if __name__ == "__main__":
    serve()
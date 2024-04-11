import os

def ValidateArguments(ConnFile, DataFile, StateFile, WorkDir):
    if (ConnFile == None or DataFile == None) and StateFile == None:
        print("Error : either both the data and connectivity files are not specified and the state file is not provided too")
        exit()
    if StateFile == None:
        if not os.path.exists(ConnFile) or not os.path.exists(DataFile):
            print("Either the data file or the connectivity file does not exist")
            exit()
    elif not os.path.exists(StateFile):
        print("Provided state file does not exist")
        exit()
    if WorkDir == None:
        print("No working directory is provied, using current directory as default")
    return True
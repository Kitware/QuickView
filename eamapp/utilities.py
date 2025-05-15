import os
from enum import Enum


class EventType(Enum):
    COL = 0
    LOG = 1
    INV = 2


def ValidateArguments(conn_file, data_file, state_file, work_dir):
    if (conn_file == None or data_file == None) and state_file == None:
        print(
            "Error : either both the data and connectivity files are not specified and the state file is not provided too"
        )
        exit()
    if state_file == None:
        if not os.path.exists(conn_file) or not os.path.exists(data_file):
            print("Either the data file or the connectivity file does not exist")
            exit()
    elif not os.path.exists(state_file):
        print("Provided state file does not exist")
        exit()
    if work_dir == None:
        print("No working directory is provided, using current directory as default")
    return True

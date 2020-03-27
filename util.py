""" Utility functions"""

import os
import json

def append_lst_to_json(new_lst, json_file):
    """ Append a list to a json file which is also a list."""
    json_lst = []
    if os.path.isfile(json_file):
        with open(json_file) as fjson:
            json_lst = json.load(fjson)

    json_lst.extend(new_lst)
    with open(json_file, 'w') as fjson:
        json.dump(json_lst, fjson, indent=4)
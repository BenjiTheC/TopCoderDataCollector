""" Utility functions"""

import os
import json
from datetime import datetime

def append_lst_to_json(new_lst, json_file):
    """ Append a list to a json file which is also a list."""
    json_lst = []
    if os.path.isfile(json_file):
        with open(json_file) as fjson:
            json_lst = json.load(fjson)

    json_lst.extend(new_lst)
    with open(json_file, 'w') as fjson:
        json.dump(json_lst, fjson, indent=4)

def parse_iso_dt(tc_date_str, fmt='%Y-%m-%d %H:%M:%S'):
    """ Parse a ISO-8601 formatted date string to given format
        default format is MySQL Datetime type compatible.
        TopCoder's date string is fixed to `yyyy-mm-ddThh:mm:ss.fffZ`
        the datetime.fromisoformat() method support string in the format of
        `YYYY-MM-DD[*HH[:MM[:SS[.mmm[mmm]]]][+HH:MM[:SS[.ffffff]]]]` P.S. no trailing 'Z' accepted!
    """
    return datetime.fromisoformat(tc_date_str[:-1]).strftime(fmt)

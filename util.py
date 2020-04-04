""" Utility functions"""

import os
import re
import json
from glob import iglob
from datetime import datetime

def append_lst_to_json(new_lst, json_file):
    """ Append a list to a json file which is also a list.
        This approach is concise and elegant but has drastic
        performance drop when the json_file becomes too large.
        Open a large json_file and read it into memory is a 
        performant disaster, so when use this function, it's
        better to split dataset into chunks.
    """
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

def concat_json_files(path, name_pattern, new_file_name):
    """ Concat the data set segments into one giant data set."""
    giant_data_set = []
    for file_name in sorted(iglob(os.path.join(path, name_pattern))):
        with open(file_name, 'r') as fjson:
            giant_data_set.extend(json.load(fjson))

    with open(os.path.join(path, new_file_name), 'w') as fwrite:
        json.dump(giant_data_set, fwrite, indent=4)

def get_sorted_filenames(path, name_pattern):
    """ Get the sorted file names sorted in integer index."""
    return sorted(iglob(os.path.join(path, name_pattern)), key=lambda p: int(re.search(r'.*_([\d]*)\.json', p).group(1)))

""" Utility functions"""

import os
import re
import logging
import pathlib
from glob import iglob
from datetime import datetime, timezone


def init_logger(log_dir: pathlib.Path, log_name: str, debug: bool) -> logging.Logger:
    """ Initiate logger for fetching."""
    log_fmt = logging.Formatter('%(asctime)s [%(filename)s:%(lineno)d] %(levelname)s - %(message)s')

    file_handler = logging.FileHandler(log_dir / f'{log_name}_{datetime.now().timestamp()}')
    file_handler.setFormatter(log_fmt)

    stream_handle = logging.StreamHandler()
    stream_handle.setFormatter(log_fmt)

    logger = logging.getLogger(log_name)
    logger.setLevel(logging.INFO if not debug else logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handle)

    return logger


def get_sorted_filenames(path, name_pattern):
    """ Get the sorted file names sorted in integer index."""
    return sorted(
        iglob(os.path.join(path, name_pattern)),
        key=lambda p: int(re.search(r'.*_([\d]*)\.json', p).group(1))
    )


def replace_datetime_tail(dt: datetime, tail: str = 'max'):
    """ Replace the hour, minute, second, microsecond, tzinfo parts of datetime object
        to either datetime.max.time() or datetime.min.time()
    """
    return (
        dt.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc)
        if tail == 'max' else
        dt.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    )


def datetime_to_isoformat(dt: datetime):
    """ The built-in datetime.isoformat doesn't have trailing Z"""
    return '{}Z'.format(dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3])

""" Utility functions"""

import os
import re
import logging
import pathlib
from glob import iglob
from typing import Optional
from collections import defaultdict
from dateutil.parser import isoparse
from datetime import datetime, timezone
from bs4 import BeautifulSoup, NavigableString, Tag, PageElement

CAMEL_CASE_REGEX = re.compile(r'(?<!^)(?=[A-Z])')


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


def snake_case_json_key(obj):
    """ When loading json into python, the dictionary/list of dictionary can be
        camelCase-keyed. we should convert it before further process/usage.
    """
    if not isinstance(obj, (list, dict)):
        return obj

    if isinstance(obj, list):
        return [snake_case_json_key(o) for o in obj]

    return {CAMEL_CASE_REGEX.sub('_', k).lower(): snake_case_json_key(v) for k, v in obj.items()}


def convert_datetime_json_value(obj):
    """ Convert the ISO-8601 datetime string to datetime object."""
    if not isinstance(obj, (list, dict)):
        try:
            dt = isoparse(obj)
        except (ValueError, TypeError):
            return obj
        else:
            return dt

    if isinstance(obj, list):
        return [convert_datetime_json_value(o) for o in obj]

    return {k: convert_datetime_json_value(v) for k, v in obj.items()}


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


def html_to_sectioned_text(html: str) -> list[dict]:
    """ Convert html file/segments to text which sectioned by header(<h*>) tag."""
    sectioned_text = defaultdict(list)
    soup = BeautifulSoup(html, 'html.parser')

    # There are some img tags and a tags that won't be extracted below, do it now.
    if soup.a:
        soup.a.decompose()
    if soup.img:
        soup.img.decompose()

    header_tags = soup.find_all(re.compile('^h'))

    if len(header_tags) == 0:
        return [{'name': 'null', 'text': soup.get_text()}]

    for header in header_tags:
        section_name = header.get_text()

        next_node: Optional[PageElement] = header
        while True:
            next_node = next_node.next_sibling

            if next_node is None:
                break

            if isinstance(next_node, NavigableString):
                sectioned_text[section_name].append(' '.join(next_node.strip().split()))
            elif isinstance(next_node, Tag):
                if next_node.name.startswith('h'):
                    break
                sectioned_text[section_name].append(' '.join(next_node.get_text().split()))

    return [{'name': name, 'text': ' '.join(texts)} for name, texts in sectioned_text.items()]

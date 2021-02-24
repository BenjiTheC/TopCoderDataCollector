""" Utility functions"""
import os
import re
import logging
import pathlib
from glob import iglob
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
    """ Rules for sectionize the text:
        - An h tag owns all the next_siblings text until there is another h tag
        - An h tag owns all the children text until there is a child h tag
        - If a tag has no h tag in its children, it's the end node
    """
    sectioned_text = defaultdict(list)
    section_name, section_lvl = 'null', 0
    h_tag_regex = re.compile(r'^h[1-6]')
    def go_down_html_tree(node: PageElement, section_name: str, section_lvl: int):
        """ Recursively parsing the text by header tag section."""
        for child_node in node.children:
            if isinstance(child_node, Tag) and h_tag_regex.match(child_node.name):
                section_name, section_lvl = child_node.get_text(), int(child_node.name[1])
                sectioned_text[(section_name, section_lvl)].append('')  # placeholder incase there is no text
                continue
            if isinstance(child_node, Tag) and child_node.find(h_tag_regex) is None:
                sectioned_text[(section_name, section_lvl)].append(' '.join(child_node.get_text().split()))
                continue
            if isinstance(child_node, NavigableString):
                if child_node.strip():
                    sectioned_text[(section_name, section_lvl)].append(' '.join(child_node.strip().split()))
                continue
            go_down_html_tree(child_node, section_name, section_lvl)

    soup = BeautifulSoup(html, 'html.parser')

    a: Tag
    img: Tag
    for a in soup.find_all('a'):
        a.replace_with(a.get_text())
    for img in soup.find_all('img'):
        img.decompose()

    go_down_html_tree(soup, section_name, section_lvl)
    return [{'name': ' '.join(name.split()), 'level': lvl, 'text': ' '.join(texts)} for (name, lvl), texts in sectioned_text.items()]

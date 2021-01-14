""" Command line interface of Topcoder data collector."""
import os
import asyncio
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta
from util import replace_datetime_tail
from static_var import Status
from fetcher import Fetcher


def init():
    """ Entrance of CLI"""
    parser = argparse.ArgumentParser(description='Asynchronous Topcoder Data Collector command line tool.')
    parser.add_argument(
        '--with-registrant',
        action='store_true',
        dest='with_registrant',
        default=False,  # Temporary setting
        help='Whether fetch registrant details or not.'
    )
    parser.add_argument(
        '--status',
        dest='status',
        default=Status.ALL,
        type=Status,
        help='The status of challenges for fetching.'
    )
    parser.add_argument(
        '-s', '--since',
        dest='since',
        default=(datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d'),
        type=lambda since: replace_datetime_tail(datetime.fromisoformat(since), 'min'),
        help='Specify the earliest of end date in UTC of a challenge.',
    )
    parser.add_argument(
        '-t', '--to',
        dest='to',
        default=datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        type=lambda to: replace_datetime_tail(datetime.fromisoformat(to), 'max'),
        help='Specify the latest of start date int UTC of a challenge.',
    )
    parser.add_argument(
        '--output-dir',
        dest='output_dir',
        default=Path(os.path.join(os.curdir, 'data')),
        type=Path,
        help='Directory for store the fetch data. Create one if not exist'
    )

    args = parser.parse_args()

    if args.since > args.to:
        print('since value should not be greatter than to value.')
        exit(1)

    if not args.output_dir.is_dir():
        os.mkdir(args.output_dir)

    asyncio.run(Fetcher(**args.__dict__).fetch())


if __name__ == '__main__':
    init()

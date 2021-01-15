""" Command line interface of Topcoder data collector."""
import os
import asyncio
import argparse
from pathlib import Path
from fetcher import Fetcher
from static_var import Status, DEFAULT_DATA_PATH
from datetime import datetime, timezone, timedelta
from util import replace_datetime_tail, init_logger


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
        default=DEFAULT_DATA_PATH,
        type=Path,
        help='Directory for storoage of the fetch data. Create one if not exist',
    )
    parser.add_argument(
        '--log-dir',
        dest='log_dir',
        default=Path(os.path.join(os.curdir, 'logs')),
        type=Path,
        help='Directory for stroage of logs. Create one if not exist',
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        default=False,
        help='Whether to log debug level message.'
    )

    args = parser.parse_args()

    if args.since > args.to:
        print('since value should not be greatter than to value.')
        exit(1)

    if not args.output_dir.is_dir():
        os.mkdir(args.output_dir)

    if not args.log_dir.is_dir():
        os.mkdir(args.log_dir)

    logger = init_logger(args.log_dir, 'fetch', args.debug)

    asyncio.run(Fetcher(args.status, args.since, args.to, args.with_registrant, args.output_dir, logger).fetch())


if __name__ == '__main__':
    init()

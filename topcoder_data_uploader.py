""" Command line interface of Topcoder data uploader."""
import os
import asyncio
import argparse
from pathlib import Path
from topcoder_mongo import TopcoderMongo
from util import init_logger


def init():
    """ Entrance of CLI"""
    parser = argparse.ArgumentParser(description='Asynchronous Topcoder Data Uploader command line tool.')
    parser.add_argument(
        '--input-dir',
        dest='input_dir',
        default=Path(os.path.join(os.curdir, 'data')),
        type=Path,
        help='Directory for storoage of the fetched data.',
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
    parser.add_argument(
        '--db',
        default='mongo',
        help='Placeholder for future MySQL database method.'
    )

    args = parser.parse_args()

    if not args.input_dir.is_dir():
        print(f'{args.input_dir} is not a directory.')
        exit(1)

    if not args.log_dir.is_dir():
        os.mkdir(args.log_dir)

    logger = init_logger(args.log_dir, f'{args.db}_upload', args.debug)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(TopcoderMongo(logger, args.input_dir).initiate_database())


if __name__ == '__main__':
    init()

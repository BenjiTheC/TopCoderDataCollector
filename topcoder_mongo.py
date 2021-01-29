""" Methods for MongoDB operation including writing fetched data and query data."""
import re
import json
import typing
import asyncio
import logging
import pathlib
import markdown
import motor.motor_asyncio
from datetime import datetime
from static_var import MONGO_CONFIG, TRACK
from util import snake_case_json_key, convert_datetime_json_value, html_to_sectioned_text

MONGO_CLIENT: typing.Any = None


def connect() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    """ Connect to the local MongoDB server. Return a handle of tuixue database."""
    global MONGO_CLIENT
    if MONGO_CLIENT is None:  # keep one alive connection will be enough (and preferred)
        MONGO_CLIENT = motor.motor_asyncio.AsyncIOMotorClient(host=MONGO_CONFIG.host, port=MONGO_CONFIG.port)

    database = MONGO_CLIENT[MONGO_CONFIG.database]
    return database


def get_collection(collection_name: str) -> motor.motor_asyncio.AsyncIOMotorCollection:
    """ Return a MongoDB collection from the established client database."""
    db = connect()
    return db.get_collection(collection_name)


class TopcoderMongo:
    """ MongoDB database operation using Motor"""
    challenge = get_collection('challenge')
    project = get_collection('project')
    regex = re.compile(r'(?P<year>[\d]{4})_(?P<page>[\d]{1,2})_challenge_lst\.json')

    def __init__(self, logger: logging.Logger, input_dir: pathlib.Path) -> None:
        self.logger = logger
        self.input_dir = input_dir

    async def initiate_database(self) -> None:
        start_initiation = datetime.now()
        await self.challenge.drop()
        await self.write_challenges()
        await self.write_projects()
        end_initiation = datetime.now()
        self.logger.info(
            'Initiation starts at %s ends at %s',
            start_initiation.strftime('%H:%M:%S'),
            end_initiation.strftime('%H:%M:%S'),
        )
        self.logger.info(
            'Initiation finished, total time used: %d seconds',
            (end_initiation - start_initiation).total_seconds()
        )

    async def write_projects(self) -> None:
        """ Methods that extract project info from challenges."""
        count_by_track_cond = {
            f'num_of_challenge_{track}': {
                '$sum': {'$toInt': {'$eq': ['$track', track]}}
            } for track in TRACK
        }

        completion_count_by_track_cond = {
            f'num_of_completed_challenge_{track}': {
                '$sum': {'$toInt': {'$and': [{'$eq': ['$track', track]}, {'$eq': ['$status', 'Completed']}]}}
            } for track in TRACK
        }

        query = [
            {
                '$group': {
                    '_id': '$project_id',
                    'id': {'$first': '$project_id'},
                    'challenge_lst': {
                        '$push': {
                            'id': '$id',
                            'start_date': '$start_date',
                            'end_date': '$end_date',
                            'track': '$track',
                            'type': '$type',
                            'status': '$status',
                        },
                    },
                    'start_date': {'$min': '$start_date'},
                    'end_date': {'$max': '$end_date'},
                    'num_of_challenge_Total': {'$sum': 1},
                    **count_by_track_cond,
                    **completion_count_by_track_cond,
                    'tracks': {'$addToSet': '$track'},
                    'types': {'$addToSet': '$type'},
                },
            },
            {
                '$set': {
                    'duration': {
                        '$toInt': {
                            '$divide': [
                                {'$subtract': ['$end_date', '$start_date']},
                                24 * 60 * 60 * 1000
                            ],
                        },
                    },
                    'num_of_challenge': [
                        {'track': track, 'count': f'$num_of_challenge_{track}'} for track in TRACK + ['Total']
                    ],
                    'completion_ratio': [
                        {
                            'track': track,
                            'ratio': {
                                '$divide': [
                                    f'$num_of_completed_challenge_{track}',
                                    {'$max': [f'$num_of_challenge_{track}', 1]},
                                ]
                            },
                        } for track in TRACK
                    ]
                },
            },
            {
                '$project': {
                    '_id': False,
                    **{f'num_of_challenge_{track}': False for track in TRACK + ['Total']},
                    **{f'num_of_completed_challenge_{track}': False for track in TRACK},
                },
            },
        ]

        self.logger.info('Creating project data from challenge data...')

        project_data = []
        async for doc in self.challenge.aggregate(query):
            self.logger.debug(
                'Project %s | number of challenges: %d',
                str(doc['id']),
                doc['num_of_challenge'][-1]['count']
            )
            project_data.append(doc)

        await self.project.drop()
        await self.project.insert_many(project_data)

    async def write_challenges(self) -> None:
        """ Methods for inserting all of the fetch challenges. (Of course we pre-process it before inserting ;-)"""
        coro_queue = [
            asyncio.create_task(
                self.write_challenge_year_page(challenge_lst_file),
                name='InsertChallenges-year-{}-page-{}'.format(
                    *map(int, self.regex.match(challenge_lst_file.name).groups())
                ),
            ) for challenge_lst_file in self.input_dir.glob('*_challenge_lst.json')
        ]

        await asyncio.gather(*coro_queue)

    async def write_challenge_year_page(self, challenge_lst_file: pathlib.Path) -> None:
        year, page = map(int, self.regex.match(challenge_lst_file.name).groups())
        self.logger.info('Year %d page %d | Inserting', year, page)

        challenge_lst = []
        with open(challenge_lst_file) as f:
            challenge_lst = convert_datetime_json_value(snake_case_json_key(json.load(f)))

        for challenge in challenge_lst:
            if 'description' in challenge and 'description_format' in challenge:
                challenge['processed_description'] = html_to_sectioned_text(
                    challenge['description']
                    if challenge['description_format'] == 'HTML' else
                    markdown.markdown(challenge['description'])
                )

            if challenge['num_of_registrants'] > 0:
                with open(self.input_dir / '{}_{}_{}_registrant_lst.json'.format(year, page, challenge['id'])) as f:
                    challenge['registrant_lst'] = convert_datetime_json_value(snake_case_json_key(json.load(f)))
                    self.logger.debug(
                        'Year %d page %d challenge %s | Read registrant list::%d',
                        year,
                        page,
                        challenge['id'],
                        len(challenge['registrant_lst']),
                    )

        await self.challenge.insert_many(challenge_lst)
        self.logger.info('Year %d page %d | Inserted %d challenges into mongo', year, page, len(challenge_lst))

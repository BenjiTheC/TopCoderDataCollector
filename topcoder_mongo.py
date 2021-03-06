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
from asyncio import AbstractEventLoop
from concurrent.futures import ThreadPoolExecutor

from url import URL
from static_var import MONGO_CONFIG, TRACK
from util import snake_case_json_key, convert_datetime_json_value, html_to_sectioned_text
from topcoder_nlp import compute_section_text_similarity

MONGO_CLIENT: typing.Any = None


def construct_mongo_url():
    """ Construct URL for connecting to MongoDB."""
    url = URL('')
    if MONGO_CONFIG.host in ['127.0.0.1', 'localhost']:
        url.scheme = 'mongodb'
        url.netloc = f'{MONGO_CONFIG.host}:{MONGO_CONFIG.port}'
    else:
        url.scheme = 'mongodb+srv'
        url.netloc = f'{MONGO_CONFIG.username}:{MONGO_CONFIG.password}@{MONGO_CONFIG.host}'
        url.path = MONGO_CONFIG.database
        url.query_param.set('retryWrites', 'true')
        url.query_param.set('w', 'majority')
    return str(url)

def connect() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    """ Connect to the local MongoDB server. Return a handle of tuixue database."""
    global MONGO_CLIENT
    if MONGO_CLIENT is None:  # keep one alive connection will be enough (and preferred)
        MONGO_CLIENT = motor.motor_asyncio.AsyncIOMotorClient(construct_mongo_url())

    database = MONGO_CLIENT[MONGO_CONFIG.database]
    return database


def get_collection(collection_name: str) -> motor.motor_asyncio.AsyncIOMotorCollection:
    """ Return a MongoDB collection from the established client database."""
    db = connect()
    return db.get_collection(collection_name)


class ProjectSection(typing.TypedDict):
    """ Type def of project in section text similarity computation."""
    project_id: int
    section_name: str
    section_texts: list[str]
    section_freq: int


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
        await self.project.drop()
        await self.write_challenges()
        await self.write_projects()
        await self.write_project_section_sim()
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
            {'$match': {'project_id': {'$ne': None}}},
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
                    'id': {'$toInt': '$id'},
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

    async def write_project_section_sim(self) -> None:
        """ Calculate project section text similarity.
            Criteria for section similarity comparison:
            1. The length of text in a section should be greater than 0.
            2. The grouped section texts shoud contain more than 1 document (i.e `len(section_texts) > 1`).
        """
        self.logger.info('Computing section text similarity for projects...')
        query = [
            {'$match': {'project_id': {'$ne': None}}},
            {
                '$project': {
                    'project_id': {'$toInt': '$project_id'},
                    'processed_description': {
                        '$filter': {
                            'input': '$processed_description',
                            'as': 'desc',
                            'cond': {'$gt': [{'$strLenCP': '$$desc.text'}, 0]},
                        },
                    },
                },
            },
            {'$unwind': '$processed_description'},
            {
                '$group': {
                    '_id': {'project_id': '$project_id', 'section_name': '$processed_description.name'},
                    'section_texts': {'$push': '$processed_description.text'},
                },
            },
            {
                '$replaceRoot': {
                    'newRoot': {
                        '$mergeObjects': [
                            '$_id',
                            {'section_texts': '$section_texts', 'section_freq': {'$size': '$section_texts'}},
                        ],
                    },
                },
            },
            {'$match': {'$expr': {
                '$and': [{'$gt': ['$section_freq', 1]}, {'$lte': [{'$strLenCP': '$section_name'}, 128]}]
            }}},
        ]

        with ThreadPoolExecutor(max_workers=2 ** 10) as executor:  # This is computationally super expensive
            await asyncio.gather(*[
                asyncio.create_task(
                    self.compute_project_section_sim(project, executor),
                    name='ProjSec-{}-{}'.format(project['project_id'], project['section_name']),
                ) async for project in self.challenge.aggregate(query)]
            )

    async def compute_project_section_sim(
        self,
        project: ProjectSection,
        executor: ThreadPoolExecutor,
    ):
        """ Compute the section text similarity."""
        loop: AbstractEventLoop = asyncio.get_running_loop()

        self.logger.debug('Computing project %d section %s', project['project_id'], project['section_name'])

        section_sim = await loop.run_in_executor(executor, compute_section_text_similarity, project['section_texts'])
        section_expr = {
            'name': project['section_name'],
            'similarity': section_sim,
            'frequency': {'$divide': [project['section_freq'], {'$max': '$num_of_challenge.count'}]},  # a little hack here
        }
        await self.project.update_one(
            {'id': project['project_id']},
            [
                {
                    '$set': {
                        'section_similarity': {
                            '$concatArrays':[{'$ifNull': ['$section_similarity', []]}, [section_expr]],
                        },
                    },
                },
            ],
        )

        self.logger.info('Updated project %s section %s sim %f', project['project_id'], project['section_name'], section_sim)

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

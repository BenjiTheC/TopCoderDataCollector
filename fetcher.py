""" Topcoder data collector using http://api.topcoder.com/v5"""
import re
import json
import logging
import asyncio
import aiohttp
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone
from util import datetime_to_isoformat
from static_var import CHALLENGE_URL, RESOURCE_URL, AUTH_TOKEN, Status
from url import URL


class Fetcher:
    """ Data Collector."""
    auth_header = AUTH_TOKEN and {'Authorization': AUTH_TOKEN}

    @staticmethod
    def construct_url_by_year(since: datetime, to: datetime) -> list[tuple[int, URL]]:
        """ Divide the time range for search by year.
            This is for the purpose of limit the number of total challenges from search results.
        """
        if since.year == to.year:
            url = CHALLENGE_URL.copy()
            url.query_param.set('endDateStart', datetime_to_isoformat(since))
            url.query_param.set('startDateEnd', datetime_to_isoformat(to))
            return [(since.year, url)]

        time_frame = []
        for year in range(since.year, to.year + 1):
            url = CHALLENGE_URL.copy()
            year_start = datetime(year, 1, 1, 0, 0, 0, 0, timezone.utc)
            year_end = datetime(year, 12, 31, 23, 59, 59, 999999, timezone.utc)

            if year == since.year:
                url.query_param.set('endDateStart',  datetime_to_isoformat(since))
                url.query_param.set('endDateEnd', datetime_to_isoformat(year_end))
            elif year == to.year:
                url.query_param.set('endDateStart', datetime_to_isoformat(year_start))
                url.query_param.set('startDateEnd', datetime_to_isoformat(to))
            else:
                url.query_param.set('endDateStart', datetime_to_isoformat(year_start))
                url.query_param.set('endDateEnd', datetime_to_isoformat(year_end))

            time_frame.append((year, url))

        return time_frame

    @staticmethod
    def update_base_url(status: Status):
        """ Update challenge api URL based on command line input"""
        if status == Status.ALL:
            CHALLENGE_URL.query_param.delete('status')
        else:
            CHALLENGE_URL.query_param.set('status', status.value)

    def __init__(
        self,
        status: Status,
        since: datetime,
        to: datetime,
        with_registrant: bool,
        output_dir: Path,
        logger: logging.Logger,
    ) -> None:
        self.status: str = status.value
        self.since = since
        self.to = to
        self.with_registrant = with_registrant
        self.output_dir = output_dir
        self.logger = logger

        self.metadata = defaultdict(dict)

        self.update_base_url(status)
        self.url_by_year = self.construct_url_by_year(since, to)

        self.logger.info('Fetcher initiated')
        self.logger.info('Fetch status: %s', self.status)
        self.logger.info('Fetch time interval: %s - %s', since.strftime('%Y-%m-%d'), to.strftime('%Y-%m-%d'))
        self.logger.debug('since param: %s', since)
        self.logger.debug('to param: %s', to)

    def construct_fetch_challenge_param(self) -> list[tuple[int, URL, int]]:
        """ Construct the parameters for fetching the challenges from the metadata (for the first time)."""
        param = []
        for year, metadata in self.metadata.items():
            for page in range(1, metadata['total_pages'] + 1):
                url: URL = metadata['url'].copy()
                url.query_param.set('page', page)
                param.append((year, url, page))

        return param

    def construct_registrant_param(self) -> list[tuple[int, int, str, URL]]:
        """ Construct the parameters for fetching the challenge registrant from
            fetched challenge (for the first time).
        """
        regex = re.compile(r'(?P<year>[\d]{4})_(?P<page>[\d]{1,2})_challenge_lst\.json')
        registrant_params: list[tuple[int, int, str, URL]] = []

        for challenge_lst_file in self.output_dir.glob('*_challenge_lst.json'):
            year, page = map(int, regex.match(challenge_lst_file.name).groups())
            with open(challenge_lst_file) as f:
                for challenge in json.load(f):
                    if challenge['numOfRegistrants'] != 0:
                        url = RESOURCE_URL.copy()
                        url.query_param.set('challengeId', challenge['id'])
                        registrant_params.append((year, page, challenge['id'], url))

                        self.logger.debug(
                            'Year %d page %d cha %s | number of registrants: %d',
                            year, page, challenge['id'], challenge['numOfRegistrants']
                        )

        self.logger.debug('Number of registrant params: %d', len(registrant_params))

        return registrant_params

    async def fetch(self) -> None:
        """ Entrance of async fetching."""

        async with aiohttp.ClientSession(headers=self.auth_header, raise_for_status=True) as session:
            await self.fetch_meta(session)
            await self.fetch_challenges(session)
            await self.fetch_registrants(session)

    async def fetch_meta(self, session: aiohttp.ClientSession) -> None:
        """ Only interpret challenge header to the total and pages."""
        self.logger.info('Fetching Metadata...')

        async def fetch_meta_by_year(session: aiohttp.ClientSession, year: int, url: URL) -> None:
            """ This function is only used in `fetch_meta` and relatively short. So I write it inside."""
            self.logger.debug('Year %d | %s', year, url)

            try:
                async with session.head(f'{url}') as response:
                    self.metadata[year]['total_pages'] = int(response.headers['X-Total-Pages'])
                    self.metadata[year]['url'] = url

                    self.logger.info(
                        'Year %d | Total pages %s | Total number of challenges %s',
                        year,
                        response.headers['X-Total-Pages'],
                        response.headers['X-Total']
                    )

                    return int(response.headers['X-Total'])
            except aiohttp.ClientResponseError:
                logging.error('Year %d | Fetching failed', year)
                return 0

        coro_queue = [
            asyncio.create_task(
                fetch_meta_by_year(session, year, url),
                name=f'FetchMeta-Year[{year}]',
            ) for year, url in self.url_by_year
        ]
        total_cha_by_year = await asyncio.gather(*coro_queue)
        self.logger.info('Total number of challenges: %d', sum(total_cha_by_year))

    async def fetch_challenges(self, session: aiohttp.ClientSession) -> list[tuple[str, int, URL]]:
        """ Call async fetch method to fetch all challenges"""
        challenge_params, unfetch_challenge_params = [], self.construct_fetch_challenge_param()
        fetch_rnd = 0

        while len(unfetch_challenge_params) > 0:
            self.logger.info('Challenges Fetch round %d | Unfetched %d', fetch_rnd, len(unfetch_challenge_params))
            challenge_params, unfetch_challenge_params = unfetch_challenge_params, []

            coro_queue = [
                asyncio.create_task(
                    self.fetch_challenge_year_page(session, year, url, page, unfetch_challenge_params),
                    name=f'FetchChallenges-year-{year}-page-{page}-round-{fetch_rnd}',
                ) for year, url, page in challenge_params
            ]
            await asyncio.gather(*coro_queue)

            fetch_rnd += 1

    async def fetch_challenge_year_page(
        self,
        session: aiohttp.ClientSession,
        year: int,
        url: URL,
        page: int,
        failed_fetch: list
    ) -> None:
        """ Fetch a singe page of challengess (100 challenges per page except for the last page)"""
        try:
            async with session.get(f'{url}') as response:
                challenge_lst = await response.json()

        except aiohttp.ClientResponseError:
            failed_fetch.append((year, url, page))
            self.logger.error('Year %d page %d | Fetching failed', year, page)
        except asyncio.TimeoutError:
            failed_fetch.append((year, url, page))
            self.logger.error('Year %d page %d | Fetching timeout', year, page)
        else:
            self.logger.info(
                'Year %d page %d | challenge list length %d | byte size %d',
                year, page, len(challenge_lst), len(json.dumps(challenge_lst).encode('utf-8'))
            )

            with open(self.output_dir / f'{year}_{page}_challenge_lst.json', 'w') as f:
                json.dump(challenge_lst, f)

    async def fetch_registrants(self, session: aiohttp.ClientSession) -> None:
        """ Insert regsitrant list into challenge object"""
        registrant_params, unfetch_registrant_params = [], self.construct_registrant_param()
        fetch_rnd = 0

        while len(unfetch_registrant_params) > 0:
            self.logger.debug('Registrants Fetch round %d | Unfetched %d', fetch_rnd, len(unfetch_registrant_params))
            registrant_params, unfetch_registrant_params = unfetch_registrant_params, []

            coro_queue = [
                asyncio.create_task(
                    self.fetch_registrant_year_page(session, year, page, challenge_id, url, unfetch_registrant_params),
                    name=f'FetchRegistrant-year-{year}-page-{page}-cha-{challenge_id}-round-{fetch_rnd}'
                ) for year, page, challenge_id, url in registrant_params
            ]
            await asyncio.gather(*coro_queue)

            fetch_rnd += 1

    async def fetch_registrant_year_page(
        self,
        session: aiohttp.ClientSession,
        year: int,
        page: int,
        challenge_id: str,
        url: URL,
        failed_fetch: list,
    ) -> None:
        """ Fetch single challenge registrant"""
        try:
            async with session.get(f'{url}') as response:
                registrant_lst = await response.json()

                self.logger.info(
                    'Year %d page %d challenge %s | registrant list length %d',
                    year, page, challenge_id, len(registrant_lst)
                )

        except aiohttp.ClientResponseError:
            failed_fetch.append((year, page, challenge_id, url))
            self.logger.error('Year %d page %d challenge %s | Fetching failed', year, page, challenge_id)
        except asyncio.TimeoutError:
            failed_fetch.append((year, page, challenge_id, url))
            self.logger.error('Year %d page %d challenge %s | Fetching timeout', year, page, challenge_id)
        else:
            with open(self.output_dir / f'{year}_{page}_{challenge_id}_registrant_lst.json', 'w') as f:
                json.dump(registrant_lst, f)

    async def fetch_member_by_handle_lower(self, session: aiohttp.ClientSession):
        """ Fetch user by handleLower."""

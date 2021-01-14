""" Topcoder data collector using http://api.topcoder.com/v5"""
import math
import json
import asyncio
import aiohttp
from pathlib import Path
from pprint import pprint
from collections import defaultdict
from datetime import datetime, timezone
from util import datetime_to_isoformat
from static_var import CHALLENGE_URL, CHALLENGE_URL_V4, AUTH_TOKEN, Status
from url import URL


BATCH = 10
SLEEP = 1.5


class Fetcher:
    """ Data Collector."""
    auth_header = AUTH_TOKEN and {'Authorization': AUTH_TOKEN}
    record_store = {'no_legacy_id': []}

    @staticmethod
    def split_time_frame(since: datetime, to: datetime) -> list[tuple[int, datetime, datetime]]:
        """ divide the time range for search by year."""
        if since.year == to.year:
            return [(since, to)]

        time_frame = []
        for year in range(since.year, to.year + 1):
            if year == since.year:
                time_frame.append(
                    (year, since, datetime(year, 12, 31, 23, 59, 59, 999999, timezone.utc))
                )
            elif year == to.year:
                time_frame.append(
                    (year, datetime(year, 1, 1, 0, 0, 0, 0, timezone.utc), to)
                )
            else:
                time_frame.append(
                    (
                        year,
                        datetime(year, 1, 1, 0, 0, 0, 0, timezone.utc),
                        datetime(year, 12, 31, 23, 59, 59, 999999, timezone.utc)
                    )
                )

        return time_frame

    @staticmethod
    def update_base_url(status: Status):
        """ Update challenge api URL based on command line input"""
        if status == Status.ALL:
            CHALLENGE_URL.query_param.delete('status')
        else:
            CHALLENGE_URL.query_param.set('status', status.value)

    def __init__(self, status: Status, since: datetime, to: datetime, with_registrant: bool, output_dir: Path) -> None:
        self.status: str = status.value
        self.time_frame = self.split_time_frame(since, to)
        self.with_registrant = with_registrant
        self.output_dir = output_dir

        self.metadata = defaultdict(dict)
        self.unfetched_challenge_params = []

        self.update_base_url(status)

    def construct_fetch_challenge_param(self) -> list[tuple[int, URL, int]]:
        """ Construct the parameters for fetching the challenges (for the first time)."""
        param = []
        for year, metadata in self.metadata.items():
            for page in range(1, metadata['total_pages'] + 1):
                url: URL = metadata['url'].copy()
                url.query_param.set('page', page)
                param.append((year, url, page))

        return param

    def construct_fetch_registrant_param(self, challenge_lst: list[dict]) -> list[tuple[str, int, URL]]:
        """ Construct the registrant parameters for challenge v4 api"""

        def build_cha_v4_url(cha_legacy_id):
            url = CHALLENGE_URL_V4.copy()
            url.path = f'{url.path}/{cha_legacy_id}'
            return url

        param = []
        for cha in challenge_lst:
            if 'legacyId' not in cha:
                self.record_store['no_legacy_id'].append((cha['id'], cha['numOfRegistrants']))

            if cha['numOfRegistrants'] > 0:
                param.append((cha['id'], cha['legacyId'], build_cha_v4_url(cha['legacyId'])))

        return param

    async def fetch(self) -> None:
        """ Entrance of async fetching."""
        await self.fetch_meta()

        async with aiohttp.ClientSession(headers=self.auth_header) as session:
            registrants_params = await self.fetch_all_challenges(session)
            print(f'\nFetched {len(registrants_params)} in total')

            if self.with_registrant:
                await self.fetch_all_registrant(session, registrants_params)

    async def fetch_meta(self) -> None:
        """ Only interpret challenge header to the total and pages."""

        async def fetch_single_meta(session: aiohttp.ClientSession, year: int, since: datetime, to: datetime) -> None:
            url = CHALLENGE_URL.copy()
            url.query_param.set('endDateStart', datetime_to_isoformat(since))
            url.query_param.set('startDateEnd', datetime_to_isoformat(to))
            self.metadata[year]['url'] = url

            try:
                async with session.head(f'{url}') as response:
                    self.metadata[year]['total_challenges'] = int(response.headers['X-Total'])
                    self.metadata[year]['total_pages'] = int(response.headers['X-Total-Pages'])
                    print(
                        'Year {} | X-Total-pages: {} | X-Total: {}'.format(
                            year, response.headers['X-Total-Pages'], response.headers['X-Total']
                        )
                    )
            except aiohttp.ClientResponseError:
                print(f'Fetching the meta for year {since.year} failed.')

        async with aiohttp.ClientSession(headers=self.auth_header, raise_for_status=True) as session:
            coro_queue = [
                asyncio.create_task(
                    fetch_single_meta(session, year, since, to),
                    name=f'FetchMeta-Year[{year}]',
                ) for year, since, to in self.time_frame
            ]
            await asyncio.gather(*coro_queue)

    async def fetch_all_challenges(self, session: aiohttp.ClientSession) -> list[tuple[str, int, URL]]:
        """ Call async fetch method to fetch all challenges"""
        registrant_params = []
        self.unfetched_challenge_params = self.construct_fetch_challenge_param()

        fetch_rnd = 0
        while len(self.unfetched_challenge_params) > 0:
            print(f'Fetch round {fetch_rnd}')

            challenge_params = self.unfetched_challenge_params
            self.unfetched_challenge_params = []

            coro_queue = [asyncio.create_task(
                self.fetch_challenge(session, year, url, page),
                name=f'FetchChallenges-year-{year}-page-{page}-round-{fetch_rnd}',
            ) for year, url, page in challenge_params]

            registrant_params.extend([param for params in await asyncio.gather(*coro_queue) for param in params])
            fetch_rnd += 1

        return registrant_params

    async def fetch_challenge(self, session: aiohttp.ClientSession, year: int, url: URL, page: int) -> None:
        """ Fetch a singe page of challengess (100 challenges per page except for the last page)"""
        try:
            async with session.get(f'{url}') as response:
                challenge_lst = await response.json()

                with open(self.output_dir / f'{year}_{page}_challenge_lst.json', 'w') as fjson:
                    json.dump(challenge_lst, fjson)

                print(
                    (
                        f'Year {year} | page {page} | challenge list length: '
                        f'{len(challenge_lst)} :: {len(json.dumps(challenge_lst))}'
                    )
                )

                return self.construct_fetch_registrant_param(challenge_lst)

        except aiohttp.ClientResponseError:
            self.unfetched_challenge_params.append((year, url, page))
            print(f'Year {year} | page {page} | Failed fetch')
            return []

    async def fetch_all_registrant(self, session, registrant_params: list[tuple[str, int, URL]]) -> None:
        """ Use topcoder challenge v4 api to fetch all registrants.
            We should focus on finding way to use v5 instead, currently
            Topcoder.com can should registrants on their web apps.
        """

        rounds = math.ceil(len(registrant_params) / BATCH)
        for rnd in range(rounds):
            sleep_sec = rnd and SLEEP
            slice_start, slice_end = BATCH * rnd, BATCH * (rnd + 1)
            print(f'Challenge fetching: {slice_start} - {slice_end}. Sleep for {sleep_sec} seconds first...')
            await asyncio.sleep(sleep_sec)

            coro_queue = [
                asyncio.create_task(
                    self.fetch_registrant(session, cha_id, legacy_id, url),
                    name=f'FetchRegistrant-{cha_id}-{legacy_id}'
                ) for cha_id, legacy_id, url in registrant_params[slice_start: slice_end]
            ]
            await asyncio.gather(*coro_queue)

            while len(self.unfetched_challenge_params) > 0:
                print(
                    (
                        f'Challenge re-fetchig: {slice_start} - {slice_end}. '
                        f'{len(self.unfetched_challenge_params)} in total...'
                    )
                )
                await asyncio.sleep(SLEEP)
                params = self.unfetched_challenge_params
                self.unfetched_challenge_params = []

                coro_queue = [
                    asyncio.create_task(
                        self.fetch_registrant(session, cha_id, legacy_id, url),
                        name=f'Re-FetchRegistrant-{cha_id}-{legacy_id}'
                    ) for cha_id, legacy_id, url in params
                ]
                await asyncio.gather(*coro_queue)

    async def fetch_registrant(self, session: aiohttp.ClientSession, cha_id: str, legacy_id: int, url: URL) -> None:
        """ Fetch data of registrant by challenge."""
        try:
            async with session.get(f'{url}') as response:
                res_json = await response.json()
                challenge = res_json['result']['content']

                if not challenge or not isinstance(challenge, dict):
                    print(f'Challenge {cha_id}/{legacy_id} | Unexpected error ', end='')
                    pprint(res_json['result'])
                    return

                registrants = challenge['registrants']
                print(f'Challenge {cha_id}/{legacy_id} | fetched regstirants {len(registrants)}')
        except aiohttp.ClientResponseError:
            self.unfetched_challenge_params.append((cha_id, legacy_id, url))
            print(f'Challenge {cha_id}/{legacy_id} | fetch failed.')

    async def fetch_member_by_handle_lower(self, session: aiohttp.ClientSession):
        """ Fetch user by handleLower."""

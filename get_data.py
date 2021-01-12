""" Fetch the challenges data."""

import os
import json
import time
import requests
from dotenv import load_dotenv
from util import append_lst_to_json, get_sorted_filenames, show_progress
load_dotenv()

API_BASE_URL = os.getenv('API_BASE_URL')
DATA_STORAGE_PATH = os.getenv('DATA_STORAGE_PATH')
SCRAPED_DATA_PATH = os.getenv('SCRAPED_DATA_PATH')

DATA_PATH = os.path.join(os.curdir, DATA_STORAGE_PATH, SCRAPED_DATA_PATH) # Ensure the path format is cross-platform compatible

WAIT_SECONDS = 1

def get_challenges(amount=500, start_offset=0):
    """ Get the gievn `amount` of challenges from API, with `limit` of records 
        per request.
    """
    url = f'{API_BASE_URL}/v4/challenges'

    file_idx = -1 
    for idx, offset in enumerate(range(start_offset, start_offset + amount, 50)):
        if idx % 2 == 0:
            file_idx += 1

        params = {
            'filter': 'status=COMPLETED',
            'limit': 50,
            'offset': offset
        }
        res = requests.get(url, params=params)

        if res.ok:
            res_json = res.json()
            challenges_lst = res_json['result']['content']
            append_lst_to_json(challenges_lst, os.path.join(DATA_PATH, f'challenges_overview_{file_idx}.json'))
            print(f'Fetched {len(challenges_lst)} challenges, offset={offset}, writing into challenges_overview_{file_idx}.json')
        else:
            print(f'Fethcing failed with status code: {res.status_code}')

        time.sleep(WAIT_SECONDS)

def get_challenge_detail():
    """ Fetch the detail of challenges."""
    challenge_id_dct = {} 
    for file_idx, file_name in enumerate(get_sorted_filenames(DATA_PATH, 'challenges_overview_*.json')):
        with open(file_name) as fjson:
            challenge_id_dct[file_idx] = [challenge['id'] for challenge in json.load(fjson)]

    print(f'Fetching details of {sum([len(l) for l in challenge_id_dct.values()])} challenges...')

    for file_idx, challenge_id_lst in challenge_id_dct.items():
        for idx, challenge_id in enumerate(challenge_id_lst, start=1):
            url = f'{API_BASE_URL}/v4/challenges/{challenge_id}'
            res = requests.get(url)

            if res.ok:
                res_json = res.json()
                challenge_detail = res_json['result']['content']
                append_lst_to_json([challenge_detail], os.path.join(DATA_PATH, f'challenges_detail_{file_idx}.json'))

                show_progress(idx, len(challenge_id_lst), prefix=f'Fetched detail of challenge {challenge_id}', suffix=f'==> challenges_detail_{file_idx}.json')
            else:
                show_progress(idx, len(challenge_id_lst), prefix=f'Fetching {challenge_id} failed: code {res.status_code}', suffix=f'==> challenges_detail_{file_idx}.json')

            time.sleep(WAIT_SECONDS)

def get_users():
    """ Fetch the data of users."""
    registrant_handles = set()
    for file_name in get_sorted_filenames(DATA_PATH, 'challenges_detail_*.json'):
        with open(file_name) as fjson:
            registrant_handles.update(str(registrant['handle']).lower() for challenge in json.load(fjson) if 'registrants' in challenge for registrant in challenge['registrants'])

    print(f'Fetching profiles of {len(registrant_handles)} users...')

    registrant_handles = sorted(registrant_handles)
    excluded_fields = ('userId', 'handle', 'handleLower', 'createdAt', 'updatedAt', 'createdBy', 'updatedBy')
    chunk_size = 100
    for file_idx, start_idx in enumerate(range(0, len(registrant_handles), chunk_size)):
        for idx, handle in enumerate(registrant_handles[start_idx: start_idx + chunk_size], start=1):

            url = f'{API_BASE_URL}/v3/members/{handle}'
            res_user = requests.get(url)

            if res_user.ok:
                res_user_json = res_user.json()
                user_profile = res_user_json['result']['content']
                print('Fetched basic profile of user {0} | {1}/{2}'.format(handle, start_idx + idx, len(registrant_handles)))

                res_user_stats = requests.get(f'{url}/stats')
                if res_user_stats.ok:
                    user_data = res_user_stats.json()['result']['content']
                    if type(user_data) is not list:
                        print('\t* User stats data type is problematic, skipping')
                        continue

                    user_stats = user_data[0] # the 'content' field is a list with only 1 element - user stats
                    user_profile.update({k: v for k, v in user_stats.items() if k not in excluded_fields}) # prevent overwriting of duplicate fields
                    print('\t* Fetched user stats: {0} wins in {1} challenges'.format(user_stats['wins'], user_stats['challenges']))
                else:
                    print(f'\t* Fetching user stats failed: status code {res_user_stats.status_code}')
                    print(res_user_stats.text)

                res_user_skills = requests.get(f'{url}/skills')
                if res_user_skills.ok:
                    user_skills = res_user_skills.json()['result']['content']['skills']
                    user_profile.update(skills=user_skills)
                    print(f'\t* Fetched user skills: {len(user_skills)} in total')
                else:
                    print(f'\t* Feteching user skills failed: status code {res_user_stats.status_code}')
                    print(res_user_skills.text)
                
                append_lst_to_json([user_profile], os.path.join(DATA_PATH, f'users_profile_{file_idx}.json'))
            else:
                print(f'Fetching user profiled failed: {handle} | {start_idx + idx}/{len(registrant_handles)}')

            time.sleep(WAIT_SECONDS)

if __name__ == '__main__':
    # get_challenges()
    # get_challenge_detail()
    get_users()

""" Fetch the challenges data."""

import os
import json
import time
import requests
from dotenv import load_dotenv
from util import append_lst_to_json
load_dotenv()

API_BASE_URL = os.getenv('API_BASE_URL')
PROXIES = {
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890',
}

def get_challenges(amount=500, start_offset=0):
    """ Get the gievn `amount` of challenges from API, with `limit` of records 
        per request.
    """
    url = f'{API_BASE_URL}/v4/challenges'
    
    for offset in range(start_offset, start_offset + amount, 50):
        params = {
            'filter': 'status=COMPLETED',
            'limit': 50,
            'offset': offset
        }
        res = requests.get(url, params=params)

        if res.status_code == 200:
            res_json = res.json()
            challenges_lst = res_json['result']['content']
            print(f'Fetched {len(challenges_lst)} challenges, offset={offset}')
            append_lst_to_json(challenges_lst, './data/challenges_overview.json')
        else:
            print(f'Request failed, status code: {res.status_code}')
            print(res.json())

        time.sleep(5)

def get_challenge_detail():
    """ Fetch the detail of challenges."""
    with open('./data/challenges_overview.json') as fjson:
        challenge_id_lst = [challenge['id'] for challenge in json.load(fjson)]

    print(f'Fetching details of {len(challenge_id_lst)} challenges...')
    for idx, challenge_id in enumerate(challenge_id_lst, start=1):
        url = f'{API_BASE_URL}/v4/challenges/{challenge_id}'
        res = requests.get(url)

        if res.ok:
            res_json = res.json()
            challenge_detail = res_json['result']['content']
            print(f'Fetched detail of challenge ID: {challenge_id} | {idx}/{len(challenge_id_lst)}')
            append_lst_to_json([challenge_detail], './data/challenges_detail.json')
        else:
            print(f'Request failed, status code: {res.status_code}')
            print(res.json())

        time.sleep(3)

def get_users():
    """ Fetch the data of users."""
    with open('./data/challenges_detail.json') as fjson:
        registrant_handles = {str(registrant['handle']).lower() for challenge in json.load(fjson) if 'registrants' in challenge for registrant in challenge['registrants']}

    print(f'Fetching profiles of {len(registrant_handles)} users...')

    excluded_fields = ('userId', 'handle', 'handleLower', 'createdAt', 'updatedAt', 'createdBy', 'updatedBy')
    for idx, handle in enumerate(sorted(registrant_handles), start=1):
        url = f'{API_BASE_URL}/v3/members/{handle}'
        res_user = requests.get(url)

        if res_user.ok:
            res_user_json = res_user.json()
            user_profile = res_user_json['result']['content']
            print('Fetched basic profile of user {0} | {1}/{2}'.format(handle, idx, len(registrant_handles)))

            res_user_stats = requests.get(f'{url}/stats')
            if res_user_stats.ok:
                user_stats = res_user_stats.json()['result']['content'][0] # the 'content' field is a list with only 1 element - user stats
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
            
            append_lst_to_json([user_profile], './data/users_profile.json')
            # time.sleep(3)
        else:
            print(f'Fetching user profiled failed: {handle} | {idx}/{len(registrant_handles)}')

if __name__ == '__main__':
    # get_challenges(amount=500)
    # get_challenge_detail()
    # get_users()

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

if __name__ == '__main__':
    # get_challenges(amount=10000)
    get_challenge_detail()

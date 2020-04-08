""" Process fetched data and prepared for database operations."""

import os
import json
from glob import iglob
from dotenv import load_dotenv
from util import append_lst_to_json, parse_iso_dt, get_sorted_filenames, show_progress
load_dotenv()

DATA_STORAGE_PATH = os.getenv('DATA_STORAGE_PATH')
SCRAPED_DATA_PATH = os.path.join(os.curdir, DATA_STORAGE_PATH, os.getenv('SCRAPED_DATA_PATH'))
PROCESS_DATA_PATH = os.path.join(os.curdir, DATA_STORAGE_PATH, os.getenv('PROCESS_DATA_PATH'))

DATA_PATH = os.path.join(os.curdir, DATA_STORAGE_PATH, SCRAPED_DATA_PATH) # Ensure the path format is cross-platform compatible

def validate_challegens():
    """ Check whether the challenges_overview_*.json and challenges_detail_*.json
        are correspondant.
    """
    overview_files = get_sorted_filenames(SCRAPED_DATA_PATH, 'challenges_overview_*.json')
    detail_files = get_sorted_filenames(SCRAPED_DATA_PATH, 'challenges_detail_*.json')

    nonidentical_file_names = []

    print('Validating files...')
    for overview_fn, detail_fn in zip(overview_files, detail_files):
        with open(overview_fn) as foverview:
            overviews = json.load(foverview)
        with open(detail_fn) as fdetail:
            details = json.load(fdetail)

        is_identical = all([overview['id'] == detail['challengeId'] for overview, detail in zip(overviews, details)])

        if is_identical is not True:
            print(f'Found nonidentical data file: {os.path.split(overview_fn)[1]} | {os.path.split(detail_fn)[1]}')
            nonidentical_file_names.append((overview_fn, detail_fn))

    if len(nonidentical_file_names) == 0:
        return True, nonidentical_file_names
    else:
        return False, nonidentical_file_names

def unify_challenge_files(nonidentical_file_names):
    """ Unify the challenges data in overview and details for givenv files"""
    print('Unifying files...')
    for overview_fn, detail_fn in nonidentical_file_names:
        with open(overview_fn) as foverview:
            overviews = json.load(foverview)
        with open(detail_fn) as fdetail:
            details = json.load(fdetail)

        challenge_id_in_details = [detail['challengeId'] for detail in details] # no need to use set since I already know the ids will be unique
        unified_overviews = [overview for overview in overviews if overview['id'] in challenge_id_in_details]

        with open(overview_fn, 'w') as fwrite:
            json.dump(unified_overviews, fwrite, indent=4)

        print(f'Found {len(details)} challenges in detail file but {len(overviews)} in overview, deleted {len(overviews) - len(details)} useless challenge overivew.')

def extract_challenges_info():
    """ Extract needed challenges data from fetched challenge details."""
    overview_files = get_sorted_filenames(SCRAPED_DATA_PATH, 'challenges_overview_*.json')
    detail_files = get_sorted_filenames(SCRAPED_DATA_PATH, 'challenges_detail_*.json')

    intact_fields = (
        'challengeId',
        'projectId',
        'forumId',
        'track', # previous challengeCommunity, one of (DEVELOP, DESIGN, DATA_SCIENCE)
        'subTrack', # previous challengeType one of (DESIGN, DEVELOPMENT, SECURITY, PROCESS, TESTING_COMPETITION, SPECIFICATION, ARCHITECTURE, COMPONENT_PRODUCTION, BUG_HUNT, DEPLOYMENT, TEST_SUITES, ASSEMBLY_COMPETITION, UI_PROTOTYPE_COMPETITION, CONCEPTUALIZATION, RIA_BUILD_COMPETITION, RIA_COMPONENT_COMPETITION, TEST_SCENARIOS, SPEC_REVIEW, COPILOT_POSTING, CONTENT_CREATION, REPORTING, DEVELOP_MARATHON_MATCH, FIRST_2_FINISH, CODE, BANNERS_OR_ICONS, WEB_DESIGNS, WIREFRAMES, LOGO_DESIGN, PRINT_OR_PRESENTATION, WIDGET_OR_MOBILE_SCREEN_DESIGN, FRONT_END_FLASH, APPLICATION_FRONT_END_DESIGN, STUDIO_OTHER, IDEA_GENERATION, DESIGN_FIRST_2_FINISH, SRM, MARATHON_MATCH)
        'challengeTitle',
        'detailedRequirements',
        'finalSubmissionGuidelines',
        'totalPrize',
        'numberOfRegistrants',
        'numberOfSubmissions',
        'numberOfSubmitters'
    )

    join_fields = ('platforms', 'technologies')

    date_fields = ('registrationStartDate', 'registrationEndDate', 'submissionEndDate', 'postingDate')

    for file_name_idx, (overview_fn, detail_fn) in enumerate(zip(overview_files, detail_files)):

        with open(overview_fn) as fjson_overview:
            challenges_overview = json.load(fjson_overview)
        with open(detail_fn) as fjson_detail:
            challenges_detail = json.load(fjson_detail)

        challenges = [{**overview, **detail} for overview, detail in zip(challenges_overview, challenges_detail)] # merge overview and detail of challenges

        extracted_challenges = []
        for idx, challenge in enumerate(challenges, start=1):
            processed_challenge = {}

            for field in intact_fields:
                processed_challenge[field] = '' if field not in challenge else challenge[field]

            for field in join_fields:
                processed_challenge[field] = '' if field not in challenge else ', '.join([str(i) for i in challenge[field]])

            for field in date_fields:
                processed_challenge[field] = '' if field not in challenge else parse_iso_dt(challenge[field])

            processed_challenge['detailedRequirements'] = processed_challenge['detailedRequirements'].replace('\ufffd', ' ')
            processed_challenge['finalSubmissionGuidelines'] = processed_challenge['finalSubmissionGuidelines'].replace('\ufffd', ' ')

            extracted_challenges.append(processed_challenge)
            show_progress(idx, len(challenges), prefix=f'Extracting challenge info {file_name_idx + 1}/{len(overview_files)}')

        with open(os.path.join(PROCESS_DATA_PATH, f'challenges_info_{file_name_idx}.json'), 'w') as fjson:
            json.dump(extracted_challenges, fjson, indent=4)

def extract_challenge_registrant():
    """ Extract the registrants of each challenge."""
    detail_files = get_sorted_filenames(SCRAPED_DATA_PATH, 'challenges_detail_*.json')

    for file_name_idx, detail_fn in enumerate(detail_files):
        
        with open(os.path.join(detail_fn)) as fjson_detail:
            challenges = json.load(fjson_detail)

        challenge_registrant_relation = []
        for idx, challenge in enumerate(challenges, start=1):

            show_progress(idx, len(challenges), prefix=f'Extracting challenge registrant relations {file_name_idx + 1}/{len(detail_files)}')

            if 'registrants' in challenge:
                for registrant in challenge['registrants']:
                    relation = {
                        'challengeId': challenge['challengeId'],
                        'handle': str(registrant['handle']).lower(),
                        'registrationDate': parse_iso_dt(registrant['registrationDate']),
                        'submissionDate': '' if 'submissionDate' not in registrant else parse_iso_dt(registrant['submissionDate'])
                    }

                    challenge_registrant_relation.append(relation)

        with open(os.path.join(PROCESS_DATA_PATH, f'challenge_registrant_relation_{file_name_idx}.json'), 'w') as fjson:
            json.dump(challenge_registrant_relation, fjson, indent=4)

def extract_challenge_winner():
    """ Extract challenge winners."""
    detail_files = get_sorted_filenames(SCRAPED_DATA_PATH, 'challenges_detail_*.json')

    for file_name_idx, detail_fn in enumerate(detail_files):
        
        with open(detail_fn) as fjson_detail:
            challenges = json.load(fjson_detail)
            challenges_with_winner = [challenge for challenge in challenges if 'winners' in challenge] # not every challenge has a winner

        winners = []
        winner_fields = ('submitter', 'rank', 'points')
        for idx, challenge in enumerate(challenges_with_winner, start=1):

            for winner in sorted(challenge['winners'], key=lambda w: w['rank'] if 'rank' in w else len(w)):
                extracted_winner = {
                    'challengeId': challenge['challengeId'],
                    'handle': str(winner['submitter']).lower(),
                    'submissionDate': parse_iso_dt(winner['submissionTime']), # to unify the field with challenge-registrant 'submissionDate'
                    'ranking': winner['rank'], # 'rank' is a reserved keywork in MySQL, use ranking instead
                    'points': winner['points']
                }
                winners.append(extracted_winner)

            show_progress(idx, len(challenges_with_winner), prefix=f'Extracting winners from challenges {file_name_idx + 1}/{len(detail_files)}', suffix=f'{len(winners)} winners in total')

        with open(os.path.join(PROCESS_DATA_PATH, f'challenge_winners_{file_name_idx}.json'), 'w') as fjson:
            json.dump(winners, fjson, indent=4)

def extract_user_profile():
    """ Extract user profile data."""
    user_profile_files = get_sorted_filenames(SCRAPED_DATA_PATH, 'users_profile_*.json')

    for file_name_idx, profile_fn in enumerate(user_profile_files):
        with open(profile_fn) as fjson_user:
            users = json.load(fjson_user)

        user_infos = []
        user_skills = []
        for idx, user in enumerate(users, start=1):
            extracted_user = {
                'handle': user['handleLower'],
                'userId': user['userId'],
                'memberSince': parse_iso_dt(user['createdAt']),
                # there are users with one or both fields missing, so merge two fields into one and competition takes priority.
                'countryCode': user['competitionCountryCode'] or user['homeCountryCode'] or '',
                'description': user['description'] or '',
                'wins': user['wins'] or 0,
                'challenges': user['challenges'] or 0,
            }
            user_infos.append(extracted_user)

            for skill in user['skills'].values():
                extracted_skill = {
                    'userId': user['userId'],
                    'skill': skill['tagName'],
                    'score': skill['score'],
                    'fromChallenge': 'CHALLENGE' in skill['sources'],
                    'fromUserEnter': 'USER_ENTERED' in skill['sources']
                }
                user_skills.append(extracted_skill)

            # print('\tExtracted user {} with {} skills | {}/{}'.format(user['userId'], len(user['skills']), idx, len(users)))
            show_progress(idx, len(users), prefix=f'Extracting user profiles {file_name_idx + 1}/{len(user_profile_files)}')

        with open(os.path.join(PROCESS_DATA_PATH, f'user_profiles_{file_name_idx}.json'), 'w') as fjson_uinfo:
            json.dump(user_infos, fjson_uinfo, indent=4)

        with open(os.path.join(PROCESS_DATA_PATH, f'user_skills_{file_name_idx}.json'), 'w') as fjson_uskill:
            json.dump(user_skills, fjson_uskill, indent=4)

if __name__ == '__main__':
    data_identical, nonidentical_file_names = validate_challegens()
    if data_identical is False:
        unify_challenge_files(nonidentical_file_names)

        double_check_data_identical, double_check_nonidentical_file_names = validate_challegens()
        if double_check_data_identical is True:
            extract_challenges_info()
            extract_challenge_registrant()
            extract_challenge_winner()
            extract_user_profile()

    else:
        extract_challenges_info()
        extract_challenge_registrant()
        extract_challenge_winner()
        extract_user_profile()

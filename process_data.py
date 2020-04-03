""" Process fetched data and prepared for database operations."""

import os
import json
from glob import iglob
from dotenv import load_dotenv
from util import append_lst_to_json, parse_iso_dt
load_dotenv()

DATA_STORAGE_PATH = os.getenv('DATA_STORAGE_PATH')
SCRAPED_DATA_PATH = os.path.join(os.curdir, DATA_STORAGE_PATH, os.getenv('SCRAPED_DATA_PATH'))
PROCESS_DATA_PATH = os.path.join(os.curdir, DATA_STORAGE_PATH, os.getenv('PROCESS_DATA_PATH'))

DATA_PATH = os.path.join(os.curdir, DATA_STORAGE_PATH, SCRAPED_DATA_PATH) # Ensure the path format is cross-platform compatible

def extract_challenges_info():
    """ Extract needed challenges data from fetched challenge details."""
    overview_files = sorted(iglob(os.path.join(SCRAPED_DATA_PATH, 'challenges_overview_*.json')))
    detail_files = sorted(iglob(os.path.join(SCRAPED_DATA_PATH, 'challenges_detail_*.json')))

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

        print(f'Extracting {len(challenges)} challenges | {file_name_idx + 1}/{len(overview_files)}')

        extracted_challenges = []
        for idx, challenge in enumerate(challenges, start=1):
            processed_challenge = {}

            for field in intact_fields:
                processed_challenge[field] = '' if field not in challenge else challenge[field]

            for field in join_fields:
                processed_challenge[field] = '' if field not in challenge else ', '.join([str(i) for i in challenge[field]])

            for field in date_fields:
                processed_challenge[field] = parse_iso_dt(challenge[field])

            extracted_challenges.append(processed_challenge)
            print('\tExtracted challenge {0} | {1}/{2}'.format(challenge['challengeId'], idx, len(challenges)))

        with open(os.path.join(PROCESS_DATA_PATH, f'challenges_info_{file_name_idx}.json'), 'w') as fjson:
            json.dump(extracted_challenges, fjson, indent=4)

def extract_challenge_registrant():
    """ Extract the registrants of each challenge."""
    detail_files = sorted(iglob(os.path.join(SCRAPED_DATA_PATH, 'challenges_detail_*.json')))

    for file_name_idx, detail_fn in enumerate(detail_files):
        
        with open(os.path.join(detail_fn)) as fjson_detail:
            challenges = json.load(fjson_detail)

        print(f'Extracting challenge registrant relations of {len(challenges)} challenges | {file_name_idx + 1}/{len(detail_files)}')

        challenge_registrant_relation = []
        for idx, challenge in enumerate(challenges, start=1):

            print('\tExtracting registrants for challege {} | {}/{}'.format(challenge['challengeId'], idx, len(challenges))) 
            print('\t  - {} registrants | {} submitters | {} submissions'\
                .format(challenge['numberOfRegistrants'], challenge['numberOfSubmitters'], challenge['numberOfSubmitters']))
            
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
    detail_files = sorted(iglob(os.path.join(SCRAPED_DATA_PATH, 'challenges_detail_*.json')))

    for file_name_idx, detail_fn in enumerate(detail_files):
        
        with open(detail_fn) as fjson_detail:
            challenges = json.load(fjson_detail)
            challenges_with_winner = [challenge for challenge in challenges if 'winners' in challenge] # not every challenge has a winner

        print(f'{len(challenges_with_winner)} out of {len(challenges)} challengs have at least a winner | {file_name_idx + 1}/{len(detail_files)}')

        winners = []
        winner_fields = ('submitter', 'rank', 'points')
        for idx, challenge in enumerate(challenges_with_winner, start=1):
            print('Extracting challenge {} | {}/{}'.format(challenge['challengeId'], idx, len(challenges_with_winner)))
            for winner in sorted(challenge['winners'], key=lambda w: w['rank']):
                extracted_winner = {
                    'handle': str(winner['submitter']).lower(),
                    'submissionTime': parse_iso_dt(winner['submissionTime']),
                    'rank': winner['rank'],
                    'points': winner['points']
                }
                winners.append(extracted_winner)

        with open(os.path.join(PROCESS_DATA_PATH, f'challenge_winners_{file_name_idx}.json'), 'w') as fjson:
            json.dump(winners, fjson, indent=4)

        print(f'\tExtract {len(winners)} winners in total')

def extract_user_profile():
    """ Extract user profile data."""
    user_profile_files = sorted(iglob(os.path.join(SCRAPED_DATA_PATH, 'users_profile_*.json')))

    for file_name_idx, profile_fn in enumerate(user_profile_files):
        with open(profile_fn) as fjson_user:
            users = json.load(fjson_user)

        print(f'Extracting profiles of {len(users)} users | {file_name_idx + 1}/{len(user_profile_files)}')

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

            print('\tExtracted user {} with {} skills | {}/{}'.format(user['userId'], len(user['skills']), idx, len(users)))

        with open(os.path.join(PROCESS_DATA_PATH, f'user_profiles_{file_name_idx}.json'), 'w') as fjson_uinfo:
            json.dump(user_infos, fjson_uinfo, indent=4)

        with open(os.path.join(PROCESS_DATA_PATH, f'user_skills_{file_name_idx}.json'), 'w') as fjson_uskill:
            json.dump(user_skills, fjson_uskill, indent=4)

if __name__ == '__main__':
    extract_challenges_info()
    extract_challenge_registrant()
    extract_challenge_winner()
    extract_user_profile()

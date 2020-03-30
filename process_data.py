""" Process fetched data and prepared for database operations."""

import os
import json
from datetime import datetime
from util import append_lst_to_json

def extract_challenges_info():
    """ Extract needed challenges data from fetched challenge details."""
    with open('./data/challenges_overview.json') as fjson_overview:
        challenges_overview = json.load(fjson_overview)
    with open('./data/challenges_detail.json') as fjson_detail:
        challenges_detail = json.load(fjson_detail)

    challenges = [{**overview, **detail} for overview, detail in zip(challenges_overview, challenges_detail)] # merge overview and detail of challenges

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

    extracted_challenges = []
    print(f'Extracting {len(challenges)} challenges...')
    for idx, challenge in enumerate(challenges, start=1):
        processed_challenge = {}

        for field in intact_fields:
            processed_challenge[field] = '' if field not in challenge else challenge[field]

        for field in join_fields:
            processed_challenge[field] = '' if field not in challenge else ', '.join([str(i) for i in challenge[field]])

        for field in date_fields:
            # consume ISO-8601 formatted UTC time string and parse a MySQL Datetime format string
            # the datetime.fromisoformat() method support string in the format of
            # `YYYY-MM-DD[*HH[:MM[:SS[.mmm[mmm]]]][+HH:MM[:SS[.ffffff]]]]` P.S. no trailing 'Z' accepted!
            processed_challenge[field] = datetime.fromisoformat(challenge[field][:-1]).strftime('%Y-%m-%d %H:%M:%S')

        extracted_challenges.append(processed_challenge)
        print('Extracted challenge {0} | {1}/{2}'.format(challenge['challengeId'], idx, len(challenges)))

    with open('./data/processed_data/challenges_info.json', 'w') as fjson:
        json.dump(extracted_challenges, fjson, indent=4)

def extract_challenge_registrant():
    """ Extract the registrants of each challenge."""
    with open('./data/challenges_detail.json') as fjson_detail:
        challenges = json.load(fjson_detail)

    challenge_registrant_relation = []
    print(f'Extracting challenge registrant relations of {len(challenges)} challenges')
    for idx, challenge in enumerate(challenges, start=1):
        print('Extracting registrants for challege {} | {}/{}'.format(challenge['challengeId'], idx, len(challenges))) 
        print('\t- {} registrants | {} submitters | {} submissions'.format(challenge['numberOfRegistrants'], challenge['numberOfSubmitters'], challenge['numberOfSubmitters']))
        
        if 'registrants' in challenge:
            for registrant in challenge['registrants']:
                relation = {}
                relation['challengeId'] = challenge['challengeId']
                relation['handle'] = str(registrant['handle']).lower() # just in case there is int type handle
                relation['registrationDate'] = registrant['registrationDate']
                relation['submissionDate'] = '' if 'submissionDate' not in registrant else registrant['submissionDate']

                challenge_registrant_relation.append(relation)

    with open('./data/processed_data/challenge_registrant_relation.json', 'w') as fjson:
        json.dump(challenge_registrant_relation, fjson, indent=4)

def extract_challenge_winner():
    """ Extract challenge winners."""

def extract_user_profile():
    """ Extract user profile data."""

if __name__ == '__main__':
    extract_challenges_info()
    extract_challenge_registrant()

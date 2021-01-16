""" Everything that's static variable or shared by other logic.
    No need to refactor if it's less than 1 kLOC
"""
import os
import enum
from dotenv import load_dotenv
from url import URL
load_dotenv()

MEMBER_URL = URL('{}/v5/members/'.format(os.getenv('API_BASE_URL')))
CHALLENGE_URL = URL('{}/v5/challenges/?{}'.format(os.getenv('API_BASE_URL'), os.getenv('DEFAULT_CHALLENGE_QUERY')))
RESOURCE_URL = URL('{}/v5/resources/?perPage=5000'.format(os.getenv('API_BASE_URL')))
AUTH_TOKEN = os.getenv('JWT') and 'Bearer {}'.format(os.getenv('JWT'))


class Status(str, enum.Enum):
    ALL = 'ALL'
    new = 'New'
    draft = 'Draft'
    active = 'Active'
    completed = 'Completed'
    deleted = 'Deleted'
    cancelled = 'Cancelled'
    cancelled_failed_review = 'Cancelled - Failed Review'
    cancelled_failed_screening = 'Cancelled - Failed Screening'
    cancelled_zero_registrations = 'Cancelled - Zero Registrations'
    cancelled_zero_submission = 'Cancelled - Zero Submissions'
    cancelled_winner_unresponsive = 'Cancelled - Winner Unresponsive'
    cancelled_client_request = 'Cancelled - Client Request'
    cancelled_requirements_infeasible = 'Cancelled - Requirements Infeasible'


class Track(str, enum.Enum):
    develop = 'Dev'
    design = 'Des'
    data_science = 'DS'
    quality_assurance = 'QA'


class ChallengeType(str, enum.Enum):
    challenge = 'CH'
    first_to_finish = 'F2F'
    task = 'TSK'


class SortOrder(str, enum.Enum):
    ascending = 'asc'
    descending = 'desc'


class SortBy(str, enum.Enum):
    updated_by = 'updatedBy'
    updated = 'updated'
    created_by = 'createdBy'
    created = 'created'
    end_date = 'endDate'
    start_date = 'startDate'
    project_id = 'projectId'
    name = 'name'
    type_id = 'typeId'
    total_prizes = 'overview.totalPrizes'

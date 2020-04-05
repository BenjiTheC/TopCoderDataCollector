""" Write the processed data into the database
    The tables are created already with the created_table.sql script
"""

import os
import json
from mysql import connector
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor
from dotenv import load_dotenv
from util import get_sorted_filenames, show_progress
load_dotenv()

PROCESS_DATA_PATH = os.path.join(os.curdir, os.getenv('DATA_STORAGE_PATH'), os.getenv('PROCESS_DATA_PATH'))

DB_CONNECTION = None

TABLE_NAME_DATA_FILE_PATTERN_MAP = {
    'Challenge': 'challenges_info_*.json',
    'Challenge_Registrant_Relation': 'challenge_registrant_relation_*.json',
    'Challenge_Winner': 'challenge_winners_*.json',
    'User_Profile': 'user_profiles_*.json',
    'User_Skill': 'user_skills_*.json'
}

def construt_insert_query(tb_name, tb_cols):
    """ Construct the insertion query with given table name and table columns name."""
    return 'INSERT INTO {} ({}) VALUES ({});'.format(tb_name, ', '.join(tb_cols), ', '.join([f'%({col})s' for col in tb_cols]))

def get_db_cnx():
    """ Connect to the databse if database is not connected
        Return a database cursor
    """
    global DB_CONNECTION

    db_config = {
        'host': os.getenv('DB_HOST'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USERNAME'),
        'password': os.getenv('DB_PASSWORD')
    }

    if DB_CONNECTION is None:
        try:
            print('Connecting to Database mysql://{}/{}'.format(db_config['host'], db_config['database']))
            DB_CONNECTION = connector.connect(**db_config)
            print('Database connected')
        except connector.Error as err:
            if err.errno == connector.errorcode.ER_ACCESS_DENIED_ERROR:
                print('Username and password are not correct')
            if err.errno == connector.errorcode.ER_BAD_DB_ERROR:
                print('Requested database doesn\'t exist')
            print(err)
            exit(1)
    
    return DB_CONNECTION

def insert_records(tb_name, data_file_pattern):
    """ A universal insertion function."""
    cnx = get_db_cnx()
    cursor = cnx.cursor()
    for data_file_name in get_sorted_filenames(PROCESS_DATA_PATH, data_file_pattern):
        with open(data_file_name) as fjson:
            data_chunk = json.load(fjson)

        for idx, data in enumerate(data_chunk, start=1):
            cursor.execute(construt_insert_query(tb_name, data.keys()), data)
            show_progress(idx, len(data_chunk), prefix=f'Uploading data to table {tb_name}', suffix=f'source: {os.path.split(data_file_name)[1]}')

        cnx.commit()

    cursor.close()

if __name__ == '__main__':
    for tb_name, data_file_patter in TABLE_NAME_DATA_FILE_PATTERN_MAP.items():
        insert_records(tb_name, data_file_patter)

    if DB_CONNECTION:
        DB_CONNECTION.close()

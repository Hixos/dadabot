import os


class Constants:
    if 'API_KEY' in os.environ:
        API_KEY = os.environ['API_KEY']
    else:
        f = open('api_key.txt')
        API_KEY = f.readline()

    if 'APP_NAME' in os.environ:
        APP_NAME = os.environ['APP_NAME']
    else:
        APP_NAME = 'dadabot1'

    if APP_NAME == 'dadabot1':
        BOT_NAME = 'dadadaze_bot'
    else:
        BOT_NAME = 'dadatest_bot'

    KEY_SQL_PSK = 'skey'
    KEY_SQL_QUERY = 'query'
    KEY_SQL_SUCCESS = 'success'
    KEY_SQL_RESULTS = 'results'
    KEY_SQL_RESULT_DATA = 'result_data'
    KEY_SQL_RESULT_AFFECTED_ROWS = 'result_affected_rows'





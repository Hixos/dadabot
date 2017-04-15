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
        APP_NAME = 'dadabot-test'

    KEY_SQL_PSK = 'skey'
    KEY_SQL_QUERY = 'query'
    KEY_SQL_SUCCESS = 'success'
    KEY_SQL_RESULTS = 'results'





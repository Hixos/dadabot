import os

if 'API_KEY' in os.environ:
    api_key = os.environ['API_KEY']
else:
    f = open('api_key.txt')
    api_key = f.readline()

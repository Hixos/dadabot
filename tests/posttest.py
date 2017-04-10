import requests
api_key = 'fake api key'

url = 'http://dadabot.altervista.org/addcommand.php'
params = {'skey': api_key, 'cmd': 'addanwer "ciao","bau":"cacca","prugna"'}
response = requests.post(url, json=params)

print(response.text)

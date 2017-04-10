import requests

url = 'http://dadabot.altervista.org/getcommands.php'
#params = {'skey': 'abcd123', 'cmd': 'addanwer "ciao","bau":"cacca","prugna"'}
response = requests.post(url)#, json=params)

print(response.text)

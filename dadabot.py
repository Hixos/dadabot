import json
import os

from telegramapi import TelegramApi
from flask import Flask, request

app = Flask(__name__)

if 'API_KEY' in os.environ:
    api_key = os.environ['API_KEY']
else:
    f = open('api_key.txt')
    api_key = f.readline()

telegram = TelegramApi(api_key)


def eval_message(msg: TelegramApi.Message):
    if msg.Text.lower().__contains__('sushi'):
        telegram.send_mess(msg.Chat.Id, 'NO!')


@app.route('/test/', methods=['GET'])
def getget():
    s = request.args.get('test')
    return 'Get! ' + str(s)


#json_data=json.loads(requests.body)
'''
updates = get_updates(json_data)  # type: list[Update]

for upd in updates:
    if upd.Id > maxid:
        maxid = upd.Id

    if upd.has_message():
        msg = upd.Message
        chat = msg.Chat
        if chat.Username == 'Hixos':
            eval_message(msg)


print(maxid)


'''
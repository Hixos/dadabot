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


@app.route('/', methods=['GET'])
def getget():
    if 'test' in request.args:
        s = request.args.get('test')
    else:
        s = "Ciao!"

    return 'Get! ' + str(s)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    app.run()


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
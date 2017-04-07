import os

from telegramapi import TelegramApi
from flask import Flask, request

app = Flask(__name__)
app_name = os.environ.get('APP_NAME', 'dadabot1')

if 'API_KEY' in os.environ:
    api_key = os.environ['API_KEY']
else:
    f = open('api_key.txt')
    api_key = f.readline()

telegram = TelegramApi(api_key, app_name)


@app.route('/' + api_key + '/', methods=['POST'])
def webhook():
    print('Received webhook \n\n')
    json = request.get_json()
    print(json + '\n\n\n')
    TelegramApi.process_updates_json(json, eval_update)


def eval_update(upd: TelegramApi.Update):
    if not upd.has_message():
        return

    msg = upd.Message
    chat = msg.Chat

    if msg.Text.lower().__contains__('sushi') and chat.Username == 'Hixos':
        telegram.send_mess(chat.Id, 'Nope')


telegram.set_webhook()

# Start the web app (only if on remote server)
if __name__ == "__main__" and 'PORT' in os.environ:
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)


import os
import logging

from telegramapi import TelegramApi
from flask import Flask, request

app = Flask(__name__)
app_name = os.environ.get('APP_NAME', 'dadabot-test')

if 'API_KEY' in os.environ:
    api_key = os.environ['API_KEY']
else:
    f = open('api_key.txt')
    api_key = f.readline()

telegram = TelegramApi(api_key, app_name)


@app.route('/' + api_key, methods=['POST'])
def webhook():
    logging.info('Received webhook')
    if request.is_json:
        j = request.get_json(silent=True)

        if j is None:
            logging.error('request.get_json() returned None')
            return 'Error'

        TelegramApi.process_update_json(j, eval_update)
    else:
        logging.warning('Received non-json request: ' + request.data)

    return 'OK'


def eval_update(upd: TelegramApi.Update):
    if not upd.has_message():
        logging.warning('Eval: Update with no message')
        return

    msg = upd.Message
    chat = msg.Chat

    if msg.Text.lower().__contains__('sushi') and chat.Username == 'Hixos':
        telegram.send_mess(chat.Id, 'Nope')


# Start the web app (only if on remote server)
if __name__ == "__main__" and 'PORT' in os.environ:
    telegram.set_webhook()

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)


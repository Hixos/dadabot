import os

from flask import Flask, request
from dadabot.messagelogic import evaluate
from dadabot.shared_data import Constants

from dadabot.logs import logger
from dadabot.telegramapi import TelegramApi

app = Flask(__name__)
app_name = os.environ.get('APP_NAME', 'dadabot-test')

telegram = TelegramApi(Constants.API_KEY, app_name)


@app.route('/' + Constants.API_KEY, methods=['POST'])
def webhook():
    logger.info('Received webhook')
    if request.is_json:
        j = request.get_json(silent=True)

        if j is None:
            logger.error('request.get_json() returned None')
            return 'Error'

        TelegramApi.process_update_json(j, evaluate_update)
    else:
        logger.warning('Received non-json request: ' + request.data)

    return 'OK'


def evaluate_update(update: TelegramApi.Update):
    evaluate(telegram, update)


# Start the web app (only if on remote server)
if __name__ == "__main__":

    if 'PORT' in os.environ:
        telegram.set_webhook()

        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)


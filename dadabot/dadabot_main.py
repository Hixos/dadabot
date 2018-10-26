import os

from flask import Flask, request
from dadabot.shared_data import Constants

from dadabot.logs import logger
from dadabot.telegramapi import TelegramApi
from dadabot.data import Database, Chat, WordMatchResponse
from dadabot.commands import handle_command_str, notify_new_match

app = Flask(__name__)

telegram = TelegramApi(Constants.API_KEY, Constants.APP_NAME)

chats: list = []

WordMatchResponse.load_list_from_database()


@app.route('/' + Constants.API_KEY, methods=['POST'])
def webhook():
    logger.info('Received webhook')
    if request.method == 'POST' and request.is_json:
        j = request.get_json(silent=True)

        if j is None:
            logger.error('request.get_json() returned None')
            return '', 400

        telegram.process_update_json(j, evaluate_update)
        return '', 200
    else:
        logger.warning('Received non-json request: ' + request.data)
        return '', 400


def load_chats():
    cols = [Chat.COL_ID]
    cols.extend(Chat.COLS)
    data = Database.select(cols, [Chat.TABLE])
    [result, rows] = Database.get_rows(data, 0)
    if result:
        for row in rows:
            chats.append(Chat.from_database(row))


def evaluate_update(update: TelegramApi.Update):
    if not update.has_message():
        logger.warning('Eval: Update with no message')
        return

    msg = update.Message

    # Check if the message is from a new chat
    chat_found = False
    for chat in chats:
        if chat.Id == msg.Chat.Id:
            chat_found = True
            break

    if not chat_found:
        c = Chat.from_message(msg)
        chats.append(c)
        c.save_to_database()

    handled = handle_command_str(msg, telegram)

    if not handled:
        logger.debug("Not a command: " + msg.Text)
        # send eventual messages
        for response in WordMatchResponse.List:  # type: WordMatchResponse
            if response.matches(msg.Text):
                notify_new_match(response.Id, msg.Chat.Id)
                response.reply(msg, telegram)
                response.increment_match_counter()


# Start the web app (only if on remote server)
if __name__ == "__main__":
    if 'PORT' in os.environ:
        telegram.set_webhook()

        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)


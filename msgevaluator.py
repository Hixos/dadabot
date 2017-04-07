import logging
import random

from telegramapi import TelegramApi

answers_negative = ['NO!', 'NON ROMPERE IL CAZZO!', 'COL CAZZO!', 'HAI ROTTO', 'NOPE']

no_trigger_words = ['sushi', 'evangelion']


def contains(msg_text: str, words):
    for w in words:
        if msg_text.lower().__contains__(w):
            return True

    return False


def evaluate(telegram: TelegramApi, update: TelegramApi.Update):
    if not update.has_message():
        logging.warning('Eval: Update with no message')
        return

    msg = update.Message
    chat = msg.Chat

    if contains(msg.Text, no_trigger_words):
        answ = random.choice(answers_negative)
        telegram.send_message(chat.Id, answ)


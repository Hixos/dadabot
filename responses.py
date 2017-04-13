from telegramapi import TelegramApi
from enum import Enum
from logs import logger
import random
import re



class WordMatchMode(Enum):
    WHOLE = 0
    ANY = 1
    EXACT = 2


def find_words(msg: str, words, mode=WordMatchMode.WHOLE):
    for word in words:  # type: str
        word = re.escape(word)
        if mode == WordMatchMode.WHOLE:
            regex = '((?<=\W)|(?<=^))(' + word + '+|(' + word + ')+)(?=\W|$)'
        elif mode == WordMatchMode.ANY:
            regex = word
            logger.debug("Matching any.")
        else:
            regex = '^' + word + '$'

        p = re.compile(regex, re.IGNORECASE)

        r = p.search(msg)
        if r is not None:
            if mode == WordMatchMode.ANY:
                logger.debug("Matched any.")
            return r.start()
    return -1

class WordMatchResponse:
    def __init__(self, words, responses, mode: WordMatchMode):
        self.Matchwords = words  # type: list[str]
        self.Responses = responses  # type: list[str]
        self.Mode = mode

    def matches(self, msg: str):
        return find_words(msg, self.Matchwords, self.Mode) >= 0

    def reply(self, msg: TelegramApi.Message, telegram: TelegramApi):
        answ = random.choice(self.Responses)  # type:

        try:
            answ = answ.format(Msg=msg)
        except (KeyError, AttributeError):
            pass

        telegram.send_message(msg.Chat.Id, answ)

import random
import re
from enum import IntEnum

from dadabot.logs import logger
from dadabot.telegramapi import TelegramApi
from dadabot.data import Database, Command, User, Chat
from dadabot.shared_data import Constants


class WordMatchMode(IntEnum):
    WHOLE = 0
    ANY = 1
    MSG = 2

    @staticmethod
    def to_string(m):
        if m == WordMatchMode.WHOLE:
            return 'matchwords'
        elif m == WordMatchMode.ANY:
            return 'matchany'
        else:
            return 'matchmsg'


def find_words(msg: str, words, mode=WordMatchMode.WHOLE):
    for word in words:  # type: str
        word = re.escape(word)
        if mode == WordMatchMode.WHOLE:
            regex = '((?<=\W)|(?<=^))(' + word + '+|(' + word + ')+)(?=\W|$)'
        elif mode == WordMatchMode.ANY:
            regex = word
        else:
            regex = '(^)(?:\s)*(' + word + '+)(?:\W)*(?:$)'

        p = re.compile(regex, re.IGNORECASE)

        r = p.search(msg)
        if r is not None:
            return r.start()
    return -1


class WordMatchResponse(Command):
    TABLE = 'match_words'
    COL_ID = TABLE + '.cmd_id'
    COL_TYPE = TABLE + '.match_type'

    WORDS_TABLE = 'words'
    RESPONSES_TABLE = 'responses'

    WORDS_COL_ID = WORDS_TABLE + '.word_id'
    WORDS_COL_TEXT = WORDS_TABLE + '.word_text'
    WORDS_COL_CMD_ID = WORDS_TABLE + '.cmd_id'

    RESPONSES_COL_ID = RESPONSES_TABLE + '.resp_id'
    RESPONSES_COL_TEXT = RESPONSES_TABLE + '.resp_text'
    RESPONSES_COL_CMD_ID = RESPONSES_TABLE + '.cmd_id'

    COLS = [COL_TYPE]
    WORD_COLS = [WORDS_COL_TEXT, WORDS_COL_CMD_ID]
    RESP_COLS = [RESPONSES_COL_TEXT, RESPONSES_COL_CMD_ID]

    List = []  # type: list[WordMatchResponse]

    def __init__(self):
        super().__init__()
        self.Matchwords = []  # type: list[str]
        self.Responses = []  # type: list[str]
        self.Mode = WordMatchMode.WHOLE

    def matches(self, msg: str):
        return find_words(msg, self.Matchwords, self.Mode) >= 0

    def reply(self, msg: TelegramApi.Message, telegram: TelegramApi):
        answ = random.choice(self.Responses)  # type:

        try:
            answ = answ.format(Msg=msg, count=self.MatchCounter)
        except (KeyError, AttributeError):
            pass

        telegram.send_message(msg.Chat.Id, answ)

    def load_from_database(self, cmddata: dict):
        C = WordMatchResponse
        super().load_from_database(cmddata)
        self.Mode = WordMatchMode(int(cmddata[WordMatchResponse.COL_TYPE]))
        id = cmddata[Command.COL_ID]

        query = Database.select_str([C.WORDS_COL_CMD_ID, C.WORDS_COL_TEXT], [C.WORDS_TABLE],
                                    [(C.WORDS_COL_CMD_ID, str(id))])
        query += '; '
        query += Database.select_str([C.RESPONSES_COL_ID, C.RESPONSES_COL_TEXT], [C.RESPONSES_TABLE],
                                     [(C.RESPONSES_COL_CMD_ID, str(id))])

        data = Database.query(query)

        success, rows = Database.get_rows(data, 0)
        if not success:
            return False

        for row in rows:
            self.Matchwords.append(row[C.WORDS_COL_TEXT])

        success, rows = Database.get_rows(data, 1)
        if not success:
            return False

        for row in rows:
            self.Responses.append(row[C.RESPONSES_COL_TEXT])

        return True

    def save_to_database(self):
        if not super().save_to_database():
            return False

        C = WordMatchResponse

        cols = [C.COL_ID]
        cols.extend(C.COLS)

        s = Database.insert_str(C.TABLE, cols, [self.Id, int(self.Mode)])

        for word in self.Matchwords:
            s += '; ' + Database.insert_str(C.WORDS_TABLE, C.WORD_COLS, [word, self.Id])

        for resp in self.Responses:
            s += '; ' + Database.insert_str(C.RESPONSES_TABLE, C.RESP_COLS, [resp, self.Id])

        logger.info(s)
        return Database.query_bool(s)


    @classmethod
    def from_database(cls, cmddata: dict):
        """
        
        :param cmddata: Dictionary containing data from tables for classes WordMatchResponse, Command, User, Chat
        :return: New instance of class WordMatchResponse
        """
        cmd = cls()
        if cmd.load_from_database(cmddata):
            return cmd
        else:
            return None

    @classmethod
    def from_message(cls, words, responses, mode: WordMatchMode, msg: TelegramApi.Message):
        wmr = cls()
        if len(words) == 0 or len(responses) == 0:
            return None

        wmr.Matchwords = words
        wmr.Responses = responses
        wmr.Mode = mode
        wmr.load_from_message(msg)

        return wmr

    @staticmethod
    def add_list_from_message(words, responses, mode, msg: TelegramApi.Message):
        cls = WordMatchResponse.from_message(words, responses, mode, msg)

        if cls is not None:
            WordMatchResponse.List.append(cls)
            cls.save_to_database()

    @staticmethod
    def add_list_from_database():
        C = WordMatchResponse
        C.List = []

        cols = [Command.COL_ID]
        cols.extend(Command.COLS)
        cols.extend(C.COLS)
        cols.extend(User.COLS)
        cols.extend(Chat.COLS)

        tables = [C.TABLE, Command.TABLE, User.TABLE, Chat.TABLE]
        equals = [(C.COL_ID, Command.COL_ID), (User.COL_ID, Command.COL_USER_ID), (Chat.COL_ID, Command.COL_CHAT_ID),
                  (Command.COL_BOT_NAME, '\'' + Constants.APP_NAME + '\'')]

        r = Database.select(cols, tables, equals)

        success, rows = Database.get_rows(r, -1)

        if success:
            for row in rows:
                cls = WordMatchResponse.from_database(row)
                if cls is not None:
                    C.List.append(cls)

        return True

import requests

from dadabot.logs import logger
from dadabot.shared_data import Constants
from dadabot.telegramapi import TelegramApi

dburl = 'http://dadabot.altervista.org/query.php'


class Database:
    _escape_chars = ['\\', '\'', '"', 'Z', '%', '_']
    _remove_chars = ['\b', '\n', '\r', '\t', '\0']

    @staticmethod
    def escape(txt: str):
        for c in Database._escape_chars:
            txt = txt.replace(c, '\\' + c)

        for c in Database._remove_chars:
            txt = txt.replace(c, '')

        return txt

    @staticmethod
    def query(q: str):
        params = {Constants.KEY_SQL_PSK: Constants.API_KEY, Constants.KEY_SQL_QUERY: q}
        r = requests.post(dburl, json=params)
        try:
            js = r.json()
            if Constants.KEY_SQL_SUCCESS not in js:
                logger.error('SQL query didn\'t return correct json')
                return {Constants.KEY_SQL_SUCCESS: False}
            else:
                return js
        except ValueError:
            logger.error("Error reading response from server. Response: " + r.text)
            return {Constants.KEY_SQL_SUCCESS: False}

    @staticmethod
    def query_bool(q: str):
        r = Database.query(q)
        return r.get(Constants.KEY_SQL_SUCCESS, False)

    @staticmethod
    def get_rows(data: dict, idx: int):
        if not data.get(Constants.KEY_SQL_SUCCESS, False):
            return False, None

        results = data.get(Constants.KEY_SQL_RESULTS, [])  # type: list[dict]
        n = len(results)

        if idx < 0:
            idx = n + idx

        if 0 <= idx < n:
            return True, results[idx]

        return False, None

    @staticmethod
    def list(data):
        q = ''
        n = len(data)
        for i, d in enumerate(data):
            q += d
            if i != n-1:
                q += ', '
        return q

    @staticmethod
    def select_str(cols, tables, equals=None, conds=None):
        ascols = []
        for c in cols:
            ascols.append(c + ' AS \'' + c + '\'')

        q = "SELECT " + Database.list(ascols) + " FROM " + Database.list(tables)

        if equals is not None or conds is not None:
            q += " WHERE "

        if equals is None:
            equals = []

        n = len(equals)

        for i, idval in enumerate(equals):
            q += idval[0] + ' = ' + idval[1]
            if i != n - 1:
                q += ' AND '

        if conds is None:
            conds = []
        else:
            if len(equals) > 0:
                q += ' AND '

        n = len(conds)
        for i, c in enumerate(conds):
            q += c
            if i != n - 1:
                q += ' AND '
        return q

    @staticmethod
    def select(cols, tables, equals=None, conds=None):
        return Database.query(Database.select_str(cols, tables, equals, conds))

    @staticmethod
    def insert_str(table, cols, data, update=False):
        edata = []
        for d in data:
            edata.append("'" + Database.escape(str(d)) + "'")

        s = "INSERT INTO " + table + " ( " + Database.list(cols) + " ) VALUES ( " + Database.list(edata) + " )"
        if not update:
            return s

        s += " ON DUPLICATE KEY UPDATE "

        upd = []
        for c in cols:
            upd.append(c + ' = VALUES(' + c + ')')

        s += Database.list(upd)

        return s

    @staticmethod
    def insert(table, cols, data):
        q = Database.insert_str(table,cols, data)

        return Database.query_bool(q)

    @staticmethod
    def replace_str(table, cols, data):
        return Database.insert_str(table, cols, data, True)

    @staticmethod
    def replace(table, cols, data):
        q = Database.replace_str(table,  cols, data)
        return Database.query_bool(q)

    @staticmethod
    def delete_str(table, where_tuple):
        q = "DELETE FROM " + table + " WHERE "
        n = len(where_tuple)

        for i, w in enumerate(where_tuple):
            q += w[0] + " = '" + Database.escape(str(w[1])) + "'"
            if i != n - 1:
                q += ' AND '

        print(q)
        return q

    @staticmethod
    def delete(table, where_tuple):
        r = Database.query(Database.delete_str(table, where_tuple))
        return r.get(Constants.KEY_SQL_RESULT_AFFECTED_ROWS, 0) > 0


class User:
    TABLE = 'users'
    COL_ID = TABLE + '.user_id'
    COL_FIRST_NAME = TABLE + '.first_name'
    COL_LAST_NAME = TABLE + '.last_name'
    COL_USERNAME = TABLE + '.username'

    COLS = [COL_FIRST_NAME, COL_LAST_NAME, COL_USERNAME]

    def __init__(self, id, first_name, last_name, username):
        self.Id = id
        self.FirstName = first_name
        self.LastName = last_name
        self.Username = username

    @classmethod
    def from_database(cls, row: dict):
        id = int(row[Command.COL_USER_ID])
        first_name = row[User.COL_FIRST_NAME]
        last_name = row[User.COL_LAST_NAME]
        username = row[User.COL_USERNAME]

        return cls(id, first_name, last_name, username)

    @classmethod
    def from_message(cls, msg: TelegramApi.Message):
        id = msg.Sender.Id
        first_name = msg.Sender.FirstName
        last_name = msg.Sender.LastName
        username = msg.Sender.Username

        return cls(id, first_name, last_name, username)

    def save_to_database_str(self):
        cols = [User.COL_ID]
        cols.extend(User.COLS)

        return Database.replace_str(User.TABLE, cols, [self.Id, self.FirstName, self.LastName, self.Username])

    def save_to_database(self):
        return Database.query_bool(self.save_to_database_str())


class Chat:
    TABLE = 'chats'
    COL_ID = TABLE + '.chat_id'
    COL_TYPE = TABLE + '.chat_type'
    COL_TITLE = TABLE + '.chat_title'
    COL_FIRST_NAME = TABLE + '.first_name'

    COLS = [COL_TYPE, COL_TITLE, COL_FIRST_NAME]

    def __init__(self, id, type, title='', first_name=''):
        self.Id = id
        self.Type = type
        self.Title = title
        self.FirstName = first_name

    @classmethod
    def from_database(cls, chatdata: dict):
        id = int(chatdata.get(Command.COL_CHAT_ID, 0))
        if id == 0:
            id = int(chatdata.get(Chat.COL_ID, 0))
        type = chatdata[Chat.COL_TYPE]
        title = chatdata[Chat.COL_TITLE]
        first_name = chatdata[Chat.COL_FIRST_NAME]

        return cls(id, type, title, first_name)

    @classmethod
    def from_message(cls, msg: TelegramApi.Message):
        id = int(msg.Chat.Id)
        type = msg.Chat.Type
        first_name = msg.Chat.FirstName
        title = msg.Chat.Title
        return cls(id, type, title, first_name)

    def save_to_database_str(self):
        cols = [Chat.COL_ID]
        cols.extend(Chat.COLS)
        return Database.replace_str(Chat.TABLE, cols, [self.Id, self.Type, self.Title, self.FirstName])

    def save_to_database(self):
        return Database.query_bool(self.save_to_database_str())


class Command:
    TABLE = 'commands'
    COL_ID = TABLE + '.cmd_id'
    COL_MATCH_COUNT = TABLE + '.match_cntr'
    COL_CREATION_TIME = TABLE + '.creation_time'
    COL_USER_ID = TABLE + '.user_id'
    COL_CHAT_ID = TABLE + '.chat_id'
    COL_BOT_NAME = TABLE + '.bot_name'

    COLS = [COL_MATCH_COUNT, COL_USER_ID, COL_CHAT_ID, COL_BOT_NAME]

    def __init__(self):
        self.Id = -1
        self.MatchCounter = 0
        self.User = None  # type: User
        self.Chat = None  # type: Chat
        self.BotName = ''

    def load_from_database(self, cmddata: dict):
        self.Id = cmddata[Command.COL_ID]
        self.MatchCounter = int(cmddata[Command.COL_MATCH_COUNT])
        self.BotName = cmddata[Command.COL_BOT_NAME]
        self.User = User.from_database(cmddata)
        self.Chat = Chat.from_database(cmddata)


    def load_from_message(self, msg: TelegramApi.Message):
        self.BotName = Constants.APP_NAME
        self.User = User.from_message(msg)
        self.Chat = Chat.from_message(msg)

    def save_to_database_str(self):
        s = self.User.save_to_database_str() + '; ' + self.Chat.save_to_database_str() + '; '
        s += Database.insert_str(Command.TABLE, Command.COLS, [self.MatchCounter, self.User.Id, self.Chat.Id,
                                                               self.BotName])
        return s

    def increment_match_counter(self):
        self.MatchCounter += 1
        q = "UPDATE  " + Command.TABLE + "SET " + Command.COL_MATCH_COUNT + " = " + Command.COL_MATCH_COUNT \
            + " + 1 WHERE " + Command.COL_ID + " = " + str(self.Id)

        logger.info("Increment query: " + q)
        if not Database.query_bool(q):
            logger.error("Error incrementing match counter.")

    def save_to_database(self):
        s = self.save_to_database_str() + "; SELECT LAST_INSERT_ID() AS 'lastid'"
        r = Database.query(s)
        success, rows = Database.get_rows(r, 0)

        if success and len(rows) == 1:
            self.Id = int(rows[0]['lastid'])
            return True
        else:
            logger.error('Error on saving data to database: Cannot retrieve command id')
            return False

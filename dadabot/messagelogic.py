import io
import os.path

import requests
from dadabot.responses import WordMatchResponse, WordMatchMode, Chat
from dadabot.shared_data import Constants
from dadabot.telegramapi import TelegramApi
from dadabot.data import Database, Command, Chat

from dadabot.commandparser import parse_command, ParseResult, MatchData, AddData
from dadabot.logs import logger
from dadabot.commands import handle_command_str, is_command

chats = []  # list[Chat]
echo_to_id = 0  # Echo messages from my chat to this chat, don't echo if 0
my_chat_id = 227067835


def list_strings(strings):
    q = ''
    n = len(strings)
    for i, d in enumerate(strings):
        q += '"' + d + '"'
        if i != n - 1:
            q += ', '
    return q


def load_commands():
    WordMatchResponse.add_list_from_database()


def load_chats():
    cols = [Chat.COL_ID]
    cols.extend(Chat.COLS)
    data = Database.select(cols, [Chat.TABLE])
    [result, rows] = Database.get_rows(data, 0)
    if result:
        for row in rows:
            chats.append(Chat.from_database(row))


def reload_commands():
    load_commands()


def exec_command(cmd: ParseResult, msg: TelegramApi.Message, telegram: TelegramApi)


def exec_command(cmd: ParseResult, msg: TelegramApi.Message, telegram: TelegramApi):
    cmdstr = cmd.Command  # type: str

    if cmdstr.startswith('!'):  # Special commands
        if cmdstr == '!reload':
            reload_commands()
            telegram.send_message(msg.Chat.Id, 'Comandi ricaricati.')
        else:
            telegram.send_message(msg.Chat.Id, cmd.Data)
    elif cmdstr == 'echo':
        if msg.Chat.Id != 227067835:
            return False

        global echo_to_id
        echo_to_id = cmd.Data
        if echo_to_id == 0:
            telegram.send_message(msg.Chat.Id, 'Echo disattivato.')
        else:
            found = False
            for chat in chats:
                if chat.Id == echo_to_id:
                    found = True
                    break
            if not found:
                echo_to_id = 0
                telegram.send_message(msg.Chat.Id, 'Chat non trovata.')
            else:
                telegram.send_message(msg.Chat.Id, 'Echo a ' + str(echo_to_id))

    elif cmdstr == "listchats":
        if msg.Chat.Id != my_chat_id:
            return False

        msgtext = ''
        for chat in chats:
            if chat.Type == 'private':
                msgtext += "[%s] %s\n" % (chat.Id, chat.FirstName)
            elif chat.Type == 'group' or chat.Type == 'supergroup':
                msgtext += "[%s] %s\n" % (chat.Id, chat.Title)
            if len(msgtext) > 4096:
                msgtext = msgtext[:4096]
                break
        telegram.send_message(msg.Chat.Id, msgtext)

    elif cmdstr.startswith('match'):
        data = cmd.Data  # type:MatchData
        logger.debug("[%s] Adding matches: %s", cmd.Command, str(data.Words))

        if cmdstr == 'matchwords':
            mode = WordMatchMode.WHOLE
        elif cmdstr == 'matchany':
            mode = WordMatchMode.ANY
        else:
            mode = WordMatchMode.MSG

        WordMatchResponse.add_list_from_message(data.Words, data.Responses, mode, msg)
        telegram.send_message(msg.Chat.Id, "Comando aggiunto! ")
    elif cmdstr == 'listmatching':
        s = cmd.Data
        matching = []  # type: list[WordMatchResponse]
        for r in WordMatchResponse.List:
            if r.matches(s):
                matching.append(r)

        msgtext = 'Comandi corrispondenti: \n'
        for m in matching:
            msgtext += '--id: ' + str(m.Id) + ' -> ' + WordMatchMode.to_string(m.Mode) + ' ' + \
                       list_strings(m.Matchwords) + ' : ' + list_strings(m.Responses) + '\n'

        telegram.send_message(msg.Chat.Id, msgtext)
    elif cmdstr.startswith('add'):
        data = cmd.Data  # type:AddData

        if cmdstr == 'addwords':
            word = 'parole'
            table = WordMatchResponse.WORDS_TABLE
            cols = WordMatchResponse.WORD_COLS
        else:
            word = 'risposte'
            table = WordMatchResponse.RESPONSES_TABLE
            cols = WordMatchResponse.RESP_COLS

        id = data.Id

        succ = 0
        error = False
        for s in data.Strings:
            r = Database.insert(table, cols, [s, id])
            if r:
                succ += 1
            else:
                error = True
                break
        if not error:
            telegram.send_message(msg.Chat.Id, word + " aggiunte con successo.")
        else:
            msgtext = "Errore: %d su %d %s aggiunte con successo" % (succ, len(data.Strings), word)
            telegram.send_message(msg.Chat.Id, msgtext)
        if succ > 0:
            reload_commands()
    elif cmdstr.startswith('remove'):
        id = cmd.Data  # type:str
        table = Command.TABLE
        col = Command.COL_ID

        success = Database.delete(table, [(col, id)])
        if success:
            telegram.send_message(msg.Chat.Id, "Comando rimosso con successo.")
            reload_commands()
        else:
            telegram.send_message(msg.Chat.Id, "Errore rimozione comando.")
    return True


load_commands()
load_chats()

def evaluate(telegram: TelegramApi, update: TelegramApi.Update):
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

    if is_command(msg):
        handle_command_str(msg, telegram)
    else:
        # send eventual messages
        for response in WordMatchResponse.List:
            if response.matches(msg.Text):
                response.reply(msg, telegram)
                response.increment_match_counter()


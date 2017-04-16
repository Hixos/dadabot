import io
import os.path

import requests
from dadabot.responses import WordMatchResponse, WordMatchMode
from dadabot.shared_data import Constants
from dadabot.telegramapi import TelegramApi
from dadabot.data import Database

from dadabot.commandparser import parse_command, ParseResult, MatchData, AddData
from dadabot.logs import logger

commands_file = 'commands.txt'

cmd_url = 'http://dadabot.altervista.org/'
cmds_get_url = cmd_url + 'getcommands.php'
cmds_add_url = cmd_url + 'addcommand.php'


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


def reload_commands():
    load_commands()


def exec_command(cmd: ParseResult, msg: TelegramApi.Message, telegram: TelegramApi):
    cmdstr = cmd.Command  # type: str
    if cmdstr.startswith('match'):
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

        msgtext = 'Comandi corrispondendti: \n'
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


load_commands()


def evaluate(telegram: TelegramApi, update: TelegramApi.Update):
    if not update.has_message():
        logger.warning('Eval: Update with no message')
        return

    msg = update.Message

    logger.info("Received message: " + msg.Text)
    text = msg.Text.replace('\n', ' ').replace('\r', '')  # type: str
    cmd = parse_command(text)

    if cmd.Found:
        if text.startswith('!') and cmd.Op.Result:  # Special commands
            logger.info('Received special command:' + text)
            if text == '!reload':
                reload_commands()
                telegram.send_message(msg.Chat.Id, 'Comandi ricaricati.')
            else:
                telegram.send_message(msg.Chat.Id, cmd.Data)

        elif cmd.Op.Result:
            logger.info('Adding received command:' + text)

            exec_command(cmd, msg, telegram)

        else:
            logger.info('Command contains errors:' + text + " -- " + cmd.Op.Text + "(" + str(cmd.Op.Index) + ")")
            telegram.send_message(msg.Chat.Id, "Errore: " + cmd.Op.Text + ". Posizione: " + str(cmd.Op.Index))

        return

    logger.debug("Iterating answers (%d):", len(WordMatchResponse.List))
    for response in WordMatchResponse.List:
        logger.debug('Answer: %s', response.Matchwords[0])
        if response.matches(msg.Text):
            logger.debug('Matched: %s', response.Matchwords[0])
            response.reply(msg, telegram)

import io
import os.path

import requests
from dadabot.responses import WordMatchResponse, WordMatchMode
from dadabot.shared_data import Constants
from dadabot.telegramapi import TelegramApi

from dadabot.commandparser import parse_command, ParseResult, ResponseData
from dadabot.logs import logger

commands_file = 'commands.txt'

cmd_url = 'http://dadabot.altervista.org/'
cmds_get_url = cmd_url + 'getcommands.php'
cmds_add_url = cmd_url + 'addcommand.php'


def exec_command(cmd: ParseResult, msg: TelegramApi.Message):
    cmdstr = cmd.Command  # type: str
    if cmdstr.startswith('match'):
        data = cmd.Data  # type:ResponseData
        logger.debug("[%s] Adding matches: %s", cmd.Command, str(data.Words))

        if cmdstr == 'matchwords':
            mode = WordMatchMode.WHOLE
        elif cmdstr == 'matchany':
            mode = WordMatchMode.ANY
        else:
            mode = WordMatchMode.MSG

        WordMatchResponse.add_list_from_message(data.Words, data.Responses, mode, msg)


def load_commands():
    WordMatchResponse.add_list_from_database()


def reload_commands():
    load_commands()


load_commands()


def save_command(cmd: str):
    file = open(commands_file, 'a+')
    file.write(cmd + '\n')
    file.close()


def save_command_remote(cmd: str):
    params = {'skey': Constants.API_KEY, 'cmd': cmd}
    response = requests.post(cmds_add_url, json=params)
    return response.text.startswith('ok')


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

            error = ''
            if not save_command_remote(text):
                logger.info('Error adding cmd to remote server:')
                error = 'Comando non salvato, verrà dimenticato in breve tempo. RIP.'

            exec_command(cmd, msg)
            telegram.send_message(msg.Chat.Id, "Comando aggiunto! " + error)
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

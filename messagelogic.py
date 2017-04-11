from logs import logger
import os.path
import requests
import io

from commandparser import parse_command, ParseResult, ResponseData
from responses import WordMatchResponse, WordMatchMode
from telegramapi import TelegramApi
from shared_data import api_key

commands_file = 'commands.txt'

cmd_url = 'http://dadabot.altervista.org/'
cmds_get_url = cmd_url + 'getcommands.php'
cmds_add_url = cmd_url + 'addcommand.php'

responses = []  # type: list[WordMatchResponse]


def exec_command(cmd: ParseResult):
    cmdstr = cmd.Command  # type: str
    if cmdstr.startswith('match'):
        data = cmd.Data  # type:ResponseData
        logger.debug("[%s] Adding matches: %s", cmd.Command, str(data.Words))

        if cmdstr == 'matchword':
            mode = WordMatchMode.WHOLE
        elif cmdstr == 'matchany':
            mode = WordMatchMode.ANY
        else:
            mode = WordMatchMode.EXACT

        responses.append(WordMatchResponse(data.Words, data.Responses, mode))


def load_commands():
    if not os.path.isfile(commands_file):
        logger.warning("Commands file does not exist, cannot load commands")
        return

    file = open(commands_file, 'r')

    while True:
        cmdstr = file.readline()
        if len(cmdstr) > 1:
            cmdstr = cmdstr[0:-1]
            logger.debug("Loading command: " + cmdstr)
            cmd = parse_command(cmdstr)

            if cmd.Found and cmd.Op.Result:
                exec_command(cmd)
            else:
                logger.error("Cannot execute loaded command: " + str(cmd))
        else:
            break

    file.close()

#load_commands()


def load_commands_remote():
    params = {'skey': api_key}
    commands = requests.post(cmds_get_url, json=params).text
    file = io.StringIO(commands)
    while True:
        cmdstr = file.readline()
        if len(cmdstr) > 1:
            cmdstr = cmdstr[0:-1]
            logger.debug("Loading command: " + cmdstr)
            cmd = parse_command(cmdstr)

            if cmd.Found and cmd.Op.Result:
                exec_command(cmd)
            else:
                logger.error("Cannot execute loaded command: " + cmdstr)
        else:
            break

load_commands_remote()


def save_command(cmd: str):
    file = open(commands_file, 'a+')
    file.write(cmd + '\n')
    file.close()


def save_command_remote(cmd: str):
    params = {'skey': api_key, 'cmd': cmd}
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
            telegram.send_message(msg.Chat.Id, cmd.Data)

        elif cmd.Op.Result:
            logger.info('Adding received command:' + text)

            error = ''
            if not save_command_remote(text):
                logger.info('Error adding cmd to remote server:')
                error = 'Comando non salvato, verrà dimenticato in breve tempo. RIP.'

            exec_command(cmd)
            telegram.send_message(msg.Chat.Id, "Comando aggiunto! " + error)
        else:
            logger.info('Command contains errors:' + text + " -- " + cmd.Op.Text + "(" + str(cmd.Op.Index) + ")")
            telegram.send_message(msg.Chat.Id, "Errore: " + cmd.Op.Text + ". Posizione: " + str(cmd.Op.Index))

        return

    logger.debug("Iterating answers (%d):", len(responses))
    for answer in responses:
        logger.debug('Answer: %s', answer.Matchwords[0])
        if answer.matches(msg.Text):
            logger.debug('Matched: %s', answer.Matchwords[0])
            answer.reply(msg, telegram)

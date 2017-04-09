from logs import logger
import os.path

from commandparser import parse_command, ParseResult, AnswerData
from answers import SingleWordMatchAnswer
from telegramapi import TelegramApi

commands_file = 'commands.txt'

answers = []  # type: list[SingleWordMatchAnswer]


def contains(msg_text: str, words):
    for w in words:
        if msg_text.lower().find(w) >= 0:
            return True

    return False


def exec_command(cmd: ParseResult):
    if cmd.Command == 'addanswer':
        data = cmd.Data  # type:AnswerData
        logger.debug("[%s] Adding matches: %s", cmd.Command, str(data.Words))
        answers.append(SingleWordMatchAnswer(data.Words, data.Answers))


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

load_commands()


def save_command(cmd: str):
    file = open(commands_file, 'a+')
    file.write(cmd + '\n')
    file.close()


def evaluate(telegram: TelegramApi, update: TelegramApi.Update):
    if not update.has_message():
        logger.warning('Eval: Update with no message')
        return

    msg = update.Message

    logger.info("Received message: " + msg.Text)
    text = msg.Text.replace('\n', ' ').replace('\r', '')  # type: str
    cmd = parse_command(text)

    if cmd.Found:
        if cmd.Op.Result:
            logger.info('Adding received command:' + text)

            save_command(text)
            exec_command(cmd)
            telegram.send_message(msg.Chat.Id, "Comando aggiunto!")
        else:
            logger.info('Command contains errors:' + text + " -- " + cmd.Op.Text + "(" + str(cmd.Op.Index) + ")")
            telegram.send_message(msg.Chat.Id, "Errore: " + cmd.Op.Text + ". Posizione: " + str(cmd.Op.Index))

        return

    logger.debug("Iterating answers (%d):", len(answers))
    for answer in answers:
        logger.debug('Answer: %s', answer.Matchwords[0])
        if answer.matches(msg.Text):
            logger.debug('Matched: %s', answer.Matchwords[0])
            answer.answer(msg, telegram)

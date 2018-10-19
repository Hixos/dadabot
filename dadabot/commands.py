from dadabot.commandparser import *
from dadabot.telegramapi import TelegramApi
from dadabot.data import Database, Command, WordMatchResponse, WordMatchMode
from dadabot.logs import logger
from dadabot.shared_data import Constants

last_match_cmdid = {}


def notify_new_match(last_cmdid, chat_id):
    global last_match_cmdid
    last_match_cmdid[chat_id] = last_cmdid


def gen_command(cmdname, parse_func, exec_func):
    return {
        'cmdname': cmdname,
        'cmdregex': re.compile('(?P<cmd>{}(?:@{})?)(?:$|\s+)'.format(cmdname, Constants.BOT_NAME)),
        'parse_func': parse_func,
        'exec_func': exec_func
    }


def is_command(msg: TelegramApi.Message):
    return msg.Text.strip().startswith("/")


def exec_match(cmd: str, cmddata: dict, msg: TelegramApi.Message, telegram: TelegramApi):
    logger.debug("exec_match")

    if cmd == '/match':
        mode = WordMatchMode.WORD
    elif cmd == '/matchany':
        mode = WordMatchMode.ANY
    elif cmd == '/matchmsg':
        mode = WordMatchMode.WHOLEMSG
    else:
        mode = None

    if cmddata is None or mode is None:
        telegram.send_message(msg.Chat.Id,
                              "Utilizzo:\n{}\nparole 1\nparole 2\nparole N\n\nrisposte 1\nrisposte 2\nrisposte N"
                              .format("/match[any|msg]"))
        return

    WordMatchResponse.add_to_list_from_message(cmddata['matchwords'], cmddata['responses'], mode, msg)
    telegram.send_message(msg.Chat.Id, "Comando aggiunto!")


def exec_remove(cmd: str, cmddata: dict, msg: TelegramApi.Message, telegram: TelegramApi):
    if cmddata is None:
        telegram.send_message(msg.Chat.Id, "Utilizzo:\n/remove <id>")
        return

    id = cmddata['id']  # type:int
    table = Command.TABLE
    col = Command.COL_ID

    success = Database.delete(table, [(col, id)])
    if success:
        telegram.send_message(msg.Chat.Id, "Comando rimosso con successo.")
        WordMatchResponse.load_list_from_database()
    else:
        telegram.send_message(msg.Chat.Id, "Nessun messaggio con l'id specificato: {}.".format(cmddata['id']))


def list_strings(l: list) -> str:
    out = ""
    for s in l:
        out += s + ", "

    return out[:-2]


def exec_list(cmd: str, cmddata: dict, msg: TelegramApi.Message, telegram: TelegramApi):
    if cmddata is None:
        telegram.send_message(msg.Chat.Id, "Utilizzo:\n/listmatching <messaggio da matchare>")
        return

    s = cmddata['str']

    matching = []  # type: list
    for r in WordMatchResponse.List:
        if r.matches(s):
            matching.append(r)

    msgtext = 'Comandi corrispondenti: \n'
    for m in matching:
        msgtext += 'id: ' + str(m.Id) + ' -> ' + WordMatchMode.to_string(m.Mode) + "\n" \
                   + "Match: " + list_strings(m.Matchwords) + '\nRisposte: ' + list_strings(m.Responses) + '\n'

    msgtext += "\nUsa /cmdinfo <cmdid> per ottenere ulteriori informazioni."

    telegram.send_message(msg.Chat.Id, msgtext)


def exec_cmdinfo(cmd: str, cmddata: dict, msg: TelegramApi.Message, telegram: TelegramApi):
    if cmddata is None:
        telegram.send_message(msg.Chat.Id, "Utilizzo:\n/cmdinfo [cmdid]")
        return
    if cmddata['hasid']:
        cmdid = cmddata['id']
    else:
        cmdid = last_match_cmdid.get(msg.Chat.Id)
        if cmdid is None:
            telegram.send_message(msg.Chat.Id, "Nessun comando utlizzato recentemente.")
            return

    for wmr in WordMatchResponse.List:  # type: WordMatchResponse
        if wmr.Id == cmdid:
            msgtext = 'id: ' + str(wmr.Id) + ' -> ' + WordMatchMode.to_string(wmr.Mode) + "\n" \
                       + "Match: " + list_strings(wmr.Matchwords) + '\nRisposte: ' + list_strings(wmr.Responses) + '\n'
            msgtext += 'creator: ' + wmr.User.FirstName + ' ' + wmr.User.LastName + ' ' + wmr.User.Username + '\n'
            msgtext += 'count: ' + str(wmr.MatchCounter)

            telegram.send_message(msg.Chat.Id, msgtext)
            return
    telegram.send_message(msg.Chat.Id, "Nessun messaggio con l'id specificato: {}.".format(cmddata['id']))


def exec_cmdcount(cmd: str, cmddata: dict, msg: TelegramApi.Message, telegram: TelegramApi):
    if cmddata is None:
        telegram.send_message(msg.Chat.Id, "Utilizzo:\n/count [cmdid]")
        return
    if cmddata['hasid']:
        cmdid = cmddata['id']
        msgstr = "Il comando n. {}"
    else:
        cmdid = last_match_cmdid.get(msg.Chat.Id)
        msgstr = "L'ultimo comando (n. {})"
        if cmdid is None:
            telegram.send_message(msg.Chat.Id, "Nessun comando utlizzato recentemente.")
            return

    for wmr in WordMatchResponse.List:  # type: WordMatchResponse
        if wmr.Id == cmdid:
            telegram.send_message(msg.Chat.Id, "{} è stato utilizzato {} volt{}"
                                  .format(msgstr.format(cmdid), wmr.MatchCounter, 'a' if wmr.MatchCounter == 1 else 'e'))
            return

    telegram.send_message(msg.Chat.Id, "Nessun messaggio con l'id specificato: {}.".format(cmddata['id']))

commands = [
    gen_command("/match", parse_match, exec_match),
    gen_command("/matchany", parse_match, exec_match),
    gen_command("/matchmsg", parse_match, exec_match),
    gen_command("/remove", parse_id, exec_remove),
    #gen_command("/removelast", parse_id, exec_remove),
    gen_command("/listmatching", parse_str, exec_list),
    gen_command("/cmdinfo", parse_id_or_empty, exec_cmdinfo),
    gen_command("/count", parse_id_or_empty, exec_cmdcount)
]


def handle_command_str(msg: TelegramApi.Message, telegram: TelegramApi):
    txt = msg.Text.lstrip()
    logger.info("Handling command: " + txt)

    for cmd in commands:
        m = cmd['cmdregex'].match(txt)
        if m is not None:
            txt = txt[m.end('cmd'):]
            logger.debug("Command identified: " + cmd['cmdname'])
            cmd['exec_func'](cmd['cmdname'], cmd['parse_func'](txt.splitlines()), msg, telegram)
            return True
    return False

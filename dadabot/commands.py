from dadabot.commandparser import *
from dadabot.telegramapi import TelegramApi
from dadabot.data import Database, Command, WordMatchResponse, WordMatchMode
from dadabot.logs import logger
from dadabot.shared_data import Constants

import re

last_match_cmdid = {}

active_commands = {}


def get_user_chat_id(msg: TelegramApi.Message):
    return str(msg.Chat.Id) + str(msg.Sender.Id)


def notify_new_match(last_cmdid, chat_id):
    global last_match_cmdid
    last_match_cmdid[chat_id] = last_cmdid


def matches_command(string, cmdname):
    return re.match('(?P<cmd>{}(?:@{})?)(?:$|\s+)'.format(cmdname, Constants.BOT_NAME), string) is not None


def gen_command(cmdname, parse_func, exec_func):
    return {
        'cmdname': cmdname,
        'cmdregex': re.compile('(?P<cmd>{}(?:@{})?)(?:$|\s+)'.format(cmdname, Constants.BOT_NAME)),
        'parse_func': parse_func,
        'exec_func': exec_func
    }


def is_command(msg: TelegramApi.Message):
    return msg.Text.strip().startswith("/")


def send_match_help(msg: TelegramApi.Message, telegram: TelegramApi):
    telegram.send_message(msg.Chat.Id,
                          "Utilizzo:\n{} -[a|s]\nparole 1\nparole 2\nparole N\n\nrisposte 1\nrisposte 2\nrisposte N"
                          .format("/match[any|msg]"))


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
        send_match_help(msg, telegram)
        return

    p = cmddata['params']
    if 'm' in p:
        exec_match_media(cmd, mode, cmddata, msg, telegram)
    else:
        exec_match_oneshot(cmd, mode, cmddata, msg, telegram)


def exec_match_oneshot(cmd: str, mode, cmddata: dict, msg: TelegramApi.Message, telegram: TelegramApi):
    if len(cmddata['responses']) == 0:
        send_match_help(msg, telegram)
        return

    responses = [{'response': x, 'type': 'text'} for x in cmddata['responses']]
    WordMatchResponse.add_to_list_from_message(cmddata['matchwords'], responses, mode, 'a' in cmddata['params'], msg)
    telegram.send_message(msg.Chat.Id, "Comando aggiunto!")


def func_save_media(msg: TelegramApi.Message, telegram: TelegramApi):
    logger.debug("func_save_media")
    sender_id = get_user_chat_id(msg)
    if msg.is_media():
        if msg.is_sticker():
            active_commands[sender_id]['media_responses'].append({"fileid": msg.Sticker.FileId, "type": "sticker"})
        elif msg.is_photo():
            active_commands[sender_id]['media_responses'].append({"fileid": msg.Photo.FileId, "type": "photo"})
        elif msg.is_animation():
            active_commands[sender_id]['media_responses'].append({"fileid": msg.Animation.FileId, "type": "animation"})
        else:
            logger.error("Media type not recognized")
            return
    elif matches_command(msg.Text, '/end'):
        responses = [{'response': x, 'type': 'text'} for x in active_commands[sender_id]['text_responses']]

        responses += [{'response': x["fileid"], 'type': x["type"]} for x in active_commands[sender_id]['media_responses']]

        if len(responses) == 0:
            telegram.send_message(msg.Chat.Id,
                                  "Utilizzo:\n{}\nparole 1\nparole 2\nparole N\n\n[risposte 1]\n[risposte 2]\n[risposte N]"
                                  .format("/match[msg|any] [-(m|s)]") + "\n\n-->In nuovi messaggi: eventuali sticker.")
        else:
            reply = 'a' in active_commands[sender_id]['params']

            WordMatchResponse.add_to_list_from_message(active_commands[sender_id]['matchwords'], responses,
                                                       active_commands[sender_id]['mode'], reply, msg)

            telegram.send_message(msg.Chat.Id, "Comando aggiunto!")

        del active_commands[sender_id]

    elif matches_command(msg.Text, '/cancel'):
        del active_commands[sender_id]
        telegram.send_message(msg.Chat.Id, "Comando annullato.")

    else:
        fail_count = active_commands[sender_id].get('fail_count', 0)
        active_commands[sender_id]['fail_count'] = fail_count + 1

        if fail_count < 2:
            telegram.send_message(msg.Chat.Id, "{}, Scrivi /end per terminare l'aggiunta di media, /cancel per annullarla."
                                  .format(msg.Sender.FirstName))
        elif fail_count == 2:
            telegram.send_message(msg.Chat.Id, "{}, SCRIVI /end OPPURE /cancel PER TERMINARE L'AGGIUNTA DI MEDIA!"
                                  .format(msg.Sender.FirstName))
        else:
            del active_commands[sender_id]
            telegram.send_message(msg.Chat.Id, "Comando annullato.")


def exec_match_media(cmd: str, mode, cmddata: dict, msg: TelegramApi.Message, telegram: TelegramApi):
    logger.debug("exec_match_media")

    if cmddata is None or mode is None:
        logger.error("CmdData is none: {}, mode is none: {}".format(cmddata is None, mode is None))
        telegram.send_message(msg.Chat.Id,
                              "Utilizzo:\n{}\nparole 1\nparole 2\nparole N\n\n[risposte 1]\n[risposte 2]\n[risposte N]"
                              .format("/match[msg|any] [-(s|m)]") + "\n\n-->In nuovi messaggi: eventuali media (sticker, foto, gif).")
        return

    sender_id = get_user_chat_id(msg)
    active_commands[sender_id] = {'cmd': cmd,
                                  'func': func_save_media,
                                  'mode': mode,
                                  'matchwords': cmddata['matchwords'],
                                  'text_responses': cmddata.get('responses', []),
                                  'params': cmddata['params'],
                                  'media_responses': []
                                  }

    telegram.send_message(msg.Chat.Id, "Ora manda i media. Scrivi /end quando hai finito, /cancel per annullare.")


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
                   + "Match: " + list_strings(m.Matchwords) + '\nRisposte: ' \
                   + list_strings([x['response'] if x['type'] == 'text' else "Media: " + x['response']
                                   for x in m.Responses]) + '\n'

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
                       + "Match: " + list_strings(wmr.Matchwords) + '\nRisposte: ' \
                      + list_strings([x['response'] if x['type'] == 'text' else "Media: " + x['response']
                                      for x in wmr.Responses]) + '\n'
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


def exec_donothing(cmd: str, cmddata: dict, msg: TelegramApi.Message, telegram: TelegramApi):
    return

commands = [
    gen_command("/match", parse_match, exec_match),
    gen_command("/matchany", parse_match, exec_match),
    gen_command("/matchmsg", parse_match, exec_match),

    gen_command("/remove", parse_id, exec_remove),
    #gen_command("/removelast", parse_id, exec_remove),
    gen_command("/listmatching", parse_str, exec_list),
    gen_command("/cmdinfo", parse_id_or_empty, exec_cmdinfo),
    gen_command("/count", parse_id_or_empty, exec_cmdcount),

    gen_command("/end", parse_nothing, exec_donothing),
    gen_command("/cancel", parse_nothing, exec_donothing)
]


def handle_command_str(msg: TelegramApi.Message, telegram: TelegramApi):
    sender_id = get_user_chat_id(msg)
    if sender_id in active_commands:
        active_commands[sender_id]['func'](msg, telegram)
        return True
    elif is_command(msg):
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

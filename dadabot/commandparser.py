import collections
import re

StrOp = collections.namedtuple('StrOp', ['Index', 'Result', 'Text'])

ParseResult = collections.namedtuple('ParseResult', ['Found', 'Command', 'Op', 'Data'])

MatchData = collections.namedtuple('ResponseData', ['Words', 'Responses'])

AddData = collections.namedtuple('AddData', ['Id', 'Strings'])

text_delimiter = '"'

dic_result = 'Op'


def skip_whitespaces(s: str, i: int):
    while i < len(s):
        c = s[i]
        if c == ' ':
            i += 1
        else:
            return StrOp(i, True, '')

    return StrOp(i, False, 'EOS')


def read_text(s: str, i: int):
    text = ''
    force_read = False

    while i < len(s):
        c = s[i]
        if force_read:
            if c == "\"":
                text += c
            else:
                text += "\\"
            force_read = False
        elif c == '\\':
            force_read = True
        elif c == text_delimiter:
            i += 1
            return StrOp(i, True, text)
        else:
            text += c

        i += 1

    return StrOp(i, False, 'EOS')


def parse_removematching(cmd: str):  # TODO: Finish implementation
    match_words = []

    i = 0

    can_proceed = True
    clean_end = False

    while i < len(cmd):
        r = skip_whitespaces(cmd, i)
        if r.Result:
            i = r.Index
        else:
            return {dic_result, r}

        if cmd[i] == text_delimiter:
            if not can_proceed:
                return {dic_result: StrOp(i, False, "Virgole mancanti")}

            r = read_text(cmd, i+1)
            if r.Result:
                i = r.Index
                match_words.append(r.Text)
                clean_end = True
            else:
                return {dic_result, r}

        elif len(match_words) == 0:
            return {dic_result: StrOp(i, False, 'Non hai specificato nessuna parola!')}

        elif cmd[i] == ',':
            i += 1
            can_proceed = True
            continue
        else:
            return {dic_result: StrOp(i, False, 'Errore di sintassi')}

        can_proceed = False


def parse_match(cmd: str):
    section = 0
    clean_end = False
    can_proceed = True

    match_words = []
    responses = []

    i = 0

    while i < len(cmd):
        clean_end = False

        r = skip_whitespaces(cmd, i)
        if r.Result:
            i = r.Index
        else:
            return {dic_result: r}

        if cmd[i] == text_delimiter:
            if not can_proceed:
                return {dic_result: StrOp(i, False, "Virgole mancanti")}

            r = read_text(cmd, i + 1)
            if r.Result:
                i = r.Index
                if section == 0:
                    match_words.append(r.Text)
                elif section == 1:
                    responses.append(r.Text)
                    clean_end = True
            else:
                return {dic_result: r}
        elif len(match_words) == 0:
            return {dic_result: StrOp(i, False, 'Non hai specificato nessuna parola!')}
        elif cmd[i] == ',':
            i += 1
            can_proceed = True
            continue
        elif cmd[i] == ':':
            i += 1
            section += 1
            can_proceed = True
            if section > 1:
                return {dic_result: StrOp(i, False, 'Il comando non termina correttamente')}

            continue
        else:
            return {dic_result: StrOp(i, False, 'Errore di sintassi')}

        can_proceed = False

    if clean_end:
        return {dic_result: StrOp(i, True, ''), 'Data': MatchData(match_words, responses)}
    elif len(responses) == 0:
        return {dic_result: StrOp(i, False, 'Non hai scritto nessuna risposta!')}
    else:
        return {dic_result: StrOp(i, False, 'Errore di sintassi')}


def parse_add(cmd: str):
    section = 0
    clean_end = False
    can_proceed = True

    id = -1
    strings = []

    i = 0

    while i < len(cmd):
        clean_end = False

        r = skip_whitespaces(cmd, i)
        if r.Result:
            i = r.Index
        else:
            return {dic_result: r}

        if cmd[i] == text_delimiter:
            if not can_proceed:
                return {dic_result: StrOp(i, False, "Virgole mancanti")}

            r = read_text(cmd, i + 1)
            if r.Result:
                i = r.Index
                if section == 0:
                    try:
                        id = int(r.Text)
                    except ValueError:
                        return {dic_result: StrOp(i, False, 'Non hai specificato un indice!')}
                elif section == 1:
                    strings.append(r.Text)
                    clean_end = True
            else:
                return {dic_result: r}
        elif id == -1:
            return {dic_result: StrOp(i, False, 'Non hai specificato un indice!')}
        elif cmd[i] == ',':
            if section == 0:
                return {dic_result: StrOp(i, False, 'Specifica un solo indice!')}
            i += 1
            can_proceed = True
            continue
        elif cmd[i] == ':':
            i += 1
            section += 1
            can_proceed = True
            if section > 1:
                return {dic_result: StrOp(i, False, 'Il comando non termina correttamente')}

            continue
        else:
            return {dic_result: StrOp(i, False, 'Errore di sintassi')}

        can_proceed = False

    if clean_end:
        return {dic_result: StrOp(i, True, ''), 'Data': AddData(id, strings)}
    elif len(strings) == 0:
        return {dic_result: StrOp(i, False, 'Non hai scritto nessuna risposta!')}
    else:
        return {dic_result: StrOp(i, False, 'Errore di sintassi')}


def parse_id(cmd: str):
    i = 0

    r = skip_whitespaces(cmd, i)
    if r.Result:
        i = r.Index
    else:
        return {dic_result: r}

    if cmd[i] == text_delimiter:

        r = read_text(cmd, i + 1)
        if r.Result:
            i = r.Index
            return {dic_result: StrOp(i, True, ''), 'Data': r.Text}
        else:
            return {dic_result: r}
    else:
        return {dic_result: StrOp(i, False, 'Errore di sintassi')}


def display_args(cmd:str):
    str1 = '1: Msg\n--Id\n--Sender (Vedi 2)\n--Date\n--Chat (Vedi 3)\n--Text\n\n'
    str2 = '2: Sender\n--Id\n--FirstName\n--LastName\n--Username\n\n'
    str3 = '3: Chat\n--Id\n--Type\n--Title\n--FirstName\n--LastName\n--Username\n\n'
    str4 = 'Esempio: "{Msg.Sender.FirstName} è il vero nome di {Msg.Sender.Username}"'

    msg = str1 + str2 + str3 + str4

    if len(cmd) == 0:
        return {dic_result: StrOp(0, True, ''), 'Data': msg}
    else:
        return {dic_result: StrOp(0, False, '')}


def display_help(cmd: str):
    str1 = '!match - Guida aggiunta risposte automatiche\n\n'
    str2 = '!msgargs - Guida stringhe speciali nella risposta'

    msg = str1 + str2

    if len(cmd) == 0:
        return {dic_result: StrOp(0, True, ''), 'Data': msg}
    else:
        return {dic_result: StrOp(0, False, '')}


def display_match(cmd: str):
    msg = 'Esempio: \nmatchwords "parola1", "parola2", "parolaN": "risposta1", "risposta2", "rispostaN"\n' \
           'Comandi disponibili: matchwords, matchany, matchmsg'

    if len(cmd) == 0:
        return {dic_result: StrOp(0, True, ''), 'Data': msg}
    else:
        return {dic_result: StrOp(0, False, '')}


def check_no_more_data(cmd: str):
    if len(cmd) == 0:
        return {dic_result: StrOp(0, True, ''), 'Data': ''}
    else:
        return {dic_result: StrOp(0, False, '')}


def echo(cmd: str):
    if len(cmd) == 0:
        return {dic_result: StrOp(0, True, ''), 'Data': 0}

    data = re.search('^[ ]+?(-?[\d]+)?$', cmd, re.IGNORECASE)
    if data is not None:
        id = int(data.group(1))
        return {dic_result: StrOp(0, True, ''), 'Data': id}

    return {dic_result: StrOp(0, False, '')}

commands = [
    ('matchwords', parse_match),
    ('matchany', parse_match),
    ('matchmsg', parse_match),
    ('listmatching', parse_id),
    ('addwords', parse_add),
    ('addresponses', parse_add),
    ('remove', parse_id),

    ('listchats', check_no_more_data),
    ('echo', echo),

    ('!msgargs', display_args),
    ('!help', display_help),
    ('!match', display_match),
    ('!reload', check_no_more_data)
]


def parse_command(cmdstr: str):
    for cmd in commands:
        cmdlen = len(cmd[0])

        if cmdstr.lower().startswith(cmd[0]) and len(cmdstr) >= cmdlen:
            r = cmd[1](cmdstr[cmdlen:])
            return ParseResult(True, cmd[0], r['Op'], r.get('Data', None))

    return ParseResult(False, '', None, None)


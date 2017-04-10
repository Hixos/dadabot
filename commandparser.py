import collections
from logs import logger

StrOp = collections.namedtuple('StrOp', ['Index', 'Result', 'Text'])

ParseResult = collections.namedtuple('ParseResult', ['Found', 'Command', 'Op', 'Data'])

AnswerData = collections.namedtuple('AnswerData', ['Words', 'Answers'])

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
            text += c
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


def parse_addanswer(cmd: str):
    section = 0
    clean_end = False
    can_proceed = True

    match_words = []
    answers = []

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
                    answers.append(r.Text)
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
        return {dic_result: StrOp(i, True, ''), 'Data': AnswerData(match_words, answers)}
    elif len(answers) == 0:
        return {dic_result: StrOp(i, False, 'Non hai scritto nessuna risposta!')}
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
    str1 = '!addanswer - Guida aggiunta risposte automatiche\n\n'
    str2 = '!msgargs - Guida stringhe speciali nella risposta'

    msg = str1 + str2

    if len(cmd) == 0:
        return {dic_result: StrOp(0, True, ''), 'Data': msg}
    else:
        return {dic_result: StrOp(0, False, '')}


def display_addanwer(cmd: str):
    str1 = 'addanswer "parola1", "parola2", "parolaN": "risposta1", "risposta2", "rispostaN"'

    msg = str1

    if len(cmd) == 0:
        return {dic_result: StrOp(0, True, ''), 'Data': msg}
    else:
        return {dic_result: StrOp(0, False, '')}

commands = [
    ('addanswer', parse_addanswer),

    ('!msgargs', display_args),
    ('!help', display_help),
    ('!addanswer', display_addanwer)
]


def parse_command(cmdstr: str):
    for cmd in commands:
        cmdlen = len(cmd[0])

        if cmdstr.lower().startswith(cmd[0]) and len(cmdstr) >= cmdlen:
            r = cmd[1](cmdstr[cmdlen:])
            return ParseResult(True, cmd[0], r['Op'], r.get('Data', None))

    return ParseResult(False, '', None, None)


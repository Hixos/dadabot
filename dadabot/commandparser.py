import collections
import re


def parse_match(lines: list):
    re_continueline = re.compile(r'/\s*$')

    state = 0
    parsing_continued_line = False

    if len(lines) == 0 or not is_empty(lines[0]):
        return None

    matchwords: list = []
    responses: list = []

    for l in lines[1:]:
        if not parsing_continued_line:
            if is_empty(l):
                if state == 0:
                    if len(matchwords) == 0:
                        return None
                    else:
                        state += 1
                        continue
                elif state == 1:
                    return None

        m = re_continueline.search(l)

        if m is not None:
            l = l[:m.start(0)]

        if parsing_continued_line:
            if state == 0:
                matchwords[-1] += "\n" + _unescape(l)
            else:
                responses[-1] += "\n" + _unescape(l)
        else:
            if state == 0:
                matchwords.append(_unescape(l))
            else:
                responses.append(_unescape(l))

        parsing_continued_line = m is not None

    if len(responses) > 0:
        return {'matchwords': matchwords, 'responses': responses}
    else:
        return None


def is_empty(string: str, start=0):
    re_empty = re.compile(r"\s*")
    return re_empty.fullmatch(string, start) is not None


def parse_add(lines: list):
    re_id = re.compile(r'\s*(?P<id>\d+)\s*$')
    re_continueline = re.compile(r'/\s*$')

    state = 0
    parsing_continued_line = False

    cmdid = 0
    words: list = []

    for l in lines:
        if not parsing_continued_line:
            if is_empty(l):
                return None

        if state == 0:
            m = re_id.fullmatch(l)
            if m is not None:
                cmdid = int(m.group('id'))
                state += 1
                continue
            return None

        m = re_continueline.search(l)

        if m is not None:
            l = l[:m.start(0)]

        if parsing_continued_line:
            words[-1] += "\n" + _unescape(l)
        else:
            words.append(_unescape(l))

        parsing_continued_line = m is not None

    if len(words) > 0:
        return {'id': cmdid, 'words': words}
    else:
        return None


def parse_id(lines: list):
    if len(lines) != 1:
        return None

    re_id = re.compile(r'\s*(?P<id>\d+)\s*$')

    m = re_id.fullmatch(lines[0])
    if m is not None:
        cmdid = int(m.group('id'))
        return {'id': cmdid}

    return None


def parse_id_or_empty(lines: list):
    if len(lines) > 1:
        return None

    if len(lines) == 0:
        return {'hasid': False}

    re_id = re.compile(r'(\s*|\s*(?P<id>\d+)\s*)')

    m = re_id.fullmatch(lines[0])
    if m is not None:
        cmdid = m.group('id')
        if id is None:
            return {'hasid': False}
        else:
            return {'hasid': True,
                    'id': int(cmdid)}

    return None


def parse_str(lines: list):
    if len(lines) != 1:
        return None
    re_str = re.compile(r'\s*(?P<str>.*)')

    m = re_str.fullmatch(lines[0])
    if m is not None:
        string = m.group('str')
        return {'str': string}

    return None


def _unescape(string: str):
    return string.replace(r'\"', '"')


def display_args(lines: list):
    str1 = '1: Msg\n--Id\n--Sender (Vedi 2)\n--Date\n--Chat (Vedi 3)\n--Text\n\n'
    str2 = '2: Sender\n--Id\n--FirstName\n--LastName\n--Username\n\n'
    str3 = '3: Chat\n--Id\n--Type\n--Title\n--FirstName\n--LastName\n--Username\n\n'
    str4 = 'Esempio: "{Msg.Sender.FirstName} è il vero nome di {Msg.Sender.Username}"'

    msg = str1 + str2 + str3 + str4

    if len(lines) == 1:
        return {'data': msg}
    else:
        return None


def nothing_to_parse(lines: list):
    if len(lines) == 1:
        return {}
    else:
        return None


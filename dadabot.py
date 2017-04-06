import requests
import os

if 'API_KEY' in os.environ:
    api_key = os.environ['API_KEY']
else:
    f = open("api_key.txt")
    api_key = f.read()

url = "https://api.telegram.org/bot" + api_key + "/"

last_update_id = 0


def get_string(field, data, default=""):
    if field in data:
        return data[field]
    else:
        return default


def get_int(field, data, default=0):
    if field in data:
        return int(data[field])
    else:
        return default


def get_bool(field, data, default=False):
    if field in data:
        return bool(data[field])
    else:
        return default


class User:
    def __init__(self, data):
        self.Id = int(data['id']);
        self.FirstName = data['first_name']
        self.LastName = get_string('last_name', data)
        self.Username = get_string('username', data)

    def to_string(self):
        return 'USER: ' + str(self.Id) + ' ' + self.FirstName + ' ' + self.LastName + ' ' + self.Username

    def printc(self):
        print(self.to_string() + '\n')


class Chat:
    def __init__(self, data):
        self.Id = int(data['id'])
        self.Type = data['type']
        self.Title = get_string('title', data)
        self.FirstName = get_string('first_name', data)
        self.LastName = get_string('last_name', data)
        self.Username = get_string('username', data)
        self.Every1Admin = get_bool('all_members_are_administrators', data)

    def to_string(self):
        return 'CHAT: ' + str(self.Id) + ' ' + self.Type + ' ' + self.Title + ' ' + self.FirstName

    def printc(self):
        print(self.to_string() + '\n')


class Message:
    def __init__(self, data):
        self.Id = int(data['message_id'])
        self.User = User(data['from']) if 'from' in data else None
        self.Date = get_int('date', data, -1)
        self.Chat = Chat(data['chat'])
        self.Text = get_string('text', data, '')

    def has_user(self) -> bool:
        return self.User is not None

    def to_string(self):
        return 'MESSAGE: ' + str(self.Id) + ' ' + self.User + ' ' + self.Text

    def printc(self):
        print(self.to_string() + '\n')


class Update:
    def __init__(self, data):
        self.Id = int(data['update_id'])
        self.Message = Message(data['message']) if 'message' in data else None

    def has_message(self) -> bool:
        return self.Message is not None

    def to_string(self):
        return 'Update: ' + str(self.Id)

    def printc(self):
        print(self.to_string() + '\n')


def get_updates(url, offset=0):
    req = url + 'getUpdates' + (('?offset=' + str(offset)) if offset != 0 else '')
    print(req + '\n')
    response = requests.get(req)

    json = response.json()
    ok = bool(json['ok'])
    updates = []

    if not ok:
        return updates

    updates_json = json['result']

    for upd in updates_json:
        updates.append(Update(upd))

    return updates

def send_mess(chat, text):
    params = {'chat_id': chat, 'text': text}
    response = requests.post(url + 'sendMessage', data=params)
    return response


def eval_message(msg: Message):
    if msg.Text.lower().__contains__('sushi'):
        send_mess(msg.Chat.Id, 'NO!')


maxid = 0

updates = get_updates(url, 432878842)  # type: list[Update]

for upd in updates:
    if upd.Id > maxid:
        maxid = upd.Id

    if upd.has_message():
        msg = upd.Message
        chat = msg.Chat
        if chat.Username == 'Hixos':
            eval_message(msg)


print(maxid)





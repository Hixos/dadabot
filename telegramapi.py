import requests


class TelegramApi:

    _offset = 0

    class User:
        def __init__(self, data):
            self.Id = int(data.get('id'))
            self.FirstName = data.get('first_name')
            self.LastName = data.get('last_name')
            self.Username = data.get('username')

        def to_string(self):
            return 'USER: ' + str(self.Id) + ' ' + self.FirstName + ' ' + self.LastName + ' ' + self.Username

        def print(self):
            print(self.to_string() + '\n')

    class Chat:
        def __init__(self, data):
            self.Id = int(data.get('id'))
            self.Type = data.get('type', '')
            self.Title = data.get('title', '')
            self.FirstName = data.get('first_name', '')
            self.LastName = data.get('last_name', '')
            self.Username = data.get('username', '')
            self.Every1Admin = bool(data.get('all_members_are_administrators', False))

        def to_string(self):
            return 'CHAT: ' + str(self.Id) + ' ' + self.Type + ' ' + self.Title + ' ' + self.FirstName

        def print(self):
            print(self.to_string() + '\n')

    class Message:
        def __init__(self, data):
            self.Id = int(data.get('message_id'))
            self.User = TelegramApi.User(data.get('from')) if 'from' in data else None
            self.Date = data.get('date', -1)
            self.Chat = TelegramApi.Chat(data.get('chat'))
            self.Text = data.get('text', '')

        def has_user(self) -> bool:
            return self.User is not None

        def to_string(self):
            return 'MESSAGE: ' + str(self.Id) + ' ' + self.User.FirstName + ' ' + self.Text

        def print(self):
            print(self.to_string() + '\n')

    class Update:
        def __init__(self, data):
            self.Id = int(data.get('update_id'))
            self.Message = TelegramApi.Message(data.get('message')) if 'message' in data else None

        def has_message(self) -> bool:
            return self.Message is not None

        def to_string(self):
            return 'Update: ' + str(self.Id)

        def print(self):
            print(self.to_string() + '\n')

    def __init__(self, api_key, app_name):
        self.api_key = api_key
        self.app_name = app_name
        self.url = "https://api.telegram.org/bot" + self.api_key + "/"

    def send_mess(self, chat, text):
        params = {'chat_id': chat, 'text': text}
        response = requests.post(self.url + 'sendMessage', data=params)
        return response

    def set_webhook(self):
        url = 'https://' + self.app_name + '.herokuapp.com/' + self.api_key
        params = {'url': url}
        response = requests.post(self.url + 'setWebhook', data=params)
        print(str(response.raw) + '\n\n')

    def delete_webhook(self):
        url = self.url + 'deleteWebhook'
        result = requests.get(url).json()
        return result.get('result', False)

    @staticmethod
    def _parse_updates(updatejson):
        updates = []

        for upd in updatejson:
            updates.append(TelegramApi.Update(upd))

        return updates

    def _get_updates(self):
        req = self.url + 'getUpdates' + (('?offset=' + str(self._offset)) if self._offset != 0 else '')
        response = requests.get(req).json()

        ok = bool(response.get('ok', True))

        updates = []

        if not ok:
            return updates

        updates_json = response.get('result')

        updates = self._parse_updates(updates_json)  # type: list[TelegramApi.Update]

        for upd in updates:
            if upd.Id >= self._offset:
                self._offset = upd.Id + 1

        return updates

    def process_updates(self, upd_eval):
        cond = True
        while cond:
            updates = self._get_updates()
            TelegramApi.process_updates_list(updates, upd_eval)
            cond = len(updates) > 0

    @staticmethod
    def process_updates_json(json_data, upd_eval):
        updates = TelegramApi._parse_updates(json_data)  # type: list[TelegramApi.Update]
        print('Number of updates: ' + str(len(updates)))
        TelegramApi.process_updates_list(updates, upd_eval)

    @staticmethod
    def process_updates_list(update_list, upd_eval):
        for upd in update_list:
            upd_eval(upd)




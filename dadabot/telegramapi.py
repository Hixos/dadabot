import requests

from dadabot.logs import logger


class TelegramApi:

    _offset = 0
    _processed = []

    class User:
        def __init__(self, data):
            self.Id = int(data.get('id'))
            self.FirstName = data.get('first_name')
            self.LastName = data.get('last_name', '')
            self.Username = data.get('username', '')

        def to_string(self):
            return 'USER: ' + str(self.Id) + ' ' + self.FirstName + ' ' + self.LastName + ' ' + self.Username

        def print(self):
            print(self.to_string() + '\n')

    class Chat:
        def __init__(self, data):
            self.Id = int(data.get('id'))
            self.Type = data.get('type')
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
            self.Sender = TelegramApi.User(data.get('from')) if 'from' in data else None
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

    def send_message(self, chat, text):
        params = {'chat_id': chat, 'text': text}
        response = requests.post(self.url + 'sendMessage', data=params)
        logger.info('Send_mess response: %s', response.text)
        if response.status_code != requests.codes.ok:
            logger.info('Status code: %s', response.status_code)
        return response

    def set_webhook(self):
        url = 'https://' + self.app_name + '.herokuapp.com/' + self.api_key

        logger.info('Setting webhook: ' + url)

        params = {'url': url}
        response = requests.post(self.url + 'setWebhook', data=params)

        logger.info("Webhook reponse: %s", str(response.raw))

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
            logger.error("Cannot get updates: %s", response.get('description', 'No reason'))
            return updates

        updates_json = response.get('result')

        updates = self._parse_updates(updates_json)  # type: list[TelegramApi.Update]

        for upd in updates:
            if upd.Id >= self._offset:
                self._offset = upd.Id + 1
        logger.info("Current offset: {}\n".format(self._offset))
        return updates

    def process_updates(self, upd_eval):
        cond = True
        while cond:
            updates = self._get_updates()
            logger.info("Updates: %d", len(updates))
            TelegramApi.process_updates_list(updates, upd_eval)
            cond = len(updates) > 0

    def process_update_json(self, json_data, upd_eval):
        update = TelegramApi.Update(json_data)
        if update.Id not in self._processed:
            self._processed.append(update.Id)
            self._offset = max(self._processed) + 1
            upd_eval(update)
        else:
            logger.warning("Discarded update with id: {}. Already processed. offset is: {}\n"
                           .format(update.Id, self._offset))

    @staticmethod
    def process_updates_list(update_list, upd_eval):
        for upd in update_list:
            upd_eval(upd)

from telegramapi import TelegramApi
import random


def find_words(msg: str, words, return_on_match=True, ignore_case=True, whole_word=True):
    """
    Looks for words in msg.
    :param msg: Message
    :param words: Words to be searched in msg
    :param return_on_match: #Return after first match
    :param ignore_case: #Ignore case of words and msg
    :param whole_word:  #Only match a whole word
    :return: A list of tuples ('word', index). Index is where the word was first found in msg
    """

    found = []
    for word in words:  # type: str
        temp_msg = msg
        temp_word = word

        if whole_word:
            temp_word = " " + temp_word + " "
        if ignore_case:
            temp_msg = msg.lower()
            temp_word = word.lower()

        index = temp_msg.find(temp_word)
        if index >= 0:
            found.append((word, index))

            if return_on_match:
                return found

    return found


class SingleWordMatchAnswer:
    Matchwords = []  # Words which trigger this answer

    Answers = []  # type: list[str]

    Options = {}

    def __init__(self, words, answers):
        self.Matchwords = words
        self.Answers = answers

    def matches(self, msg: str):
        return len(find_words(msg, self.Matchwords, **self.Options)) > 0

    def answer(self, msg: TelegramApi.Message, telegram: TelegramApi):
        answ = random.choice(self.Answers)  # type: str
        answ = answ.format(Msg=msg)
        telegram.send_message(msg.Chat.Id, answ)


















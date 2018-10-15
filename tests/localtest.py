from dadabot.dadabot_main import telegram, evaluate_update
from dadabot.responses import WordMatchResponse, WordMatchMode, Chat

#telegram.delete_webhook()

matching = []  # type: list[WordMatchResponse]
for r in WordMatchResponse.List:
    if int(r.Id) > 465:
        print('id: {}. Words:', r.Id)
        for w in r.Matchwords:
            print('-{}', w)

telegram.process_updates(evaluate_update)

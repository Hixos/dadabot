from dadabot import telegram, evaluate_update

telegram.delete_webhook()

telegram.process_updates(evaluate_update)

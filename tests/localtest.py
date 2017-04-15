from dadabot.dadabot_main import telegram, evaluate_update

telegram.delete_webhook()

telegram.process_updates(evaluate_update)

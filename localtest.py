from dadabot import telegram, eval_update

telegram.delete_webhook()

telegram.process_updates(eval_update)

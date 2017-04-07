from dadabot import telegram, eval_update, app

telegram.delete_webhook()

if __name__ == "__main__":
    app.run()

#telegram.process_updates(eval_update)

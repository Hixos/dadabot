import sys 
sys.path.append('..')

from dadabot.dadabot_main import telegram, evaluate_update
import time

telegram.delete_webhook()

while True:
    print("Processing...")
    telegram.process_updates(evaluate_update)
    time.sleep(5)

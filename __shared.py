from os import getenv
from dotenv import load_dotenv
from ig import IGBot
from telegram.ext import Updater
load_dotenv()

# instagram bot
ig_username = getenv('ig_username')
ig_password = getenv('ig_password')

igbot = None
if ig_username and ig_password:
    igbot = IGBot(ig_username, ig_password)
else:
    print("[!] IG credentials not configured")


# telegram bot
tg_bot_token = getenv('tg_bot_token')
if not tg_bot_token:
    print("[!] Telegram token not defined")
    exit(-1)

tgupdater = Updater(tg_bot_token)
tgbot = tgupdater.bot

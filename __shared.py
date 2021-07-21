from os import getenv
from dotenv import load_dotenv
from ig import IGBot
from telegram.ext import Updater
load_dotenv()

# instagram bot
username = getenv('username')
password = getenv('password')
if not username or not password:
    print("[!] Credentials not configured")
    exit(-1)

igbot = IGBot(username, password)

# telegram bot
bot_token = getenv('bot_token')
if not bot_token:
    print("[!] Telegram token not defined")
    exit(-1)

tgupdater = Updater(bot_token)
tgbot = tgupdater.bot

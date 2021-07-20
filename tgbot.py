#!/usr/bin/python3
from ig import IGBot
import os
from dotenv import load_dotenv
import urllib.request
from urllib.parse import urlparse

from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters

load_dotenv()

username = os.getenv('username')
password = os.getenv('password')
if not username or not password:
    print("credentials not configured")
    exit(-1)

igbot = IGBot(username, password)

for sv in ['instagram', 'youtube', 'pinterest']:
    path = "/tmp/" + sv
    if not os.path.exists(path):
        os.makedirs(path)

def url_filename(url):
    parsed = urlparse(url)
    return os.path.basename(parsed.path)

def message_handler(update, context):
    global igbot
    media_url = igbot.get_media_url(update.message.text)
    if not media_url:
        context.bot.send_message(chat_id=update.effective_chat.id,
        text = "Please check the link you sent")
        return

    file_name = url_filename(media_url)
    download_path = "/tmp/instagram/" + file_name
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', igbot.user_agent)]
    urllib.request.install_opener(opener)
    urllib.request.urlretrieve(media_url, download_path)

    if not os.path.exists(download_path):
        context.bot.send_message(chat_id=update.effective_chat.id,
        text = "Unable to download media")
        return
    document = open(download_path, 'rb')
    context.bot.send_document(document = document,
    chat_id=update.effective_chat.id)
    document.close()

bot_token = os.getenv('bot_token')
if not bot_token:
    print("Bot token not defined")
    exit(-1)

updater = Updater(bot_token)
handler = MessageHandler(Filters.text, message_handler)
updater.dispatcher.add_handler(handler)

updater.start_polling()
updater.idle()

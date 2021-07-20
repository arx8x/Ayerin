#!/usr/bin/python3
import os
from __shared import igbot
import urllib.request
from urllib.parse import urlparse
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters

# helper functions
def url_filename(url):
    parsed = urlparse(url)
    return os.path.basename(parsed.path)

def message_handler(update, context):
    media_url = igbot.get_media_url(update.message.text)
    if not media_url:
        context.bot.send_message(chat_id=update.effective_chat.id,
        text = "Please check the link you sent")
        return

def download_file(url, local_path, headers=[]):
    opener = urllib.request.build_opener()
    opener.addheaders = headers
    urllib.request.install_opener(opener)
    urllib.request.urlretrieve(url, local_path)
    if os.path.exists(local_path):
        return True
    return False

# bot message handlers
def message_handler(update, context):
    media_url = igbot.get_media_url(update.message.text)
    if not media_url:
        context.bot.send_message(chat_id=update.effective_chat.id,
        text = "The media type you sent may not be supported")
        return
    file_name = url_filename(media_url)
    download_path = "/tmp/instagram/" + file_name

    if not download_file(media_url, download_path, [('User-Agent', igbot.user_agent)]):
        context.bot.send_message(chat_id=update.effective_chat.id,
        text = "Unable to download media")
        return

    document = open(download_path, 'rb')
    context.bot.send_document(document = document,
    chat_id=update.effective_chat.id)
    document.close()

## BEGIN PROCEDURE
# create temporary downlaod paths
for sv in ['instagram', 'youtube', 'pinterest']:
    path = "/tmp/" + sv
    if not os.path.exists(path):
        os.makedirs(path)

bot_token = os.getenv('bot_token')
if not bot_token:
    print("Bot token not defined")
    exit(-1)

updater = Updater(bot_token)
handler = MessageHandler(Filters.text, message_handler)
updater.dispatcher.add_handler(handler)

updater.start_polling()
updater.idle()

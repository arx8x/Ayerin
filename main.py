#!/usr/bin/python3
import os
import re
from __shared import igbot
import urllib.request
from urllib.parse import urlparse
from telegram import constants as tgconstants
from telegram.ext import Updater, MessageHandler, Filters


# helper functions
def url_filename(url):
    parsed = urlparse(url)
    return os.path.basename(parsed.path)


def download_file(url, local_path, headers=[]):
    opener = urllib.request.build_opener()
    opener.addheaders = headers
    urllib.request.install_opener(opener)
    urllib.request.urlretrieve(url, local_path)
    if os.path.exists(local_path):
        return True
    return False


# bot message handlers
# TODO: handle IG stuff separately, streamline media operations
def message_handler(update, context):
    message = update.message.text
    chat_id = update.effective_chat.id
    # bot currently only supports instagram
    # assuming all links are instagram links
    regex = re.compile('.*instagram.com/([\w\-\_]{2,}?)(?:\?.*|$)')
    matches = regex.findall(message)
    # this regex is for matching username
    # if mathches, get username and send back profile picture
    if matches:
        try:
            username = matches[0]
            userinfo = igbot.username_info(username)
            image_url = userinfo['user']['hd_profile_pic_url_info']['url']
            username = userinfo['user']['username']
            full_name = userinfo['user']['full_name']
            download_path = f"/tmp/instagram/{username}.jpg"
            if not download_file(image_url, download_path):
                raise Exception("file not found")
            document = open(download_path, 'rb')
            context.bot.send_document(document=document,
                                      filename=f"{username}.jpg",
                                      chat_id=chat_id, caption=full_name)
            os.unlink(download_path)
        except Exception:
            context.bot.send_message("Unable to download profile picture")
        return

    # TODO: pick media objects from igbot rather than raw dicts
    media_urls = igbot.get_media_urls(message)
    if not media_urls:
        context.bot.send_message(chat_id=chat_id, text="The media type you "
                                 "sent may not be supported")
        return
    # TODO: filesize(from media objects) before download and send chat action
    for media_url in media_urls:
        file_name = url_filename(media_url)
        download_path = "/tmp/instagram/" + file_name
        if not download_file(media_url, download_path,
                             [('User-Agent', igbot.user_agent)]):
            context.bot.send_message(chat_id=chat_id,
                                     text="Unable to download media")
            return
        document = open(download_path, 'rb')
        document.seek(0, os.SEEK_END)
        file_size = document.tell()
        if file_size > 1048576:  # 1 MB
            context.bot.send_chat_action(chat_id,
                                         tgconstants.CHATACTION_UPLOAD_DOCUMENT)
        document.seek(0, os.SEEK_SET)
        context.bot.send_document(document=document, chat_id=chat_id)
        document.close()
        os.unlink(download_path)


# BEGIN PROCEDURE
# create temporary downlaod paths
for sv in ['instagram', 'youtube', 'pinterest']:
    path = "/tmp/" + sv
    if not os.path.exists(path):
        os.makedirs(path)

# TODO: move to __shared
bot_token = os.getenv('bot_token')
if not bot_token:
    print("Bot token not defined")
    exit(-1)

updater = Updater(bot_token)
handler = MessageHandler(Filters.text, message_handler)
updater.dispatcher.add_handler(handler)

updater.start_polling()
updater.idle()

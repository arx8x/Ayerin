#!/usr/bin/python3
import os
import re
from __shared import igbot, tgbot, tgupdater
from telegram import (constants as tgconstants,
                      InputMediaDocument as TGMediaDocument)
from telegram.ext import MessageHandler, Filters
from utils import download_file

# bot message handlers


def message_handler(update, context):
    message = update.message.text
    chat_id = update.effective_chat.id
    # bot currently only supports instagram
    # assuming all links are instagram links
    download_handler_instagram(message, chat_id)
    return


def download_handler_instagram(message, chat_id):
    regex = re.compile('.*instagram.com/([\w\-\_\.]{2,}?)(?:\?.*|$)')
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
            tgbot.send_document(document=document,
                                filename=f"{username}.jpg",
                                chat_id=chat_id, caption=full_name)
            os.unlink(download_path)
        except Exception:
            tgbot.send_message(chat_id=chat_id,
                               text="Unable to download profile picture")
        return

    media_items = igbot.get_post_media(message)
    if not media_items:
        tgbot.send_message(chat_id=chat_id, text="The media type you "
                           "sent may not be supported")
        return

    send_media(chat_id, media_items)


def send_media(chat_id, media_array, group=True, send_caption=False):
    if not media_array:
        return
    caption = media_array[0].caption if send_caption else ''
    if len(media_array) == 1:
        tgbot.send_document(chat_id,
                            document=media_array[0].url, caption=caption)
        return
    input_media_files = []
    tgbot.send_chat_action(chat_id, tgconstants.CHATACTION_UPLOAD_DOCUMENT)
    for media_item in media_array:
        if group:
            caption = media_item.caption if send_caption else ''
            input_media = TGMediaDocument(media_item.url, caption=caption)
            input_media_files.append(input_media)
        else:
            caption = media_item.caption if send_caption else ''
            tgbot.send_document(document=media_item.url, chat_id=chat_id)

    if input_media_files:
        print("Send group")
        tgbot.send_media_group(chat_id, input_media_files)


# BEGIN PROCEDURE
# create temporary downlaod paths
for sv in ['instagram', 'youtube', 'pinterest']:
    path = "/tmp/" + sv
    if not os.path.exists(path):
        os.makedirs(path)


handler = MessageHandler(Filters.text, message_handler)
tgupdater.dispatcher.add_handler(handler)

tgupdater.start_polling()
tgupdater.idle()

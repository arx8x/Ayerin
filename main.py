#!/usr/bin/python3
import os
import re
from time import sleep
import validators
from __shared import igbot, tgbot, tgupdater
from telegram import (constants as tgconstants,
                      InputMediaDocument as TGMediaDocument)
from telegram.ext import MessageHandler, Filters
import utils

# global variable to hold the current Update
# this only works since these handlers are blocking/synchronous
# RENOVE THIS WHEN DOING Async to avoid race conditions
current_update = None


# bot message handlers
def message_handler(update, context):
    global current_update
    message = update.message.text
    current_update = update
    # chat_id = update.effective_chat.id
    if validators.url(message):
        url_handler(message)
    else:
        chat_message_handler(message)
    return


def chat_message_handler(message):
    tgbot.send_message(current_update.effective_chat.id,
                       "Send me a social media link to begin")


def url_handler(url):
    url_info = utils.url_split(url)
    if 'instagram.com' in url_info.domain:
        service_handler_instagram(url_info)
    else:
        text = "Sorry, I can't download media from that website yet"
        tgbot.send_message(current_update.effective_chat.id, text)
    return


def service_handler_instagram(url_info):
    chat_id = current_update.effective_chat.id
    components_length = len(url_info.components)
    if not components_length:
        text = "That instagram link is malformed or no media exists at link"
        tgbot.send_message(chat_id, text)
        return

    if components_length == 1:
        # 1 means it's a username (assumed)
        username = url_info.components[0]
        userinfo = igbot.username_info(username)
        image_url = userinfo['user']['hd_profile_pic_url_info']['url']
        username = userinfo['user']['username']
        full_name = userinfo['user']['full_name']
        tgbot.send_document(document=image_url, filename=f"{username}.jpg",
                            chat_id=chat_id, caption=full_name)
        return

    link_type = url_info.components[0]
    if link_type == 'p' or link_type == 'reel':  # post and reels
        media_items = igbot.get_post_media(url_info.url)
        if not media_items:
            text = "The media type you sent may not be supported"
            tgbot.send_message(chat_id, text=text)
            return

        send_media(chat_id, media_items)
        return
    elif link_type == 'stories':
        media_id = url_info.components[2]
        media = igbot.get_story_media(media_id)
        send_media(chat_id, media)
        return

    return


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

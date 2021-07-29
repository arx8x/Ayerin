#!/usr/bin/python3
import os
from io import BufferedIOBase
from yt import YT
import validators
from __shared import igbot, tgbot, tgupdater
from telegram import (constants as tgconstants,
                      InputMediaDocument as TGMediaDocument)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, Filters, CallbackQueryHandler
import utils
from pin import Pin
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


def callback_query_handler(update, context):
    global current_update
    # print(update.callback_query.message.message_id)
    # print(update.callback_query.data)
    current_update = update
    args = update.callback_query.data.split(':')
    if not args:
        return
    if args[0] == 'yt':
        service_handler_youtube_callback(args)


def chat_message_handler(message):
    tgbot.send_message(current_update.effective_chat.id,
                       "Send me a social media link to begin")


def url_handler(url):
    url_info = utils.url_split(url)
    # TODO: better way to check URL
    if 'instagram.com' in url_info.domain:
        service_handler_instagram(url_info)
    elif 'pinterest.' in url_info.domain or 'pin.it' in url_info.domain:
        service_handler_pinterest(url_info)
    elif 'youtube.com' in url_info.domain or 'youtu.be' in url_info.domain:
        service_handler_youtube(url_info)
    else:
        text = "Sorry, I can't download media from that website yet"
        tgbot.send_message(current_update.effective_chat.id, text)
    return


def service_handler_pinterest(url_info):
    chat_id = current_update.effective_chat.id
    pin = Pin(url_info)
    media = pin.get_video()
    print(media)
    if not media:
        text = "Sorry, I was unable to find any media at the given link"
        tgbot.send_message(chat_id, text)
        return
    send_media(chat_id, [media], send_caption=True)


def service_handler_youtube(url_info):
    chat_id = current_update.effective_chat.id
    tgbot.send_chat_action(chat_id, action=tgconstants.CHATACTION_TYPING)
    id = url_info.components[0] if url_info.domain == \
        'youtu.be' else url_info.query['v'][0]
    yt = YT(id, 0)
    video_info = yt.video_info()

    thumb_markup = ''
    # link a '.' with youtube preview so that the image will appear
    # on the message as a preview (a neat little trick)
    if len(video_info['thumbnails']) > 0:
        thumb_index = 0
        try:
            if video_info['thumbnails'][3]:
                thumb_index = 3
            elif video_info['thumbnails'][2]:
                thumb_index = 2
        except IndexError:
            thumb_index = 0
        thumb_url = video_info['thumbnails'][thumb_index]['url']
        thumb_markup = f"<a href='{thumb_url}'>.</a>\n"
    text = f"<b>{video_info['title']}</b>{thumb_markup}"

    # views and ratings
    # text += (f"👁 {video_info['view_count']}   {video_info['like_count']}  👎 "
    #          f"{video_info['dislike_count']}\n")

    # video description
    if video_info['description']:
        description = video_info['description']
        text += description if len(
            description) < 120 else f"{description[:120]}..."
        text += "\n"

    inline_buttons = []
    button_buffer = []
    for index, (name, format) in enumerate(video_info['formats'].items()):
        post_process = 1
        add_audio = 0
        format_id = format['format_id']
        # flag to indicate, the file can be downloaded and sent without
        # any processing
        if format['ext'] == 'mp4' and format['fps'] and format['asr']:
            post_process = 0
            # * in button text indicates it'll be faster
            # since there's no post processing
            name += '*'
        if not format['asr']:
            add_audio = 1
        if name == 'tiny':
            name = 'MP3 Audio'
            format_id = 'AUD'
        button = InlineKeyboardButton(
            name,
            callback_data=f"yt:{id}:{format_id}:{post_process}:{add_audio}")
        # create a matrix of 2 buttons per row
        if len(button_buffer) < 2:
            button_buffer.append(button)
        else:
            inline_buttons.append(button_buffer)
            button_buffer = [button]
    # if total number of formats is odd, the last button can be left out
    # because the condifion above pushes it to final array when the
    # button_buffer has 2 button
    if button_buffer:
        inline_buttons.append(button_buffer)

    tgbot.sendMessage(chat_id, text, reply_markup=InlineKeyboardMarkup(
        inline_buttons), parse_mode=tgconstants.PARSEMODE_HTML)


def service_handler_youtube_callback(args):
    if len(args) < 5:
        return
    id = args[1]
    format = args[2]
    post_process = args[3] != '0'
    add_audio = args[4] != '0'
    message_id = current_update.callback_query.message.message_id
    chat_id = current_update.effective_chat.id
    tgbot.edit_message_reply_markup(
        chat_id, reply_markup=None, message_id=message_id)
    text = "Your video is being processed. Please wait..."
    tgbot.answer_callback_query(current_update.callback_query.id, text)

    yt = YT(id, format)
    yt.post_process = post_process
    yt.add_audio = add_audio
    yt.audio_only = format == 'AUD'
    media = yt.download()
    if media:
        send_media(chat_id, [media])


def service_handler_instagram(url_info):
    chat_id = current_update.effective_chat.id
    if not igbot:
        tgbot.send_message(chat_id, "<b>Error</b>\n"
                           "Sorry, I'm unable to handle the instagram media.\n"
                           "Please use /report command to report this issue.",
                           parse_mode=tgconstants.PARSEMODE_HTML)
        return
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
    if link_type in ['reel', 'p']:  # post and reels
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
    # TODO: check file size before sending
    if not media_array:
        return
    tgbot.send_chat_action(chat_id, tgconstants.CHATACTION_UPLOAD_DOCUMENT)
    if len(media_array) == 1:
        group = False

    input_media_files = []
    for media_item in media_array:
        file = None
        if media_item.url:
            file = media_item.url
        elif media_item.local_path:
            if os.path.exists(media_item.local_path):
                file = open(media_item.local_path, 'rb')
        if not file:
            continue

        if group:
            caption = media_item.caption if send_caption else ''
            input_media = TGMediaDocument(
                file, caption=caption, filename=media_item.file_name)
            input_media_files.append(input_media)
        else:
            caption = media_item.caption if send_caption else ''
            tgbot.send_document(document=file, chat_id=chat_id,
                                filename=media_item.file_name, caption=caption)
        if isinstance(file, BufferedIOBase):
            file.close()

    if input_media_files:
        print("Send group")
        tgbot.send_media_group(chat_id, input_media_files)


# BEGIN PROCEDURE
# create temporary downlaod paths
for sv in ['instagram', 'youtube', 'pinterest']:
    path = "/tmp/" + sv
    if not os.path.exists(path):
        os.makedirs(path)


message_handler1 = MessageHandler(Filters.text, message_handler)
callback_query_handler1 = CallbackQueryHandler(callback_query_handler)
tgupdater.dispatcher.add_handler(message_handler1)
tgupdater.dispatcher.add_handler(callback_query_handler1)

tgupdater.start_polling()
tgupdater.idle()

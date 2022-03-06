#!/usr/bin/python3
import os
from io import BufferedIOBase
from time import sleep as tsleep
import threading
from yt import YT
import validators
from __shared import igbot, tgbot, tgupdater, tg_local_bot
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


class AyerinBot:

    def __init__(self, update, timeout=180):
        self.progress_message_id = None
        self.timeout = timeout
        self.url_info = None
        self.chat_id = None
        self.__is_sending_chat_action = False
        self.__send_chat_action = False
        self.callback_query_id = None
        self.message_id = None
        self.update = update
        if update.effective_chat.id:
            self.chat_id = update.effective_chat.id

    def handle_update(self):
        if self.update.callback_query:
            self.__handle_callback_query()
        elif self.update.message and self.update.message.text:
            self.__handle_text_message()

    def start_sending_upload_action(self):
        def file_upload_action_thread():
            max_count = 120
            if self.__is_sending_chat_action:
                return
            self.__is_sending_chat_action = True
            self.__send_chat_action = True
            for i in range(max_count):
                if not self.__send_chat_action:
                    self.__is_sending_chat_action = False
                    return
                self.send_file_sending_action()
                if(i >= max_count):
                    return
                tsleep(4)
        thread = threading.Thread(
            target=file_upload_action_thread, name='action_file_upload')
        thread.daemon = True  # exit with main if it keeps running
        thread.start()

    def stop_sending_upload_action(self):
        self.__send_chat_action = False

    def __handle_text_message(self):
        self.text_message = self.update.message.text
        # chat_id = update.effective_chat.id
        if validators.url(self.text_message):
            self.__handle_url(self.text_message)
        else:
            self.reply_chat_message(self.text_message)
        return

    def __handle_url(self, url):
        url_info = utils.url_split(url)
        self.url_info = url_info
        if not url_info:
            # handle error
            return
            # TODO: better way to check URL
        if 'instagram.com' in url_info.domain:
            self.__handle_instagram_url()
        elif 'pinterest.' in url_info.domain or 'pin.it' in url_info.domain:
            self.__handle_pinterest_url()
        elif 'youtube.com' in url_info.domain or 'youtu.be' in url_info.domain:
            self.__handle_youtube_url()
        else:
            text = "Sorry, I can't download media from that website yet"
            tgbot.send_message(current_update.effective_chat.id, text)
        return

    def send_message(self, message, send_as_reply=False,
                     reply_markup=None, parse_mode=None):
        result = tgbot.send_message(self.chat_id,
                                    message, reply_markup=reply_markup,
                                    parse_mode=parse_mode)
        return result

    def update_progress_message(self, message, send_new=False,
                                parse_mode=None):
        if not self.progress_message_id:
            result = tgbot.send_message(self.chat_id, text=message,
                                        parse_mode=parse_mode)
            if result:
                self.progress_message_id = result.message_id
            return

        return tgbot.edit_message_text(chat_id=self.chat_id, text=message,
                                       message_id=self.progress_message_id,
                                       parse_mode=parse_mode)

    def send_typing_action(self):
        tgbot.send_chat_action(
            self.chat_id, action=tgconstants.CHATACTION_TYPING)

    def send_file_sending_action(self):
        tgbot.send_chat_action(
            self.chat_id, action=tgconstants.CHATACTION_UPLOAD_DOCUMENT)

    def reply_chat_message(self, message):
        self.send_message("Send me a media link to begin")

    def __handle_callback_query(self):
        args = self.update.callback_query.data.split(':')
        self.callback_query_id = self.update.callback_query.id
        if not args:
            return
        if args[0] == 'yt':
            self.__handle_youtube_callback(args)

    def remove_inline_keyboard(self, message_id=0):
        if not message_id:
            message_id = self.update.callback_query.message.message_id
        tgbot.edit_message_reply_markup(
            self.chat_id, reply_markup=None, message_id=message_id)

    def __handle_youtube_callback(self, args):
        self.remove_inline_keyboard()
        if len(args) < 5:
            return
        id = args[1]
        format = args[2]
        post_process = args[3] != '0'
        add_audio = args[4] != '0'

        text = "Your video is being processed. Please wait..."
        self.answer_callback_query(text)

        yt = YT(id, format)
        yt.add_audio = add_audio
        yt.audio_only = format == 'AUD'
        # post processing is disabled for videos in buttons
        yt.post_process = post_process
        try:
            self.start_sending_upload_action()
            progress = ("<b>Processing</b>\nPlease don't send additional "
                        "requests and wait patiently.")
            result = self.update_progress_message(progress,
                                                  parse_mode=tgconstants.
                                                  PARSEMODE_HTML)
            if result:
                self.progress_message_id = result.message_id
            media = yt.download()
            progress = "<b>Uploading</b>\nUploading your media.\nPlease wait."
            self.update_progress_message(progress,
                                         parse_mode=tgconstants.PARSEMODE_HTML)
            if media:
                self.send_media([media], send_caption=True)
                self.update_progress_message("<b>Done</b>",
                                             parse_mode=tgconstants.
                                             PARSEMODE_HTML)
            else:
                self.send_message("Error")
        except Exception:
            self.send_message("Error")
        finally:
            self.stop_sending_upload_action()

    def answer_callback_query(self, message):
        if not (callback_id := self.callback_query_id):
            return
        tgbot.answer_callback_query(callback_id, message)

    def __handle_instagram_url(self):
        if not igbot:
            self.send_message("<b>Error</b>\n"
                              "Sorry, I'm unable to handle the instagram media.\n"
                              "Please use /report command to report this issue.",
                              parse_mode=tgconstants.PARSEMODE_HTML)
            return

        components_length = len(self.url_info.components)
        if not components_length:
            text = "That instagram link is malformed or no media exists at link"
            self.send_message(text)
            return

        if components_length == 1:
            # 1 means it's a username (assumed)
            username = self.url_info.components[0]
            media = igbot.get_profile_image(username)
            if media:
                self.send_media([media], send_caption=True)
            return
        elif components_length == 3:
            link_type = self.url_info.components[1]
        else:
            link_type = self.url_info.components[0]
        if link_type in ['reel', 'p']:  # post and reels
            media_items = igbot.get_post_media(self.url_info.url)
            if not media_items:
                text = "The media type you sent may not be supported"
                self.send_message(text)
                return
            self.send_media(media_items)
        elif link_type == 'stories':
            media_id = self.url_info.components[2]
            media = igbot.get_story_media(media_id)
            self.send_media(media)
            return

    def __handle_youtube_url(self):
        self.send_typing_action()
        id = self.url_info.components[0] if self.url_info.domain == \
            'youtu.be' else self.url_info.query['v'][0]
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
        # text += (f"👁 {video_info['view_count']}    video_info['like_count']}  👎 "
        #          f"{video_info['dislike_count']}\n")

        # video description
        if video_info['description']:
            description = video_info['description']
            text += description if len(
                description) < 120 else f"{description[:120]}..."
            text += "\n"

        inline_buttons = []
        button_buffer = []
        audio_added = False
        for index, (name, format) in enumerate(video_info['formats'].items()):
            post_process = 0
            add_audio = 0
            format_id = format['format_id']
            abr = format.get('abr')
            vbr = format.get('vbr')
            tbr = format.get('tbr')
            asr = format.get('asr')
            fps = format.get('fps')

            if not abr and not vbr:
                continue

            # flag to indicate, the file can be downloaded and sent without
            # any processing
            if format['ext'] == 'mp4' and fps and asr:
                post_process = 0
                # * in button text indicates it'll be faster
                # since there's no post processing
                name += '*'
            if not format.get('asr'):
                # no asr typically means there's no audio
                add_audio = 1
            if abr and asr and not vbr:
                if audio_added:
                    continue
                name = f'MP3 Audio'
                post_process = 1
                format_id = 'AUD'
                audio_added = True
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

        self.send_message(text,
                          reply_markup=InlineKeyboardMarkup(inline_buttons),
                          parse_mode=tgconstants.PARSEMODE_HTML)

    def __handle_pinterest_url(self):
        pin = Pin(self.url_info)
        media = pin.get_media()
        print(media)
        if not media:
            text = "Sorry, I was unable to find any media at the given link"
            self.send_message(text)
            return
        self.send_media([media], send_caption=True)

    def send_media(self, media_array, group=True, send_caption=False):
        if not media_array:
            return
        if len(media_array) == 1:
            group = False

        input_media_files = []
        for media_item in media_array:
            file = None

            # assign file variable
            if media_item.url and not media_item.local_path:
                file = media_item.url
                file_size = None
                if media_item.filesize:
                    file_size = media_item.filesize
                else:
                    file_size = utils.get_remote_filesize(file)

                # If file size is greater than 20 MB, telegram won't download
                # the file automatically. So we'll download and upload it
                if file_size and file_size > 18974368:
                    print("remote file is too big; downloading and sending")
                    dl_filename = media_item.file_name
                    if not dl_filename:
                        dl_filename = utils.url_filename(file)
                    if dl_filename:
                        dl_path = f"/tmp/downloads/{dl_filename}"
                        utils.download_file(file, dl_path)
                        if os.path.exists(dl_path):
                            if tg_local_bot:
                                file = dl_path
                            else:
                                file = open(dl_path, 'rb')

            elif media_item.local_path:
                if not os.path.exists(media_item.local_path):
                    continue
                if tg_local_bot:
                    file = media_item.local_path
                else:
                    file = open(media_item.local_path, 'rb')

            if not file:
                continue

            thumb = None
            thumb_local_path = None
            if isinstance(media_item.thumbnail, str):
                if validators.url(media_item.thumbnail):
                    thumb_local_path = f"/tmp/thumbs/{media_item.file_name}"
                    if not os.path.exists(thumb_local_path):
                        utils.download_file(
                            media_item.thumbnail, thumb_local_path)
                else:
                    thumb_local_path = media_item.thumbnail

            if thumb_local_path and os.path.exists(thumb_local_path):
                thumb = open(thumb_local_path, 'rb')

            if group:
                caption = media_item.caption if send_caption else ''
                input_media = TGMediaDocument(
                    file, caption=caption, filename=media_item.file_name)
                input_media_files.append(input_media)
            else:
                caption = media_item.caption if send_caption else ''
                tgbot.send_document(document=file, chat_id=self.chat_id,
                                    filename=media_item.file_name,
                                    caption=caption,
                                    timeout=self.timeout,
                                    thumb=thumb)
            if isinstance(file, BufferedIOBase):
                file.close()
            if isinstance(thumb, BufferedIOBase):
                thumb.close()

        if input_media_files:
            print("Send group")
            tgbot.send_media_group(self.chat_id, input_media_files)


# BEGIN PROCEDURE
# create temporary downlaod paths
for sv in ['instagram', 'youtube', 'pinterest', 'thumbs', 'downloads']:
    path = "/tmp/" + sv
    if not os.path.exists(path):
        os.makedirs(path)


def message_handler(update, context):
    bot_instance = AyerinBot(update)
    bot_instance.handle_update()


message_handler1 = MessageHandler(
    Filters.all, message_handler, run_async=True)
callback_query_handler1 = CallbackQueryHandler(message_handler, run_async=True)
tgupdater.dispatcher.add_handler(message_handler1)
tgupdater.dispatcher.add_handler(callback_query_handler1)

tgupdater.start_polling()
tgupdater.idle()

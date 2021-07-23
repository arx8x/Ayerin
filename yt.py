import youtube_dl
from json import dumps as j
from telegram import bot, InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
import os


class YT:
    options = {
        'call_home': False,
        'no_color': True,
        'forcefilename': True
    }
    work_path = '/tmp/youtube/'
    format
    id
    post_process = True

    def __init__(self, id, format):
        self.id = id
        self.url = f"https://youtube.com/watch?v={id}"
        self.format = format
        if not os.path.exists(self.work_path):
            os.makedirs(self.work_path)
        self.options['cachedir'] = self.work_path
        self.options['cookiefile'] = f"{self.work_path}.cookie"
        self.options['outtmpl'] = f"{self.work_path}%(id)s_{self.format}.%(ext)s"

    def video_info(self):
        yt = youtube_dl.YoutubeDL(self.options)
        video_info = yt.extract_info(self.url, download=False)

        qualities = {}
        for index, format in enumerate(video_info['formats']):
            format_name = format['format_note'] if format['format_note'] else format['quality']
            print(f"format: {format_name} -- {format['format_id']} -- {index}")
            if format_name not in qualities:
                print("new format")
                qualities[format_name] = format
            else:
                if qualities[format_name]['ext'] == 'mp4' and \
                 qualities[format_name]['fps'] and qualities[format_name]['asr']:
                    print("quality already optimal")
                    continue
                if format['fps'] and format['asr']:
                    # if fps and asr (audio sample rate) are non-null, that
                    # means video and audio exist in the format and there will
                    # be no need to post-process
                    qualities[format_name] = format
                elif format['ext'] == 'mp4':
                    qualities[format_name] = format
                # elif 'abr' in format and format['abr'] == format['tbr']:
                #     # abr (audio bit rate) == tbr (total bit rate)
                #     # means it's audio only
                #     print("audio only format")
                #     if format['abr'] > qualities[format_name]['abr']:
                #         qualities[format_name] = format
        video_info['formats'] = qualities
        return video_info

    def download_audio(self):
        self.options['format'] = 'bestaudio'
        if self.post_process:
            self.options['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3'
            }]
            file_path = f"{self.work_path}{self.id}_{self.format}.mp3"
        downloader = youtube_dl.YoutubeDL(self.options)
        info = downloader.extract_info(self.url)
        if not self.post_process:
            file_path = downloader.prepare_filename(info)
        return file_path

    def download_video(self):
        self.options['format'] = f"{self.format}+bestaudio"
        if self.post_process:
            self.options['postprocessors'] = [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'
            }]
            file_path = f"{self.work_path}{self.id}_{self.format}.mp4"
        downloader = youtube_dl.YoutubeDL(self.options)
        info = downloader.extract_info(self.url)
        if not self.post_process:
            file_path = downloader.prepare_filename(info)
        return file_path

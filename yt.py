import yt_dlp as youtube_dl
# import youtube_dl
import os
from mediatypes import MediaObject, MediaType
from utils import replace_extension

class YT:
    options = {
        'call_home': False,
        'no_color': True,
    }
    work_path = '/tmp/youtube/'
    format
    id
    post_process = True
    add_audio = False
    audio_only = False

    def __init__(self, id, format):
        self.id = id
        self.url = f"https://youtube.com/watch?v={id}"
        self.format = str(format)
        if not os.path.exists(self.work_path):
            os.makedirs(self.work_path)
        self.options['cachedir'] = self.work_path
        self.options['cookiefile'] = f"{self.work_path}.cookie"
        self.options['outtmpl'] = f"{self.work_path}/%(id)s/%(format_id)s/%(title)s.%(ext)s"
        self.options['postprocessors'] = []
        # self.options['outtmpl'] = (
        #     f"{self.work_path}%(id)s_{self.format}.%(ext)s"
        # )

    def video_info(self):
        yt = youtube_dl.YoutubeDL(self.options)
        video_info = yt.extract_info(self.url, download=False)
        return self.__video_info(video_info)

    def __video_info(self, video_info):
        qualities = {}
        for index, format in enumerate(video_info['formats']):
            format_name = format['format_note'] if \
                format['format_note'] else format['quality']
            print(f"format: {format_name} -- {format['format_id']} -- {index}")
            if format_name not in qualities:
                print("new format")
                qualities[format_name] = format
            else:
                if qualities[format_name].get('ext') == 'mp4' and \
                   qualities[format_name].get('fps') and \
                   qualities[format_name].get('asr'):
                    print("quality already optimal")
                    continue
                if format.get('fps') and format.get('asr'):
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

    def download(self):
        self.options['format'] = self.format
        media_type = MediaType.VIDEO
        extension = None

        if self.add_audio and not self.audio_only:
            self.options['format'] += "+bestaudio"

        if self.audio_only and self.post_process:
            extension = 'mp3'
            media_type = MediaType.AUDIO
            self.options['format'] = 'bestaudio'
            if self.post_process:
                self.options['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': extension
                }]
        elif self.post_process:
            extension = 'mp4'
            if self.post_process:
                self.options['postprocessors'] = [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': extension
                }]

        print(self.options)
        downloader = youtube_dl.YoutubeDL(self.options)
        info = downloader.extract_info(self.url)
        file_path = downloader.prepare_filename(info)
        print(file_path)
        if extension:
            file_path = replace_extension(file_path, extension)

        if not os.path.exists(file_path):
            print("replace_extension")
            file_path = replace_extension(file_path, 'mkv')

        # if not self.post_process:
        #     file_path = predetermined_filename
        #     # this function can often return a wrong filename
        #     if not os.path.exists(file_path):
        #         # if prepare_filename returns a wrong filename,
        #         # mkv is the best guess
        #         file_path = f"{self.work_path}{self.id}_{self.format}.mkv"
        #     print("auto_path", file_path)
        if not os.path.exists(file_path):
            print("yt: no file")
            return None
        media = MediaObject(url=None, mediatype=media_type)
        if info['thumbnails']:
            if info['thumbnails'][0]:
                media.thumbnail = info['thumbnails'][0]['url']
        media.local_path = file_path
        media.caption = info['title']
        media.file_name = info['title'] + os.path.splitext(file_path)[1]
        return media

import youtube_dl
import os
from mediatypes import MediaOject, MediaType


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
    add_audio = False
    audio_only = False

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

    def download(self):
        media_type = MediaType.VIDEO
        if self.audio_only:
            media_type = MediaType.AUDIO
            self.options['format'] = 'bestaudio'
            if self.post_process:
                self.options['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3'
                }]
                file_path = f"{self.work_path}{self.id}_{self.format}.mp3"
                self.options['outtmpl'] = file_path
        else:
            self.options['format'] = self.format
            if self.add_audio:
                self.options['format'] += "+bestaudio"
            if self.post_process:
                self.options['postprocessors'] = [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4'
                }]
                file_path = f"{self.work_path}{self.id}_{self.format}.mp4"
                self.options['outtmpl'] = file_path

        print(self.options)
        downloader = youtube_dl.YoutubeDL(self.options)
        info = downloader.extract_info(self.url)
        if not self.post_process:
            file_path = downloader.prepare_filename(info)
            # this function can often return a wrong filename
            if not os.path.exists(file_path):
                # if prepare_filename returns a wrong filename,
                # mkv is the best guess
                file_path = f"{self.work_path}{self.id}_{self.format}.mkv"
            print("auto_path", file_path)
        if not os.path.exists(file_path):
            print("no file")
            return None
        media = MediaOject(url=None, mediatype=media_type)
        media.local_path = file_path
        media.caption = info['title']
        print(file_path)
        media.file_name = info['title'] + os.path.splitext(file_path)[1]
        return media

import json
import codecs
import os.path
import validators
from utils import url_filename
from mediatypes import MediaOject, MediaType
from instagram_private_api import (
        Client, ClientCookieExpiredError, ClientLoginRequiredError)


def to_json(python_object):
    if isinstance(python_object, bytes):
        return {'__class__': 'bytes',
                '__value__': codecs.encode(python_object, 'base64').decode()}
    raise TypeError(repr(python_object) + ' is not JSON serializable')


def from_json(json_object):
    if '__class__' in json_object and json_object['__class__'] == 'bytes':
        return codecs.decode(json_object['__value__'].encode(), 'base64')
    return json_object


class IGBot(Client):
    def __init__(self, username, password):
        device_id = None
        try:
            settings_file_path = '.ig_config'
            if not os.path.isfile(settings_file_path):
                # settings file does not exist
                print('Unable to find file: {0!s}'.format(settings_file_path))
                # login new
                super().__init__(username, password)
                with open(settings_file_path, 'w') as file:
                    json.dump(self.settings, file, default=to_json)
                    print('SAVED: {0!s}'.format(settings_file_path))
            else:
                with open(settings_file_path) as file_data:
                    settings = json.load(file_data, object_hook=from_json)
                # re-use auth info
                print('Reusing settings: {0!s}'.format(settings_file_path))
                device_id = settings.get('device_id')
                super().__init__(username, password, settings=settings)

        except (ClientCookieExpiredError, ClientLoginRequiredError) as e:
            print('ClientCookieExpiredError/ClientLoginRequiredError: {0!s}'
                  .format(e))

            # Login expired
            # Do relogin but use default ua, keys and such
            super().__init__(
                username, password,
                device_id=device_id)
            with open(settings_file_path, 'w') as file:
                json.dump(self.__settings, file, default=to_json)
                print('SAVED: {0!s}'.format(settings_file_path))

    def get_post_media(self, media_url):
        if not validators.url(media_url):
            print("Invalid post url")
            return None
        embed_info = self.oembed(media_url)
        media_id = embed_info['media_id']
        return self.__media_objects_from_media_id(media_id)

    def __media_objects_from_media_id(self, media_id):
        try:
            media_info_base = self.media_info(media_id)
            media_info = media_info_base['items'][0]
            caption = media_info['caption']['text'] \
                if media_info['caption'] else None
            if media_info['media_type'] <= 2:  # photo and video
                media = self.__create_media_object(media_info)
                media.caption = caption
                return [media]
            elif media_info['media_type'] == 8:  # carousel
                media_array = []
                carousel_media = media_info['carousel_media']
                for carousel_media_info in carousel_media:
                    media = self.__create_media_object(carousel_media_info)
                    media.caption = caption
                    media_array.append(media)
                return media_array
        except Exception as e:
            print(e)
            return None

    def __create_media_object(self, media_dict):
        # key_dict = {
        #     1: 'image_versions2',
        #     2: 'video_versions'
        # }
        # key = key_dict[media_dict['media_type']]
        # if not key:
        #     return None
        if media_dict['media_type'] == 1:
            selected_media = media_dict['image_versions2']['candidates'][0]
            type = MediaType.IMAGE
        elif media_dict['media_type'] == 2:
            selected_media = media_dict['video_versions'][0]
            type = MediaType.VIDEO

        media = MediaOject(selected_media['url'], mediatype=type)
        media.height = selected_media['height']
        media.width = selected_media['width']
        media.file_name = url_filename(media.url)
        return media

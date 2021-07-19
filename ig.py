import json
import codecs
import datetime
import os.path
import validators
from instagram_private_api import (
        Client, ClientError, ClientLoginError,
        ClientCookieExpiredError, ClientLoginRequiredError)


def to_json(python_object):
    if isinstance(python_object, bytes):
        return {'__class__': 'bytes',
                '__value__': codecs.encode(python_object, 'base64').decode()}
    raise TypeError(repr(python_object) + ' is not JSON serializable')


def from_json(json_object):
    if '__class__' in json_object and json_object['__class__'] == 'bytes':
        return codecs.decode(json_object['__value__'].encode(), 'base64')
    return json_object


def onlogin_callback(api, new_settings_file):
    cache_settings = api.settings
    with open(new_settings_file, 'w') as outfile:
        json.dump(cache_settings, outfile, default=to_json)
        print('SAVED: {0!s}'.format(new_settings_file))


class IGBot(Client):

    def __init__(self, username, password):
        device_id = None
        try:
            settings_file_path = 'config'
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
            print('ClientCookieExpiredError/ClientLoginRequiredError: {0!s}'.format(e))

            # Login expired
            # Do relogin but use default ua, keys and such
            super().__init__(
                username, password,
                device_id=device_id)
            with open(settings_file_path, 'w') as file:
                json.dump(self.__settings, file, default=to_json)
                print('SAVED: {0!s}'.format(settings_file_path))

    def get_media_url(self, media_url):
        if not validators.url(media_url):
            print("Invalid post url")
            return None
        try:
            embed_info = self.oembed(media_url)
            media_id = embed_info['media_id']
            media_info_base = self.media_info(media_id)
            # print(json.dumps(media_info_base))
            media_info = media_info_base['items'][0]
            if media_info['media_type'] == 1: # Photo
                image_variants = media_info['image_versions2']
                largest_image = image_variants['candidates'][0]
                return largest_image['url']
            elif media_info['media_type'] == 2: # video
                video_variants = media_info['video_versions']
                return video_variants[0]['url']
        except:
            return None

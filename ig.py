import validators
from utils import url_filename
from mediatypes import MediaObject, MediaType
from instagram_private_api import (
    Client, ClientCookieExpiredError, ClientLoginRequiredError)
import pickle


class UserNotFollowingException(Exception):
    pass


class IGBot(Client):
    def __init__(self, username, password):
        settings_file_path = '.ig_config'
        settings_file = open(settings_file_path, 'ab+')
        settings_file.seek(0)
        try:
            # attempt to re-use auth info
            settings = pickle.load(settings_file)
            print(f"Reusing settings from {settings_file_path}")
            super().__init__(username, password, settings=settings)
        except (ClientCookieExpiredError, ClientLoginRequiredError,
                EOFError, pickle.UnpicklingError) as e:
            # Login expired or invalid
            # re-login and save login data
            print(f"Cannot use saved config: {e}")
            super().__init__(username, password)
            settings_file.seek(0)
            settings_file.truncate(0)
            pickle.dump(self.settings, settings_file)
        finally:
            settings_file.close()

    def get_post_media(self, media_url):
        if not validators.url(media_url):
            print("Invalid post url")
            return None
        embed_info = self.oembed(media_url)
        media_id = embed_info['media_id']
        return self.__media_objects_from_media_id(media_id)

    def get_profile_image(self, username):
        userinfo = self.username_info(username)
        if not userinfo:
            return None
        image_url = userinfo['user']['hd_profile_pic_url_info']['url']
        username = userinfo['user']['username']
        full_name = userinfo['user']['full_name']
        media = MediaObject(url=image_url, mediatype=MediaType.IMAGE)
        media.file_name = f"{username}.jpg"
        media.caption = full_name
        return media

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

    def get_story_media(self, media_id):
        return self.__media_objects_from_media_id(media_id)

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

        media = MediaObject(selected_media['url'], mediatype=type)
        media.height = selected_media['height']
        media.width = selected_media['width']
        media.file_name = url_filename(media.url)
        return media

    def __user_list(self, method, user_id, max=1000) -> dict:
        # list following and followers
        users = {}
        total_read = 0
        rank_token = self.generate_uuid()
        # rank_token is the identifier for the pagination list
        # max_id is the offset in the pagination list
        if not callable(method):
            return users

        while True:
            user_batch = method(user_id, rank_token=rank_token, max_id=total_read)
            if not (user_batch := user_batch.get('users')):
                break
            read_count = len(user_batch)
            for user in user_batch:
                users[user.get('pk')] = user
            total_read += read_count
            if not read_count:
                break
        return users

    def leech_list(self, username):
        user = self.username_info(username)
        user_id = None
        is_private = None
        try:
            user_id = user['user']['pk']
            is_private = user['user']['is_private']
        except KeyError:
            return None
        if is_private:
            # attempt to follow
            friendship_status = self.friendships_create(user_id)
            following = False
            try:
                following = friendship_status['friendship_status']['following']
            except KeyError:
                return None
            if not following:
                raise UserNotFollowingException("User is private but not following")

        following = self.__user_list(self.user_following, user_id)
        followers = self.__user_list(self.user_followers, user_id)
        leechers = {}
        for user_id, user in following.items():
            if user_id not in followers:
                leechers[user_id] = user

        return leechers

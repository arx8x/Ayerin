import os
from mediatypes import MediaObject, MediaType
import urllib.request as urlrequest
import validators
from utils import url_split, URLInfo, get_redirect_url
import re
import json

# Pinterest is a weird website. Why does it exist?
# Pinterest has two types of urls. Direct url to the pin and shortened
# urls. The direct urls render the actual website with the pin media in it.
# These pages contains the json data required to render the page client side.
# We use the json to find the video dict and pick an mp4 for our use.
# The shortened urls are redirected to a url with some get params attached.
# These params make the content generator backend render a page without the
# direct mp4 urls. So, we get the pin id by checking the redirect location
# and building the url by ourself. The we parse the json like normal


class Pin:

    def __init__(self, pin_id):
        self.__page_data = None
        self.title = None
        self.url = None
        self.id = None
        if type(pin_id) == URLInfo:
            if 'pinterest.com' in pin_id.url:
                self.__init_ivars_from_urlinfo(pin_id)
            elif 'pin.it' in pin_id.url:
                self.__init_ivars_from_short_url(pin_id.url)
        elif type(pin_id) == str:
            if validators.url(pin_id):
                if 'pinterest.com' in pin_id:
                    url_info = url_split(pin_id)
                    self.__init_ivars_from_urlinfo(url_info)
                elif 'pin.it' in pin_id:
                    self.__init_ivars_from_short_url(pin_id.url)
            else:
                self.url = f"https://in.pinterest.com/pin/{pin_id}/"
        if not self.url:
            return

        self.__page_data = None
        page_data_str = ''
        try:
            request = urlrequest.urlopen(self.url)
            page_data = request.read()
            page_data_str = page_data.decode('utf-8')
        except Exception as e:
            # pinterest can sometimes do a region based redirect
            redirect_url = e.headers.get('location')
            if redirect_url:
                print(f"Pinterest is redirecting to {redirect_url}")
                request = urlrequest.urlopen(redirect_url)
                page_data = request.read()
                page_data_str = page_data.decode('utf-8')
        regex = r"\<script\s+id=\"initial\-state\".+?\>(\{.+?\})\<\/script\>"
        # extract json page data from the source
        matches = re.findall(regex, page_data_str)
        if not matches:
            return
        dict = json.loads(matches[0])
        if dict:
            try:
                self.__page_data = \
                            dict['resourceResponses'][0]['response']['data']
            except KeyError:
                print("Can't find data")

    def __init_ivars_from_short_url(self, short_url):
        # read the header to find the redirect location
        # build a url where there's will be page data in json
        # format.
        redirect_url = get_redirect_url(short_url)
        if redirect_url:
            print(f"short url: got redirect url: {redirect_url}")
            url_info = url_split(redirect_url)
            self.__init_ivars_from_urlinfo(url_info)

    def __init_ivars_from_urlinfo(self, urlinfo: URLInfo):
        # rebuild the url to reduce the chances of pinterest's
        # region based redirects
        if urlinfo.url and len(urlinfo.components) >= 2:
            self.id = urlinfo.components[1]
            self.url = f"https://in.pinterest.com/pin/{self.id}/"

    def get_video(self):
        if not self.__page_data:
            return None
        video_list = None
        try:
            video_list = self.__page_data['videos']['video_list']
        except KeyError as e:
            print(e)
            return None

        selected_video = None
        for key, format in video_list.items():
            url = format['url']
            extension = os.path.splitext(url)[1]
            if extension != '.mp4':
                continue
            if not selected_video:
                selected_video = format
            else:
                # choose the highest quality
                if format['height'] > selected_video['height']:
                    selected_video = format
        if selected_video:
            media = MediaObject(selected_video['url'], MediaType.VIDEO)
            caption = self.__page_data.get('grid_title')
            media.caption = caption
            return media
        return None

#!/usr/bin/python3
from ig import IGBot
import os
from dotenv import load_dotenv
import urllib.request
from urllib.parse import urlparse

def url_filename(url):
    parsed = urlparse(url)
    return os.path.basename(parsed.path)

load_dotenv()
username = os.getenv('username')
password = os.getenv('password')
if not username or not password:
    print("credentials not configured")
    exit(-1)

ig = IGBot(username, password)
print(ig.user_agent)
media_url = ig.get_media_url('https://www.instagram.com/reel/CRQMooXDtQp/?utm_medium=copy_link')
if not media_url:
    print("unable to get media url")
    exit(-1)

file_name = url_filename(media_url)
print(media_url)
opener = urllib.request.build_opener()
opener.addheaders = [('User-Agent', ig.user_agent)]
urllib.request.install_opener(opener)
urllib.request.urlretrieve(media_url, file_name)


print("Ok")

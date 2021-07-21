from os import path
import urllib.request
from urllib.parse import urlparse


def url_filename(url):
    parsed = urlparse(url)
    return path.basename(parsed.path)


def download_file(url, local_path, headers=[]):
    opener = urllib.request.build_opener()
    opener.addheaders = headers
    urllib.request.install_opener(opener)
    urllib.request.urlretrieve(url, local_path)
    if path.exists(local_path):
        return True
    return False

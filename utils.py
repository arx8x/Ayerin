from os import path
import urllib.request
from urllib.parse import urlparse, parse_qs
from collections import namedtuple

UrlInfo = namedtuple(
    "URLInfo", ['url', 'domain', 'components', 'scheme', 'query', 'fragment'],
    defaults=(None,) * 5)


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


def url_split(url):
    url_split = urlparse(url, allow_fragments=True)
    if not url_split.netloc:
        return ()
    components = [c for c in url_split.path.split('/') if c]
    query = parse_qs(url_split.query)
    pathinfo = UrlInfo(url, url_split.netloc, components,
                       url_split.scheme, query, url_split.fragment)
    return pathinfo

from os import path
import urllib.request
from urllib.error import HTTPError
from urllib.parse import urlparse, parse_qs
from collections import namedtuple

URLInfo = namedtuple(
    "URLInfo", ['url', 'domain', 'components', 'scheme', 'query', 'fragment'],
    defaults=(None,) * 5)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def get_redirect_url(url):
    # urllib.request follows  rediects automatically
    # build a custom opener that neuters this behavior
    # so we'll get the redirect url from header without
    # going to the redirect url
    redirect_url = None
    try:
        opener = urllib.request.build_opener(NoRedirect)
        urllib.request.install_opener(opener)
        urllib.request.urlopen(url)
    except HTTPError as e:
        header_info = e.info()
        redirect_url = header_info.get('location')
    except Exception as e:
        print(e)

    # restore original behavior
    urllib.request.install_opener(
        urllib.request.build_opener(urllib.request.HTTPRedirectHandler))
    return redirect_url


def get_remote_filesize(url):
    if not url:
        return None
    try:
        r = urllib.request.urlopen(url)
        header_info = r.info()
        if (size := header_info.get('content-length')):
            return int(size)
    except Exception as e:
        print(e)
    return None


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
    pathinfo = URLInfo(url, url_split.netloc, components,
                       url_split.scheme, query, url_split.fragment)
    return pathinfo

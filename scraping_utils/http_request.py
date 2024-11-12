import re
import time
import logging
from urllib.parse import urlparse

import requests

# Timeout for web server response (seconds)
TIMEOUT = 5

# Maximum retries count for executing request if an error occurred
MAX_RETRIES = 3

# The delay after executing an HTTP request (seconds)
SLEEP_TIME = 0.5

# HTTP headers for making the scraper more "human-like"
HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) '
                   'Gecko/20100101 Firefox/132.0'),
    'Accept': '*/*',
}

ICANHAZIP_URL = 'http://icanhazip.com'

class HttpRequest():
    def __init__(self, headers: dict=HEADERS, max_retries: int=MAX_RETRIES,
                 timeout: float=TIMEOUT, sleep_time: float=SLEEP_TIME,
                 proxies=None):
        # These attributes may be changed directly
        self.headers = headers
        self.max_retries = max_retries
        self.timeout = timeout
        self.sleep_time = sleep_time
        self.proxies = proxies

    def _request(self, func, **args) -> requests.Response:
        args['headers'] = self.headers
        args['timeout'] = self.timeout
        args['proxies'] = self.proxies
        for attempt in range(0, self.max_retries):
            try:
                r = func(**args)
            except requests.exceptions.RequestException:
                time.sleep(self.sleep_time)
            else:
                time.sleep(self.sleep_time)
                if r.status_code != requests.codes.ok:
                    logging.error(f'Error {r.status_code} '
                                  + f'while accessing {args["url"]}.')
                    return None
                return r

        logging.error("Can't execute HTTP request while accessing "
                      + args['url'])
        return None

    def get(self, url: str, params: dict=None):
        args = {
            'url': url,
            'params': params,
        }
        func = requests.get
        return self._request(func=func, **args)

    def post(self, url: str, data: dict=None):
        args = {
            'url': url,
            'data': data,
        }
        func = requests.post
        return self._request(func=func, **args)

    def get_ip(self) -> str:
        ip = self.get(ICANHAZIP_URL)
        if ip == None:
            return None

        return ip.text.strip()

    def get_html(self, url: str, params: dict=None) -> str:
        r = self.get(url, params)
        if r == None:
            return None
        return r.text

    def check_url(self, url: str) -> bool:
        r = self.get(url)
        if r == None:
            return False

        # Soft checking for redirect
        base_url_part = re.sub(r'^www\.', '', urlparse(url.lower()).netloc)
        base_url_part = base_url_part.split('.')[0]
        if base_url_part not in r.url.lower():
            # There was a redirect, so we didn't access the actual url
            return False

        return True

    # Retrieve an image from URL and save it to a file
    def save_image(self, url: str, filename: str) -> bool:
        r = self.get(url)

        try:
            with open(filename, 'wb') as f:
                f.write(r.content)
        except OSError:
            logging.exception(f"Can't save the image to the file {filename}.")
            return False
        except Exception:
            logging.exception(f'Failure while retrieving an image from {url}.')
            return False

        return True

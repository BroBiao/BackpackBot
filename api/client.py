import json
import httpx
from . import utils
from . import consts as c


class Client(object):

    def __init__(self, api_key=None, api_secret=None, proxy=None):

        self.API_KEY = api_key
        self.API_SECRET = api_secret
        self.window = c.DEFAULT_WINDOW
        self.client = httpx.Client(http2=True, proxy=proxy)

    def _request(self, instruction, method, request_path, params):

        url = c.API_URL + request_path
        if isinstance(params, dict):
            params = utils.clean_dict_none(params)
        else:  # For batch orders execution
            params = [utils.clean_dict_none(each) for each in params]

        timestamp = utils.get_timestamp()  # local time
        # timestamp = self._get_timestamp()  # server time

        if instruction:  # Authenticated Endpoints
            if isinstance(params, dict):
                str_to_sign = utils.pre_hash(instruction, params, timestamp, self.window)
            else:  # For batch orders execution
                str_to_sign = utils.pre_hash_batch_orders(instruction, params, timestamp, self.window)
            sign = utils.sign(str_to_sign, self.API_SECRET)
            header = utils.get_header(self.API_KEY, sign, timestamp, self.window)
        else:  # Public Endpoints
            header = {}

        # print("url:", url)
        # print("headers:", header)

        if method == c.GET:
            response = self.client.request(method=method, url=url, headers=header, params=params)
        else:
            response = self.client.request(method=method, url=url, headers=header, json=params)

        # exception handle
        # print(response.headers)

        response.raise_for_status()

        if not response.content:
            if str(response.status_code).startswith('2'):
                return 'success'
            else:
                return None
        else:
            try:
                return response.json()
            except json.decoder.JSONDecodeError:
                return response.text

    def _request_without_params(self, instruction, method, request_path):
        return self._request(instruction, method, request_path, {})

    def _request_with_params(self, instruction, method, request_path, params):
        return self._request(instruction, method, request_path, params)

    def _get_timestamp(self):
        url = c.API_URL + c.SYSTEM_TIME.path
        response = self.client.get(url)
        if response.status_code == 200:
            return response.text
        else:
            return ""

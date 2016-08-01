"""RestSession class for creating 'connections' to the Cisco Spark APIs."""


import urlparse
import requests
from .exceptions import ciscosparkapiException, SparkApiError
from copy import deepcopy


# Default api.ciscospark.com base URL
DEFAULT_API_URL = 'https://api.ciscospark.com/v1/'

# Cisco Spark cloud Expected Response Codes (HTTP Response Codes)
ERC = {
    'GET': 200,
    'POST': 200,
    'PUT': 200,
    'DELETE': 204
}

# Spark API responds with:
# Response Code [429] - The number of allowed requests is exceeded.  
# Please try your request later
_API_THROTTLE_STATUS_CODE = 429

# if API throttling occurs, how much time to wait by default?
_DEFAULT_BACKOFF_TIME = 300


def _validate_base_url(base_url):
    parsed_url = urlparse.urlparse(base_url)
    if parsed_url.scheme and parsed_url.netloc:
        return parsed_url.geturl()
    else:
        error_message = "base_url must contain a valid scheme (protocol " \
                        "specifier) and network location (hostname)"
        raise ciscosparkapiException(error_message)


def _raise_if_extra_kwargs(kwargs):
    if kwargs:
        raise TypeError("Unexpected **kwargs: %r" % kwargs)


def _extract_and_parse_json(response):
    return response.json()


class RestSession(object):

    def __init__(self, access_token, base_url=DEFAULT_API_URL, timeout=None):
        super(RestSession, self).__init__()
        self._base_url = _validate_base_url(base_url)
        self._access_token = access_token
        self._req_session = requests.session()
        self._timeout = None
        self._last_response = None
        self._ratelimit_callback = None
        self.update_headers({'Authorization': 'Bearer ' + access_token,
                             'Content-type': 'application/json;charset=utf-8'})
        self.timeout = timeout


    def _check_response_code(self, response, erc):
        self._last_response = deepcopy(response)

        if not response.status_code in erc:
            raise SparkApiError(response.status_code,
                                request=response.request,
                                response=response)

    def _req_wrapper(self, method, url, erc, **kwargs):
        """ this wraps the actual request. If it gets throttled (429) 
            then there's multiple options:
            - no callback defined: it just errors out with ciscosparkapiException
            - if the callback is defined: calls callback with suggested cool down time

            if the callback returns True then the request is attempted again
            if the callback returns False then a ciscosparkapiException is raised
        """

        # make the response code a list if it's just an int
        if isinstance(erc, int):
            ercList = list((erc,))
        else:
            ercList = erc

        # if 429 (API throttling) is in list, remove it
        if _API_THROTTLE_STATUS_CODE in ercList:
            ercList.remove(_API_THROTTLE_STATUS_CODE)

        done = False
        while not done:
            r = self._req_session.request(method, url, **kwargs)
            if r.status_code ==  _API_THROTTLE_STATUS_CODE:
                retry_after = int(r.headers.get('Retry-After', 0))
                if retry_after > 0:
                    sleep_time = retry_after
                else:
                    sleep_time = _DEFAULT_BACKOFF_TIME
                if self._ratelimit_callback is not None:
                    done = not self._ratelimit_callback(sleep_time)
                else:
                    done = True
            else:
                done = True
        self._check_response_code(r, ercList)
        return r

    @property
    def ratelimit_callback(self):
        """ get the API throttling callback"""
        return self._ratelimit_callback

    @ratelimit_callback.setter
    def ratelimit_callback(self, fn):
        """ set the API throttling callback"""
        self._ratelimit_callback = fn

    @property
    def last_response(self):
        """ retrieve the last response from the API"""
        return self._last_response

    @property
    def base_url(self):
        return self._base_url

    @property
    def access_token(self):
        return self._access_token

    @property
    def headers(self):
        return self._req_session.headers.copy()

    def update_headers(self, headers):
        assert isinstance(headers, dict)
        self._req_session.headers.update(headers)

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        assert value is None or value > 0
        self._timeout = value

    def urljoin(self, suffix_url):
        return urlparse.urljoin(self.base_url, suffix_url)

    def get(self, url, params=None, **kwargs):
        # Process args
        assert isinstance(url, basestring)
        assert params is None or isinstance(params, dict)
        abs_url = self.urljoin(url)
        # Process kwargs
        timeout = kwargs.pop('timeout', self.timeout)
        erc = kwargs.pop('erc', ERC['GET'])
        _raise_if_extra_kwargs(kwargs)
        # API request
        response = self._req_wrapper('GET', abs_url, erc, 
                                         params=params,
                                         timeout=timeout)
        # Process response
        return _extract_and_parse_json(response)

    def get_pages(self, url, params=None, **kwargs):
        # Process args
        assert isinstance(url, basestring)
        assert params is None or isinstance(params, dict)
        abs_url = self.urljoin(url)
        # Process kwargs
        timeout = kwargs.pop('timeout', self.timeout)
        erc = kwargs.pop('erc', ERC['GET'])
        _raise_if_extra_kwargs(kwargs)
        # API request - get first page
        response = self._req_wrapper('GET', abs_url, erc,
                                         params=params,
                                         timeout=timeout)
        while True:
            # Process response - Yield page's JSON data
            yield _extract_and_parse_json(response)
            # Get next page
            if response.links.get('next'):
                next_url = response.links.get('next').get('url')
                # API request - get next page
                response = self._req_wrapper('GET', next_url, erc, timeout=timeout)
            else:
                raise StopIteration

    def get_items(self, url, params=None, **kwargs):
        # Get iterator for pages of JSON data
        pages = self.get_pages(url, params=params, **kwargs)
        # Process pages
        for json_page in pages:
            # Process each page of JSON data yielding the individual JSON
            # objects contained within the top level 'items' array
            assert isinstance(json_page, dict)
            items = json_page.get(u'items')
            if items:
                for item in items:
                    yield item
            else:
                error_message = "'items' object not found in JSON data: %r" \
                                % json_page
                raise ciscosparkapiException(error_message)

    def post(self, url, json_dict, **kwargs):
        # Process args
        assert isinstance(url, basestring)
        assert isinstance(json_dict, dict)
        abs_url = self.urljoin(url)
        # Process kwargs
        timeout = kwargs.pop('timeout', self.timeout)
        erc = kwargs.pop('erc', ERC['POST'])
        _raise_if_extra_kwargs(kwargs)
        # API request
        response = self._req_wrapper('POST', abs_url, erc, 
                                          json=json_dict,
                                          timeout=timeout)
        # Process response
        return _extract_and_parse_json(response)

    def put(self, url, json_dict, **kwargs):
        # Process args
        assert isinstance(url, basestring)
        assert isinstance(json_dict, dict)
        abs_url = self.urljoin(url)
        # Process kwargs
        timeout = kwargs.pop('timeout', self.timeout)
        erc = kwargs.pop('erc', ERC['PUT'])
        _raise_if_extra_kwargs(kwargs)
        # API request
        response = self._req_wrapper('PUT', abs_url, erc, 
                                         json=json_dict,
                                         timeout=timeout)
        # Process response
        return _extract_and_parse_json(response)

    def delete(self, url, **kwargs):
        # Process args
        assert isinstance(url, basestring)
        abs_url = self.urljoin(url)
        # Process kwargs
        timeout = kwargs.pop('timeout', self.timeout)
        erc = kwargs.pop('erc', ERC['DELETE'])
        _raise_if_extra_kwargs(kwargs)
        # API request
        response = self._req_wrapper('DELETE', abs_url, erc, timeout=timeout)
        # Process response

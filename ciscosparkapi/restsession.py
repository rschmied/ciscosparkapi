"""RestSession class for creating 'connections' to the Cisco Spark APIs."""


import urlparse
import requests
from .exceptions import ciscosparkapiException, SparkApiError
from copy import deepcopy
from datetime import datetime
from ciscosparkapi.helperfunc import sparkISO8601, utf8


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
# given in the n-th Fibonacci number (9th = 34s)
_DEFAULT_BACKOFF = 9


def _del_url_query_part(url, qp):
    """ removes query part from url """
    parts = urlparse.urlsplit(url)
    query = urlparse.parse_qs(parts.query)
    new_parts = list(parts)

    try:
       del query[qp]
    except KeyError as e:
       return url
    new_parts[3] = '&'.join(["%s=%s" % (k,v[0]) for (k, v) in query.items()])

    return urlparse.urlunsplit(new_parts)


def _validate_base_url(base_url):
    parsed_url = urlparse.urlparse(base_url)
    if parsed_url.scheme and parsed_url.netloc:
        return parsed_url.geturl()
    else:
        error_message = "base_url must contain a valid scheme (protocol " \
                        "specifier) and network location (hostname)"
        raise ciscosparkapiException(error_message)


def _process_args(what, apiattr, args):
    """ make sure the arguments have the proper type / encoding
        also move args in the apiattr into a separate dict
        which will be passed as the 'json' parameter to the request
    """

    data = dict()
    for k, v in args.items():
        if isinstance(v, basestring):
            args[k] = utf8(v)
        elif isinstance(v, datetime):
            args[k] = sparkISO8601(v)
        else:
            pass
        if k in apiattr:
            v = args.pop(k)
            data[k] = v

    if len(data) > 0:
        if what in ['POST', 'PUT']:
            args['json'] = data
        elif what in ['GET', 'DELETE']:
            args['params'] = data
        else:
            raise ValueError("Unexpected method %r" % what)
    return args


def _extract_and_parse_json(response):
    return response.json()


def _fib():
    """a Fibonacci generator"""
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b


def fib(n):
    """give the n-th Fibonacci number"""
    f = _fib()
    counter = 0
    for i in f:
        if counter < n:
            counter += 1
        else:
            break
    return i


class RestSession(object):

    def __init__(self, access_token, base_url=DEFAULT_API_URL, timeout=None):
        super(RestSession, self).__init__()
        self._base_url = _validate_base_url(base_url)
        self._access_token = access_token
        self._req_session = requests.session()
        self._timeout = None
        self._last_response = None
        self._ratelimit_callback = None
        self._ratelimit_step = _DEFAULT_BACKOFF
        self.update_headers({'Authorization': 'Bearer ' + access_token,
                             'Content-type': 'application/json;charset=utf-8'})
        self.timeout = timeout

    def _req_wrapper(self, method, url, erc, apiattr, **kwargs):
        """ this wraps the actual request. If it gets throttled (429) 
            then there's multiple options:
            - no callback defined: it just errors out with ciscosparkapiException
            - if the callback is defined: calls callback with suggested cool down time

            if the callback returns True then the request is attempted again
            if the callback returns False then a ciscosparkapiException is raised

            There's two ways to back off:
            - server sends 'Retry-After' header, we can use that time
            - if no Retry-After is sent, we apply a Fibonacci sequence and increase
              the wait. The class remembers the last 'step' and for every successful
              response the step is decreased until it reaches the _DEFAULT_BACKOFF step

            The 'sleep time' is reported to the callback (if configured).
        """

	#print url, kwargs

        done = False
        while not done:
            done = True
            r = self._req_session.request(method, url, **kwargs)
            # was rate limiting in effect?
            if r.status_code == _API_THROTTLE_STATUS_CODE:
                # does the server respond with a rate-limit header?
                retry_after = int(r.headers.get('Retry-After', 0))
                if retry_after > 0:
                    sleep_time = retry_after
                    self._ratelimit_step = _DEFAULT_BACKOFF
                else:
                    sleep_time = fib(self._ratelimit_step)
                # has a callback been configured?
                # if yes, call it and see if we should try again
                if self._ratelimit_callback is not None:
                    done = not self._ratelimit_callback(sleep_time)
                    self._ratelimit_step += 1
            else:
                # no throttling: reduce the backoff step, if above threshold
                if self._ratelimit_step > _DEFAULT_BACKOFF:
                    self._ratelimit_step -= 1

        # check response code
        self._last_response = deepcopy(r)
        if not r.status_code in erc:
            raise SparkApiError(r.status_code,
                                request=r.request,
                                response=r)
        return r

    def _process(self, what, url, apiattr, **kwargs):
        """ prepare the ERC list, process the argument list
            converting dates and strings
        """
        # Process args
        assert isinstance(url, basestring)
        assert isinstance(apiattr, list)
        abs_url = self.urljoin(url)

        # make the response code a list if it's just an int
        erc = kwargs.pop('erc', ERC[what])
        if isinstance(erc, int):
            ercList = list((erc,))
        elif isinstance(erc, list):
            ercList = erc
        else:
            raise TypeError('unexpected response code type <%r>' % erc)

        # if 429 (API throttling) is in list, remove it
        if _API_THROTTLE_STATUS_CODE in ercList:
            ercList.remove(_API_THROTTLE_STATUS_CODE)

        # ensure proper encoding and parameter handling
        kwargs = _process_args(what, apiattr, kwargs)
        return self._req_wrapper(what, abs_url, ercList, apiattr, **kwargs)

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

    def get_pages(self, url, apiattr, **kwargs):
        response = self._process('GET', url, apiattr, **kwargs)
        while True:
            # Process response - Yield page's JSON data
            yield _extract_and_parse_json(response)
            # Get next page
            if response.links.get('next'):
                next_url = response.links.get('next').get('url')
                #
                # API request - get next page
                # FIXME: args aren't truly passed since the Spark API
                # returns another set of queryparms which can interfere
                # with the ones passed in kwargs.
                # in theory, the combined next_url and kwargs had to be
                # linted / made unique in a way. But e.g. 'before' or
                # 'beforeMessage' can interfere, which one takes
                # precedence then?
                #
                #response = self._process('GET', next_url, apiattr, **kwargs)
                response = self._process('GET', next_url, apiattr)
            else:
                raise StopIteration

    def get_items(self, url, apiattr, **kwargs):
        # Get iterator for pages of JSON data
        pages = self.get_pages(url, apiattr, **kwargs)
        # Process pages
        for json_page in pages:
            # Process each page of JSON data yielding the individual JSON
            # objects contained within the top level 'items' array
            assert isinstance(json_page, dict)
            # sometimes there's an empty list returned
            # I guess this should not happen server side, but if there's
            # a lengthy list then the last page can have zero elements
            # and the 2nd to last page still has a 'next' link header
            items = json_page.get(u'items', None)
            if items is not None:
                for item in items:
                    yield item
            else:
                error_message = "'items' object not found in JSON data: %r" \
                                % json_page
                raise ciscosparkapiException(error_message)

    def get(self, url, apiattr, **kwargs):
        return _extract_and_parse_json(self._process('GET', url, apiattr, **kwargs))

    def post(self, url, apiattr, **kwargs):
        return _extract_and_parse_json(self._process('POST', url, apiattr, **kwargs))

    def put(self, url, apiattr, **kwargs):
        return _extract_and_parse_json(self._process('PUT', url, apiattr, **kwargs))

    def delete(self, url, apiattr, **kwargs):
        return _extract_and_parse_json(self._process('DELETE', url, apiattr, **kwargs))

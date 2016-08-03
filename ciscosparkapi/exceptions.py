"""ciscosparkapi exception classes."""


class ciscosparkapiException(Exception):
    """Base class for all ciscosparkapi package exceptions."""

    def __init__(self, *args, **kwargs):
        super(ciscosparkapiException, self).__init__(*args, **kwargs)


class SparkApiError(ciscosparkapiException):
    """Errors returned by requests to the Cisco Spark cloud APIs."""

    def __init__(self, response_code, request=None, response=None):
        assert isinstance(response_code, int)
        self.response_code = response_code
        self.request = request
        self.response = response

        self.response_text = response.json().get('message')
        error_message = "Response Code [%s] - %s" % \
                        (response_code, self.response_text)
        super(SparkApiError, self).__init__(error_message)

"""Spark - Messages API - wrapper classes."""


from ciscosparkapi.exceptions import ciscosparkapiException
from ciscosparkapi.helperfunc import utf8, sparkISO8601
from ciscosparkapi.restsession import RestSession
from ciscosparkapi.api.sparkobject import SparkBaseObject


_ATTRIBUTES = ['id', 'created', 'roomId', 'roomType',
               'text', 'files', 'personId', 'personEmail']
_DOCSTRINGS = ['Message ID', 'date created, ISO8601', 'Room ID', 'group or direct', 'actual message',
               'array of file attachment URIs', 'ID of person who sent message',
               'email of person who sent message']


class Message(SparkBaseObject):
    """Cisco Spark Message Object"""

    _API = dict(zip(_ATTRIBUTES, _DOCSTRINGS))

    def __init__(self, arg=None):
        super(Message, self).__init__(arg)


class MessagesAPI(object):
    """Spark Messages API request wrapper."""

    def __init__(self, session):
        assert isinstance(session, RestSession)
        super(MessagesAPI, self).__init__()
        self.session = session

    def list(self, roomId, max=None, **query_params):
        """List messages.

        roomId is mandatory.

        By default, lists rooms to which the authenticated user belongs.

        This method supports Cisco Spark's implmentation of RFC5988 Web Linking
        to provide pagination support.  It returns an iterator that
        incrementally yields all rooms returned by the query.  It will
        automatically and efficiently request the additional 'pages' of
        responses from Spark as needed until all responses have been exhausted.

        Args:
            roomId (): List messages for a room, by ID.
            max(int): Limit the maximum number of messages in the response.

        **query_params:
            before (): List messages sent before a date and time, in datetime format
            beforeMessage (): List messages sent before a message, by ID.

        Returns:
            A Message iterator.

        Raises:
            SparkApiError: If the list request fails.
        """
        # Process args
        assert max is None or isinstance(max, int)
        assert isinstance(roomId, basestring) and len(roomId) > 0

        params = {}
        if max:
            params[u'max'] = max
        params[u'roomId'] = utf8(roomId)

        # Process query_param keyword arguments
        if query_params:
            for param, value in query_params.items():
                if isinstance(value, datetime):
                    value = sparkISO8601(value)
                if isinstance(value, basestring):
                    value = utf8(value)
                params[utf8(param)] = value
        # API request - get items
        items = self.session.get_items('messages', params=params)
        # Yield message objects created from the returned items JSON objects
        for item in items:
            yield Message(item)

    def create(self, roomId=None, **kwargs):
        """Creates a message.

        The authenticated user is automatically added as a member of the room.

        Args:
            roomId(string): The room Id
            toPersonId(string): The ID of the recipient when sending 1:1 messages
            toPersonEmail(string): The email of the recipient when sending 1:1 messages
            text(string): the text (as alternatetext when Markdown or HTML is sent)
            markdown(string): the text in Markdown
            html(string): the text in HTML
            files(string): attachment

        Raises:
            SparkApiError: If the create operation fails.

        Returns:
            Message object
        """
        # Process args
        params = {}
        for k, v in kwargs.items():
            params[k] = utf8(v)
        if roomId is not None:
            params[u'roomId'] = utf8(roomId)

        # API request
        json_message_obj = self.session.post('messages', params)
        # Return a Room object created from the response JSON data
        return Message(json_message_obj)

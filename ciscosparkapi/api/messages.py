"""Spark - Messages API - wrapper classes."""

from collections import OrderedDict
from ciscosparkapi.exceptions import ciscosparkapiException
from ciscosparkapi.helperfunc import utf8, sparkISO8601
from ciscosparkapi.restsession import RestSession
from ciscosparkapi.api.sparkobject import SparkBaseObject
from datetime import datetime


_API_KEYS = ['id',
             'created',
             'roomId',
             'roomType',
             'text',
             'markdown',
             'html',
             'files',
             'personId',
             'personEmail',
             'mentionedPeople'
             ]
_API_ATTRS = [('Message ID (string)', basestring),
              ('date created, ISO8601 (string)', datetime),
              ('Room ID (string)', basestring),
              ('"group" or "direct" (string)', basestring),
              ('actual message as text (string)', basestring),
              ('actual message as markdown (string)', basestring),
              ('actual message as HTML (string)', basestring),
              ('array of file attachment URIs (list)', list),
              ('ID of person who sent message (string)', basestring),
              ('email of person who sent message (string)', basestring),
              ('people mentioned in message personId (string)', basestring)
              ]
_API_ENTRY_SUFFIX = 'messages'


class Message(SparkBaseObject):
    """Cisco Spark Message Object"""

    _API = OrderedDict(zip(_API_KEYS, _API_ATTRS))

    def __init__(self, arg=None):
        super(Message, self).__init__(arg)

    def __str__(self):
        return self.text


class MessagesAPI(object):
    """Spark Messages API request wrapper."""

    def __init__(self, session):
        assert isinstance(session, RestSession)
        super(MessagesAPI, self).__init__()
        self.session = session

    def list(self, roomId, **kwargs):
        """List messages.

        roomId is mandatory.

        Lists messages in the given room

        This method supports Cisco Spark's implmentation of RFC5988 Web Linking
        to provide pagination support.  It returns an iterator that
        incrementally yields all rooms returned by the query.  It will
        automatically and efficiently request the additional 'pages' of
        responses from Spark as needed until all responses have been exhausted.

        Args:
            roomId (string): List messages for a room, by ID.

        **kwargs:
            max(int): Limit the maximum number of messages in the response.
            before (): List messages sent before a date and time, in datetime format
            beforeMessage (): List messages sent before a message, by ID.

        Returns:
            A Message iterator.

        Raises:
            SparkApiError: If the list request fails.
        """
        # Process args
        assert isinstance(roomId, basestring) and len(roomId) > 0

        # API request - get items
        apiattr = ['roomId', 'before', 'beforeMessage', 'max']
        kwargs['roomId'] = roomId
        items = self.session.get_items(_API_ENTRY_SUFFIX, apiattr, **kwargs)
        # Yield message objects created from the returned items JSON objects
        for item in items:
            yield Message(item)

    def create(self, **kwargs):
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
        # API request
        apiattr = ['roomId', 'toPersonId', 'toPersonEmail', 'text', 'markdown', 'html', 'files']
        # Return a Room object created from the response JSON data
        return Message(self.session.post(_API_ENTRY_SUFFIX, apiattr, **kwargs))

    def details(self, messageId, **kwargs):
        """ Shows details for a message, by message ID.

            Specify the message ID in the messageId parameter in the URI.

        Args:
            messageId (string): The message Id

        Raises:
            SparkApiError: If the create operation fails.

        Returns:
            Message object
        """
        # API request
        apiattr = ['messageId']
        kwargs['messageId'] = messageId
        # Return a Room object created from the response JSON data
        return Message(self.session.get(_API_ENTRY_SUFFIX, apiattr, **kwargs))

    def delete(self, messageId, **kwargs):
        """ Deletes a message, by message ID.

            Specify the message ID in the messageId parameter in the URI.

        Args:
            messageId (string): The message Id

        Raises:
            SparkApiError: If the create operation fails.

        Returns:
            Message object
        """
        # API request
        apiattr = ['messageId']
        kwargs['messageId'] = messageId
        # Return a Room object created from the response JSON data
        return Message(self.session.delete(_API_ENTRY_SUFFIX, apiattr, **kwargs))

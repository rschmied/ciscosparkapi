"""Spark - Messages API - wrapper classes."""

from collections import OrderedDict
from ciscosparkapi.exceptions import ciscosparkapiException
from ciscosparkapi.helperfunc import utf8, sparkISO8601
from ciscosparkapi.api.rooms import RoomsAPI, Room
from ciscosparkapi.api.sparkobject import SparkBaseObject, SparkBaseAPI
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


class Message(SparkBaseObject):
    """Cisco Spark Message Object"""

    _API = OrderedDict(zip(_API_KEYS, _API_ATTRS))

    def __init__(self, arg=None):
        super(Message, self).__init__(arg)

    def __str__(self):
        return self.text


class MessagesAPI(SparkBaseAPI):
    """Spark Messages API request wrapper."""

    _API_ENTRY_SUFFIX = 'messages'

    def __init__(self, api):
        super(MessagesAPI, self).__init__()
        self.api = api

    def list(self, room, **kwargs):
        """List messages.

        room is mandatory.

        Lists messages in the given room

        This method supports Cisco Spark's implmentation of RFC5988 Web Linking
        to provide pagination support.  It returns an iterator that
        incrementally yields all rooms returned by the query.  It will
        automatically and efficiently request the additional 'pages' of
        responses from Spark as needed until all responses have been exhausted.

        It also goes beyond the pages using a cursor to go back until room
        creation time.

        Args:
            room (Room): List messages for a Room object.

        **kwargs:
            max (int): Limit the maximum number of messages in the response.
            before (datetime): List messages sent before a date and time
            beforeMessage (Message): List messages sent before a message

        Returns:
            A Message iterator.

        Raises:
            SparkApiError: If the list request fails.
        """
        # Process args
        assert isinstance(room, Room)
        kwargs['roomId'] = room.id

        # need to get referred message details?
        beforeMessage = kwargs.pop('beforeMessage', None)
        if beforeMessage:
            assert isinstance(beforeMessage, Message)
            kwargs['before'] = beforeMessage.created

        room = self.api.rooms.details(room)

        # API request - get items
        # 'beforeMessage' will never make it to the API
        # as we convert it to 'before' above
        apiattr = ['roomId', 'before', 'beforeMessage', 'max']

        cursor = kwargs.pop('before', datetime.utcnow())
        assert isinstance(cursor, datetime)

        while cursor > room.created:
            counter = 0
            items = self.api.session.get_items(
                self._API_ENTRY_SUFFIX, apiattr, before=cursor, **kwargs)
            for item in items:
                counter = + 1
                # Yield message objects created from the returned items JSON
                # objects
                message = Message(item)
                yield message
            if counter > 0:
                cursor = message.created
            else:
                cursor = room.created

    def create(self, room=None, person=None, email=None, **kwargs):
        """Creates a message.

        The authenticated user is automatically added as a member of the room.
        Either room, person or email is required

        Args:
            room (Room): The room where the message should go
            person (Person): The person of the recipient when sending 1:1 messages
            email (string): The email of the recipient when sending 1:1 messages

        **kwargs:
            text (string): the text (as alternatetext when Markdown or HTML is sent)
            markdown (string): the text in Markdown
            html (string): the text in HTML
            files (string): attachment

        Raises:
            SparkApiError: If the create operation fails.

        Returns:
            Message object
        """

        if room:
            assert isinstance(room, Room)
            kwargs['roomId'] = room.id

        if person:
            assert isinstance(person, Person)
            kwargs['toPersonId'] = person.id

        if email:
            assert isinstance(email, basestring)
            kwargs['toPersonEmail'] = email

        # API request
        apiattr = ['roomId', 'toPersonId', 'toPersonEmail',
                   'text', 'markdown', 'html', 'files']
        # Return a new Message object
        return Message(self.api.session.post(self._API_ENTRY_SUFFIX, apiattr, **kwargs))

    def details(self, message, **kwargs):
        """ Shows details for a message, by message ID.

            Specify the ID in the message object.

        Args:
            message (Message): The message (with ID)

        Raises:
            SparkApiError: If the details operation fails.

        Returns:
            Message object
        """

        if isinstance(message, Message):
            messageId = message.id
        elif isinstance(message, basestring):
            messageId = message

        # API request
        apiattr = ['messageId']
        # Return a Message object with details
        return Message(self.api.session.get(self._uri_append(messageId), apiattr, **kwargs))

    def delete(self, message, **kwargs):
        """ Deletes a message, by message ID.

            Specify the ID in the message object.

        Args:
            message (Message): The message (with ID)

        Raises:
            SparkApiError: If the delete operation fails.

        Returns:
            None
        """

        if isinstance(message, Message):
            messageId = message.id
        elif isinstance(message, basestring):
            messageId = message

        # API request
        apiattr = ['messageId']
        self.api.session.delete(self._uri_append(messageId), apiattr, **kwargs)

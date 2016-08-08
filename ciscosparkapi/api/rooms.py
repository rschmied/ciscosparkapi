"""Spark - Rooms API - wrapper classes."""

from collections import OrderedDict
from ciscosparkapi.exceptions import ciscosparkapiException
from ciscosparkapi.helperfunc import utf8
from ciscosparkapi.api.sparkobject import SparkBaseObject, SparkBaseAPI
from datetime import datetime

_API_KEYS = ['id',
             'created',
             'type',
             'title',
             'isLocked',
             'lastActivity',
             'teamId'
             ]
_API_ATTRS = [('Room ID (string)', basestring),
              ('date created, ISO8601 (string)', datetime),
              ('"group" or "direct" (string)', basestring),
              ('title of the room (string)', basestring),
              ('true or false (bool)', bool),
              ('date of last activity, ISO8601 (string)', datetime),
              ('team ID of the room (string)', basestring),
              ]


class Room(SparkBaseObject):
    """Cisco Spark Room Object"""

    _API = OrderedDict(zip(_API_KEYS, _API_ATTRS))

    def __init__(self, arg=None):
        super(Room, self).__init__(arg)

    def __str__(self):
        return self.title


class RoomsAPI(SparkBaseAPI):
    """Spark Rooms API request wrapper."""

    _API_ENTRY_SUFFIX = 'rooms'

    def __init__(self, api):
        super(RoomsAPI, self).__init__()
        self.api = api

    def list(self, **kwargs):
        """List rooms.

        By default, lists rooms to which the authenticated user belongs.

        This method supports Cisco Spark's implmentation of RFC5988 Web Linking
        to provide pagination support.  It returns an iterator that
        incrementally yields all rooms returned by the query.  It will
        automatically and efficiently request the additional 'pages' of
        responses from Spark as needed until all responses have been exhausted.

        Args:

        **kwargs:
            teamId (string): Limit the rooms to those associated with a team, by ID.
            max (int): Limits the maximum number of rooms in the response.
            type(string):
                'direct': returns all 1-to-1 rooms.
                'group': returns all group rooms.

        Returns:
            A Room iterator.

        Raises:
            SparkApiError: If the list request fails.
        """
        apiparm = ['teamId', 'max,', 'type']
        items = self.api.session.get_items(
            self._API_ENTRY_SUFFIX, apiparm, **kwargs)
        # Yield Room objects created from the returned items JSON objects
        for item in items:
            yield Room(item)

    def create(self, title, **kwargs):
        """Creates a room.

        The authenticated user is automatically added as a member of the room.

        Args:
            title (string): A user-friendly name for the room.

        **kwargs:
            teamId (string): The team ID with which this room is associated.

        Raises:
            SparkApiError: If the create operation fails.
        """
        assert isinstance(title, str) and len(title) > 0
        kwargs['title'] = title
        apiparm = ['title', 'teamId']
        return Room(self.api.session.post(self._API_ENTRY_SUFFIX, apiparm, **kwargs))

    def details(self, room, **kwargs):
        """Gets the details of a room.

        Args:
            room (Room or string): The requested room.

        Raises:
            SparkApiError: If the get operation fails.
        """
        if isinstance(room, Room):
            roomId = room.id
        elif isinstance(room, basestring):
            roomId = room
        else:
            raise ValueError("missing room Id")
        apiparm = []
        return Room(self.api.session.get(self._uri_append(roomId), apiparm, **kwargs))

    def update(self, room, **kwargs):
        """Updates details for a room. Only change of the title is
           actually used.

        Args:
            room (Room or string): The room object of the room to be updated.

        **kwargs:
            title (string): only needed if room is passed as an ID

        Returns:
            A Room object with the updated details.

        Raises:
            SparkApiError: If the update operation fails.
        """
        if isinstance(room, Room):
            roomId = room.id
            kwargs['title'] = room.title
        elif isinstance(message, basestring):
            roomId = room
        else:
            raise ValueError("missing room Id")
        apiparm = ['title']
        return Room(self.api.session.put(self._uri_append(roomId), apiparm, **kwargs))

    def delete(self, room, **kwargs):
        """Delete a room.

        Args:
            room (Room or string): The room object to be deleted.

        Raises:
            SparkApiError: If the delete operation fails.

        Returns:
            Nothing
        """
        if isinstance(room, Room):
            roomId = room.id
        elif isinstance(message, basestring):
            roomId = room
        else:
            raise ValueError("missing room Id")
        apiparm = ['roomId']
        self.api.session.delete(
            '/'.join((self._API_ENTRY_SUFFIX, roomId)), apiparm, **kwargs)

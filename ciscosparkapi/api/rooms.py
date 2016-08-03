"""Spark - Rooms API - wrapper classes."""

from collections import OrderedDict
from ciscosparkapi.exceptions import ciscosparkapiException
from ciscosparkapi.helperfunc import utf8
from ciscosparkapi.restsession import RestSession
from ciscosparkapi.api.sparkobject import SparkBaseObject
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
_API_ENTRY_SUFFIX = 'rooms'


class Room(SparkBaseObject):
    """Cisco Spark Room Object"""

    _API = OrderedDict(zip(_API_KEYS, _API_ATTRS))

    def __init__(self, arg=None):
        super(Room, self).__init__(arg)

    def __str__(self):
        return self.title


class RoomsAPI(object):
    """Spark Rooms API request wrapper."""

    def __init__(self, session):
        assert isinstance(session, RestSession)
        super(RoomsAPI, self).__init__()
        self.session = session

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
        items = self.session.get_items(_API_ENTRY_SUFFIX, apiparm, **kwargs)
        # Yield Room objects created from the returned items JSON objects
        for item in items:
            yield Room(item)

    def create(self, title, **kwargs):
        """Creates a room.

        The authenticated user is automatically added as a member of the room.

        **kwargs:
            title(string): A user-friendly name for the room.
            teamId(string): The team ID with which this room is associated.

        Raises:
            SparkApiError: If the create operation fails.
        """
        assert isinstance(title, str) and len(title) > 0
        kwargs['title'] = title
        apiparm = ['title', 'teamId']
        return Room(self.session.post(_API_ENTRY_SUFFIX, apiparm, **kwargs))

    def get(self, roomId):
        """Gets the details of a room.

        Args:
            roomId(string): The roomId of the room.

        Raises:
            SparkApiError: If the get operation fails.
        """
        # Process args
        assert isinstance(roomId, basestring) and len(roomId) > 0
        kwargs['roomId'] = roomId
        apiparm = ['roomId']
        return Room(self.session.get(_API_ENTRY_SUFFIX, apiparm, **kwargs))

    def update(self, roomId, title, **kwargs):
        """Updates details for a room.

        Args:
            roomId (string): The roomId of the room to be updated.
            title (string): the new title

        Returns:
            A Room object with the updated Spark room details.

        Raises:
            SparkApiError: If the update operation fails.
        """
        # Process args
        assert isinstance(roomId, basestring) and len(roomId) > 0
        assert isinstance(title, basestring) and len(title) > 0
        kwargs['title']=title
        apiparm = ['title']
        return Room(self.session.put('/'.join((_API_ENTRY_SUFFIX, roomId)), apiparm, **kwargs))

    def delete(self, roomId):
        """Delete a room.

        Args:
            roomId(string): The roomId of the room to be deleted.

        Raises:
            SparkApiError: If the delete operation fails.
        """
        assert isinstance(roomId, basestring) and len(roomId) > 0
        kwargs['roomId']=roomId
        apiparm=['roomId']
        return Room(self.session.delete(_API_ENTRY_SUFFIX, apiparm, **kwargs))

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


class RoomsAPI(object):
    """Spark Rooms API request wrapper."""

    def __init__(self, session):
        assert isinstance(session, RestSession)
        super(RoomsAPI, self).__init__()
        self.session = session

    def list(self, max=None, **query_params):
        """List rooms.

        By default, lists rooms to which the authenticated user belongs.

        This method supports Cisco Spark's implmentation of RFC5988 Web Linking
        to provide pagination support.  It returns an iterator that
        incrementally yields all rooms returned by the query.  It will
        automatically and efficiently request the additional 'pages' of
        responses from Spark as needed until all responses have been exhausted.

        Args:
            max(int): Limits the maximum number of rooms returned from the
                Spark service per request.

        **query_params:
            teamId(string): Limit the rooms to those associated with a team.
            type(string):
                'direct': returns all 1-to-1 rooms.
                'group': returns all group rooms.

        Returns:
            A Room iterator.

        Raises:
            SparkApiError: If the list request fails.
        """
        # Process args
        assert max is None or isinstance(max, int)
        params = {}
        if max:
            params[u'max'] = max
        # Process query_param keyword arguments
        if query_params:
            for param, value in query_params.items():
                if isinstance(value, basestring):
                    value = utf8(value)
                params[utf8(param)] = value
        # API request - get items
        items = self.session.get_items(_API_ENTRY_SUFFIX, params=params)
        # Yield Room objects created from the returned items JSON objects
        for item in items:
            yield Room(item)

    def create(self, title, teamId=None):
        """Creates a room.

        The authenticated user is automatically added as a member of the room.

        Args:
            title(string): A user-friendly name for the room.
            teamId(string): The team ID with which this room is associated.

        Raises:
            SparkApiError: If the create operation fails.
        """
        # Process args
        assert isinstance(title, basestring)
        assert teamId is None or isinstance(teamId, basestring)
        post_data = {}
        post_data[u'title'] = utf8(title)
        if teamId:
            post_data[u'teamId'] = utf8(teamId)
        # API request
        json_room_obj = self.session.post(_API_ENTRY_SUFFIX, json=post_data)
        # Return a Room object created from the response JSON data
        return Room(json_room_obj)

    def get(self, roomId):
        """Gets the details of a room.

        Args:
            roomId(string): The roomId of the room.

        Raises:
            SparkApiError: If the get operation fails.
        """
        # Process args
        assert isinstance(roomId, basestring)
        # API request
        json_room_obj = self.session.get(_API_ENTRY_SUFFIX / + roomId)
        # Return a Room object created from the response JSON data
        return Room(json_room_obj)

    def update(self, roomId, **update_attributes):
        """Updates details for a room.

        Args:
            roomId(string): The roomId of the room to be updated.

        **update_attributes:
            title(string): A user-friendly name for the room.

        Returns:
            A Room object with the updated Spark room details.

        Raises:
            ciscosparkapiException: If an update attribute is not provided.
            SparkApiError: If the update operation fails.
        """
        # Process args
        assert isinstance(roomId, basestring)
        # Process update_attributes keyword arguments
        if not update_attributes:
            error_message = "You must provide at least one " \
                            "**update_attributes keyword argument; 0 provided."
            raise ciscosparkapiException(error_message)
        put_data = {}
        for param, value in update_attributes.items():
            if isinstance(value, basestring):
                value = utf8(value)
            put_data[utf8(param)] = value
        # API request
        json_room_obj = self.session.put(
            _API_ENTRY_SUFFIX / + roomId, put_data)
        # Return a Room object created from the response JSON data
        return Room(json_room_obj)

    def delete(self, roomId):
        """Delete a room.

        Args:
            roomId(string): The roomId of the room to be deleted.

        Raises:
            SparkApiError: If the delete operation fails.
        """
        # Process args
        assert isinstance(roomId, basestring)
        # API request
        self.session.delete(_API_ENTRY_SUFFIX / + roomId)

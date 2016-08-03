"""Spark - Membership API - wrapper classes."""

from collections import OrderedDict
from ciscosparkapi.exceptions import ciscosparkapiException
from ciscosparkapi.helperfunc import utf8, sparkISO8601
from ciscosparkapi.restsession import RestSession
from ciscosparkapi.api.sparkobject import SparkBaseObject
from datetime import datetime


_API_KEYS = ['id',
             'created',
             'roomId',
             'personId',
             'personEmail',
             'personDisplayName',
             'isModerator',
             'isMonitor'
             ]
_API_ATTRS = [('Membership ID (string)', basestring),
              ('date created, ISO8601 (str, ISO8601 date)', datetime),
              ('Room ID (string)', basestring),
              ('ID of the member (string)', basestring),
              ('email of member (string)', basestring),
              ('display name of member (string)', basestring),
              ('is the member a moderator? (bool)', bool),
              ('monitor, what does this? (bool)', bool)
              ]

_API_ENTRY_SUFFIX = 'memberships'


class Membership(SparkBaseObject):
    """Cisco Spark Membership Object"""

    _API = OrderedDict(zip(_API_KEYS, _API_ATTRS))

    def __init__(self, arg=None):
        super(Membership, self).__init__(arg)


class MembershipsAPI(object):
    """Spark Membership API request wrapper."""

    def __init__(self, session):
        assert isinstance(session, RestSession)
        super(MembershipsAPI, self).__init__()
        self.session = session

    def list(self, **query_params):
        """List memberships.

        roomId is mandatory.

        By default, lists rooms to which the authenticated user belongs.

        This method supports Cisco Spark's implmentation of RFC5988 Web Linking
        to provide pagination support.  It returns an iterator that
        incrementally yields all rooms returned by the query.  It will
        automatically and efficiently request the additional 'pages' of
        responses from Spark as needed until all responses have been exhausted.

        **query_params:
            roomId (str): List memberships for a room, by ID.
            personId (str): list membership for this person's ID
            personEmail (str): list membership for this person's email
            max(int): Limit the maximum number of memberships in the response.

        Returns:
            A Membership iterator.

        Raises:
            SparkApiError: If the list request fails.
        """

        params = dict()
        # Process query_param keyword arguments
        if query_params:
            for param, value in query_params.items():
                if isinstance(value, basestring):
                    value = utf8(value)
                params[utf8(param)] = value
        # API request - get items
        items = self.session.get_items(_API_ENTRY_SUFFIX, params=params)
        # Yield membership objects created from the returned items JSON objects
        for item in items:
            yield Membership(item)

    def create(self, roomId, **kwargs):
        """Creates a membership.

        Creates a membership of the specified user (via id or email) to the given room.
        E.g. adds the specified user to the room.

        Args:
            roomId(string): The room Id

        **query_params:
            personId(string): The ID of the member
            personEmail(string): The email of the member
            isModerator(bool): set to True if this person should be moderator

        Raises:
            SparkApiError: If the create operation fails.

        Returns:
            Membership object or None if the user is already member of the room
        """

        assert isinstance(roomId, basestring) and len(roomId) > 0
        params = dict()
        params[u'roomId'] = utf8(roomId)

        # Process args
        for k, v in kwargs.items():
            if isinstance(v, basestring):
                params[k] = utf8(v)
            else:
                params[k] = v

        # API request
        # one could argue that 409 is a valid resonse status_code
        # (meaning 'user already in room')
        json_membership_obj = self.session.post(_API_ENTRY_SUFFIX, params)
        # Return a Membership object created from the response JSON data
        if self.session.last_response.status_code == 200:
            return Membership(json_membership_obj)
        else:
            return None

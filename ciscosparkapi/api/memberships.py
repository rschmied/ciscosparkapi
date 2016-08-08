"""Spark - Membership API - wrapper classes."""

from collections import OrderedDict
from ciscosparkapi.exceptions import ciscosparkapiException
from ciscosparkapi.helperfunc import utf8, sparkISO8601
from ciscosparkapi.api.sparkobject import SparkBaseObject, SparkBaseAPI
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


class Membership(SparkBaseObject):
    """Cisco Spark Membership Object"""

    _API = OrderedDict(zip(_API_KEYS, _API_ATTRS))

    def __str__(self):
        return '(%s is member of %s)' % (self.personDisplayName, self.roomId)

    def __init__(self, arg=None):
        super(Membership, self).__init__(arg)


class MembershipsAPI(SparkBaseAPI):
    """Spark Membership API request wrapper."""

    _API_ENTRY_SUFFIX = 'memberships'

    def __init__(self, api):
        super(MembershipsAPI, self).__init__()
        self.api = api

    def list(self, room=None, person=None, email=None, **kwargs):
        """List memberships.

        Lists all room memberships. By default, lists memberships for 
        rooms to which the authenticated user belongs.
        Use query parameters to filter the response.
        Use roomId to list memberships for a room, by ID.
        Use either personId or personEmail to filter the results.

        This method supports Cisco Spark's implmentation of RFC5988 Web Linking
        to provide pagination support.  It returns an iterator that
        incrementally yields all rooms returned by the query.  It will
        automatically and efficiently request the additional 'pages' of
        responses from Spark as needed until all responses have been exhausted.


        Args:
            room (Room): List memberships for a room
            person (Person): list membership for this person
            email (string): list membership for this email address

        **kwargs:
            max(int): Limit the maximum number of memberships in the response.

        Returns:
            A Membership iterator.

        Raises:
            SparkApiError: If the list request fails.
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

        apiattr = ['roomId', 'personId', 'personEmail', 'max']
        items = self.api.session.get_items(
            self._API_ENTRY_SUFFIX, apiattr, **kwargs)
        # Yield membership objects created from the returned items JSON objects
        for item in items:
            yield Membership(item)

    def create(self, room, person, moderator=False, **kwargs):
        """Creates a membership.

        Creates a membership of the specified user (via id or email) to the given room.
        E.g. adds the specified user to the room.

        Args:
            room (Room): The room
            person (Person): the person to be added
            moderator (bool): is this person a moderator?

        Raises:
            SparkApiError: If the create operation fails.

        Returns:
            Membership object or None if the user is already member of the room
        """

        # process args
        assert isinstance(room, Room)
        kwargs['roomId'] = room.id
        assert isinstance(person, Person)
        if person.id:
            kwargs['toPersonId'] = person.id
        if person.email:
            kwargs['toPersonEmail'] = person.email
        kwargs['isModerator'] = isModerator

        apiattr = ['roomId', 'personId', 'personEmail', 'isModerator']
        # API request
        # 409 is a valid resonse status_code
        # (meaning 'user already in room')
        json_membership_obj = self.api.session.post(
            self._API_ENTRY_SUFFIX, apiattr, erc=[200, 409], **kwargs)
        # Return a Membership object created from the response JSON data
        if self.api.session.last_response.status_code == 200:
            return Membership(json_membership_obj)
        else:
            return None

    def details(self, membership, **kwargs):
        """Get membership details.

        Get details for a given membership.

        Args:
            membership (Membership): The membership object

        Raises:
            SparkApiError: If the operation fails.

        Returns:
            Membership object or None if the user is not a member of the room
        """
        # process args
        if isinstance(membership, Membership):
            membershipId = membership.id
        elif isinstance(membership, basestring):
            membershipId = membership
        else:
            raise ValueError("missing membership Id")
        apiattr = []
        # API request
        return Membership(self.api.session.get(self._uri_append(membershipId), apiattr, erc=[200, 404], **kwargs))

    def update(self, membership, **kwargs):
        """Updates properties for a membership object.

        Only the 'isModerator' attribute can be modified. 

        Args:
            membership (Membership): The membership object

        Raises:
            SparkApiError: If the create operation fails.

        Returns:
            Membership object or None if the user is not a member of the room
        """
        # process args
        if isinstance(membership, Membership):
            membershipId = membership.id
        elif isinstance(membership, basestring):
            membershipId = membership
        else:
            raise ValueError("missing membership Id")

        kwargs['isModerator'] = membership.isModerator
        apiattr = ['isModerator']
        # API request
        return Membership(self.api.session.put(self._uri_append(membershipId), apiattr, **kwargs))

    def delete(self, membership, **kwargs):
        """Deletes a membership object.

        Args:
            membership (Membership): The membership object

        Raises:
            SparkApiError: If the create operation fails.

        Returns:
            Nothing
        """

        # process args
        if isinstance(membership, Membership):
            membershipId = membership.id
        elif isinstance(membership, basestring):
            membershipId = membership
        else:
            raise ValueError("missing membership Id")
        apiattr = []
        # API request
        self.api.session.delete(self._uri_append(
            membershipId), apiattr, **kwargs)

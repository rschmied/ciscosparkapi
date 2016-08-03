"""Spark - People API - wrapper classes."""

from collections import OrderedDict
from ciscosparkapi.exceptions import ciscosparkapiException
from ciscosparkapi.helperfunc import utf8, sparkISO8601
from ciscosparkapi.restsession import RestSession
from ciscosparkapi.api.sparkobject import SparkBaseObject
from datetime import datetime


_API_KEYS = ['id',
             'created',
             'emails',
             'displayName',
             'avatar'
             ]
_API_ATTRS = [('Person ID (string)', basestring),
              ('date created, ISO8601 (string)', datetime),
              ('Emails (list)', list),
              ('display name (string)', basestring),
              ('Avatar URL (string)', basestring)
              ]
_API_ENTRY_SUFFIX = 'people'


class Person(SparkBaseObject):
    """Cisco Spark Person Object"""

    _API = OrderedDict(zip(_API_KEYS, _API_ATTRS))

    def __init__(self, arg=None):
        super(Person, self).__init__(arg)

    def __str__(self):
        return self.displayName


class PeopleAPI(object):
    """Spark Messages API request wrapper."""

    def __init__(self, session):
        assert isinstance(session, RestSession)
        super(PeopleAPI, self).__init__()
        self.session = session

    def list(self, **kwargs):
        """List people.

        List people in your organization.

        This method supports Cisco Spark's implmentation of RFC5988 Web Linking
        to provide pagination support.  It returns an iterator that
        incrementally yields all rooms returned by the query.  It will
        automatically and efficiently request the additional 'pages' of
        responses from Spark as needed until all responses have been exhausted.

        **kwargs:
            email (string): list people with this email address
            displayName (string): List people whose name starts with this string
            max (int): Limit the maximum number of persons in the response.

        Returns:
            A Person iterator.

        Raises:
            SparkApiError: If the list request fails.
        """
        # Process args
        for k, v in kwargs.items():
            if isinstance(v, basestring):
                kwargs['k'] = utf8(v)
            if isinstance(value, datetime):
                value = sparkISO8601(value)
        # API request - get items
        items = self.session.get_items(_API_ENTRY_SUFFIX, **kwargs)
        # Yield message objects created from the returned items JSON objects
        for item in items:
            yield Person(item)

    def details(self, personId='me', **kwargs):
        """get details of a person.

        If the personId is not set, return the details of the authenticated user.

        Args:
            personId(string): The ID of the user

        Raises:
            SparkApiError: If the create operation fails.

        Returns:
            Person object
        """
        # Process args
        for k, v in kwargs.items():
            if isinstance(v, basestring):
                kwargs['k'] = utf8(v)
            if isinstance(value, datetime):
                value = sparkISO8601(value)
        # API request
        json_person_obj = self.session.get(
            '%s/%s' % (_API_ENTRY_SUFFIX, personId), erc=[200, 404], **kwargs)
        if self.session.last_response.status_code == 200:
            # Return a Room object created from the response JSON data
            return Person(json_person_obj)
        else:
            return None

"""Spark - People API - wrapper classes."""

from collections import OrderedDict
from ciscosparkapi.exceptions import ciscosparkapiException
from ciscosparkapi.helperfunc import utf8, sparkISO8601
from ciscosparkapi.api.sparkobject import SparkBaseObject, SparkBaseAPI
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


class Person(SparkBaseObject):
    """Cisco Spark Person Object"""

    _API = OrderedDict(zip(_API_KEYS, _API_ATTRS))

    def __init__(self, arg=None):
        super(Person, self).__init__(arg)

    def __str__(self):
        return self.displayName


class PeopleAPI(SparkBaseAPI):
    """Spark Messages API request wrapper."""

    _API_ENTRY_SUFFIX = 'people'

    def __init__(self, api):
        super(PeopleAPI, self).__init__()
        self.api = api

    def list(self, email=None, name=None, **kwargs):
        """List people.

        List people in your organization.

        This method supports Cisco Spark's implmentation of RFC5988 Web Linking
        to provide pagination support.  It returns an iterator that
        incrementally yields all rooms returned by the query.  It will
        automatically and efficiently request the additional 'pages' of
        responses from Spark as needed until all responses have been exhausted.

        Args:
            email (string): list people with this email address
            name (string): List people whose name starts with this string

        **kwargs:
            max (int): Limit the maximum number of persons in the response.

        Returns:
            A Person iterator.

        Raises:
            SparkApiError: If the list request fails.
        """

        if email:
            assert isinstance(email, basestring)
            kwargs['email'] = email

        if name:
            assert isinstance(name, basestring)
            kwargs['displayName'] = displayName

        # API request - get items
        querylist = ['email', 'displayName', 'max']
        items = self.api.session.get_items(
            self._API_ENTRY_SUFFIX, querylist, **kwargs)
        # Yield message objects created from the returned items JSON objects
        for item in items:
            yield Person(item)

    def details(self, person='me', **kwargs):
        """get details of a person.

        If the person is not set, return the details of the authenticated user.

        Args:
            person (string): The ID of the user

        Raises:
            SparkApiError: If the create operation fails.

        Returns:
            Person object or None (if not found)
        """

        if isinstance(person, Person):
            personId = person.id
        elif isinstance(person, basestring):
            personId = person

        # API request
        querylist = ['personId']
        json_person_obj = self.api.session.get(self._uri_append(
            personId), querylist, erc=[200, 404], **kwargs)
        if self.api.session.last_response.status_code == 200:
            # Return a Room object created from the response JSON data
            return Person(json_person_obj)
        else:
            return None

import exceptions
from restsession import RestSession
from api.rooms import Room, RoomsAPI
from api.messages import Message, MessagesAPI
from api.memberships import Membership, MembershipsAPI


class CiscoSparkAPI(object):
    """Cisco Spark API wrapper class."""

    def __init__(self, access_token, base_url=None, timeout=None):
        # Process args
        assert isinstance(access_token, basestring)
        # Process kwargs
        session_args = {}
        if base_url:  session_args['base_url'] = base_url
        if timeout:  session_args['timeout'] = timeout
        # Create API session
        self.session = RestSession(access_token, **session_args)
        # Setup Spark API wrappers
        self.rooms = RoomsAPI(self.session)
        self.messages = MessagesAPI(self.session)
        self.memberships = MembershipsAPI(self.session)

    @property
    def access_token(self):
        return self.session.access_token

    @property
    def base_url(self):
        return self.session.base_url

    @property
    def timeout(self):
        return self.session.timeout

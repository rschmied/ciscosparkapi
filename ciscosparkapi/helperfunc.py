"""Package helper functions."""

from datetime import datetime

def utf8(string):
    """Return the 'string' as a UTF-8 unicode encoded string."""
    assert isinstance(string, basestring)
    if isinstance(string, unicode):
        return string
    elif isinstance(string, str):
        return unicode(string, encoding='utf-8')

def sparkISO8601(dt):
    """Return the datetime as an ISO8601 formated string
       (according to spark, it must look like 2016-07-28T13:14:35.000Z)
    """
    assert isinstance(dt, datetime)
    return dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
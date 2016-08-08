import json
import copy
from collections import OrderedDict
from datetime import datetime
from ciscosparkapi.helperfunc import sparkParseTime, sparkISO8601


def _priv(item):
    return '_' + item


def _addValueFn(className, item, docstring):
    attrName = _priv(item)

    def fnGet(self):
        return getattr(self, attrName, None)

    def fnSet(self, value):
        setattr(self, attrName, value)

    setattr(className, attrName, None)
    setattr(className, item, property(fnGet, fnSet, doc=docstring))


class SparkBaseAPI(object):
    """Base object for all API wrappers of the SparkBaseAPI"""

    def __init__(self):
        super(SparkBaseAPI, self).__init__()

    def _uri_append(self, what):
        return '/'.join((self._API_ENTRY_SUFFIX, what))


class SparkBaseObject(object):
    """ Base object for all SparkObjects like messages and rooms """

    def __init__(self, arg=None):
        super(SparkBaseObject, self).__init__()
        # does not work for base class
        if self.__class__.__name__ == 'SparkBaseObject':
            raise Exception, "can't use base class"
        # has the class been set up yet?
        if not getattr(self.__class__, '_classInitialized', None):
            for key, attribute in self._API.items():
                _addValueFn(self.__class__, key, attribute[0])
            setattr(self.__class__, '_classInitialized', True)
        # initial value provided?
        if arg is not None:
            self.__copy__(arg)

    def __items__(self):
        data = list()
        for item in self._API.keys():
            d = getattr(self, _priv(item), None)
            if d is not None:
                data.append((item, d))
        return data

    def __copy__(self, data):
        """ copies from data into self. accepts either the same type 
            as the instance or a dictionary.
            If a dictionary is presented, the keys must match the 
            current instance.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if hasattr(self.__class__, _priv(key)):
                    if self._API.get(key)[1] == datetime:
                        setattr(self, _priv(key), sparkParseTime(value))
                    else:
                        setattr(self, _priv(key), value)
                else:
                    raise Exception, ('<%s>: unknown attribute!' % key)
        elif type(self) == type(data):
            for k, v in data.__items__():
                setattr(self, k, copy.copy(v))
        else:
            raise ValueError("can't copy %r into %r" % (type(data), type(self)))

    def dumps(self):
        """ dumps the Spark object as JSON"""
        data = OrderedDict()
        for k, v in self.__items__():
            if type(v) == datetime:
                v = sparkISO8601(v)
            data[k] = v
        return json.dumps(data)

    def loads(self, input):
        """ loads the input JSON string into the object. 
        """

        assert isinstance(input, str)
        try:
            data = json.loads(input)
        except ValueError:
            raise Exception, 'invalid JSON'
        self.__copy__(data)

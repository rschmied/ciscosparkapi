import json
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

    def __copy__(self, data):
        if isinstance(data, dict):
            for key, value in data.items():
                if hasattr(self.__class__, _priv(key)):
                    if self._API.get(key)[1] == datetime:
                        setattr(self, _priv(key), sparkParseTime(value))
                    else:
                        setattr(self, _priv(key), value)
                else:
                    raise Exception, ('<%s>: unknown attribute!' % key)

    def dumps(self):
        """ dumps the Spark object as JSON"""
        data = OrderedDict()
        for item in self._API.keys():
            d = getattr(self, _priv(item), None)
            if d is not None:
                if type(d) == datetime:
                    d = sparkISO8601(d)
                data[item] = d
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

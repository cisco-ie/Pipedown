from netaddr import IPAddress
from netaddr.core import AddrFormatError

class Validator(object):
    counter = 0
    def __init__(self):
        self.private = '_%s_%d' % (self.__class__.__name__.lower(), Validator.counter)
        Validator.counter += 1

    def __get__(self, obj, objtype=None):
        return getattr(obj, self.private)

    def __set__(self, obj, value):
        self.validate(value)
        setattr(obj, self.private, value)

    def validate(self, value):
        pass

class Protocol(Validator):
    def __init__(self, *options):
        Validator.__init__(self)
        self.options = set(options)

    def __set__(self, obj, protocols):
        for place, protocol in enumerate(protocols):
            self.validate(protocol)
            protocol = protocol.replace('-', '').lower()
            protocols[place] = protocol
        setattr(obj, self.private, protocols)

    def validate(self, protocol):
        if not isinstance(protocol, str):
            raise TypeError('Protocol should be a str instead of %r.' % protocol)
        if protocol.lower() not in self.options:
            raise ValueError('Invalid protocol type %r.' % protocol)

class Address(Validator):
    def __init__(self):
        Validator.__init__(self)

    def validate(self, address):
        if not isinstance(address, str):
            raise TypeError('IP Address should be a str instead of %r' % type(address))
        try:
            IPAddress(address)
        except AddrFormatError:
            raise

"""
This class provides a utility for logging in all of the modules.

Taken from Vinay Sanjip on StackOverflow.
"""
import logging

class LogMixin(object):
    @property
    def logger(self):
        name = '.'.join([__name__, self.__class__.__name__])
        return logging.getLogger(name)
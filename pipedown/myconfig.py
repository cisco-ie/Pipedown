from ConfigParser import SafeConfigParser

class MyConfig(object):
    def __init__(self, filename):
        parser = SafeConfigParser()
        found = parser.read(filename)
        if not found:
            raise ValueError('No config file found.')
        section_names = parser.sections()
        self.sections = {}
        for name in section_names:
            self.sections[name] = Section(name, parser)

    def __repr__(self):
        return '{}(sections = {})'.format(
            self.__class__.__name__,
            self.sections
        )

    def __str__(self):
        return 'Pipedown Configuration: Sections = {}'.format(
            self.sections
            )

class Section(object):
    def __init__(self, section, parser):
        self.health = False
        self.__dict__.update(parser.items(section))
        try:
            self.__int__('interval',
                         'jitter_thres',
                         'pkt_loss',
                         'bw_thres')
        except AttributeError:
            #These are optional parameters.
            pass
        try:
            self.__dict__['protocols'] = list(self.__dict__['protocols'])
        except AttributeError:
            #This is NOT an optional parameter.
            raise

    def __int__(self, *args):
        """Convert multiple values to int."""
        for arg in args:
            self.__dict__[arg] = int(self.__dict__[arg])

    def __repr__(self):
        return '{}(section.__dict__ = {})'.format(
            self.__class__.__name__,
            self.__dict__
        )

    def __str__(self):
        return 'Section Dictionary = {}'.format(self.__dict__)

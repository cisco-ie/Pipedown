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

class Section(object):
    def __init__(self, section, parser):
        self.health = False
        self.__dict__.update(parser.items(section))

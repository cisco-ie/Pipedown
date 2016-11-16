from ConfigParser import SafeConfigParser

class MyConfig(object):
    def __init__(self, filename):
        parser = SafeConfigParser()
        found = parser.read(filename)
        if not found:
            raise ValueError('No config file found')
        section_names = parser.sections()
        print section_names
        self.sections = []
        for name in section_names:
            self.sections.append(Section(name, parser))

class Section(object):
    def __init__(self, section, parser):
        self.section = section
        self.__dict__.update(parser.items(section))

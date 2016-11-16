from ConfigParser import SafeConfigParser

class MyConfig(object):
    def __init__(self, filename):
        parser = SafeConfigParser()
        found = parser.read(filename)
        if not found:
            raise ValueError('No config file found.')
        self.sections = parser.sections()
        for name in self.sections:
            temp = {}
            new_dict = {}
            new_dict[name] = temp.update(parser.items(name))
            self.__dict__.update(new_dict)

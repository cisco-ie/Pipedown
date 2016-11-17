from ConfigParser import SafeConfigParser

class MyConfig(object):
    """Configuration class for Pipedown config file.
       Adds a dictionary of Section objects to __dict__, making it accessible
       by dot notation.

       Example:
       >>> config = MyConfig('monitor.config')
       >>> config.BGP
       Section(section.__dict__ = {'interval': 2, 'grpc_pass': 'vagrant', 'flush_bgp_as': '65000', 'text_alert': '+14087784819', 'grpc_server': '127.0.0.1', 'destination': '6.6.6.6', 'source': '12.1.1.10', 'drop_policy_name': 'drop', 'grpc_user': 'vagrant', 'health': False, 'protocols': ['bgp'], 'yang': 'openconfig', 'jitter_thres': 20, 'bw_thres': 200, 'pkt_loss': 3, 'pass_policy_name': 'pass', 'grpc_port': '57777'})
       >>> config.BGP.interval
       10
    """
    def __init__(self, filename):
        parser = SafeConfigParser()
        found = parser.read(filename)
        if not found:
            raise ValueError('No config file found.')
        section_names = parser.sections()
        self.sections = {}
        for name in section_names:
            self.sections[name] = Section(name, parser)
        self.__dict__.update(self.sections)

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
    """Section class for each section on the configuration file for Pipedown.
    Adds the items to the __dict__ in order to make them accessible with dot
    notation.
    Needs a parser object already created and passed into Section.
    """
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
            self.__dict__['protocols'] = [self.__dict__['protocols']]
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

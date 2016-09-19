import multiprocessing
import time
import sys
import logging
from Monitor.link import Link
class monitoring():
    def monitor(section):
        '''
        add a confiuration file details here
        '''
        location = os.path.dirname(os.path.realpath(__file__))
        config = ConfigParser.ConfigParser()
        try:
            config.read('monitor.config')
            destination = config.get(section, 'destination')
            source = config.get(section, 'source')
            protocol = config.get(section, 'protocol')
            grpc_server = config.get(section, 'grpc_server')
            grpc_port = config.get(section, 'grpc_port')
            grpc_user = config.get(section, 'grpc_user')
            grpc_pass = config.get(section, 'grpc_pass')
            flush_as = config.get(section, 'flush_as')
        while True:
            linkstate = linkstate(destination, source, protocol)
            if result.iperf == True:
                time.sleep(1)
                flush(grpc_server, grpc_port, grpc_user, grpc_pass, flush_as)

    def linkstate(destination, source):
        logging.basicConfig(filename='example.log',level=logging.DEBUG)
        link = Link(destination, source, protocol)
        result = link.health(BGP)
        logging.info(result)
        return result.iperf

    def flush(grpc_server, grpc_port, grpc_user, grpc_pass, flush_as):
        #calling Quan script
        return

if __name__ == '__main__':
    multiprocessing.log_to_stderr(logging.DEBUG)
    d = multiprocessing.Process(name='myApp', target=monitor, args=(section))
    d.daemon = True
    d.start()

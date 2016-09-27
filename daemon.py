import multiprocessing
import time
import sys
import logging
import os
import ConfigParser
from Tools.grpc_cisco_python.client.cisco_grpc_client import CiscoGRPCClient
from Monitor.link import Link
def monitor(section):
    '''
    add a confiuration file details here
    '''
    #Read in Configuration for Daemon
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
    except (ConfigParser.Error, ValueError), e:
	print e
        sys.exit(1)

    #Set up gRPC client
    client = CiscoGRPCClient(grpc_server, grpc_port, 10, grpc_user, grpc_pass)

    #Run Link Tool
    while True:
        result = linkstate(destination, source, protocol)
        print result
        if result == True:
            time.sleep(1)
            flush(grpc_server, grpc_port, grpc_user, grpc_pass, flush_as)

def linkstate(destination, source, client, protocol):
    logging.basicConfig(filename='example.log',level=logging.DEBUG)
    link = Link(destination, source)
    result = link.health(protocol)
    logging.info(result)
    return result

def flush(grpc_server, grpc_port, grpc_user, grpc_pass, flush_as):
    #calling Quan script
    print "Trigger flush"
    return

if __name__ == '__main__':
#    multiprocessing.log_to_stderr(logging.DEBUG)
#    d = multiprocessing.Process(name='myApp', target=monitor, args=('router1',))
#    d.daemon = True
#    d.start()
     monitor('router1')

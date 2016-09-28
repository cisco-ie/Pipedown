import multiprocessing
import sys
import logging
import os
import ConfigParser
from Tools.grpc_cisco_python.client.cisco_grpc_client import CiscoGRPCClient
from Monitor.link import Link
from Flush.bgp_flush import Flush_BGP
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
        drop_policy_name = config.get(section, 'drop_policy_name')
    except (ConfigParser.Error, ValueError), e:
	print e
        sys.exit(1)

    #Set up gRPC client
    client = CiscoGRPCClient(grpc_server, int(grpc_port), 10, grpc_user, grpc_pass)
    logging.basicConfig(filename='example.log',level=logging.DEBUG)
    #Run Link Tool
    while True:
        result = linkstate(destination, source, client, protocol)
        logging.info(result)
        if result == True:
            flush(client, flush_as, drop_policy_name, 'Flush/get-neighborsq.json')
            sys.exit(1)

def linkstate(destination, source, client, protocol):
    link = Link(destination, source, client)
    result = link.health(protocol)
    return result

def flush(client, ext_as, drop_policy_name, bgp_config_fn):
    #calling Quan script
    print "Triggering flush"
    flush_bgp = Flush_BGP(client, [int(ext_as)], drop_policy_name, bgp_config_fn)
    rm_neighbors = flush_bgp.get_bgp_neighbors()
    print "Flush triggered"
    logging.info(rm_neighbors)
    return

if __name__ == '__main__':
#    multiprocessing.log_to_stderr(logging.DEBUG)
#    d = multiprocessing.Process(name='myApp', target=monitor, args=('router1',))
#    d.daemon = True
#    d.start()
     monitor('router1')

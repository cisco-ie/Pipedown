"""
Daemon to monitor a link to Data Center using iPerf. If the link is faulty
deemed by the thresholds set,then the policy on the link to the Internet
is changed to stop peering with external routers.
"""
import multiprocessing
import sys
import ConfigParser
import log
from Tools.grpc_cisco_python.client.cisco_grpc_client import CiscoGRPCClient
from Monitor.link import Link
from Flush.bgp_flush import Flush_BGP

LOGGER = log.log()

def monitor(section):
    #Read in Configuration for Daemon.
    config = ConfigParser.ConfigParser()
    try:
        config.read('monitor.config')
        destination = config.get(section, 'destination')
        source = config.get(section, 'source')
        protocol = config.get(section, 'protocol')
        bw_thres = config.getint(section, 'bw_thres')
        jitter_thres = config.getint(section, 'jitter_thres')
        pkt_loss = config.getint(section, 'pkt_loss')
        interval = config.getint(section, 'interval')
        grpc_server = config.get(section, 'grpc_server')
        grpc_port = config.getint(section, 'grpc_port')
        grpc_user = config.get(section, 'grpc_user')
        grpc_pass = config.get(section, 'grpc_pass')
        flush_as = config.get(section, 'flush_as')
        drop_policy_name = config.get(section, 'drop_policy_name')
    except (ConfigParser.Error, ValueError), e:
        LOGGER.error('Config file error: %s', e)
        sys.exit(1)

    #Set up a gRPC client.
    client = CiscoGRPCClient(grpc_server, grpc_port, 10, grpc_user, grpc_pass)
    while True:
        #Checking link to data center.
        LOGGER.info('Checking link health of %s', source)
        link = Link(destination, source, client, bw_thres, jitter_thres, pkt_loss, interval)
        result = link.health(protocol)
        if result is False:
            LOGGER.info('Link is good.')
        else:
            #Flushing connection to Internet due to Data center link being faulty.
            LOGGER.warning('Link is down, triggering Flush.')
            #This is currently static, as we support more types will add to config file.
            bgp_config_fn = 'Flush/get-neighborsq.json'
            try:
                # Putting string of AS into a list
                ext_as = flush_as.split()
                ext_as = map(int, ext_as)
            except ValueError:
                LOGGER.error('Flush AS is in the wrong format for %s node', section)
                sys.exit(1)

            flush_bgp = Flush_BGP(client, ext_as, drop_policy_name, bgp_config_fn, LOGGER)
            rm_neighbors = flush_bgp.get_bgp_neighbors()
            rm_neighbors_string = str(rm_neighbors).strip('[]')
            LOGGER.info('Removed neighbors and policy: %s', rm_neighbors_string)
            break

def grab_sections():
    #Reading config file for section headers.
    config = ConfigParser.ConfigParser()
    try:
        config.read('monitor.config')
        sections = config.sections()
        return sections
    except (ConfigParser.Error), e:
        sys.exit(e)

def daemon():
    #Spawn process per a section header.
    sections = grab_sections()
    jobs = []
    for section in sections:
        d = multiprocessing.Process(name=section, target=monitor, args=(section,))
        jobs.append(d)
        d.start()

if __name__ == '__main__':
    daemon()

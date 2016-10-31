# Copyright 2016 Cisco Systems All rights reserved.
#
# The contents of this file are licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with the
# License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

"""
Daemon to monitor a link to Data Center using iPerf. If the link is faulty
deemed by the thresholds set,then the policy on the link to the Internet
is changed to stop peering with external routers.
"""
import multiprocessing
import sys
import ConfigParser
import log as log
from Tools.grpc_cisco_python.client.cisco_grpc_client import CiscoGRPCClient
from Monitor.link import Link
from Response import response

LOGGER = log.log()

def monitor(section, lock, health):
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
        grpc_server = config.get('DEFAULT', 'grpc_server')
        grpc_port = config.getint('DEFAULT', 'grpc_port')
        grpc_user = config.get('DEFAULT', 'grpc_user')
        grpc_pass = config.get('DEFAULT', 'grpc_pass')
        alert = config.getboolean('DEFAULT', 'alert')
        flush = config.getboolean('DEFAULT', 'flush')
        if alert:
            alert_type = config.get('DEFAULT', 'alert_type')
            alert_address = config.get('DEFAULT', 'alert_address')
        if flush:
            yang = config.get('DEFAULT', 'yang')
            try:
                bgp_as = config.get('DEFAULT', 'bgp_as')
            except ValueError:
                LOGGER.error('BGP AS must be an integer.')
                sys.exit(1)
            drop_policy_name = config.get('DEFAULT', 'drop_policy_name')
            pass_policy_name = config.get('DEFAULT', 'pass_policy_name')
    except (ConfigParser.Error, ValueError), e:
        LOGGER.error('Config file error: %s', e)
        sys.exit(1)

    #Set up a gRPC client.
    client = CiscoGRPCClient(grpc_server, grpc_port, 10, grpc_user, grpc_pass)
    flushed = False
    while True:
        #Checking link to data center.
        LOGGER.info('Checking link health of %s', source)
        link = Link(destination, source, client, bw_thres, jitter_thres, pkt_loss, interval)
        result = link.health(protocol)
        if result is False:
            LOGGER.info('Link is good.')
            if flushed:
                LOGGER.warning('Link is back up, adding neighbor...')
                #This is currently static, as we support more types will add to config file.
                lock.acquire()
                if flush:
                    reply = response.model_selection(yang, client, bgp_as, pass_policy_name)
                    LOGGER.info(reply)
                else:
                    reply = 'Link is back up, but no action has been taken.'
                    LOGGER.info(reply)
                lock.release()
                flushed = False
        else:
            #Flushing connection to Internet due to Data center link being faulty.
            LOGGER.warning('Link %s is down.', section)
            #This is currently static, as we support more types will add to config file.
            lock.acquire()
            health[section] = result
            if all(health.values()):
                if flush and not flushed:
                    reply = response.model_selection(yang, client, bgp_as, drop_policy_name)
                    LOGGER.info(reply)
                    if 'Error' not in reply:
                        flushed = True
                elif flush and flushed:
                    LOGGER.info('Link already flushed.')
            else:
                reply = section
            if alert:
                response.alert(alert_type, alert_address, reply)
                alert = False
            lock.release()

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
    #Creating a multiprocessing dictionary
    manager = multiprocessing.Manager()
    health = manager.dict()
    for section in sections:
        health[section] = False
    #Create lock object to ensure gRPC is only used once
    lock = multiprocessing.Lock()
    for section in sections:
        d = multiprocessing.Process(name=section, target=monitor, args=(section, lock, health))
        jobs.append(d)
        d.start()
    d.join()

if __name__ == '__main__':
    daemon()
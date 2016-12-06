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
import signal
import os
import sys
from netaddr.core import AddrFormatError
from tabulate import tabulate
from grpc.framework.interfaces.face.face import AbortionError

import log
from myconfig import MyConfig
from Tools.grpc_cisco_python.client.cisco_grpc_client import CiscoGRPCClient
from Monitor.link import Link
from Monitor.health import health
from Response import response
from Tools.exceptions import GRPCError

LOGGER = log.log()

def monitor(section, lock, config, health_dict):
    """TODO: Add docstring here.
        Args:
            section (str): Section name.
            lock (multiprocessing.Lock): Lock to prevent other threads from using gRPC
                                        simultaneously.
            config (MyConfig): The config object for the current config section.
            health_dict (multiprocessing.Manager): Multi-threaded dictionary.
    """
    #Silence keyboard interrupt signal. TODO: Do I need this?
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    #Access the section in config.
    sec_config = config.__dict__[section]
    alerted = False
    #Set up a gRPC client.
    client = CiscoGRPCClient(
        sec_config.grpc_server,
        int(sec_config.grpc_port),
        10,
        sec_config.grpc_user,
        sec_config.grpc_pass
        )
    while True:
        #Checking link to data center.
        try:
            result = link_check(sec_config, client)
            #If there are no problems.
            if result is False:
                with lock:
                    health_dict[section] = False
                    if health_dict['flushed'] is True:
                        LOGGER.warning('Link is back up, adding neighbor...')
                        health_dict['flushed'] = healthy_link(client, sec_config)
                        #We want to alert that the link is back up.
                        alerted = False
                    else:
                        LOGGER.info('Link is good.')
            #If there is a problem on the link.
            else:
                LOGGER.warning('Link %s is down.', section)
                #If the link is not already flushed.
                with lock:
                    health_dict[section] = True
                    if health_dict['flushed'] is False:
                        if all(values[1] for values in health_dict.items()
                               if values[0] != 'flushed'):
                            health_dict['flushed'] = problem_flush(client, sec_config)
                    else:
                        LOGGER.info('Link already flushed.')
                if not alerted:
                    alerted = problem_alert(config, section)
        except (GRPCError, AbortionError):
            LOGGER.critical(
                'GRPC error when checking link health, health cannot be determined.'
            )

def link_check(sec_config, client):
    """Checks the health of the link.

    Args:
        sec_config (Section): The section object for the current config section.
        client (GRPCClient): The gRPC client object.

    Return:
        result (bool): False if the health is good, True if there is a problem.
    """
    LOGGER.info('Checking link health of %s', sec_config.source)
    try:
        link = Link(sec_config.destination, sec_config.source, sec_config.protocols)
    except (TypeError, ValueError, AddrFormatError) as err:
        LOGGER.critical(err)
        return False
    try:
        result = health(
            link,
            client,
            sec_config.bw_thres,
            sec_config.jitter_thres,
            sec_config.pkt_loss,
            sec_config.interval
            )
        return result
    except (GRPCError, AbortionError):
        raise

def healthy_link(client, sec_config):
    """Response when the link is healthy.
    BGP relationship will be returned to it's original policy if it was flushed.
    No action will be taken if the BGP relationship was never flushed.

    Args:
        sec_config (Section): The Section object for the current config section.

    Return:
        False (bool):Sets Flushed back to False.
    """
    try:
        reply = response.model_selection(
            sec_config.yang,
            client,
            sec_config.flush_bgp_as,
            sec_config.pass_policy_name
            )
        LOGGER.info('\n%s',
                    tabulate(
                        reply,
                        headers=[
                            "Neighbor",
                            "Link Type",
                            "Old Policy",
                            "New Policy"
                        ],
                        tablefmt="rst"
                    )
                   )
        #Set flushed back to False
        return False
    except (GRPCError, AbortionError):
        LOGGER.error('No neighbors updated due to GRPC Merge Error.')
        return True

def problem_alert(sec_config, section):
    """Alert because there are problems on the link.

        Args:
            sec_config (Section): The Section object for the current config
                                  section.
            section (str): String name of section.

        Return:
            alerted (bool): Sets alerted to True if an alert was sent.
    """
    alerted = False
    try:
        response.text_alert(sec_config.text_alert, section)
        #Prevent spamming the alert.
        alerted = True
    except AttributeError:
        #There is no text_alert option
        pass
    try:
        response.email_alert(sec_config.email_alert, section)
        #Prevent spamming the alert.
        alerted = True
    except AttributeError:
        #There is no email alert option.
        pass
    return alerted

def problem_flush(client, sec_config):
    """If there are problems on the link flush, alert with text and/or email,
       or both.

    Args:
        client (GRPCClient): The gRPC client object.
        sec_config (Section): The config object for the current config section.

    Return:
         flushed (bool): Updates monitor's flushed to True if the link
                        is flushed.
    """
    try:
        #If all the links are down.
        reply = response.model_selection(
            sec_config.yang,
            client,
            sec_config.flush_bgp_as,
            sec_config.drop_policy_name
            )
        LOGGER.info('\n%s',
                    tabulate(
                        reply,
                        headers=[
                            "Neighbor",
                            "Link Type",
                            "Old Policy",
                            "New Policy"
                        ],
                        tablefmt="rst"
                    )
                   )
        return True
    except (GRPCError, AbortionError):
        LOGGER.error('No neighbors updated due to GRPC Merge Error.')
        return False

def daemon():
    #Spawn process per a section header.
    location = os.path.dirname(os.path.realpath(__file__))
    try:
        config = MyConfig(os.path.join(location, 'monitor.config'))
    except (ValueError, KeyError) as msg:
        LOGGER.critical(msg)
        sys.exit(1)
    manager = multiprocessing.Manager()
    health_dict = manager.dict()
    #Can I move this into the below loop? <------------------------###
    for section in config.__dict__.keys():
        health_dict[section] = False
    health_dict['flushed'] = False
    jobs = []
    #Create lock object to ensure gRPC is only used once
    lock = multiprocessing.Lock()
    for section in config.__dict__.keys():
        d = multiprocessing.Process(name=section, target=monitor, args=(
            section,
            lock,
            config,
            health_dict
            )
        )
        jobs.append(d)
        d.start()
    try:
        for job in jobs:
            job.join()
    except KeyboardInterrupt:
        print 'Keyboard interrupt received.'
        for job in jobs:
            job.terminate()
            job.join()

if __name__ == '__main__':
    daemon()

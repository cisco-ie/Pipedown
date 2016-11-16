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
from grpc.framework.interfaces.face.face import AbortionError

import log
from myconfig import MyConfig
from Tools.grpc_cisco_python.client.cisco_grpc_client import CiscoGRPCClient
from Monitor.link import Link
from Monitor.health import health
from Response import response
from Tools.exceptions import GRPCError, ProtocolError

LOGGER = log.log()

def monitor(section, lock, health_dict, config):
    #Silence keyboard interrupt signal.
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    #Read in Configuration for Daemon.
    config = config.__dict__[section]
    alerted = False
    flushed = False
    #Set up a gRPC client.
    client = CiscoGRPCClient(
        config.grpc_server,
        config.grpc_port,
        10,
        config.grpc_user,
        config.grpc_pass
        )
    while True:
        #Checking link to data center.
        result = link_check(config)
        if result:
            if result is False:
                flushed = healthy_link(config, flushed, lock)
            else:
                #Flushing connection to Internet due to Data center link being faulty.
                flushed, alerted = problem_link(
                    client,
                    config,
                    flushed,
                    alerted,
                    health_dict,
                    lock,
                    section
                    )

def link_check(config):
    """Checks the health of the link.

    Args:
        config (MyConfig): The config object for the current config section.

    Return:
        result (bool): False if the health is good, True if there is a problem.
    """
    LOGGER.info('Checking link health of %s', config.source)
    try:
        link = Link(config.destination, config.source, config.protocols)
    except ProtocolError:
        LOGGER.error('One of the protocols is invalid: %s', config.protocols)
    try:
        result = health(
            link,
            config.client,
            config.bw_thres,
            config.jitter_thres,
            config.pkt_loss,
            config.interval
            )
        return result
    except (GRPCError, AbortionError):
        LOGGER.error(
            'GRPC error when checking link health, health cannot be determined.'
        )

def healthy_link(config, flushed, lock):
    """Response when the link is healthy.
    BGP relationship will be returned to it's original policy if it was flushed.
    No action will be taken if the BGP relationship was never flushed.

    Args:
        config (MyConfig): The config object for the current config section.
        flushed (bool): True if the BGP relationship was already flushed.
        lock (multiprocessing.Lock): Lock to prevent other threads from using gRPC
                                     simultaneously.

    Return:
        False (bool):Sets Flushed back to False.
    """
    LOGGER.info('Link is good.')
    if flushed:
        LOGGER.warning('Link is back up, adding neighbor...')
        #This is currently static, as we support more types will add to config file.
        lock.acquire()
        try:
            reply = response.model_selection(
                config.yang,
                config.client,
                config.bgp_as,
                config.pass_policy_name
                )
            LOGGER.info(reply)
        except AttributeError:
            reply = 'Link is back up, but no action has been taken.'
            LOGGER.info(reply)
        lock.release()
    #Set flushed to False.
    return False

def problem_link(client, config, flushed, alerted, health_dict, lock, section):
    """If there are problems on the link flush, alert with text and/or email, or both.

    Args:
        client (GRPCClient): The gRPC client object.
        config (MyConfig): The config object for the current config section.
        flushed (bool): True if the BGP relationship was already flushed.
        alerted (bool): True if the client has been alerted already.
        health_dict (dict): Dictionary holding health of all links. Only if all
                            links are down will BGP relationship get flushed.
        lock (multiprocessing.Lock): Lock to prevent other threads from using gRPC
        simultaneously.
        section (str): The config section.
    """
    actions = [flushed, alerted]
    LOGGER.warning('Link %s is down.', section)
    #This is currently static, as we support more types will add to config file.
    lock.acquire()
    health_dict[section] = True
    #If all the links are down.
    if all(health_dict.values()):
        #If the link is not already flushed.
        if not flushed:
            try:
                reply = response.model_selection(
                    config.yang,
                    client,
                    config.bgp_as,
                    config.drop_policy_name
                    )
                LOGGER.info(reply)
                if 'Error' not in reply:
                    actions[0] = True
            except AttributeError:
                actions[0] = False
        elif flushed:
            LOGGER.info('Link already flushed.')
    else:
        reply = section
    if alerted:
        try:
            response.text_alert(config.text_alert, reply)
            #Prevent spamming the alert.
            actions[1] = True
        except AttributeError:
            #There is no text_alert option
            pass
        try:
            response.email_alert(config.email_alert, reply)
            #Prevent spamming the alert.
            actions[1] = True
        except AttributeError:
            #There is no email alert option.
            pass
    lock.release()
    return actions

def daemon():
    #Spawn process per a section header.
    location = os.path.dirname(os.path.realpath(__file__))
    config = MyConfig(os.path.join(location, 'monitor.config'))
    jobs = []
    #Creating a multiprocessing dictionary
    manager = multiprocessing.Manager()
    health_dict = manager.dict()
    #Can I move this into the below loop? <------------------------###
    for section in config.sections:
        health_dict[section] = False
    #Create lock object to ensure gRPC is only used once
    lock = multiprocessing.Lock()
    for section in config.sections:
        d = multiprocessing.Process(name=section, target=monitor, args=(
            section,
            lock,
            health_dict,
            config
            )
        )
        jobs.append(d)
        d.start()
    try:
        for job in jobs:
            job.join()
    except KeyboardInterrupt:
        print "Keyboard interrupt received."
        for job in jobs:
            job.terminate()
            job.join()

if __name__ == '__main__':
    daemon()

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

import subprocess
import logging
from grpc.framework.interfaces.face.face import AbortionError

from Tools.exceptions import GRPCError


LOGGER = logging.getLogger()

def run_iperf(link, bw_thres=400, jitter_thres=10, pkt_loss_thres=2,
              interval=5):
    """Run iPerf to check the health of the link.

    Returns False if NO problems are detected, returns True if there
    are issues on the link.

    Args:
        link (Link): Link object with destination server location and current
        interface information.
        bw_thres (int): The bandwidth threshold. Default to 400 KBits.
        jitter_thres (int): Jitter threshold. Default 10ms.
        pkt_loss (int): Number of acceptable lost packets. Default 2.
        interval (int): The interval time in seconds between periodic bandwidth,
        jitter, and loss reports. Default 5 seconds.

    Returns:
        bool: False if no problems, True if problems

    """
    cmd = "iperf -c %s -B %s -t %d -i %d -u -y C" % \
    (link.destination, link.interface, interval, interval)
    # Perform the network monitoring task.
    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    out, err = process.communicate()
    if err:
        if 'Connection refused' in err:
            LOGGER.critical(
                'Connection to iPerf destination refused. Assuming link is down.'
                )
        return True
    # Parse the output.
    try:
        transferred_bytes = float(out.splitlines()[2].split(',')[7])
    except IndexError:
        LOGGER.error('Problem with the iPerf output: %s', out)
    bps = (transferred_bytes * 8) / float(interval)
    bandwidth = bps/1024.0
    jitter = out.splitlines()[2].split(',')[9]
    pkt_loss = out.splitlines()[2].split(',')[12]
    verdict = any(
        [
            float(bandwidth) < float(bw_thres),
            float(jitter) > float(jitter_thres),
            float(pkt_loss) > float(pkt_loss_thres)
        ]
    )
    # False is good! iPerf link sees no problems.
    # True is bad, there are problems on the link.
    return verdict

def check_cisco_rib(link, grpc_client):
    """Returns False (no error) if there is a route in the RIB, True if not.

    Checks if there is a route to the neighbor from the link.interface
    of the protocol given (typically ISIS and/or BGP).

    If there are multiple protocols on the link as long as one protocol is
    healthy we assume the link is good and do not flush.

    Uses gRPC to read the routing table, checking specifically that the
    interface has a route (and of the type specified).

    Args:
        link (Link): The link to be checked.
        grpc_client (CiscoGRPCClient): The grpc_client object.

    Returns:
        bool: False if no errors, True if errors in RIB.

    """
    path = '{{"Cisco-IOS-XR-ip-rib-ipv{v}-oper:{ipv6}rib": {{"vrfs": {{"vrf": [{{"afs": {{"af": [{{"safs": {{"saf": [{{"ip-rib-route-table-names": {{"ip-rib-route-table-name": [{{"routes": {{"route": {{"address": "{link}"}}}}}}]}}}}]}}}}]}}}}]}}}}}}'
    ipv6 = ''
    if link.version == 6:
        ipv6 = 'ipv6-'
    path = path.format(v=link.version, ipv6=ipv6, link=link.destination)
    try:
        err, output = grpc_client.getoper(path)
        if err:
            raise GRPCError(err)
        #If one protocol on the link is functioning, we assume the link is up.
        #On GRPCError, protocols not found, or not active, return True.
        return any(protocol not in output or '"active": true' not in output
                   for protocol in link.protocols)
    except GRPCError as e:
        LOGGER.error(e.message)
        raise
    except AbortionError:
        LOGGER.critical(
            'Unable to connect to local box, check your gRPC destination.'
            )
        raise

#TODO 
def check_openconfig_rib(link, grpc_client):
    """Returns False (no error) if there is a route in the RIB, True if not.

    Checks if there is a route to the neighbor from the link.interface
    of the protocol given (typically ISIS and/or BGP).

    If there are multiple protocols on the link as long as one protocol is
    healthy we assume the link is good and do not flush.

    Uses gRPC to read the routing table, checking specifically that the
    interface has a route (and of the type specified).

    Args:
        link (Link): The link to be checked.
        grpc_client (CiscoGRPCClient): The grpc_client object. If using Juniper 
                                        devices this should be a netconf client.

    Returns:
        bool: False if no errors, True if errors in RIB.

    """
    #https://github.com/openconfig/public/blob/master/release/models/network-instance/openconfig-network-instance.yang
    path = '{{"Cisco-IOS-XR-ip-rib-ipv{v}-oper:{ipv6}rib": {{"vrfs": {{"vrf": [{{"afs": {{"af": [{{"safs": {{"saf": [{{"ip-rib-route-table-names": {{"ip-rib-route-table-name": [{{"routes": {{"route": {{"address": "{link}"}}}}}}]}}}}]}}}}]}}}}]}}}}}}'
    ipv6 = ''
    if link.version == 6:
        ipv6 = 'ipv6-'
    path = path.format(v=link.version, ipv6=ipv6, link=link.destination)
    try:
        err, output = grpc_client.getoper(path)
        if err:
            raise GRPCError(err)
        #If one protocol on the link is functioning, we assume the link is up.
        #On GRPCError, protocols not found, or not active, return True.
        return any(protocol not in output or '"active": true' not in output
                   for protocol in link.protocols)
    except GRPCError as e:
        LOGGER.error(e.message)
        raise
    except AbortionError:
        LOGGER.critical(
            'Unable to connect to local box, check your gRPC destination.'
            )
        raise

def ping_test(link, timeout=10):
    """Uses scapy to send ICMP packets and listen for response.
        Args:
            link (Link): The link to be checked.
            timeout (int): ICMP timeout time in seconds.

        Returns:
        bool: False if no errors, True if error.
    """
    from scapy.all import sr1, IP, ICMP, IPv6
    if link.version == 4:
        resp = sr1(
            IP(src=link.interface, dst=link.destination)/ICMP(),
            timeout=timeout,
            verbose=False
        )
    elif link.version == 6:
        resp = sr1(
            IPv6(src=link.interface, dst=link.destination)/ICMP(),
            timeout=timeout,
            verbose=False
        )
    if resp:
        return False
    else:
        return True

def health(link, grpc_client, bw_thres=400, jitter_thres=10, pkt_loss=2,
           interval=5):
    """Returns False if error on link, True if no errors.
     Runs both check_rib and run_iperf.

    Args:
        link (Link): The link to be checked.
        grpc_client (CiscoGRPCClient): gRPC Client object
        bw_thres (int): The bandwidth threshold. Default to 400 KBits.
        jitter_thres (int): Jitter threshold. Default 10ms.
        pkt_loss (int): Number of acceptable lost packets. Default 2.
        interval (int): The interval time in seconds between periodic bandwidth,
        jitter, and loss reports. Default 5 seconds.

    Returns:
        bool: False if no errors, True if error.

    """
    try:
        #If we are using cisco model
        routing = check_cisco_rib(link, grpc_client)
        #If we are using OpenConfig, the Network Instance model is not yet available
        #on box. If the link is IPv6 we can check the neighbor-reachability in the 
        #open-config-interfaces model. If it is IPv4 we can only check the link health
        #if it is a BGP link.
    except (GRPCError, AbortionError):
        raise
    if not routing: #If there is NOT an error in routing.
        iperf = run_iperf(link, bw_thres, jitter_thres, pkt_loss, interval)
        return iperf
    else:
        return routing

def model_selection(model, link, client):
    """Based on the model-type selected in the configuration file, call the
       correct function.
        As support for more models are added they will get added to the
        dictionary for selection.

        Args:
            grpc_client (CiscoGRPCClient): the initiated GRPC client.
            model (str): The yang model in use.
            link (Link): The link to be checked.

        Return:
            bool: True if there is a problem, False if not.
    """
    functions = {
        'cisco': check_cisco_rib,
        'openconfig': check_openconfig_rib,
    }
    #Call the correct function and return its return value.
    return functions[model](link, client)

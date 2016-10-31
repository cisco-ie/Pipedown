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

from pipedown.Tools.exceptions import GRPCError


LOGGER = logging.getLogger()

def run_iperf(link, bw_thres=400, jitter_thres=10, pkt_loss=2,
              interval=5):
    """Run iPerf to check the health of the link.
    Returns False if NO problems are detected, returns True if there
    are issues on the link.

    :param link: Link object with destination server location and current
    interface information.
    :param bw_thres: The bandwidth threshold. Default to 400 KBits.
    :param jitter_thres: Jitter threshold. Default 10ms.
    :param pkt_loss: Number of acceptable lost packets. Default 2.
    :param interval: The interval time in seconds between periodic bandwidth,
    jitter, and loss reports. Default 5 seconds.

    :type link: Link object
    :type bw_thres: int
    :type jitter_thres: int
    :type pkt_loss: int
    :type interval: int
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
    transferred_bytes = float(out.splitlines()[2].split(',')[7])
    bps = (transferred_bytes * 8) / float(interval)
    bandwidth = bps/1024.0
    jitter = out.splitlines()[2].split(',')[9]
    pkt_loss = out.splitlines()[2].split(',')[12]
    verdict = any(
        [
            float(bandwidth) < float(bw_thres),
            float(jitter) > float(jitter_thres),
            float(pkt_loss) > float(pkt_loss)
        ]
    )
    # False is good! iPerf link sees no problems.
    # True is bad, there are problems on the link.
    return verdict

def check_routing(link, grpc_client):
    """Returns False (no error) if there is a route in the RIB, True if not.

    Checks if there is a route to the neighbor from the link.interface
    of the protocol given (typically ISIS and/or BGP).

    If there are multiple protocols on the link as long as one protocol is
    healthy we assume the link is good and do not flush.

    Uses gRPC to read the routing table, checking specifically that the
    interface has a route (and of the type specified).

    :param link: The link to be checked.
    :param grpc_client: The grpc_client object.
    :type link: Link object.
    :type grpc_client: grpc_client object.
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

def health(link, grpc_client, bw_thres=400, jitter_thres=10, pkt_loss=2,
           interval=5):
    """Check the health of the link, returns True if there is an error,
    False if no error.
    Runs both check_routing and run_iperf.

    :param link: The link to be checked.
    :param grpc_client: gRPC Client object
    :param bw_thres: The bandwidth threshold. Default to 400 KBits.
    :param jitter_thres: Jitter threshold. Default 10ms.
    :param pkt_loss: Number of acceptable lost packets. Default 2.
    :param interval: The interval time in seconds between periodic bandwidth,
    jitter, and loss reports. Default 5 seconds.

    :type link: Link object.
    :type grpc_client: gRPC Client object
    :type bw_thres: int
    :type jitter_thres: int
    :type pkt_loss: int
    :type interval: int
    """
    try:
        routing = check_routing(link, grpc_client)
    except (GRPCError, AbortionError):
        raise
    if not routing: #If there is NOT an error in routing.
        iperf = run_iperf(link, bw_thres, jitter_thres, pkt_loss, interval)
        return iperf
    else:
        return routing

"""This module contains the MonitoriPerf class"""

import subprocess
from Tools.grpc_cisco_python.client.cisco_grpc_client import CiscoGRPCClient

class Monitor(object):
    """A class for monitor interfaces with iPerf.
    :param server: The iPerf server ip address.
    :param: interface: The outgoing interface.
    :param: bw_thres: The bandwidth threshold. Default to 400 KBits.
    :param jitter_thres: Jitter threshold. Default 10ms.
    :param pkt_loss: Number of acceptable lost packets.
    :param interval: The interval time in seconds between periodic bandwidth,
    jitter, and loss reports.

    :type server: str
    :type interface: sr
    :type bw_thres: int
    :type jitter_thres: int
    :type pkt_loss: int
    :type interval: int
    """
    def __init__(self, server, interface, bw_thres=400, jitter_thres=10,
                 pkt_loss=2, interval=10):
        self.bw_thres = bw_thres
        self.jitter_thres = jitter_thres
        self.pkt_loss = pkt_loss
        self.interval = interval
        self.interface = interface
        self.server = server

    def run_iperf(self):
        """Run iPerf to check the health of the link"""
        cmd = "iperf -c %s -B %s -t %d -i %d -u -y C" % \
        (self.server, self.interface, self.interval, self.interval)
        # Perform the network monitoring task
        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        out, err = process.communicate()
        if err: # Will we need more information? This could be an iPerf server problem.
            return True
        # Parse the output.
        transferred_bytes = float(out.splitlines()[2].split(',')[7])
        bps = (transferred_bytes * 8) / float(self.interval)
        bandwidth = bps/1024.0
        jitter = out.splitlines()[2].split(',')[9]
        pkt_loss = out.splitlines()[2].split(',')[12]
        verdict = any(
            [
                float(bandwidth) < float(self.bw_thres),
                float(jitter) > float(self.jitter_thres),
                float(pkt_loss) > float(self.pkt_loss)
            ]
        )
        # False is good! iPerf link sees no problems.
        # True is bad, there are problems on the link.
        return verdict

    def check_routing(self, link, protocol):
        """Check if there is a route to the neighbor based on the link_type.
        Uses gRPC to read the routing table, checking specifically that the interface
        has a route (and of the type specified).
        :param protocol: ISIS or BGP
	:param link: IP address of the link
        :type protocol: str
	:type link: str
        """
        client = CiscoGRPCClient('10.1.1.1', 57777, 10, 'vagrant', 'vagrant')
	path = '{{"Cisco-IOS-XR-ip-rib-ipv4-oper:rib": {{"vrfs": {{"vrf": [{{"afs": {{"af": [{{"safs": {{"saf": [{{"ip-rib-route-table-names": {{"ip-rib-route-table-name": [{{"routes": {{"route": {{"address": "{link}"}}}}}}]}}}}]}}}}]}}}}]}}}}}}'
	path = path.format(link=link)
        output = client.getoper(path)
        return(protocol in output and '"active": true' in output) # Could there be multiple instances of the link?

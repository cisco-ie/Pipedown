"""This module contains the MonitoriPerf class"""

import subprocess

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
        cmd = "iperf -c %s -b %s -t %d -i %d -u -y C" % \
        (self.server, self.interface, self.interval, self.interval)
        # Perform the network monitoring task
        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        out, _ = process.communicate()  # Don't worry about stderr.
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
        return verdict

    def check_routing(self, link_type):
        """Check if there is a route to the neighbor based on the link_type.
        Uses gRPC to read the routing table, checking specifically that the interface
        has a route (and of the type specified).
        :param link_type: ISIS or BGP
        :type link_type: str
        """
        path = '{"Cisco-IOS-XR-ip-rib-ipv4-oper:{link_type}": [null]}'
        #GRPC Stuff
        #parse output
        if self.interface in output:
            return True
        else:
            return False

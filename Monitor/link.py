"""This module contains the Link class"""

import subprocess
from grpc.framework.interfaces.face.face import AbortionError

class Link(object):
    """A class for monitoring interfaces with iPerf.
    :param server: The iPerf server ip address.
    :param interface: The outgoing interface.
    :param grpc_client: gRPC Client object.
    :param bw_thres: The bandwidth threshold. Default to 400 KBits.
    :param jitter_thres: Jitter threshold. Default 10ms.
    :param pkt_loss: Number of acceptable lost packets.
    :param interval: The interval time in seconds between periodic bandwidth,
    jitter, and loss reports.

    :type server: str
    :type interface: sr
    :type grpc_client: gRPC Client object
    :type bw_thres: int
    :type jitter_thres: int
    :type pkt_loss: int
    :type interval: int
    """
    def __init__(self, server, interface, grpc_client, bw_thres=400, jitter_thres=10,
                 pkt_loss=2, interval=10):
        self.bw_thres = bw_thres
        self.jitter_thres = jitter_thres
        self.pkt_loss = pkt_loss
        self.interval = interval
        self.interface = interface
        self.server = server
        self.grpc_client = grpc_client

    def __repr__(self):
        return '{}(Server = {}, Interface = {}, gRPC_Client = {}, ' \
                'Bandwidth_Threshold = {}, Jitter_Threshold = {}, ' \
                'Packet_Loss = {}, Interval = {}' \
                ')'.format(
                    self.__class__.__name__,
                    self.server,
                    self.interface,
                    self.grpc_client,
                    self.bw_thres,
                    self.jitter_thres,
                    self.pkt_loss,
                    self.interval
                    )

    @staticmethod
    def _check_protocol(protocol):
        """Ensure the protocol entered is valid, return True if valid and
        False if invalid.

        :param protocol: The given protocol.
        :type protocol: str
        """
        protocols = [
            'ISIS',
            'BGP', 
            'MOBILE',
            'SUBSCRIBER',
            'CONNECTED',
            'DAGR',
            'RIP',
            'OSPF',
            'STATIC',
            'RPL',
            'EIGRP',
            'LOCAL',
        ]
        return protocol.upper() in protocols

    def run_iperf(self):
        """Run iPerf to check the health of the link.
        Returns False if no problems are detected, returns True if there
        are issues on the link.
        """
        cmd = "iperf -c %s -B %s -t %d -i %d -u -y C" % \
        (self.server, self.interface, self.interval, self.interval)
        # Perform the network monitoring task.
        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        out, err = process.communicate()
        if err:
            if 'Connection refused' in err:
                print 'Connection refused. Check the connection to the server.'
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

    def check_routing(self, protocol):
        """Returns False (no error) if there is a route in the RIB, True if not.

        Checks if there is a route to the neighbor from the link.interface
        of the protocol given (typically ISIS or BGP).

        Uses gRPC to read the routing table, checking specifically that the
        interface has a route (and of the type specified).

        :param protocol: ISIS or BGP
        :param link: IP address of the link
        :param client: gRPC Client object
        :type protocol: str
        :type link: str
        :type client: gRPC Client object
        """
        if self._check_protocol(protocol):
            path = '{{"Cisco-IOS-XR-ip-rib-ipv{v}-oper:{ipv6}rib": {{"vrfs": {{"vrf": [{{"afs": {{"af": [{{"safs": {{"saf": [{{"ip-rib-route-table-names": {{"ip-rib-route-table-name": [{{"routes": {{"route": {{"address": "{link}"}}}}}}]}}}}]}}}}]}}}}]}}}}}}'
            version = 4
            ipv6 = ''
            if ':' in self.interface: # Checks if it is an IPv6 link.
                version = 6
                ipv6 = 'ipv6-'
            path = path.format(v=version, ipv6=ipv6, link=self.interface)
            try:
                err, output = self.grpc_client.getoper(path)
                # Could there be multiple instances of the link?
                return protocol not in output or '"active": true' not in output
            except AbortionError:
                print 'Unable to connect to box, check your gRPC server.'
        else:
            print "Invalid protocol type '{}'.".format(protocol)

    def health(self, protocol):
        """Check the health of the link, returns True if there is an error,
        False if no error.
        Runs both check_routing and run_iperf.

        :param protocol: Routing protocol (ex. IS-IS or BGP)
        :param client: gRPC Client object

        :type protocol: str
        :type client: gRPC Client object
        """
        if isinstance(protocol, str):
            routing = self.check_routing(protocol)
            if not routing: #If there is NOT an error in routing.
                iperf = self.run_iperf()
                return iperf
            else:
                return routing
        else:
            print "Expecting type string as the argument."


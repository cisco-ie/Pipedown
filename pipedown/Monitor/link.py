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

"""This module contains the Link class.

The link includes the destination router IP address, the IP address of the
interface on the host router (the router this program is running on), and the
list of protocols that should be tested on the interface. Multiple protocols are
accepted in the form of a list.

Works in python 2.7 and Python 3+.

Author: Lisa Roach
"""

from Tools.exceptions import ProtocolError

import logging
import sys
from netaddr import IPAddress
from netaddr.core import AddrFormatError

LOGGER = logging.getLogger()

def _not_valid():
    if sys.version_info[0] >= 3:
        return NotImplemented
    else:
        print('Link object unorderable.')

class Link(object):
    """A class for monitoring interfaces with iPerf.
    Both IPv6 and IPv4 are supported.
    Raises errors if IP address is not in valid format or protocol is not valid.

    :param destination: The destination IP of the peer router port.
    :param interface: The outgoing interface IP address.
    :param protocols: The protocols of the link that should be checked.

    :type destination: str
    :type interface: str
    :type protocols: list
    """
    def __init__(self, destination, interface, protocols):
        self.interface = interface
        self.destination = destination
        self.protocols = protocols
        #Detect IPv4 or IPv6 for interface.
        if ':' in interface:
            self.version = 6
        else:
            self.version = 4

    @property
    def interface(self):
        return self._interface

    @interface.setter
    def interface(self, interface):
        try:
            #Check validity of interface address.
            IPAddress(interface)
            self._interface = interface
        except (AddrFormatError, TypeError) as e:
            LOGGER.critical(e)
            raise

    @property
    def destination(self):
        return self._dest

    @destination.setter
    def destination(self, destination):
        try:
            #Check validity of interface address.
            IPAddress(destination)
            self._dest = destination
        except (AddrFormatError, TypeError) as e:
            LOGGER.critical(e)
            raise

    @property
    def protocols(self):
        return self._protocols

    @protocols.setter
    def protocols(self, protocols):
        self._protocols = []
        try:
            for protocol in protocols:
                self._check_protocol(protocol.upper())
                #If they are valid protocols, set them.
                self.protocols.append(protocol.upper())
        except ProtocolError as e:
            LOGGER.critical(e.message)
            raise
        except TypeError as e:
            LOGGER.critical(e)
            raise

    def __repr__(self):
        return '{}(destination = {}, interface = {}, protocols = {})'.format(
            self.__class__.__name__,
            self.destination,
            self.interface,
            self.protocols
        )

    def __str__(self):
        return ('{} Object(Destination IP: {},'\
        'Host Router Interface IP: {},'\
        'Link Protocols to Check: {})').format(
            self.__class__.__name__,
            self.destination,
            self.interface,
            [x.upper() for x in self.protocols]
        )

    def __eq__(self, other):
        """Compares the equality of two Link objects. Returns a bool.
        Must have the same protocols listed, order and case don't matter.

        >>> l = Link('10.1.1.2', '10.1.1.1', ['BGP', 'ospf', 'ISIS'])
        >>> l2 = Link('10.1.1.2', '10.1.1.1', ['BGP', 'ISIS', 'OSPF'])
        >>> l == l2
        True
        >>> l = Link('10.1.1.3', '10.1.1.1', ['BGP', 'ospf', 'ISIS'])
        >>> l2 = Link('10.1.1.2', '10.1.1.1', ['BGP', 'ISIS', 'OSPF'])
        >>> l == l2
        False
        >>> l = Link('10.1.1.2', '10.1.1.1', ['BGP', 'ospf', 'ISIS'])
        >>> l2 = Link('10.1.1.2', '10.1.1.1', ['BGP', 'OSPF'])
        >>> l == l2
        False
        """
        return (isinstance(other, Link)
                and set(self._protocols) == set(other.protocols)
                and self.dest == other.dest
                and self.interface == other.interface
               )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __gt__(self, other):
        return _not_valid()

    def __lt__(self, other):
        return _not_valid()

    def __ge__(self, other):
        return _not_valid()

    def __le__(self, other):
        return _not_valid()

    @staticmethod
    def _check_protocol(protocol):
        """Ensure the protocol entered is valid. Raise ProtocolError
        if invalid.

        :param protocol: The given protocol.
        :type protocol: str

        >>> _check_protocol('isis')
        True
        >>> _check_protocol('')
        False
        >>> _check_protocol(9)
        False
        >>> _check_protocol('bpg')
        False

        """
        if isinstance(protocol, str):
            protocols = [
                'ISIS',
                'IS-IS',
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
            if not protocol in protocols:
                raise ProtocolError(protocol)
        else:
            raise ProtocolError(protocol)


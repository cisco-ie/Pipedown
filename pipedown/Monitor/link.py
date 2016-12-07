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

import logging
import sys
from Monitor.validators import Protocol, Address

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

    Args:
        destination (str): The destination IP of the peer router port.
        interface (str): The outgoing interface IP address.
        protocols (list): The protocols of the link that should be checked.

    """
    protocol_options = [
        'isis',
        'is-is',
        'bgp',
        'mobile',
        'subscriber',
        'connected',
        'dagr',
        'rip',
        'ospf',
        'static',
        'rpl',
        'eigrp',
        'local',
    ]

    interface = Address()
    destination = Address()
    protocols = Protocol(*protocol_options)

    def __init__(self, destination, interface, protocols):
        self.interface = interface
        self.destination = destination
        self.protocols = protocols

    @property
    def version(self):
        """Detects what version (4 or 6) the IP Address is."""
        if ':' in self.interface:
            return 6
        else:
            return 4

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
                and set(self.protocols) == set(other.protocols)
                and self.destination == other.destination
                and self.interface == other.interface
               )

    def __hash__(self):
        return hash((set(self.protocols), self.destination, self.interface))

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

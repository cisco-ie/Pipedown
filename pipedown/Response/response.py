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
Removes all BGP neighbors of a given external AS using GRPC to send and commit
configurations in IOS-XR.
"""

import logging
import json
import smtplib
from collections import OrderedDict
from email.mime.text import MIMEText
import requests
from grpc.framework.interfaces.face.face import AbortionError

from Tools.exceptions import GRPCError

LOGGER = logging.getLogger()

def nested_lookup(col, key, *keys):
    """Search dictionaries nested in dictionaries nested in lists, etc, for key.

    Args:
        col (dict or list): The collection to be searched through.
        key (str): The key to locate in the collection.
        keys (iterable): The keys to iterate through before finding key.

    Returns:
        str or dict or list: Returns the value of the key.

    """
    if keys:
        if isinstance(col, dict):
            return nested_lookup(col.get(key, {}), *keys)
        elif isinstance(col, list):
            if len(col) > 1:
                return nested_lookup(col[col.index(key)+1], *keys)
            else:
                return nested_lookup(col[0].get(key, {}), *keys)
    if isinstance(col, dict):
        return col.get(key)
    elif isinstance(col, list):
        if isinstance(col[0], dict):
            return col[0].get(key)
        else:
            return col[0]

def cisco_update(grpc_client, neighbor_as, new_policy_name):
    """Initiate the GRPC client to perform the neighbor removal and commits,
    using Cisco YANG models.

    Args:
        grpc_client (CiscoGRPCClient): the initiated GRPC client.
        neighbor_as (list): List of neighbor AS numbers.
        new_policy_name (str): Name of the new policy.

    Returns:
        str: Updated neighbors' IPs and the policy that changed.
    """
    #Brackets closures left on one line for consistency in unit tests that
    #use json.loads (which places no space between closing brackets).
    bgp_config_template = '''
    {"Cisco-IOS-XR-ipv4-bgp-cfg:bgp":
      {"instance":
        [{"instance-name":
            "default","instance-as":
              [{"four-byte-as":
                  [{"default-vrf":
                      {"bgp-entity":
                        {"neighbors":
                          {"neighbor":
                            [{"neighbor-afs":
                                {"neighbor-af": []},"remote-as": {}}]}}}}]}]}]}}
    '''
    #Get rid of newlines and spaces. Mostly for cosmetics.
    bgp_config_template = ' '.join(bgp_config_template.split())
    # Get the BGP config.
    try:
        bgp_config = get_bgp_config(grpc_client, bgp_config_template)
    except (GRPCError, AbortionError):
        raise
    # Drill down to the neighbors to be flushed or added.
    bgp_config = json.loads(bgp_config)
    neighbors = nested_lookup(bgp_config,
                              *['Cisco-IOS-XR-ipv4-bgp-cfg:bgp',
                                'instance',
                                'instance-as',
                                'four-byte-as',
                                'default-vrf',
                                'bgp-entity',
                                'neighbors',
                                'neighbor'
                               ]
                             )
    updated_neighbors = []
    for neighbor in neighbors:
        as_val = neighbor['remote-as']['as-yy']
        if as_val in neighbor_as:
            for ipv in neighbor['neighbor-afs']['neighbor-af']:
                # Change the policy to drop or pass.
                curr_policy = ipv['route-policy-out']
                ipv['route-policy-out'] = new_policy_name
                # Add the removed or added neighbors to list.
                updated_neighbors.append(
                    (
                        neighbor['neighbor-address'],
                        ipv['af-name'],
                        curr_policy,
                        new_policy_name
                        )
                    )
    try:
        apply_policy(grpc_client, bgp_config)
    except (GRPCError, AbortionError):
        raise
    return updated_neighbors

def open_config_update(grpc_client, neighbor_as, new_policy_name):
    """Flush_BGP object that will initiate the GRPC client to perform the
   neighbor removal and commits, using Cisco YANG models.

   Args:
        grpc_client (CiscoGRPCClient): the initiated GRPC client.
        neighbor_as (list): List of neighbor AS numbers.
        new_policy_name (str): Name of the new policy.

    Returns:
        str: Updated neighbors' IPs and the policy that changed.
    """
    bgp_config_template = '{"openconfig-bgp:bgp": {"neighbors": [null]}}'
    # Get the BGP config.
    try:
        bgp_config = get_bgp_config(grpc_client, bgp_config_template)
    except (GRPCError, AbortionError):
        raise
    # Drill down to the neighbors to be flushed.
    bgp_config = json.loads(bgp_config, object_pairs_hook=OrderedDict)
    neighbors = nested_lookup(bgp_config,
                              *['openconfig-bgp:bgp',
                                'neighbors',
                                'neighbor'
                               ]
                             )
    updated_neighbors = []
    for neighbor in neighbors:
        as_val = neighbor['config']['peer-as']
        if as_val in neighbor_as:
            # Change the policy to drop.
            for ipv in neighbor['afi-safis']['afi-safi']:
                curr_policy = nested_lookup(ipv,
                                            *['apply-policy',
                                              'config',
                                              'export-policy'
                                             ]
                                           )
                ipv['apply-policy']['config']['export-policy'] = [new_policy_name]
                # Add the removed neighbors to list.
                updated_neighbors.append(
                    (
                        neighbor['neighbor-address'],
                        ipv['afi-safi-name'],
                        str(curr_policy[0]),
                        new_policy_name
                        )
                    )
    try:
        apply_policy(grpc_client, bgp_config)
    except (GRPCError, AbortionError):
        raise
    return updated_neighbors


def get_bgp_config(grpc_client, bgp_config_template):
    """Use gRPC to grab the current BGP configuration on the box.
    Args:
        grpc_client (CiscoGRPCClient): the initiated GRPC client.
        bgp_config_template (JSON str): Unpopulated YANG model to be filled.

    Returns:
        bgp_config (str): Populated YANG model.

    """
    try:
        err, bgp_config = grpc_client.getconfig(bgp_config_template)
        if err:
            raise GRPCError(err)
        return bgp_config
    except GRPCError as e:
        LOGGER.error(e.message)
        raise
    except AbortionError:
        LOGGER.critical(
            'Unable to connect to local box, check your gRPC destination.'
            )
        raise

def apply_policy(grpc_client, bgp_config):
    """Apply the new BGP policy by using gRPC.

    Args:
        grpc_client (CiscoGRPCClient): the initiated GRPC client.
        bgp_config (dict): Updated YANG model with new policy.

    Returns:
        None

    """
    LOGGER.info('Changing the bgp neighbors...')
    bgp_config = json.dumps(bgp_config)
    try:
        response = grpc_client.mergeconfig(bgp_config)
        if response.errors:
            err = json.loads(response.errors)
            raise GRPCError(err)
    except GRPCError as e:
        LOGGER.critical(e.message)
        raise
    except AbortionError:
        LOGGER.critical(
            'Unable to connect to local box, check your gRPC destination.'
            )
        raise

def email_alert(email_address, message):
    """Send an email alert that the link is down.

    Args:
        email_address (str): The email address to contact.
        message (str): The message to send.

    Response:
        None
    """
    m_from = 'nobody@cisco.com'
    log = open('router_connected.log', 'rb')
    msg = MIMEText(log.read())
    log.close()
    msg['Subject'] = message
    msg['From'] = m_from
    msg['To'] = email_address
    send = smtplib.SMTP('outbound.cisco.com')
    #email_address is a list, make sure to break it up like one <--------------------####
    send.sendmail(m_from, email_address, msg.as_string())
    send.quit()

def text_alert(phone_number, message):
    """Send text message alert for link status.

    Args:
        phone_number (str): Phone number to text.
        reply (str): The message to send.

    Response:
        None
    """
    token = '416978636d5774754655457466614d6f6a4a4574464c4941584777475a7870496758446f5775474f65535176'
    url = 'http://api.tropo.com/1.0/sessions'
    payload = {'token':token, 'msg':message, 'phone_number':phone_number}
    req = requests.post(url, data=json.dumps(payload))
    if req.status_code != 200:
        LOGGER.error(req.text)

def model_selection(model, client, neighbor_as, policy_name):
    """Based on the model-type selected in the configuration file, call the
       correct function.
        As support for more models are added they will get added to the
        dictionary for selection.

        Args:
            grpc_client (CiscoGRPCClient): the initiated GRPC client.
            neighbor_as (list): List of neighbor AS numbers.
            policy_name (str): Name of the new policy.

        Return:
            str: The updated neighbors plus a string message.
    """
    # Putting string of AS into a list
    neighbor_as = neighbor_as.split()
    neighbor_as = map(int, neighbor_as)
    functions = {
        'cisco': cisco_update,
        'openconfig': open_config_update,
    }
    #Call the correct function and return its return value.
    return functions[model](client, neighbor_as, policy_name)

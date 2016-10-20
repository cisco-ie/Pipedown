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
import sys
import json
from collections import OrderedDict
import requests
import smtplib
from email.mime.text import MIMEText
from grpc.framework.interfaces.face.face import AbortionError

from Tools.exceptions import GRPCError

LOGGER = logging.getLogger()


def cisco_update_connection(grpc_client, neighbor_as, new_policy_name):
    """Initiate the GRPC client to perform the
   neighbor removal and commits, using Cisco YANG models.

    :param grpc_client: the initiated GRPC client.
    :param neighbor_as: List of neighbor AS numbers.
    :param new_policy_name: Name of the policy file to be used when
                             updating a neighbor.
    """
    try:
        # Putting string of AS into a list
        neighbor_as = neighbor_as.split()
        neighbor_as = map(int, neighbor_as)
    except ValueError:
        LOGGER.error('Flush AS is in the wrong format')
        sys.exit(1)
    bgp_config_template = '{"Cisco-IOS-XR-ipv4-bgp-cfg:bgp": {"instance": [{"instance-name": "default","instance-as": [{"four-byte-as": [{"default-vrf": {"bgp-entity": {"neighbors": {"neighbor": [{"neighbor-afs": {"neighbor-af": []},"remote-as": {}}]}}}}]}]}]}}'
    # Get the BGP config.
    bgp_config = get_bgp_config(grpc_client, bgp_config_template)
    # Drill down to the neighbors to be flushed or added.
    bgp_config = json.loads(bgp_config)
    neighbors = bgp_config['Cisco-IOS-XR-ipv4-bgp-cfg:bgp']['instance'][0]
    neighbors = neighbors['instance-as'][0]['four-byte-as'][0]['default-vrf']
    neighbors = neighbors['bgp-entity']['neighbors']['neighbor']

    updated_neighbors = []
    for neighbor in neighbors:
        as_val = neighbor['remote-as']['as-yy']
        if as_val in neighbor_as:
            # Change the policy to drop or pass.
            curr_policy = neighbor['neighbor-afs']['neighbor-af'][0]['route-policy-out']
            neighbor['neighbor-afs']['neighbor-af'][0]['route-policy-out'] = new_policy_name
            # Add the removed or added neighbors to list.
            updated_neighbors.append((neighbor['neighbor-address'], curr_policy))
    updated_neighbors = json.dumps(updated_neighbors)
    return 'Updated neighbors and policy: %s' % updated_neighbors

def open_config_flush(grpc_client, neighbor_as, new_policy_name):
    """Flush_BGP object that will initiate the GRPC client to perform the
   neighbor removal and commits, using Cisco YANG models.

    :param grpc_client: the initiated GRPC client.
    :param neighbor_as: List of neighbor AS numbers.
    :param new_policy_name: Name of the policy file to be used when
                             updating a neighbor.
    """
    try:
        # Putting string of AS into a list
        neighbor_as = neighbor_as.split()
        neighbor_as = map(int, neighbor_as)
    except ValueError:
        LOGGER.error('Flush AS is in the wrong format')
        sys.exit(1)
    bgp_config_template = '{"openconfig-bgp:bgp": {"neighbors":[null]}}'
    # Get the BGP config.
    bgp_config = get_bgp_config(grpc_client, bgp_config_template)
    # Drill down to the neighbors to be flushed.
    bgp_config = json.loads(bgp_config, object_pairs_hook=OrderedDict)
    updated_neighbors = []
    neighbors = bgp_config['openconfig-bgp:bgp']['neighbors']['neighbor']
    for neighbor in neighbors:
        as_val = neighbor['config']['peer-as']
        if as_val in neighbor_as:
            # Change the policy to drop.
            ipvs = neighbor['afi-safis']['afi-safi']
            for ipv in ipvs:
                curr_policy = ipv['apply-policy']['config']['export-policy']
                ipv['apply-policy']['config']['export-policy'] = new_policy_name
                ip_type = ipv['afi-safi-name']
                # Add the removed neighbors to list.
                updated_neighbors.append((neighbor['neighbor-address'], ip_type, curr_policy))
    updated_neighbors = json.dumps(updated_neighbors)
    return 'Updated neighbors and policy: %s' % updated_neighbors

def get_bgp_config(grpc_client, bgp_config_template):
    """Use gRPC to grab the current BGP configuration on the box."""
    try:
        err, bgp_config = grpc_client.getconfig(bgp_config_template)
        if err:
            raise GRPCError(err)
        return bgp_config
    except GRPCError as e:
        LOGGER.error(e.message)
        return None
    except AbortionError:
        LOGGER.critical(
            'Unable to connect to local box, check your gRPC destination.'
            )
        return None

def apply_policy(grpc_client, bgp_config):
    """Apply the new BGP policy by using gRPC."""
    LOGGER.info('Changing the bgp neighbors...')
    bgp_config = json.dumps(bgp_config)
    try:
        response = grpc_client.mergeconfig(bgp_config)
        if response.errors:
            err = json.loads(response.errors)
            raise GRPCError(err)
    except GRPCError as e:
        LOGGER.error(e.message)
        return None
    except AbortionError:
        LOGGER.critical(
            'Unable to connect to local box, check your gRPC destination.'
            )
        return None

def alert(model, arg):
    """Alert the user (email or console) if there is an error.
    """
    message = 'Link is down, check router'
    if model == 'text':
        phone_number = arg
        token = '416978636d5774754655457466614d6f6a4a4574464c4941584777475a7870496758446f5775474f65535176'
        url = 'http://api.tropo.com/1.0/sessions'
        payload = {'token':token, 'msg':message, 'phone_number':phone_number}
        req = requests.post(url, data=json.dumps(payload))
        if req.status_code != 200:
           LOGGER.error(req.text)
           return
        else:
           return 'Successfully sent Text Message'
    elif model == 'email':
        m_from = 'kkumara3@cisco.com'
        m_to = arg
        log = open('router_connected.log', 'rb')
        msg = MIMEText(log.read())
        log.close()
        msg['Subject'] = message
        msg['From'] = m_from
        msg['To'] = m_to
        send = smtplib.SMTP('outbound.cisco.com')
        send.sendmail(m_from, [m_to], msg.as_string())
        send.quit()
        return 'Successfully sent Email'

def model_selection(model, client, arg1, arg2):
    """Based on the model-type selected in the configuration file, call the
       correct function.
       Will contain a switch statement of all the functions (cisco_flush,
       open_config_flush, etc.).

       If someone wants to add a response option, they will add the function
       to this module and add to the switch statement here.
    """
    functions = {
        'cisco_flush': cisco_update_connection,
        'open_config_flush': open_config_flush,
        'alert' : alert,
    }
    return functions[model](client, arg1, arg2)

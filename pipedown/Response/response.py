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

LOGGER = logging.getLogger()

def cisco_flush(grpc_client, neighbor_as, drop_policy_name):
    """Flush_BGP object that will initiate the GRPC client to perform the
   neighbor removal and commits, using Cisco YANG models.

    :param grpc_client: the initiated GRPC client.
    :param neighbor_as: List of neighbor AS numbers.
    :param drop_policy_name: Name of the policy file to be used when
                             dropping a neighbor.
    """
    bgp_config_template = '{"Cisco-IOS-XR-ipv4-bgp-cfg:bgp": {"instance": [{"instance-name": "default","instance-as": [{"four-byte-as": [{"default-vrf": {"bgp-entity": {"neighbors": {"neighbor": [{"neighbor-afs": {"neighbor-af": []},"remote-as": {}}]}}}}]}]}]}}'
    # Get the BGP config.
    err, bgp_config = grpc_client.getconfig(bgp_config_template)
    if err:
        err = json.loads(err)
        try:
            message = err["cisco-grpc:errors"]["error"][0]["error-message"]
        except KeyError:
            message = err["cisco-grpc:errors"]["error"][0]["error-tag"]
        LOGGER.error('There was a problem loading current config: %s', message)
        return None
    # Drill down to the neighbors to be flushed.
    bgp_config = json.loads(bgp_config)
    neighbors = bgp_config['Cisco-IOS-XR-ipv4-bgp-cfg:bgp']['instance'][0]
    neighbors = neighbors['instance-as'][0]['four-byte-as'][0]['default-vrf']
    neighbors = neighbors['bgp-entity']['neighbors']['neighbor']

    removed_neighbors = []
    for neighbor in neighbors:
        as_val = neighbor['remote-as']['as-yy']
        if as_val in neighbor_as:
            # Change the policy to drop.
            curr_policy = neighbor['neighbor-afs']['neighbor-af'][0]['route-policy-out']
            neighbor['neighbor-afs']['neighbor-af'][0]['route-policy-out'] = drop_policy_name
            # Add the removed neighbors to list.
            removed_neighbors.append((neighbor['neighbor-address'], curr_policy))
    # flush the neighbors from the configuration
    LOGGER.info('Flushing the bgp neighbors...')
    bgp_config = json.dumps(bgp_config)
    response = grpc_client.mergeconfig(bgp_config)
    if response.errors:
        err = json.loads(response.errors)
        try:
            message = err["cisco-grpc:errors"]["error"][0]["error-message"]
        except KeyError:
            message = err["cisco-grpc:errors"]["error"][0]["error-tag"]
        LOGGER.error('There was a problem flushing BGP: %s', message)
        return None
    return json.dumps(removed_neighbors)

def open_config_flush(grpc_client, neighbor_as, drop_policy_name):
    """Flush_BGP object that will initiate the GRPC client to perform the
   neighbor removal and commits, using Cisco YANG models.

    :param grpc_client: the initiated GRPC client.
    :param neighbor_as: List of neighbor AS numbers.
    :param drop_policy_name: Name of the policy file to be used when
                             dropping a neighbor.
    """
    bgp_config_template = '{"openconfig-bgp:bgp": {"neighbors":[null]}}'
    # Get the BGP config.
    err, bgp_config = grpc_client.getconfig(bgp_config_template)
    if err:
        err = json.loads(err)
        try:
            message = err["cisco-grpc:errors"]["error"][0]["error-message"]
        except KeyError:
            message = err["cisco-grpc:errors"]["error"][0]["error-tag"]
        LOGGER.error('There was a problem loading current config: %s', message)
        return None
    # Drill down to the neighbors to be flushed.
    bgp_config = json.loads(bgp_config)
    removed_neighbors = []
    neighbors = bgp_config['openconfig-bgp:bgp']['neighbors']['neighbor']
    for neighbor in neighbors:
        as_val = neighbor['config']['peer-as']
        if as_val in neighbor_as:
            # Change the policy to drop.
            ipvs = neighbor['afi-safis']['afi-safi']
            for ipv in ipvs:
                curr_policy = ipv['apply-policy']['config']['export-policy']
                ipv['apply-policy']['config']['export-policy'] = drop_policy_name
                ip_type = ipv['afi-safi-name']
                # Add the removed neighbors to list.
                removed_neighbors.append((neighbor['neighbor-address'], ip_type, curr_policy))
    LOGGER.info('Flushing the bgp neighbors...')
    bgp_config = json.dumps(bgp_config)
    response = grpc_client.mergeconfig(bgp_config)
    if response.errors:
        err = json.loads(response.errors)
        try:
            message = err["cisco-grpc:errors"]["error"][0]["error-message"]
        except KeyError:
            message = err["cisco-grpc:errors"]["error"][0]["error-tag"]
        LOGGER.error('There was a problem flushing BGP: %s', message)
        return None
    return json.dumps(removed_neighbors)

def yang_selection(model):
    """Based on the model-type selected in the configuration file, call the
       correct function.
       Will contain a switch statement of all the functions (cisco_flush,
       open_config_flush, etc.).

       If someone wants to add a response option, they will add the function
       to this module and add to the switch statement here.
    """
    pass

def alert():
    """Alert the user (email or console) if there is an error.
    """
    pass

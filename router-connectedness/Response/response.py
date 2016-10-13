"""
Removes all BGP neighbors of a given external AS using GRPC to send and commit
configurations in IOS-XR.
Must include the neighborsq.json path. This is the standard BGP configuration
template that is used for flushing.
"""
import logging
import json
import sys
from ast import literal_eval

LOGGER = logging.getLogger()

def flush(grpc_client, neighbor_as, drop_policy_name):
    """Flush_BGP object that will initiate the GRPC client to perform the
   neighbor removal and commits.

    :param grpc_client: the initiated GRPC client.
    :param neighbor_as: List of neighbor AS numbers.
    :param drop_policy_name: Name of the policy file to be used when
                             dropping a neighbor.
    """
    bgp_config_template = '{"Cisco-IOS-XR-ipv4-bgp-cfg:bgp": {"instance": [{"instance-name": "default","instance-as": [{"four-byte-as": [{"default-vrf": {"bgp-entity": {"neighbors": {"neighbor": [{"neighbor-afs": {"neighbor-af": []},"remote-as": {}}]}}}}]}]}]}}"'
    # Get the BGP config.
    err, bgp_config = grpc_client.getconfig(bgp_config_template)
    if err:
        err = literal_eval(err)
        message = err["cisco-grpc:errors"]["error"][0]["error-message"]
        LOGGER.error('There was a problem loading current config: %s', message)
        return None
    # Drill down to the neighbors to be flushed.
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
    err, _ = grpc_client.mergeconfig(bgp_config_template)
    if err:
        err = literal_eval(err)
        message = err["cisco-grpc:errors"]["error"][0]["error-message"]
        LOGGER.error('There was a problem flushing BGP: %s', message)
        return None
    return json.dumps(removed_neighbors)

def alert():
    pass

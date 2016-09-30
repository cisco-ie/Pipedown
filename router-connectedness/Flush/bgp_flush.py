import sys
import logging
sys.path.insert(1, '../Tools/grpc_cisco_python/client')

import copy
import json
from pprint import pprint

""" Removes all BGP neighbors of a given external AS using GRPC to send and commit configurations in IOS-XR.
    Must include the neighborsq.json path. This is the standard BGP configuration template that is used for flushing.
"""


#logging.basicConfig(level=logging.INFO)

class Flush_BGP(object):
    """Flush_BGP object that will initiate the GRPC client to perform the neighbor removal and commits.

    Attributes:
        grpc_client: the intiaited GRPC client
        ext_as: the list of external AS
        drop_policy_name = name of the policy file to be used when dropping a neighbor
        bgp_config_fn = name and location of the BGP configuration template
    """
    def __init__(self, grpc_client, ext_as, drop_policy_name, bgp_config_fn, logger):

        self.neighbor_as = ext_as
        self.drop_policy_name = drop_policy_name
        self.bgp_config_fn = bgp_config_fn
        self.client = grpc_client
        self.logger = logging.getLogger()

        # load the BGP config file
        bgp_config = self.__load_bgp_template__(self.bgp_config_fn)

        # get the BGP config
        err, res = self.client.getconfig(bgp_config)
        # decodes the current BGP config into JSON
        self.res = json.loads(res)

    def get_bgp_neighbors(self):
        """ Retreives the BGP neighbors by matching the AS. """
        c = copy.deepcopy(self.res)
        l = c['Cisco-IOS-XR-ipv4-bgp-cfg:bgp']['instance'][0]
        l = l['instance-as'][0]
        l = l['four-byte-as'][0]
        l = l['default-vrf']['bgp-entity']['neighbors']['neighbor']

        removed_neighbors = []
        for neighbor in l:
            as_val = neighbor['remote-as']['as-yy']
            if as_val in self.neighbor_as:
                # change the policy to drop
                curr_policy = neighbor['neighbor-afs']['neighbor-af'][0]['route-policy-out']
                neighbor['neighbor-afs']['neighbor-af'][0]['route-policy-out'] = self.drop_policy_name
                removed_neighbors.append((neighbor['neighbor-address'], curr_policy))

        c = json.dumps(c)

        # flush the neighbors from the configuration
        flush_resp = self.__flush_bgp_neighbors__(c)
        return json.dumps(removed_neighbors)

    def check_flush_neighbors(self, rm_neighbors):
        """ Checks if the correct neighbors were removed by checking the router's current configuration.

            params:
            rm_neighbors: list of removed BGP neighbors
        """
        self.logger.info('Checking if neighbors were flushed....')

        # create the template for BGP neigbors
        template = {}
        template["neighbor-address"] = "NA"
        template["neighbor-afs"] = {"neighbor-af": []}

        # load the main BGP config
        fn = 'neighbor.json'
        bgp = self.__load_bgp_template__(fn)
        bgp_json = json.loads(bgp)

        # access the neighbors list part of the JSOn input
        k = bgp_json["Cisco-IOS-XR-ipv4-bgp-cfg:bgp"]["instance"][0]["instance-as"][0]["four-byte-as"][0]
        k = k["default-vrf"]["bgp-entity"]["neighbors"]["neighbor"]

        for ip in rm_neighbors:
            dup = copy.deepcopy(template)
            dup['neighbor-address'] = ip
            k.append(dup)

        # get the BGP config
        resp = self.client.getconfig(json.dumps(bgp_json))
        resp = json.loads(resp)

        k2 = resp["Cisco-IOS-XR-ipv4-bgp-cfg:bgp"]["instance"][0]["instance-as"][0]["four-byte-as"][0]
        k2 = k2["default-vrf"]["bgp-entity"]["neighbors"]["neighbor"]

        for line in k2:
            ip = line["neighbor-address"]
            curr_policy_name = line["neighbor-afs"]["neighbor-af"][0]['route-policy-out']

            if curr_policy_name != self.drop_policy_name:
                s = "Failed policy for " + ip
                sys.exit(s)
        self.logger.info("Successfully flushed all BGP neighbors.")


    def __flush_bgp_neighbors__(self, flush_bgp_config):
        """ Remove the neighbor from the router configuration with GRPC call. """
        self.logger.info('Flushing the bgp neighbors...')
        resp = self.client.mergeconfig(flush_bgp_config)

        if resp == None:
            return 'Flush successful!'
        else:
            return resp

    def __load_bgp_template__(self, fn):
        """ Function to read in a template. """
        with open(fn, 'r') as f:
            config = f.read()
        return config


def main():
    """
        Main function that tests the functionality. Initiate the GRPC client and provide sample config
        and drop policy file names.
    """
    router_ip = '10.85.138.39'
    ext_as = [2235, 44444]
    config_fn = "get-neighborsq.json"
    drop_policy_name = 'drop'

    # start the GRPC client
    logging.info('starting the GRPC client......')
    client = CiscoGRPCClient(router_ip, 57400, 10, 'cisco', 'cisco')

    # start the GRPC client
    #bgp_flush = Flush_BGP(client, ext_as, drop_policy_name, config_fn)

    # flush the neighbors matching the AS
    # bgp_neighbors = bgp_flush.get_bgp_neighbors()
    # print 'removed external BGP neighbors and previous policy:', bgp_neighbors

    # check if properly flushed
    # rm_neighbors = list(zip(*bgp_neighbors)[0])
    # #rm_neighbors = ["2.2.3.7"]
    # bgp_flush.check_flush_neighbors(rm_neighbors)



if __name__ == '__main__':
    main()


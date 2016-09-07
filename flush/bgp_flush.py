import sys
sys.path.insert(0, '../')
from lib.cisco_grpc_client import CiscoGRPCClient
from pprint import pprint
import json
import pickle 
import copy 


def load_bgp(fn):
    with open(fn, 'r') as f:
        bgp = f.read()
    return bgp

def flush_config_neighbors(neighbor_as, config_json, drop_policy):
    c = copy.deepcopy(config_json)
    l = c['Cisco-IOS-XR-ipv4-bgp-cfg:bgp']['instance'][0]
    l = l['instance-as'][0]
    l = l['four-byte-as'][0]
    l = l['default-vrf']['bgp-entity']['neighbors']['neighbor']
    
    removed_neighbors = []
    for neighbor in l:
        as_val = neighbor['remote-as']['as-yy']
        if as_val in neighbor_as:
            # change the policy to drop 
            removed_neighbors.append(neighbor['neighbor-address'])
            neighbor['neighbor-afs']['neighbor-af'][0]['route-policy-out'] = drop_policy

    print 'removed external BGP neighbors:', removed_neighbors
    #pprint(c)
    c = json.dumps(c)
    return c

def confirm_flush(bgp_config):
    #pprint(bgp_config)
     
   
             
def main():
    # start the GRPC client 
    client = CiscoGRPCClient('10.85.138.39', 57400, 10, 'cisco', 'cisco')

    # load the BGP config template 
    bgp = load_bgp("/home/ubuntu/ios-xr-grpc-python/examples/get-neighborsq.json")
    res = client.getconfig(bgp)
    res = json.loads(res)                       # encode the output into json
    
    
    # TESTING on local
    #pickle.dump( res, open( "out.p", "wb" ) )
    #res = pickle.load(open("/Users/quale/workspace/twitter_correct/out.p", 'rb'))
   
    # create the new BGP config with the drop policy 
    new_config = flush_config_neighbors([2235], res, u'drop')

    # flush the router with the external BGPs 
    resp = client.mergeconfig(new_config)
    assertEqual(resp.errors, u'')

    # confirm flushing has occured
    bgp_flush = client.getconfig(bgp)
    confirm_flush(json.loads(bgp_flush))
    
if __name__ == '__main__':
    main()

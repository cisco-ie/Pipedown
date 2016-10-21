#!/bin/bash
echo "Stopping all current impairments."
sudo tc qdisc del dev eth1 root &> /dev/null
sudo tc qdisc del dev eth2 root &> /dev/null
echo "Starting packet loss on rtr1 link."
sudo tc qdisc add dev eth1 root netem loss 7%

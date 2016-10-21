#!/bin/bash

echo "Stopping impairment on all the links"
sudo tc qdisc del dev eth1 root &> /dev/null
sudo tc qdisc del dev eth2 root &> /dev/null

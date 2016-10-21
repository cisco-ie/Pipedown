#!/bin/bash

apt-get update
apt-get -y install bridge-utils lxc
ifconfig eth1 promisc
ifconfig eth2 promisc

ifconfig eth1 up
ifconfig eth2 up

brctl addbr br0
brctl addif br0 eth1
brctl addif br0 eth2
ifconfig br0 up

chmod u+x start_impair.sh
chmod u+x stop_impair.sh


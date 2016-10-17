#!/bin/bash

# Grab the container from Lisa Roach's Box folder
curl -L 'https://cisco.box.com/shared/static/kg2w7jqeurzoyaysamkpndjsw8wbjz9k.tgz' -o 'monitor.tgz'

# Launch the iPerf container
cd /misc/app_host/
sudo mkdir monitor
sudo mv /home/vagrant/monitor.tgz .
tar -zvxf monitor.tgz -C monitor/ > /dev/null
sudo -i virsh create /home/vagrant/demo.xml
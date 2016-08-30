#!/bin/bash

# Grab the container from Lisa Roach's Box folder
curl -L 'https://cisco.box.com/shared/static/w9di3jxh9znxiijc6t03wcnmu31irdni.gz' -o 'pathchecker_rootfs.tar.gz'
# Launch the iPerf container
cd /misc/app_host/
sudo mkdir monitor
sudo mv /home/vagrant/pathchecker_rootfs.tar.gz .
tar -zvxf pathchecker_rootfs.tar.gz -C monitor/ > /dev/null
sudo -i virsh create /home/vagrant/demo.xml
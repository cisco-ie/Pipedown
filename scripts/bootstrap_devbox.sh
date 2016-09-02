#!/usr/bin/env bash

curl -L https://github.com/Exa-Networks/exabgp/archive/3.4.16.tar.gz | sudo tar zx -C /home/vagrant/  > /dev/null
sudo ip route add 10.1.1.0/24 via 11.1.1.10
sudo ip route add 12.1.1.0/24 via 11.1.1.10
sudo ip route add 13.0.2.0/24 via 11.1.1.10
cp /vagrant/configs/exabgp-router-conf.ini /home/vagrant/exabgp-router-conf.ini
sudo chmod 777 /home/vagrant/exabgp-router-conf.ini

screen -S exabgp -dm bash -c 'sudo env exabgp.tcp.bind="11.1.1.20" exabgp.tcp.port=179 /home/vagrant/exabgp-3.4.16/sbin/exabgp /home/vagrant/exabgp-router-conf.ini'

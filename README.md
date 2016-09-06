## Vagrant for Router-Connectedness App

This environment is intended to act as a testbed for playing with the router-connectedness app. 

![Router Diagram](Router-Connectedness.png)

Onetime config command:
``` VBoxManage natnetwork add --netname Internet --network "13.0.2.0/24" --enable --dhcp off ```
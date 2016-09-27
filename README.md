## Vagrant for Router-Connectedness App

This environment is intended to act as a testbed for playing with the router-connectedness app. 

![Router Diagram](Router-Connectedness.png)

Onetime config command:
``` VBoxManage natnetwork add --netname Internet --network "13.0.2.0/24" --enable --dhcp off ```


Run iPerf Server on rtr1:
```iperf -s -B 10.1.1.2 -u```


Test iPerf client on rtr2:
```iperf -c 10.1.1.2 -B 10.1.1.1 -t 10 -i 10 -u -y C```

### Impair the Link

1. Jump into the bridge vagrant:

```vagrant ssh bridge```

2. Run the start_impair script:

```./start_impair.sh```


### Repair the Link

1. Jump into the bridge vagrant:

```vagrant ssh bridge```

2. Run the stop_impair script:

```./stop_impair.sh```
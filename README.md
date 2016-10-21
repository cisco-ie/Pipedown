# Pipedown
### Router Connectedness Application

##### Author: Lisa Roach, Karthik Kumaravel, Quan Le
##### Contact: Please use the Issues page to ask questions or open bugs and feature requests.

## Description

The end goal of the Pipedown is to monitor a CDN router and ensures that it has a stable link to the data center, and if it does not, take it offline by removing its link to the internet.

The application solves the end goal by checking a link that connects back to the data center and ensure that it is healthy. The link is determined to be healthy using [iPerf](https://iperf.fr/) based on parameters such as jitter, bandwidth, packet loss, and dropped packets. If the link is determined to be unhealthy, then the link connecting to the internet would be flushed using [gRPC](http://www.grpc.io/) based on a user defined AS and policy.

#### Current Limitations:

Currently for monitoring multiple links, each link needs to have its own source ip address.

### Vagrant

For an easy Pipedown-in-a-box demonstration, please refer to the [vagrant](https://github.com/cisco-ie/Pipedown/tree/master/vagrant) directory. Here you will be able to download a fully functional vagrant environment that has Router-Connectedness up and running already.

## Usage

Step 1: Clone this repo and cd into router-connectedness

Step 2: It is highly recommended you install and use a [virtualenv](https://virtualenv.pypa.io/en/stable/).

```
pip install virtualenv

virtualenv venv

source venv/bin/activate
```

Step 3: Install gRPC.

`pip install grpcio`

Step 4: Configuring the router.

Ensure these things are configured on the router:

- Turn on gRPC.
- Route-policy that will drop everything, (how the app flushes the internet connection).

Step 5: Create a monitor.config file in the router-connectedness directory and fill in the values in the key:value pair.

```
[Name-for-connection]
destination : ip_address          # IP address of where iPerf is running in the data center
source : ip_address               # IP address of your souce link
protocol : protocol               # Protocol you want to monitor [isis, BGP]
bw_thres : bandwidth              # Integer value of Bandwidth in KB that you determine is the minmum value for the link
jitter_thres : jitter_threshold   # Integer value of Jitter Threshold
pkt_loss : packet loss            # Integer value of number of packets allowed to lose
interval : interval               # Integer value in seconds of how often you want the test to run
grpc_server : ip_address          # IP address of the router you are monitoring (Can be local loopback 127.0.0.1)
grpc_port : port                  # gRPC port number
grpc_user : username              # Username for AAA authentication
grpc_pass : password              # Password for AAA authentication
flush_as : flush_as               # The AS number of the neighbor group for the internet
drop_policy_name: drop_policy_name # The policy name that you want when the flush is activated.
```
Example:
```
[IS-IS]
destination : 5.5.5.5
source : 10.1.1.1
protocol : isis
bw_thres : 200
jitter_thres : 20
pkt_loss : 3
interval : 10
grpc_server : 127.0.0.1
grpc_port : 57777
grpc_user : vagrant
grpc_pass : vagrant
flush_as : 65000
drop_policy_name: drop
```

Step 6: Turn on iPerf on destination box.

The iPerf server must be running on another router or server (the router to whom you are trying to connect your link) in order to test iPerf.

Use following command to launch iPerf:

```iperf -s -B ip_address -u```

*Replace ip_address with the destination ip address.

Step 7: Run deamon.

Run the monitor daemon. It uses multithreading so a instance will spawn for every link you want to monitor. You can check the log to ensure it is working.

```python monitor_daemony.py```


## Testing

### Unit Tests

Do this at the top-level directory:

```python -m unittest discover Tests```

### Integration Tests

**Running iPerf Server**

The iPerf server must be running on another router (the router to whom you are trying to connect your link) in order to test iPerf.

Use following command to launch iPerf:


```iperf -s -B 10.1.1.2 -u```

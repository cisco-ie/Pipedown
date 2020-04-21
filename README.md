** This project is no longer being maintained, please use at your own discretion! **
# Pipedown
### Router Connectedness Application

##### Pipedown 1.5.1

##### Released November 3, 2016

##### Author: Lisa Roach, Karthik Kumaravel, Quan Le, Bruce McDougall
##### Contact: Please use the Issues page to ask questions or open bugs and feature requests.

## Description

Pipedown is designed to be a modular, configurable, and extensible application (think of a python-based version of Cisco Embedded Event Manager, or Junos SLAX scripts), for doing any number of automated network tasks – monitoring, diagnostics, packet generation, event notification, problem remediation, etc.  In its initial release Pipedown can run in IOS-XR’s linux shell, or an operator installed LXC on an IOS-XR router.  Because Pipedown is written in python, its use cases are not constrained by IOS-XR’s (or any other vendor’s) internal tooling and configuration syntax; ie, Pipedown can incorporate existing linux or python tools (iPerf, Scapy, etc.), or the user may write their own.  This first release of Pipedown includes a CDN monitoring application, whose end goal is to monitor a CDN router’s connectivity and ensure it has a stable link to its backend data center.  If its backend link degrades or fails, the application will take the CDN router offline by withdrawing its route advertisements to the internet.

The application solves the end goal by checking a link that connects back to the data center and ensuring that it is healthy. The link is determined to be healthy using [iPerf](https://iperf.fr/) based on parameters such as jitter, bandwidth, packet loss, and dropped packets. If the link is determined to be unhealthy, then the link connecting to the internet would be flushed using [gRPC](http://www.grpc.io/) based on a user defined AS and policy.

#### Prerequisites:

Cisco IOS-XR box running version 6.1.2 and above.

This version of Pipedown has been developed to run in a Linux container on the IOS-XR. It has been tested on an Ubuntu 14.04 container running Python 2.7. If you run Pipedown in a different scenario we welcome any feedback you have.

Pipedown attempts to be compatible with Python 3 wherever possible, but since gRPC does not officially support Python 3 yet Python 2.7 should be used. 

#### Current Limitations:

- For monitoring multiple links, each link needs to have its own source ip address.
- The link to the internet must be a BGP connection, the monitored link can be either BGP/IS-IS

### Vagrant

For an easy Pipedown-in-a-box demonstration, please refer to the [vagrant directory](https://github.com/cisco-ie/Pipedown/tree/master/vagrant). Here you will be able to download a fully functional vagrant environment that has Pipedown up and running already. This demonstration uses concepts that can be better understood by consulting the IOS-XR tutorials: https://xrdocs.github.io/application-hosting/tutorials/.

## Usage
The following steps are to be done in a IOS-XR container. If you need help getting started with containers and IOS-XR: [App-hosting](https://xrdocs.github.io/application-hosting/tutorials/2016-06-16-xr-toolbox-part-4-bring-your-own-container-lxc-app/)

Step 1: Clone this repo and cd into Pipedown

Step 2: It is highly recommended you install and use a [virtualenv](https://virtualenv.pypa.io/en/stable/).

```
pip install virtualenv

virtualenv venv

source venv/bin/activate
```

Step 3: Install gRPC. (If you chose to install outside of a virtualenv, you may have some trouble at this step).

`pip install grpcio`

Step 4: Run the `setup.py` script.

`python setup.py install`

Step 5: Configuring the router (Not done in the container).

Ensure these things are configured on the router (You can use cli):

- Turn on gRPC. Example:
```
!! IOS XR
!
grpc
!
end
```

- Route-policy that will drop everything, (how the app flushes the internet connection). Example: 

```
!! IOS XR
!
route-policy drop
  drop
end-policy
!
end
```
Step 6: Create a monitor.config file in the router-connectedness directory and fill in the values in the key:value pair.

```
# [TRANSPORT]
# In this section you must include all of your transport object needs.
# Currently, grpc is the only supported transport, so the following options
# are required options:
# grpc_server : ip_address # IP address of the router you are monitoring (Can be local loopback 127.0.0.1)
# grpc_port : port # gRPC port number
# grpc_user : username # Username for AAA authentication
# grpc_pass : password # Password for AAA authentication

# [Name-for-connection]
##### REQUIRED OPTIONS ######
# destination : ip_address # IP address of where iPerf is running in the data center
# source : ip_address # IP address of your source link
# protocols : protocol # Protocols you want to monitor [IS-IS, BGP]

##### iPERF OPTIONS #####
# bw_thres : bandwidth # Integer value of Bandwidth in KB that you determine is the minimum value for the link
# jitter_thres : jitter_threshold # Integer value of Jitter Threshold
# pkt_loss : packet loss # Integer value of number of packets allowed to lose
# interval : interval # Integer value in seconds of how often you want the test to run


##### FLUSH OPTIONS #####
# flush_bgp_as : flush_as # The AS number of the neighbor group for the internet. Indicates you want the link flushed.
# yang: yang model type # The type of yang to use. Options are cisco and openconfig.
# drop_policy_name: drop_policy_name # The policy name that you want when the flush is activated.
# pass_policy_name: pass_policy_name # The policy name that is originally allowing traffic to pass to the internet.

##### ALERT OPTIONS #####
# hostname: The hostname of your router. Used to clarify messages.
# text_alert: phone_number # The phone number to text. Indicates texting is desired.
# email_alert: email_address # Email address to be emailed. Indicates emails are desired. Can be multiple values.
```
Example:
```
[TRANSPORT]
grpc_server : 127.0.0.1
grpc_port : 57777
grpc_user : vagrant
grpc_pass : vagrant

[DEFAULT]
hostname: rtr1
text_alert : +14087784819
# email_alert:  pipedown@cisco.com
yang: openconfig
flush_bgp_as : 65000
drop_policy_name : drop
pass_policy_name : pass

[IS-IS]
destination : 5.5.5.5
source : 10.1.1.1
protocols : isis
bw_thres : 200
jitter_thres : 20
pkt_loss : 3
interval : 2
```

Step 7: Install iPerf on both the container and the end host you are monitoring against. The end host can be either a router or a server.

On a linux container, install iPerf how you normally would for your OS. Example:

`apt-get install iperf`

On a native IOS-XR box, use yum:

`sudo yum install iperf`

iPerf will need to be turned on on the data center router whom you are testing connectivity to.

To turn on iPerf on your data center router that you are testing the connection to, use this command:

`iperf -s -B <port address to bind to> -u`


Step 8: In the container run the deamon.

Run the monitor daemon. It uses multithreading so a instance will spawn for every link you want to monitor. You can check the log to ensure it is working.

```python monitor_daemony.py```


## Testing

### Unit Tests

Do this at the ~/Pipedown/pipedown directory:


```python -m unittest discover Tests```


**Note**: iPerf must be installed, or two tests will fail. If you do not want to install iPerf just ignore the error messages.


### Integration Tests

**Running iPerf Server**

The iPerf server must be running on another router (the router to whom you are trying to connect your link) in order to test iPerf.

Use the following command to launch iPerf:


```iperf -s -B 10.1.1.2 -u```

## Attribution

The Pipedown project came about as an effort to give network operators an onboard toolset to diagnose, and potentially mitigate problems that arise due to the fact that router control plane applications (BGP, ISIS, etc.) do not have a complete and holistic understanding of network health.  This problem space is well articulated Tim Hoffman and Micah Croff’s NANOG 67 presentation: [Suffering Withdrawal An automated approach to connectivity](https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=1&cad=rja&uact=8&ved=0ahUKEwi8vdTk_6vTAhVTImMKHRmjBPkQFggjMAA&url=https%3A%2F%2Fwww.nanog.org%2Fsites%2Fdefault%2Ffiles%2FHoffman_Suffering_Withdrawal.pdf&usg=AFQjCNGiC4NZXl5RyPQgLrmY04p--48p8A&sig2=befyoVNqipkFmGyXmtR-Vw)

## License
>You can check out the full license [here](https://github.com/cisco-ie/Pipedown/blob/master/LICENSE)

This project is licensed under the terms of the **APACHE-2.0** license.

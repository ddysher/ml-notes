<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Experiments](#experiments)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

*Date: 03/25/2017*

[shrike](https://github.com/TalkingData/Shrike) is a simple network solution for docker network from
talkingdata. A new bridge 'br0' is created and both container interface and physical interface are
attached to the bridge, forming a large L2 network. The focus in this doc is to look into docker IPAM
plugin.

# Experiments

**Set host range**

Running the host-range command will create host range; and corresponding etcd instance will have
following items:

    $ oam-docker-ipam host-range --ip-start 192.168.0.4/24 --ip-end 192.168.0.6/24 --gateway 192.168.223.2

    /talkingdata/hosts/pool/192.168.0.4
    /talkingdata/hosts/pool/192.168.0.5
    /talkingdata/hosts/pool/192.168.0.6
    /talkingdata/hosts/config/{"Subnet":"192.168.0.0/24","Gateway":"192.168.223.2"}

**Set container ip range**

Similarly for container ip range:

    oam-docker-ipam ip-range --ip-start 192.168.0.100/24 --ip-end 192.168.0.200/24

    /talkingdata/containers/192.168.0.0/config/{"Ipnet":"192.168.0.0","Mask":"24"}
    /talkingdata/containers/192.168.0.0/pool/192.168.0.100
    /talkingdata/containers/192.168.0.0/pool/192.168.0.101
    ...
    /talkingdata/containers/192.168.0.0/pool/192.168.0.200

**Start docker network plugin server**

This command will start ipam plugin server, which will conform to docker plugin API and creates a
socket under `/var/run/docker/plugins`.

    ./oam-docker-ipam --debug=true --cluster-store=http://localhost:2379 server

**Create network**

    ./oam-docker-ipam --cluster-store=http://localhost:2379 create-network --ip 192.168.0.5

This will create a docker network 'mynet' (hardcoded), using following command:

     docker network create
     --opt=com.docker.network.bridge.enable_icc=true
     --opt=com.docker.network.bridge.enable_ip_masquerade=false
     --opt=com.docker.network.bridge.host_binding_ipv4=0.0.0.0
     --opt=com.docker.network.bridge.name=br0
     --opt=com.docker.network.driver.mtu=1500
     --ipam-driver=talkingdata
     --subnet='container ip subnet, e.g. 192.168.0.0/24'
     --gateway='container gateway, e.g. 192.168.0.1'
     --aux-address=DefaultGatewayIPv4='container gateway, e.g.192.168.223.2
     mynet

The ipam server will output the following log:

     INFO[0003] GetDefaultAddressSpaces
     INFO[0003] RequestPool: {"AddressSpace":"","Pool":"192.168.0.0/24","SubPool":"","Options":{},"V6":false}
     INFO[0003] RequestAddress {"PoolID":"192.168.0.0","Address":"192.168.0.6","Options":{"RequestAddressType":"com.docker.network.gateway"}}
     DEBU[0003] Get key /talkingdata/containers/192.168.0.0/config with value {"Ipnet":"192.168.0.0","Mask":"24"}
     DEBU[0003] GetConfig {"Ipnet":"192.168.0.0","Mask":"24"} from network 192.168.0.0
     INFO[0003] Skip allocate gateway ip 192.168.0.6

Note that docker daemon requests address space pool '192.168.0.0/24', which is the option `--subnet`
passed to `docker network create` command. It is converted in `docker/daemon/network.go#createNetwork`.

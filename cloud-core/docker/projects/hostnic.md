<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Experiment](#experiment)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

[docker-plugin-hostnic](https://github.com/yunify/docker-plugin-hostnic) is a docker network plugin
which can bind a special host nic to a container. Simple enough, but record here anyway for reference.

# Experiment

**Build and run**

After running the plugin, we'll see hostnic plugin socket.

    $ ./build
    $ sudo ./bin/docker-plugin-hostnic
    $ sudo ls /run/docker/plugins
    hostnic.sock

**Create docker network**

The following command creates a docker network.

     docker network create -d hostnic --subnet=192.168.3.0/24 --gateway 192.168.3.1 --ip-range=192.168.3.128/28 hostnic

- '--subnet' option tells docker to allocate IP address from that subnet (which is the router subnet in the experiment environment)
- '--gateway' is the route's IP.
- '--ip-range': since we already used some addresses in this subnet (e.g. home-desktop), we ask docker to allocate IP in higher range. Note alternatively, we can allocate IP statically when creating container.

**Create virtual nic**

As we have only one physical interface (enp0s31f6), we can create a macvlanas a virtual nic for the
plugin to bind. Also, the plugin takes mac address as input, we'll need to find mac address of the
virtual nic:

    $ sudo ip link add hostnicvirtual0 link enp0s31f6 type macvlan mode bridge
    $ ip a
    1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
        link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
        inet 127.0.0.1/8 scope host lo
           valid_lft forever preferred_lft forever
        inet6 ::1/128 scope host
           valid_lft forever preferred_lft forever
    2: enp0s31f6: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
        link/ether 2c:4d:54:ed:38:45 brd ff:ff:ff:ff:ff:ff
        inet 192.168.3.34/24 brd 192.168.3.255 scope global enp0s31f6
           valid_lft forever preferred_lft forever
        inet6 fe80::780d:af91:a854:32e9/64 scope link
           valid_lft forever preferred_lft forever
    3: docker0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN group default
        link/ether 02:42:2f:1b:e2:84 brd ff:ff:ff:ff:ff:ff
        inet 172.17.0.1/16 scope global docker0
           valid_lft forever preferred_lft forever
    10: hostnicvirtual0@enp0s31f6: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default qlen 1000
        link/ether b2:77:e8:60:25:84 brd ff:ff:ff:ff:ff:ff
        inet 192.168.3.44/24 brd 192.168.3.255 scope global hostnicvirtual0
           valid_lft forever preferred_lft forever
        inet6 fe80::8137:48d8:bb1b:df97/64 scope link
           valid_lft forever preferred_lft forever

**Create container**

Now that we create a container using this interface. Note the name and IP address of the interface
has changed. IP address is changed because of the options we passed to docker network.

    $ docker run -it --mac-address b2:77:e8:60:25:84 --network hostnic busybox sh
    / # ip a
    1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue qlen 1000
        link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
        inet 127.0.0.1/8 scope host lo
           valid_lft forever preferred_lft forever
    10: eth0@if2: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue qlen 1000
        link/ether b2:77:e8:60:25:84 brd ff:ff:ff:ff:ff:ff
        inet 192.168.3.128/24 scope global eth0
           valid_lft forever preferred_lft forever

**Inspecting plugin output**

The plugin output shows its interaction with docker daemon (via libnetwork protocol), and how it
handles the operations:

    $ sudo ./bin/docker-plugin-hostnic -d
    2017-04-18T16:17:59+08:00 mangosteen ./bin/docker-plugin-hostnic[11395]: INFO Run hostnic
    2017-04-18T16:17:59+08:00 mangosteen ./bin/docker-plugin-hostnic[11395]: INFO Load config from [/etc/docker/hostnic/config.json]
    2017-04-18T16:17:59+08:00 mangosteen ./bin/docker-plugin-hostnic[11395]: DEBUG root group found. gid: 0
    2017/04/18 16:18:07 Entering go-plugins-helpers createnetwork
    2017-04-18T16:18:07+08:00 mangosteen ./bin/docker-plugin-hostnic[11395]: DEBUG CreateNetwork Called: [ &{NetworkID:1bacc246410b1540111172f82c9007d2231ffb0eff7b2b38d4acee1238ac2f7b Options:map[com.docker.network.enable_ipv6:false com.docker.network.generic:map[]] IPv4Data:[0xc4200f2680] IPv6Data:[]} ]
    2017-04-18T16:18:07+08:00 mangosteen ./bin/docker-plugin-hostnic[11395]: DEBUG CreateNetwork IPv4Data len : [ 1 ]
    2017-04-18T16:18:07+08:00 mangosteen ./bin/docker-plugin-hostnic[11395]: INFO RegisterNetwork [1bacc246410b1540111172f82c9007d2231ffb0eff7b2b38d4acee1238ac2f7b] IPv4Data : [ &{AddressSpace:LocalDefault Pool:192.168.3.0/24 Gateway:192.168.3.1/24 AuxAddresses:map[]} ]
    2017-04-18T16:18:07+08:00 mangosteen ./bin/docker-plugin-hostnic[11395]: DEBUG Save config [map[1bacc246410b1540111172f82c9007d2231ffb0eff7b2b38d4acee1238ac2f7b:0xc4200c52c0]] to [/etc/docker/hostnic/config.json]
    2017-04-18T16:18:11+08:00 mangosteen ./bin/docker-plugin-hostnic[11395]: DEBUG CreateEndpoint Called: [ &{NetworkID:1bacc246410b1540111172f82c9007d2231ffb0eff7b2b38d4acee1238ac2f7b EndpointID:1c9873e0ced43e13befd3c1f319860c1745f0a31af4c463eb3d549ec5e3ed08d Interface:0xc420013da0 Opions:map[com.docker.network.endpoint.exposedports:[] com.docker.network.endpoint.macaddress:snfoYCWE com.docker.network.portmap:[]]} ]
    2017-04-18T16:18:11+08:00 mangosteen ./bin/docker-plugin-hostnic[11395]: DEBUG r.Interface: [ &{Address:192.168.3.128/24 AddressIPv6: MacAddress:b2:77:e8:60:25:84} ]
    2017-04-18T16:18:11+08:00 mangosteen ./bin/docker-plugin-hostnic[11395]: INFO Add nic [&{Name:hostnicvirtual0 HardwareAddr:b2:77:e8:60:25:84 Address:192.168.3.45/24 endpoint:<nil>}] to nic talbe
    2017-04-18T16:18:11+08:00 mangosteen ./bin/docker-plugin-hostnic[11395]: DEBUG CreateEndpoint resp interface: [ &{Address: AddressIPv6: MacAddress:} ]
    2017-04-18T16:18:11+08:00 mangosteen ./bin/docker-plugin-hostnic[11395]: DEBUG Join Called: [ &{NetworkID:1bacc246410b1540111172f82c9007d2231ffb0eff7b2b38d4acee1238ac2f7b EndpointID:1c9873e0ced43e13befd3c1f319860c1745f0a31af4c463eb3d549ec5e3ed08d SandboxKey:/var/run/docker/netns/87cd964126e8 Options:map[com.docker.network.endpoint.exposedports:[] com.docker.network.portmap:[]]} ]
    2017-04-18T16:18:11+08:00 mangosteen ./bin/docker-plugin-hostnic[11395]: DEBUG Join resp : [ {InterfaceName:{SrcName:hostnicvirtual0 DstPrefix:eth} Gateway:192.168.3.1 GatewayIPv6: StaticRoutes:[] DisableGatewayService:false} ]
    2017-04-18T16:18:11+08:00 mangosteen ./bin/docker-plugin-hostnic[11395]: DEBUG ProgramExternalConnectivity Called: [ &{NetworkID:1bacc246410b1540111172f82c9007d2231ffb0eff7b2b38d4acee1238ac2f7b EndpointID:1c9873e0ced43e13befd3c1f319860c1745f0a31af4c463eb3d549ec5e3ed08d Options:map[ com.docker.network.endpoint.exposedports:[] com.docker.network.portmap:[]]} ]
    2017-04-18T16:18:11+08:00 mangosteen ./bin/docker-plugin-hostnic[11395]: DEBUG EndpointInfo Called: [ &{NetworkID:1bacc246410b1540111172f82c9007d2231ffb0eff7b2b38d4acee1238ac2f7b EndpointID:1c9873e0ced43e13befd3c1f319860c1745f0a31af4c463eb3d549ec5e3ed08d} ]
    2017-04-18T16:18:11+08:00 mangosteen ./bin/docker-plugin-hostnic[11395]: DEBUG EndpointInfo resp.Value : [ map[hostNic.HardwareAddr:b2:77:e8:60:25:84 id:1c9873e0ced43e13befd3c1f319860c1745f0a31af4c463eb3d549ec5e3ed08d srcName:hostnicvirtual0 hostNic.Name:hostnicvirtual0 hostNic.Addr:192.168.3.128/24] ]
    2017-04-18T16:18:11+08:00 mangosteen ./bin/docker-plugin-hostnic[11395]: DEBUG EndpointInfo Called: [ &{NetworkID:1bacc246410b1540111172f82c9007d2231ffb0eff7b2b38d4acee1238ac2f7b EndpointID:1c9873e0ced43e13befd3c1f319860c1745f0a31af4c463eb3d549ec5e3ed08d} ]
    2017-04-18T16:18:11+08:00 mangosteen ./bin/docker-plugin-hostnic[11395]: DEBUG EndpointInfo resp.Value : [ map[srcName:hostnicvirtual0 hostNic.Name:hostnicvirtual0 hostNic.Addr:192.168.3.128/24 hostNic.HardwareAddr:b2:77:e8:60:25:84 id:1c9873e0ced43e13befd3c1f319860c1745f0a31af4c463eb3d549ec5e3ed08d] ]
    2017-04-18T16:18:17+08:00 mangosteen ./bin/docker-plugin-hostnic[11395]: DEBUG RevokeExternalConnectivity Called: [ &{NetworkID:1bacc246410b1540111172f82c9007d2231ffb0eff7b2b38d4acee1238ac2f7b EndpointID:1c9873e0ced43e13befd3c1f319860c1745f0a31af4c463eb3d549ec5e3ed08d} ]
    2017-04-18T16:18:17+08:00 mangosteen ./bin/docker-plugin-hostnic[11395]: DEBUG Leave Called: [ &{NetworkID:1bacc246410b1540111172f82c9007d2231ffb0eff7b2b38d4acee1238ac2f7b EndpointID:1c9873e0ced43e13befd3c1f319860c1745f0a31af4c463eb3d549ec5e3ed08d} ]
    2017-04-18T16:18:17+08:00 mangosteen ./bin/docker-plugin-hostnic[11395]: DEBUG DeleteEndpoint Called: [ &{NetworkID:1bacc246410b1540111172f82c9007d2231ffb0eff7b2b38d4acee1238ac2f7b EndpointID:1c9873e0ced43e13befd3c1f319860c1745f0a31af4c463eb3d549ec5e3ed08d} ]

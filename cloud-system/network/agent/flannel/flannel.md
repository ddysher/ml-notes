<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
  - [Introduction](#introduction)
  - [IP masquerade](#ip-masquerade)
- [Implementation](#implementation)
  - [Backend](#backend)
  - [Network](#network)
  - [Backend manager](#backend-manager)
  - [Subnet manager](#subnet-manager)
  - [Network manager](#network-manager)
  - [Bootstrapping](#bootstrapping)
- [Backends](#backends)
  - [vxlan](#vxlan)
- [Experiment](#experiment)
  - [Bring up a flannel](#bring-up-a-flannel)
- [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

## Introduction

flannel is a virtual network that gives a subnet to each host for use with container runtimes.

```json
{
  "Network": "10.0.0.0/8",
  "SubnetLen": 20,
  "SubnetMin": "10.10.0.0",
  "SubnetMax": "10.99.0.0",
  "Backend": {
    "Type": "udp",
    "Port": 7890
  }
}
```

## IP masquerade

When setting `--ip-masq` flag in flannel, flannel will set following rules (note network range in the
setup is '10.1.0.0/16', host chooses '10.1.89.0/24):

```
vagrant at vagrant-ubuntu-trusty-64 in ~/code/workspace/src/github.com/coreos/flannel on master!
$ sudo ./flannel -iface eth1 --ip-masq
I0517 05:50:25.870526 03367 main.go:126] Installing signal handlers
I0517 05:50:25.871637 03367 manager.go:163] Using 192.168.33.33 as external interface
I0517 05:50:25.871675 03367 manager.go:164] Using 192.168.33.33 as external endpoint
I0517 05:50:25.891750 03367 local_manager.go:179] Picking subnet in range 10.1.1.0 ... 10.1.255.0
I0517 05:50:25.895976 03367 ipmasq.go:47] Adding iptables rule: -s 10.1.0.0/16 -d 10.1.0.0/16 -j RETURN
I0517 05:50:25.900202 03367 ipmasq.go:47] Adding iptables rule: -s 10.1.0.0/16 ! -d 224.0.0.0/4 -j MASQUERADE
I0517 05:50:25.904306 03367 ipmasq.go:47] Adding iptables rule: ! -s 10.1.0.0/16 -d 10.1.0.0/16 -j MASQUERADE
I0517 05:50:25.909471 03367 manager.go:246] Lease acquired: 10.1.89.0/24
I0517 05:50:25.910016 03367 network.go:58] Watching for L3 misses
I0517 05:50:25.910857 03367 network.go:66] Watching for new subnet leases

vagrant at vagrant-ubuntu-trusty-64 in ~/code/workspace/src/github.com/coreos/flannel on master!
$ ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    link/ether 08:00:27:22:cb:22 brd ff:ff:ff:ff:ff:ff
    inet 10.0.2.15/24 brd 10.0.2.255 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::a00:27ff:fe22:cb22/64 scope link
       valid_lft forever preferred_lft forever
3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    link/ether 08:00:27:5c:b4:37 brd ff:ff:ff:ff:ff:ff
    inet 192.168.33.33/24 brd 192.168.33.255 scope global eth1
       valid_lft forever preferred_lft forever
    inet6 fe80::a00:27ff:fe5c:b437/64 scope link
       valid_lft forever preferred_lft forever
4: docker0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1450 qdisc noqueue state UP group default
    link/ether 02:42:db:a1:44:51 brd ff:ff:ff:ff:ff:ff
    inet 10.1.89.1/24 scope global docker0
       valid_lft forever preferred_lft forever
    inet6 fe80::42:dbff:fea1:4451/64 scope link
       valid_lft forever preferred_lft forever
5: br-b9c95bab7fe5: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN group default
    link/ether 02:42:13:c6:2e:9d brd ff:ff:ff:ff:ff:ff
    inet 172.20.0.1/16 scope global br-b9c95bab7fe5
       valid_lft forever preferred_lft forever
6: flannel.1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1450 qdisc noqueue state UNKNOWN group default
    link/ether 22:66:7d:6f:9a:60 brd ff:ff:ff:ff:ff:ff
    inet 10.1.89.0/16 scope global flannel.1
       valid_lft forever preferred_lft forever
    inet6 fe80::2066:7dff:fe6f:9a60/64 scope link
       valid_lft forever preferred_lft forever
14: vethf80dec1@if13: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1450 qdisc noqueue master docker0 state UP group default
    link/ether a6:8b:b0:e1:68:3e brd ff:ff:ff:ff:ff:ff
    inet6 fe80::a48b:b0ff:fee1:683e/64 scope link
       valid_lft forever preferred_lft forever
```

The rules are:

```
-A POSTROUTING -s 10.1.0.0/16 -d 10.1.0.0/16 -j RETURN
-A POSTROUTING -s 10.1.0.0/16 ! -d 224.0.0.0/4 -j MASQUERADE
-A POSTROUTING ! -s 10.1.0.0/16 -d 10.1.0.0/16 -j MASQUERADE
```

- The first rule makes sure we don't NAT traffic within overlay network (e.g. coming out of docker0),
  e.g. if a container with address 10.1.89.2 accesses another container with address 10.1.99.2.
- The second rule will NAT traffic from container to outside, except multicast traffic, e.g. if
  container with address 10.1.89.2 accesses google.com, before the packet is sent out, source IP
  address will be changed to host network address. This rule makes sure container has internet access.
- The third rule will masquerade anything headed towards flannel from the host, e.g. from host, access
  container 10.1.89.2, container will see traffic coming from 10.1.89.1 (docker's address). TODO: even
  if the last rule is deleted, container will still see traffic coming from 10.1.89.1.

# Implementation

## Backend

Backend is the underline implementation, e.g. vxlan, udp, gce, hostgw, etc. See `backend/common.go#Backend`
interface. Backend registers itself via init(), which is called at import time in main.go. Inside backend,
it has the concept of 'Network', which provides the actual functionalities of the backend, see
`backend/common.go#Network`; this is different from the 'Network' defined in flannel, see below.

## Network

A network is one that has IP address range, interfaces, etc. Flannel has an experimental feature:
multi-network mode. Multi-network mode allows a single flannel daemon to join multiple networks. Each
network is independent from each other and has its own configuration, IP space, interfaces. See [here](https://github.com/coreos/flannel/tree/ebb362ba5ee8fbfb21855d7caa6b1f48881dd751#multi-network-mode-experimental)

## Backend manager

Backend manager manages all backends, knows how to find them, etc. Each backend has a Run() method
running in a goroutine launched in backend manager. Note it is launched on demand; that is, the Run()
method is called only when a specific backend is used in flannel. For example, hostgw#Run() method won't
be called if we only use vxlan backend.

## Subnet manager

Subnet manager is an interface which manages all subnets, e.g. AcquireLease, RenewLease, AddReservation,
etc. See 'subnet/' folder for details. As of version v0.7.0, there are two main subnet managers:
1. local manager, which does subnet allocation in flannel itself, and uses etcd for acquiring lease.
2. kube, which acquires lease from kubernetes apiserver; kubernetes controller manager will do the subnet calculation, etc.

Subnet allocation is called in each backend (vxlan, udp, etc) when initializing backend network.

## Network manager

Network manager is the umbrella manager which includes subnet manager, backend manager, a list of
networks (in multi-network mode), etc.

## Bootstrapping

When starting, flannel creates a network manager and runs it in a goroutine, wait for it to complete
(which never returns normally).

Control is then handed over from main.go to network/manager.go#Run(). In NetworkManager.Run(), it
creates a new network based on cli configuration and starts the network via flannel/network/manager.go#runNetwork().

In Manager.runNetwork(), it in turn calls Network.Run() to start the network. Network.Run() is the
main loop for this network (if there are multiple network, then network manager will call runNetwork()
multiple times). For this network, network manager calls runOnce which:

1. initialize the network with retry. Initialize the network is just getting config from etcd and call
   Backend.RegisterNetwork() to register the backend  network, aquire lease, etc, get backend network, etc;
2. after initialization, call a hook passed from network manager. The after initialization hook write
   out information to /var/run/flannel.env file;
3. call BackendNetwork.Run() to start the backend network (note, start the backend network, which is
   part of a backend, see above concept);
4. call subnet.WatchLease to watch for all lease changes of the network;
5. start a loop that handles lease changes from step 4, as well as regular renew (default is 1hr).

Most of the work is done via BackendNetwork.Run() and how it works depends on the type of backend
specified. The easiest is probably host-gw, which watches entire network leases and update host
routes accordingly. Note, network manager also watches network leases, but they have different
purposes, one for routes update and one for lease renew. There is also a sync loop in host-gw to make
sure routes are correct.

# Backends

## vxlan

vxlan is the most widely used flannel backend, see references for details. Note how flannel vxlan
handles L3 misses. A little bit background:
- L3 miss means network device (router, etc) can't find 'IP -> Mac' bindings.
- L2 miss means network device (switch, etc) can't find 'Mac -> Port' bindings.

Flannel daemon dynamically populates FDB and ARP table according to the kernel requests via the
'L2/L3 miss' notification machanism. In case of L3 miss, kernel asks flannel to populate local ARP
table when necessary instead of broadcasting ARP request packet. In case of L2 miss, kernel asks
flannel to populate FDB when necessary.

# Experiment

## Bring up a flannel

Bring up etcd, then build and run flannel

```
vagrant at vagrant-ubuntu-trusty-64 in ~
$ etcd
2017-05-17 05:47:40.967084 I | etcdmain: etcd Version: 3.1.7
2017-05-17 05:47:40.967138 I | etcdmain: Git SHA: 43b7507
2017-05-17 05:47:40.967144 I | etcdmain: Go Version: go1.7.5
2017-05-17 05:47:40.967148 I | etcdmain: Go OS/Arch: linux/amd64
...

$ etcdctl set /coreos.com/network/config  '{ "Network": "10.1.0.0/16", "Backend": { "Type": "vxlan", "VNI": 1 } }'
{ "Network": "10.1.0.0/16", "Backend": { "Type": "vxlan", "VNI": 1 } }

vagrant at vagrant-ubuntu-trusty-64 in ~/code/workspace/src/github.com/coreos/flannel on master!
$ sudo ./flannel -iface eth1 --ip-masq
I0517 05:50:25.870526 03367 main.go:126] Installing signal handlers
I0517 05:50:25.871637 03367 manager.go:163] Using 192.168.33.33 as external interface
I0517 05:50:25.871675 03367 manager.go:164] Using 192.168.33.33 as external endpoint
I0517 05:50:25.891750 03367 local_manager.go:179] Picking subnet in range 10.1.1.0 ... 10.1.255.0
I0517 05:50:25.895976 03367 ipmasq.go:47] Adding iptables rule: -s 10.1.0.0/16 -d 10.1.0.0/16 -j RETURN
I0517 05:50:25.900202 03367 ipmasq.go:47] Adding iptables rule: -s 10.1.0.0/16 ! -d 224.0.0.0/4 -j MASQUERADE
I0517 05:50:25.904306 03367 ipmasq.go:47] Adding iptables rule: ! -s 10.1.0.0/16 -d 10.1.0.0/16 -j MASQUERADE
I0517 05:50:25.909471 03367 manager.go:246] Lease acquired: 10.1.89.0/24
I0517 05:50:25.910016 03367 network.go:58] Watching for L3 misses
I0517 05:50:25.910857 03367 network.go:66] Watching for new subnet leases
```

To use flannel with docker, do "source /run/flannel/subnet.env" and pass them to docker daemon.

# References

- https://wangtaox.github.io/2016/07/29/flannel-vxlan.html
- https://www.slideshare.net/enakai/how-vxlan-works-on-linux

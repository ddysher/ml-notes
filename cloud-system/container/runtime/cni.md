<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
  - [Objective](#objective)
  - [Specification](#specification)
  - [Plugin API](#plugin-api)
  - [Workflow](#workflow)
  - [Example config](#example-config)
- [Plugins](#plugins)
  - [bridge](#bridge)
  - [flannel](#flannel)
- [CNI and Libnetwork](#cni-and-libnetwork)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

## Objective

The CNI (Container Network Interface) project consists of a specification and libraries for writing
plugins to configure network interfaces in Linux containers, along with a number of supported plugins.

CNI concerns itself only with network connectivity of containers and removing allocated resources
when the container is deleted. CNI defines a standard for container network interface and provides
networking facility for containers as a pluggable and extensible mechanism.

## Specification

https://github.com/containernetworking/cni/blob/master/SPEC.md

## Plugin API

Each CNI plugin is implemented as an executable that is invoked by the container management system
(e.g. rkt or Docker). For example, bridge plugin is similar to docker's bridge network mode. Apart
from CNI network plugin, there are also IPAM plugins which are responsible for IP assignment.

The CNI executable command-line API uses the type of network as the name of the executable to
invoke, e.g. bridge, ipvlan. It will then look for this executable in a list of predefined directories.
Once found, it will invoke the executable using predefined environment variables, e.g. CNI_VERSION,
CNI_COMMAND, CNI_CONTAINERID, etc.

## Workflow

- The cni interface calls the API of the cni plugin to set up container networking.
- The cni plugin is responsible for creating the network interface to the container.
- The cni plugin calls the ipam plugin to set up the IP address for the container.
- The cni plugin needs to implement an API for network creation and deletion.
- The plugin type and parameters are specified as a JSON file that the container runtime reads and sets up.
- Available cni plugins are bridge, macvlan, ipvlan, and ptp. Available ipam plugins are host-local
  and DHCP. cni plugins and the IPAM plugin can be used in any combination.
- External cni plugins such as flannel and weave are also supported. External plugins reuse the bridge
  plugin to set up the final networking.

## Example config

```
$ mkdir -p /etc/cni/net.d
$ cat >/etc/cni/net.d/10-mynet.conf <<EOF
{
    "name": "mynet",
    "type": "bridge",
    "bridge": "cni0",
    "isGateway": true,
    "ipMasq": true,
    "ipam": {
        "type": "host-local",
        "subnet": "10.22.0.0/16",
        "routes": [
            { "dst": "0.0.0.0/0" }
        ]
    }
}
EOF
$ cat >/etc/cni/net.d/99-loopback.conf <<EOF
{
    "type": "loopback"
}
EOF
```

# Plugins

There are many existing plugins in core cni repository. cni provides a package that can be easily
used by plugin authors.

## bridge

Bridge uses cni plugin package, netlink library to implement the bridge similar to that of docker bridge.

## flannel

flannel plugin is a meta plugin, it requires flannel daemon to be running, as well as a delegate
plugin. When flannel daemon is started, it outputs a `/run/flannel/subnet.env` file that looks like
this:


     FLANNEL_NETWORK=10.1.0.0/16
     FLANNEL_SUBNET=10.1.17.1/24
     FLANNEL_MTU=1472
     FLANNEL_IPMASQ=true

This information reflects the attributes of flannel network on the host. The flannel CNI plugin uses
this information to configure another CNI plugin, such as bridge plugin, e.g. flannel cni plugin
takes input with content like:

     {
       "name": "mynet",
       "type": "flannel"
     }

This is passed from stdin as specified in cni. flannel cni then generates another config file to
delegate plugin, e.g.

     {
       "name": "mynet",
       "type": "bridge",
       "mtu": 1472,
       "ipMasq": false,
       "isGateway": true,
       "ipam": {
         "type": "host-local",
         "subnet": "10.1.17.0/24"
       }
     }

Note, we didn't specify delegate plugin, flannel meta plugin defaults to bridge.

# CNI and Libnetwork

Refer to docker/network.md

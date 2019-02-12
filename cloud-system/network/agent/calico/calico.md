<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Architecture](#architecture)
  - [Felix](#felix)
  - [etcd](#etcd)
  - [confd](#confd)
  - [BGP Client (BIRD)](#bgp-client-bird)
  - [BGP Route Reflector (BIRD)](#bgp-route-reflector-bird)
  - [Orchestrator Plugin](#orchestrator-plugin)
  - [calicoctl (and 'calico/node' image)](#calicoctl-and-caliconode-image)
- [Kubernetes](#kubernetes)
  - [Normal installation](#normal-installation)
  - [Etcdless installation](#etcdless-installation)
- [Experiments](#experiments)
  - [Create calico cluster](#create-calico-cluster)
  - [Tasks](#tasks)
- [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Architecture

*Date: 04/13/2017, calico v2.1*

## Felix

[Felix](https://github.com/projectcalico/felix) is a daemon that runs on every machine that provides
endpoints: in most cases that means on nodes that host containers or VMs. It is responsible for
programming routes and ACLs, and anything else required on the host, in order to provide the desired
connectivity for the endpoints on that host. In particular, felix will ensure that the host responds
to ARP requests from each workload with the MAC of the host, and will enable IP forwarding for
interfaces that it manages. For more details, see reference documentation. Following is several
takeaways from reading felix code base and docs:

**syncer and calculation graph**

Felix starts background processing goroutines, which load and keep in sync with the state from the
datastore: the "calculation graph". In the following kubernetes integration part we'll see later, in
normal case, 'syncer' backend is etcd; in etcdless case, 'syncer' backend is kubernetes API, see
[here]( https://github.com/projectcalico/libcalico-go/tree/2c13cbb31b1aad738942517c46351bdd7cd64246/lib/backend).

From code comment:

```go
// Now create the calculation graph, which receives updates from the
// datastore and outputs dataplane updates for the dataplane driver.
//
// The Syncer has its own thread and we use an extra thread for the
// Validator, just to pipeline that part of the calculation then the
// main calculation graph runs in a single thread for simplicity.
// The output of the calculation graph arrives at the dataplane
// connection via channel.
//
// Syncer -chan-> Validator -chan-> Calc graph -chan->   dataplane
//        KVPair            KVPair             protobufs
```

**dataplane**

dataplanes are abstracted as managers, which implement an 'OnUpdate' method to send controls messages
(through netlink) to linux kernel. Example managers are endpointManager, policyManager, ipipManager,
etc. The main features used are linux route, iptables (+ipset).

**arp proxy**

From code comment:

```
// Enable proxy ARP, this makes the host respond to all ARP requests with its own
// MAC.  This has a couple of advantages:
//
// - In OpenStack, we're forced to configure the guest's networking using DHCP.
//   Since DHCP requires a subnet and gateway, representing the Calico network
//   in the natural way would lose a lot of IP addresses.  For IPv4, we'd have to
//   advertise a distinct /30 to each guest, which would use up 4 IPs per guest.
//   Using proxy ARP, we can advertise the whole pool to each guest as its subnet
//   but have the host respond to all ARP requests and route all the traffic whether
//   it is on or off subnet.
//
// - For containers, we install explicit routes into the containers network
//   namespace and we use a link-local address for the gateway.  Turing on proxy ARP
//   means that we don't need to assign the link local address explicitly to each
//   host side of the veth, which is one fewer thing to maintain and one fewer
//   thing we may clash over.
```

Proxy ARP is the technique in which one host, usually a router, answers ARP requests intended for
another machine. By "faking" its identity, the router accepts responsibility for routing packets to
the "real" destination. Proxy ARP can help machines on a subnet reach remote subnets without the need
to configure routing or a default gateway. Once enabled (e.g. through proc fs), linux proxy arp
answers all ARP requests with its own MAC address. In container deployments, Calico only uses proxy
ARP for resolving the 169.254.1.1 address.

The routing table inside the container ensures that all traffic goes via the 169.254.1.1 gateway so
that is the only IP that will be ARPed by the container.

**link local address**

In a Calico network, each host acts as a gateway router for the workloads that it hosts. In container
deployments, Calico uses 169.254.1.1 as the address for the Calico router. By using a link-local
address, Calico saves precious IP addresses and avoids burdoning the user with configuring a suitable
address.

While the routing table may look a little odd to someone who is used to configuring LAN networking,
using explicit routes rather than subnet-local gateways is fairly common in WAN networking. Calico
tries hard to avoid interfering with any other configuration on the host. Rather than adding the
gateway address (192.168.1.1) to the host side of each workload interface, Calico sets the 'proxy_arp'
flag on the interface. This makes the host behaves like a gateway, responding to ARPs for 169.254.1.1
without having to actually allocate the IP address to the interface.

From the following commands, we see that host interface `cali4c55fadc8ab@if5` has mac address `b6:0f:27:a6:57:17`
but no IP address. In corresponding container, we see that the container interface `cali0@if6` has
address `192.168.84.192/32` which is allocated from calico (also with fixed mac address `ee:ee:ee:ee:ee:ee`).
Gateway is `192.254.1.1` as mentioned above; using `ip neigh` shows the gateway mac address is
`b6:0f:27:a6:57:17`, which is exactly the mac address of `cali0@if6`.

```
vagrant@calico-01:~$ ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
2: enp0s3: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    link/ether 08:00:27:32:ed:09 brd ff:ff:ff:ff:ff:ff
    inet 10.0.2.15/24 brd 10.0.2.255 scope global enp0s3
       valid_lft forever preferred_lft forever
3: enp0s8: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    link/ether 08:00:27:ed:ae:3b brd ff:ff:ff:ff:ff:ff
    inet 172.17.8.101/24 brd 172.17.8.255 scope global enp0s8
       valid_lft forever preferred_lft forever
4: docker0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN group default
    link/ether 02:42:2b:cc:42:23 brd ff:ff:ff:ff:ff:ff
    inet 172.18.0.1/16 scope global docker0
       valid_lft forever preferred_lft forever
6: cali4c55fadc8ab@if5: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default
    link/ether b6:0f:27:a6:57:17 brd ff:ff:ff:ff:ff:ff link-netnsid 0
8: cali378282f6388@if7: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default
    link/ether 76:17:df:0e:68:df brd ff:ff:ff:ff:ff:ff link-netnsid 1
10: cali0d6c6e2d54d@if9: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default
    link/ether 66:59:3d:2a:3a:4e brd ff:ff:ff:ff:ff:ff link-netnsid 2

vagrant@calico-01:~$ docker exec -it workload-A sh
/ # ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue qlen 1
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
5: cali0@if6: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue
    link/ether ee:ee:ee:ee:ee:ee brd ff:ff:ff:ff:ff:ff
    inet 192.168.84.192/32 scope global cali0
       valid_lft forever preferred_lft forever
/ # ip r
default via 169.254.1.1 dev cali0
169.254.1.1 dev cali0
/ # ip neigh
169.254.1.1 dev cali0 lladdr b6:0f:27:a6:57:17 used 0/0/0 probes 1 STALE
/ # exit
```

## etcd

etcd is a distributed key-value store that has a focus on consistency. Calico uses etcd to provide
the communication between components and as a consistent data store, which ensures Calico can always
build an accurate network.

## confd

- https://github.com/kelseyhightower/confd
- https://github.com/projectcalico/confd

The confd templating engine monitors the etcd datastore for any changes to BGP configuration (and
some top level global default configuration such as AS Number, logging levels, and IPAM information).
Confd dynamically generates BIRD configuration files based on the data in etcd, triggered automatically
from updates to the data. When the configuration file changes, confd triggers BIRD to load the new
files. Calico uses a fork of the main confd repo which includes an additional change to improve
performance with the handling of watch prefixes.

Following is `confd` process in calico container created from `calico/node` image.

```
confd -confdir=/etc/calico/confd -interval=5 -watch --log-level=debug -node=http://172.17.8.101:2379 -client-key= -client-cert= -client-ca-keys=
```

## BGP Client (BIRD)

- http://bird.network.cz/
- https://github.com/osrg/gobgp
- https://github.com/projectcalico/calico-bird

Calico deploys a BGP client on every node that also hosts a Felix. The role of the BGP client is to
read routing state that Felix programs into the kernel and distribute it around the data center. In
Calico, this BGP component is most commonly BIRD, though any BGP client, such as GoBGP that can draw
routes from the kernel and distribute them is suitable in this role.

There are two BIRD processes running in the calico-node container. One for IPv4 (bird) and one for
IPv6 (bird6). Calico uses a fork of the main BIRD repo, to include an additionalfeature required for
IPIP support when running Calico in a cloud environment.

Following is `bird` processes in calico container created from `calico/node` image.

```
bird -R -s /var/run/calico/bird.ctl -d -c /etc/calico/confd/config/bird.cfg
bird6 -R -s /var/run/calico/bird6.ctl -d -c /etc/calico/confd/config/bird6.cfg
```

## BGP Route Reflector (BIRD)

For larger deployments, simple BGP can become a limiting factor because it requires every BGP client
to be connected to every other BGP client in a mesh topology. This requires an increasing number of
connections that rapidly become tricky to maintain, due to the N^2 nature of the increase. For that
reason, in larger deployments, Calico will deploy a BGP route reflector. This component, commonly used
in the Internet, acts as a central point to which the BGP clients connect, preventing them from needing
to talk to every single BGP client in the cluster. For redundancy, multiple BGP route reflectors can
be deployed seamlessly.

The route reflectors are purely involved in the control of the network: no endpoint data passes through
them. In Calico, this BGP component is also most commonly BIRD, configured as a route reflector rather
than as a standard BGP client. http://docs.projectcalico.org/v2.0/usage/bird-rr-config

## Orchestrator Plugin

**overview**

- https://github.com/projectcalico/libnetwork-plugin
- https://github.com/projectcalico/cni-plugin
- https://github.com/openstack/networking-calico

There are separate plugins for each major cloud orchestration platform (e.g. openstack, kubernetes).
This actually narrows down to Neutron ML2, CNI, CNM. The orchestrator will inevitably have its own
set of APIs for managing networks.

The orchestrator plugin's primary job is to translate those APIs into Calico's data-model and then
store it in Calico's datastore.

**libnetwork-plugin**

In libnetwork-plugin, CreateNetwork checks network parameters, it doesn't do any more setups.
CreateEndpoint checks parameters (requested IP address, etc), and record it in backend (etcd). Join
will create veth pair: The one end will stay in the host network namespace - named caliXXXXX; The
other end is given a temporary name. It's moved into the final network namespace by libnetwork
itself. Note that the communication between libnetwork-plugin and other calico components are through
etcd, i.e. when we record endpoint (or profile) information to etcd, felix will receive updates and
does network setup accordingly.

**cni-plugin**

Similarly, cni-plugin will do network setup according to cni spec. Per spec, instead of multiple steps
(CreateNetwork, CreateEndpoint, Join, etc), in cni, only CmdAdd is required. Therefore, cni-plugin will
do the above setups at once (including create veth, record endpoint creation/update, etc), plus a few
more steps, like calling ipam plugin.

From code comment:

```go
if endpoint != nil {
  // There is an existing endpoint - no need to create another.
  // This occurs when adding an existing container to a new CNI network
  // Find the IP address from the endpoint and use that in the response.
  // Don't create the veth or do any networking.
  // Just update the profile on the endpoint. The profile will be created if needed during the
  // profile processing step.
  ...
} else {
  // There's no existing endpoint, so we need to do the following:
  // 1) Call the configured IPAM plugin to get IP address(es)
  // 2) Configure the Calico endpoint
  // 3) Create the veth, configuring it on both the host and container namespace.
  ...
}
```

**k8s-policy**

- https://github.com/projectcalico/k8s-policy

The controller watches kubernetes networkpolicy, pods, namespaces; processes and stores them as
calico policy definition for calico/node to read. k8s-policy controller and calico/node (felix)
use the same etcd cluster. Note, as we'll see in the following `Etcdless installation` approach,
felix will directly list/watch kubernetes for networkpolicy (pod, namespace, etc). Therefore, in
such setup, k8s-policy component is not needed; policy enforcement is done in felix.

## calicoctl (and 'calico/node' image)

- https://github.com/projectcalico/calicoctl

The command line interface for calico. calicoctl repostiory also contains the Dockerfile for `calico/node`
along with various configuration files that are used to configure and "glue" these components together.
'calico/node' image can be regarded as a helper container that bundles together the various components
required for networking containers with Calico. The key components are: Felix, BIRD, confd. In addition,
calico uses runit for logging (svlogd) and init (runsv) services. Note that the 'calico/node' may be
run in policy only mode in which Felix runs, but both BIRD and confd are removed. This provides policy
management without route distribution between hosts. This mode can be enabled by setting the environment
variable `CALICO_NETWORKING=false` before starting the node with calicoctl node run.

# Kubernetes

*Date: 04/13/2017, calico v2.1*

## Normal installation

- http://docs.projectcalico.org/v2.0/getting-started/kubernetes/installation/integration
- http://docs.projectcalico.org/v2.0/getting-started/kubernetes/installation/hosted/hosted

There are multiple install methods for calico, a normal installation need the following components:
- calico/node: this is the above mentioned core calico component, which contains felix, bird, etc; it
  should run on all master/nodes. Note in normal case, calico/node requires a etcd cluster; it can
  share the etcd cluster in kubernetes.
- calico-cni: i.e. cni-plugin. calico-cni bridges between kubernetes and calico. In manual installation,
  we put 'calico', 'calico-ipam' under '/opt/cni/bin', as well as configurations (under 'etc/cni/net.d').
  In hosted installation, a container 'calico-cni' is used to install the binaries/configs, then sleep
  forever. Therefore, there is no such process named 'calico-cni', in hosted installation, a endless
  sleep is used to prevents Kubernetes from restarting the pod repeatedly.
- policy-controller, i.e. k8s-policy. As mentioned above, this is a controller running in kubernetes to
  translate kubernetes API object to calico policy in order to enforce network policy.

## Etcdless installation

- http://docs.projectcalico.org/v2.0/getting-started/kubernetes/installation/hosted/k8s-backend/

Etcdless installation is a way to install calico without requiring an etcd cluster. Calico typically
uses etcd to store information about Kubernetes Pods, Namespaces, and NetworkPolicies. This information
is populated to etcd by the Calico CNI plugin and policy controller, and is interpreted by Felix and
BIRD to program the dataplane on each host in the cluster. The above manifest deploys Calico such that
Felix uses the Kubernetes API directly to learn the required information to enforce policy, removing
Calico's dependency on etcd and the need for the Calico kubernetes policy controller. The Calico CNI
plugin is still required to configure each pod's virtual ethernet device and network namespace.

There are a few limitations in etcdless installation:
- Calico without etcd performs policy enforcement only and does not yet support Calico BGP networking.
- Calico without etcd does not yet support Calico IPAM. It is recommended to use host-local IPAM in conjunction with Kubernetes pod CIDR assignments.
- Calico without etcd does not yet support the full set of calicoctl commands.

Etcdless installation is commonly used in canal project; where calico is only used to enforce policy,
while flannel (with vxlan) is used to provide container connectivity. In this setup, we'll need to
disable calico bgp networking by setting `CALICO_NETWORKING_BACKEND` environment variable to 'none'.

# Experiments

*Date: 04/13/2017, calico v2.1*

## Create calico cluster

Follow official doc to start a ubuntu cluster:
- http://docs.projectcalico.org/v2.0/getting-started/docker/installation/vagrant-ubuntu/

Apart from starting etcd, etc, it is easy to start a calico cluster: just download 'calicoctl' and
run `calicoctl node run`. The later command will run a node container using image "calico/node:v1.0.2";
the container contains most components mentioned above, including felix, bird, plugin, etc, see below.

```
/ # ps aux
PID   USER     TIME   COMMAND
    1 root       0:00 /sbin/runsvdir -P /etc/service/enabled
   79 root       0:00 runsv libnetwork
   80 root       0:00 runsv bird6
   81 root       0:00 runsv confd
   82 root       0:00 runsv bird
   83 root       0:00 runsv felix
   84 root       0:00 svlogd -tt /var/log/calico/bird
   85 root       0:00 bird -R -s /var/run/calico/bird.ctl -d -c /etc/calico/confd/config/bird.cfg
   86 root       0:00 svlogd /var/log/calico/confd
   87 root       0:00 confd -confdir=/etc/calico/confd -interval=5 -watch --log-level=debug -node=http://172.17.8.101:2379 -client-key= -
   88 root       0:00 svlogd -tt /var/log/calico/bird6
   89 root       0:00 bird6 -R -s /var/run/calico/bird6.ctl -d -c /etc/calico/confd/config/bird6.cfg
   90 root       0:00 svlogd /var/log/calico/felix
   91 root       0:01 calico-felix
   92 root       0:00 svlogd /var/log/calico/libnetwork
   93 root       0:00 libnetwork-plugin
  116 root       0:00 calico-iptables-plugin
  117 root       0:00 calico-iptables-plugin
  266 root       0:00 sh
  278 root       0:00 ps aux
```

## Tasks

- http://docs.projectcalico.org/v2.0/getting-started/docker/tutorials/simple-policy
- http://docs.projectcalico.org/v2.0/getting-started/docker/tutorials/advanced-policy

# References

- http://docs.projectcalico.org/v2.0/reference/architecture/
- http://docs.projectcalico.org/v2.0/reference/repo-structure
- https://github.com/projectcalico/calico/blob/a0198d69642555190bb5bbd314ed9609be42c30d/master/usage/troubleshooting/faq.md

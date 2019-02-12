<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Pod Networking (Routes controller)](#pod-networking-routes-controller)
- [Service Proxy (Services controller)](#service-proxy-services-controller)
- [Network Policy (Policy controller)](#network-policy-policy-controller)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

- *Date: 05/14/2017, v0.0.1*
- *Date: 10/07/2018, v0.2.0*

[kube-router](https://github.com/cloudnativelabs/kube-router) is a distributed load balancer,
firewall and router for Kubernetes. Kube-router can be configured to provide on each cluster node:
- a IPVS/LVS based service proxy on each node for ClusterIP and NodePort service types, providing
  service discovery and load balancing
- an ingress firewall for pods running on the node as per defined Kubernetes network policies using
  iptables and ipset
- a BGP router to advertise and learn the routes to the pod IP's for cross-node pod-to-pod connectivity

Therefore, Kube-router can ben seens as a replacement for kube-proxy, calico, flannel etc. However,
it doesn't integrate with ingress right now.

*References*
- https://github.com/cloudnativelabs/kube-router/blob/v0.2.0/docs

# Pod Networking (Routes controller)

kube-router handles Pod networking efficiently with direct routing thanks to the BGP protocol and
the GoBGP Go library. It uses the native Kubernetes API to maintain distributed pod networking state.
That means no dependency on a separate datastore to maintain in your cluster.

kube-router's elegant design also means there is no dependency on another CNI plugin. The official
`bridge` plugin provided by the CNI project is all you need. Using [GoBGP](https://github.com/osrg/gobgp)
also means we don't need any external BGP agent.

Kube-router is expected to run on each node. Subnet of the node is learnt by kube-router from the
CNI configuration file on the node or through the `node.PodCidr`. Each kube-router instance on the
node acts a BGP router and advertise the pod CIDR assigned to the node. Each node peers with rest
of the nodes in the cluster forming full mesh. Learned routes about the pod CIDR from the other
nodes (BGP peers) are injected into local node routing table. On the data path, inter node pod-to-pod
communication is done by routing stack on the node.

# Service Proxy (Services controller)

kube-router uses the Linux kernel's LVS/IPVS features to implement its K8s Services Proxy. Kube-router
fully leverages power off LVS/IPVS to provide rich set of scheduling options and unique features like
DSR (Direct Server Return), L3 load balancing with ECMP for deployments where high throughput, minimal
latency and high-availability are crucial.

*References*
- https://cloudnativelabs.github.io/post/2017-05-10-kube-network-service-proxy/

# Network Policy (Policy controller)

Network policy controller provides an ingress firewall for the pods as per the defined network
policies. It uses ipsets with iptables to ensure your firewall rules have as little performance
impact on your cluster as possible.

Kube-router supports the `networking.k8s.io/NetworkPolicy` API or network policy V1/GA semantics and
also network policy beta semantics. Below is a few important points based on the above blog post and
project homepage.

Each pod running on the node whose default ingress policy is to deny the traffic gets a pod specific
chian. Example chain name is `KUBE-POD-FW-xxx`; the last part is hash of namespacee plus pod name.
Note that only pod has default ingress policy set to `deny` has pod specific chain. In the following
example, `10.1.3.104` is the address of a pod, which satisfy the condition. This means we have an
ingress resource selecting it, via `networkPolicy.Spec.PodSelector` in kubernetes.

There are different communication patterns in kubernetes, e.g. pod to pod on the same node (and
different node), pod to service on the same node (and different node), etc. kube-router adds rules
in FORWARD and OUTPUT chain so that traffic destinated to another pod will be caught and send to
pod specific iptables chain.
```
-A FORWARD -d 10.1.3.104/32 -m physdev --physdev-is-bridged -j KUBE-POD-FW-2DVC47KBKHHM5TXB
-A FORWARD -d 10.1.3.104/32 -j KUBE-POD-FW-2DVC47KBKHHM5TXB
-A OUTPUT  -d 10.1.3.104/32 -j KUBE-POD-FW-2DVC47KBKHHM5TXB
```

Based on kube-route README, the three rules match the following conditions:
- traffic getting switched between the pods on the same node through bridge
- traffic getting routed between the pods on different nodes
- traffic originating from a pod and going through the service proxy and getting routed to pod on same node

Note for the last case, `-d` option still uses pod IP not service IP, since we already changed
service IP to pod IP. In kube-router, this is done using ipvs masq. In kube-proxy, this is nat in
OUTPUT chain; that is, in kube-proxy, when pod sends traffic to a service, packet will be sent to
OUTPUT chain, where kube-proxy has rules to DNAT it to real pod IP: this happens before the last
rule in the above example. In the pod FW chain, we'll see rules as follows:
```
-A KUBE-POD-FW-2DVC47KBKHHM5TXB -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A KUBE-POD-FW-2DVC47KBKHHM5TXB -j KOBE-NWPLCY-53UF3AYLTFB3U2WC
-A KUBE-POD-FW-2DVC47KBKHHM5TXB -j REJECT --reject-with icmp-port-unreachable
```

Each pod specific firewall chain has default rule to block the traffic. Rules are added to jump
traffic to the network policy specific policy chains. Rules cover only policies that apply to the
destination pod ip. A rule is added to accept the established traffic to permit the return traffic.
In the above example, only one network policy applies to destination IP `10.1.3.104`, so there is
only one in the middle; if there are more, we'll see something like this:
```
-A KUBE-POD-FW-2DVC47KBKHHM5TXB -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A KUBE-POD-FW-2DVC47KBKHHM5TXB -j KOBE-NWPLCY-53UF3AYLTFB3U2WC
-A KUBE-POD-FW-2DVC47KBKHHM5TXB -j KOBE-NWPLCY-JFIO2EJWOI3HEFJE
-A KUBE-POD-FW-2DVC47KBKHHM5TXB -j KOBE-NWPLCY-JIEOJ8JFO1FJEF3K
-A KUBE-POD-FW-2DVC47KBKHHM5TXB -j REJECT --reject-with icmp-port-unreachable
```

Each network policy has an iptable chain, which has rules expressed through ipsets matching source
and destination pod ip's. Example chain name is: `KUBE-NWPLCY-XXX`, the last part is hash of namespace
plus policy name. Note there is also source ipset chain, i.e. `KUBE-SRC-XXX`, where the last part is
namesapce plus policy name plus ingress rule number (since we can have multiple ingress rule per
ingress resource in kubernetes). Similarly, there is the destination ipset chain, i.e. `KUBE-DST-XXX`,
where the last part is namspace plus policy name. Continuing the above example, we'll have:
```
-A KUBE-NWPLCY-53UF3AYLTFB3U2WC -p tcp -m set --match-set KUBE-SRC-R3V4H2RP5PLYAJKA src -m set --match-set KUBE-DST-53UF3AYLTFB3U2WC dst -m tcp --dport 6379 -j ACCEPT
```

Look a look at ipset, we'll see roughly the following. Note `10.1.3.104` is in the `KUBE-DST-xxxx`
chain.

```
# ipset --list
Name: KUBE-DST-53UF3AVLTFB3U2WC
Type: hash:ip
...
Members:
10.1.3.104 timeout 0
10.1.1.190 timeout 0
10.1.2.4 timeout 0

Name: KUBE-SRC-R3V4H2RP5PLYAJKA
type: hash:ip
...
Members:
10.1.2.138 timeout 8
10.1.1.191 timeout 0
10.1.3.105 timeout 0
```

*References*
- https://cloudnativelabs.github.io/post/2017-05-1-kube-network-policies/

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [KEPs](#keps)
  - [20180101 - pod-ready++](#20180101---pod-ready)
  - [20180101 - ipvs based service](#20180101---ipvs-based-service)
  - [20180101 - node-local dns cache](#20180101---node-local-dns-cache)
  - [20181024 - topology-aware service routing](#20181024---topology-aware-service-routing)
  - [20190125 - ingress api group](#20190125---ingress-api-group)
  - [20190423 - service lb finalizer](#20190423---service-lb-finalizer)
  - [20190603 - endpointslice api](#20190603---endpointslice-api)
  - [20191227 - app protocol](#20191227---app-protocol)
- [Feature & Design](#feature--design)
  - [(large) networking](#large-networking)
  - [(large) kubernetes dns specification](#large-kubernetes-dns-specification)
  - [(large) network policy](#large-network-policy)
  - [(medium) command execution portforwarding](#medium-command-execution-portforwarding)
  - [(medium) external source ip preservation](#medium-external-source-ip-preservation)
  - [(small) service external name](#small-service-external-name)
  - [(small) traffic shaping with kubenet and cni](#small-traffic-shaping-with-kubenet-and-cni)
  - [(small) configurable nodeport ip range](#small-configurable-nodeport-ip-range)
  - [(small) configurable resolv.conf](#small-configurable-resolvconf)
  - [(small) hostname alias](#small-hostname-alias)
  - [(deprecated) node-local service](#deprecated-node-local-service)
  - [(deprecated) full service discovery](#deprecated-full-service-discovery)
- [Implementation](#implementation)
  - [how ip-per-pod works](#how-ip-per-pod-works)
  - [how service with udp proxy works](#how-service-with-udp-proxy-works)
  - [how dns works v1](#how-dns-works-v1)
  - [how dns works v2](#how-dns-works-v2)
  - [how dns works v3, with coredns](#how-dns-works-v3-with-coredns)
  - [how network related controllers works](#how-network-related-controllers-works)
  - [how network plugin works](#how-network-plugin-works)
  - [how cluster cidr subnet manager works in flannel](#how-cluster-cidr-subnet-manager-works-in-flannel)
  - [how pod hostname/subdomain works](#how-pod-hostnamesubdomain-works)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

> A collection of proposals, designs, features in Kubernetes network.

- [SIG-Network KEPs](https://github.com/kubernetes/enhancements/blob/master/keps/sig-network)
- [SIG-Network Proposals](https://github.com/kubernetes/community/blob/master/contributors/design-proposals/network)
- [SIG-Network Community](https://github.com/kubernetes/community/tree/master/sig-network)

# KEPs

## 20180101 - pod-ready++

- *Date: 09/07/2018, v1.11*
- *Date: 06/16/2019, v1.14, stable*

The proposal extends pod readiness with extension points to allow more readiness checks. For
example, a pod won't be considered ready if related service or ingress rules are not setup
properly.

In the following official example, two additional conditions are used to determine pod readiness.
External controllers responsible for maintaining the two features are required to update the
conditions. For example, if `feature-1` is network policy, then network policy controller should
update the condition to "True" if network policy for the pod is setup.

```yaml
Kind: Pod
…
spec:
  readinessGates:
  - conditionType: www.example.com/feature-1
  - conditionType: www.example.com/feature-2
…
status:
  conditions:
  - lastProbeTime: null
    lastTransitionTime: 2018-01-01T00:00:00Z
    status: "False"
    type: Ready
  - lastProbeTime: null
    lastTransitionTime: 2018-01-01T00:00:00Z
    status: "False"
    type: www.example.com/feature-1
  - lastProbeTime: null
    lastTransitionTime: 2018-01-01T00:00:00Z
    status: "True"
    type: www.example.com/feature-2
  containerStatuses:
  - containerID: docker://xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    ready : true
…
```

**Alternatives**

- Fix the workloads: there are a lot of workloads and many 3rd party workloads as well, which
  do not care about resources other than Pods, etc.
- Extend container readiness: container readiness is tied to low level constructs such as runtime

*References*

- [pod ready KEP link](https://github.com/kubernetes/enhancements/blob/1bad2ecb356323429a6ac050f106af4e1e803297/keps/sig-network/0007-pod-ready%2B%2B.md)

## 20180101 - ipvs based service

- *Date: 05/18/2017*
- *Date: 06/08/2017, v1.6, design*
- *Date: 07/09/2018, v1.11, stable*

Notes on ipvs implementation:
- For in cluster service, a dummy interface (called `kube-ipvs0`) will be created on each host and
  all service cluster IPs will be attached to the dummy interface. An ipvs virtual service will be
  created for each kubernetes service ip + port + protocol combination, with each kubernetes endpoint
  as ipvs real server.
- For node port, the same applies except: 1. ipvs service ip is the node ip. 2. dummy interface is not used.
- For service external ip, it's similar to node ip: ipvs service ip is the external ip.
- For loadbalacner type, same as external ip.
- For node local type, ipvs will do the same as iptables, i.e. just forward local endpoints.

*References*

- [ipvs proxier KEP link](https://github.com/kubernetes/enhancements/blob/master/keps/sig-network/0011-ipvs-proxier.md)
- https://github.com/kubernetes/community/pull/692
- https://kubernetes.io/blog/2018/07/09/ipvs-based-in-cluster-load-balancing-deep-dive/

## 20180101 - node-local dns cache

- *Date: 09/15/2019, v1.15, alpha*
- *Date: 03/31/2020, v1.18, stable*

This KEP aims to improve DNS performance by running a dns caching agent on all cluster nodes as a
Daemonset. After running the Daemonset, Pod will talk to local dns instead of kube-dns server for
DNS query. The choice of local dns server is also CoreDNS. The KEP has more detailed motivations,
following is a quick summary.

First of all, a new Daemonset is created, which is running in hostNetwork and contains a single
node-cache container (CoreDNS). All DNS queries will go through the cache agent. The agent will
query cluster kube-dns in case of cache misses in cluster's configured DNS suffix and for all
reverse lookups (in-addr.arpa and ip6.arpa).

```shell
$ kubectl get ds -n kube-system
NAME             DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR   AGE
node-local-dns   1         1         1       1            1           <none>          105m

$ kubectl exec -it -n kube-system node-local-dns-brpzt -c node-cache sh
# cat /etc/coredns/Corefile
cluster.local:53 {
    errors
    cache {
        success 9984 30
        denial 9984 5
    }
    reload
    loop
    bind 169.254.20.10
    forward . 10.0.0.10 {
        force_tcp
    }
    prometheus :9253
    health 169.254.20.10:8080
}
in-addr.arpa:53 {
    errors
    cache 30
    reload
    loop
    bind 169.254.20.10
    forward . 10.0.0.10 {
        force_tcp
    }
    prometheus :9253
}
ip6.arpa:53 {
    errors
    cache 30
    reload
    loop
    bind 169.254.20.10
    forward . 10.0.0.10 {
        force_tcp
    }
    prometheus :9253
}
.:53 {
    errors
    cache 30
    reload
    loop
    bind 169.254.20.10
    forward . /etc/resolv.conf {
        force_tcp
    }
    prometheus :9253
}
```

The daemonset will create a dummy interface and assign a link local address:

```shell
$ ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: enp2s0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 4c:ed:fb:c8:ae:e0 brd ff:ff:ff:ff:ff:ff
    inet 192.168.50.179/24 brd 192.168.50.255 scope global enp2s0
       valid_lft forever preferred_lft forever
    inet6 fe80::4eed:fbff:fec8:aee0/64 scope link
       valid_lft forever preferred_lft forever
...
34: nodelocaldns: <BROADCAST,NOARP> mtu 1500 qdisc noop state DOWN group default
    link/ether 9a:1b:f8:ce:4e:0a brd ff:ff:ff:ff:ff:ff
    inet 169.254.20.10/32 brd 169.254.20.10 scope global nodelocaldns
       valid_lft forever preferred_lft forever
...
```

Since daemonset runs in hostNetwork, we'll be able to query cluster DNS using the link local address:

```
# inside host
$ nslookup kubernetes.default.svc.cluster.local 169.254.20.10
Server:		169.254.20.10
Address:	169.254.20.10#53

Name:	kubernetes.default.svc.cluster.local
Address: 10.0.0.1
```

Kubelet is started with config `--cluster-dns=169.254.20.10`, which means Pod will have following
resolve.conf:

```shell
# inside a pod container
root@nginx:/# cat /etc/resolv.conf
nameserver 169.254.20.10
search default.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
```

At last, iptables NOTRACK rules are added for connections to and from the nodelocal dns IP. As
mentioned in motivation section, skipping iptables DNAT and connection tracking will help reduce
conntrack races and avoid UDP DNS entries filling up conntrack table.

```shell
$ sudo iptables-save | grep -C 15 NOTRACK
# Generated by iptables-save v1.6.1 on Sun Sep 15 19:51:37 2019
*raw
:PREROUTING ACCEPT [423:65951]
:OUTPUT ACCEPT [403:63154]
-A PREROUTING -d 169.254.20.10/32 -p udp -m udp --dport 53 -j NOTRACK
-A PREROUTING -d 169.254.20.10/32 -p tcp -m tcp --dport 53 -j NOTRACK
-A OUTPUT -s 169.254.20.10/32 -p udp -m udp --sport 53 -j NOTRACK
-A OUTPUT -s 169.254.20.10/32 -p tcp -m tcp --sport 53 -j NOTRACK
...
```

**Graduation to Beta**

To move node-local dns to beta, the above KEP needs to be improved to provide HA setup, that is, in
case of node-local dns agent failure, DNS query should continue to work.

The KEP proposes the following:
- Node-local dns caching agent listens to two addresses: 169.254.20.10 and kube-dns Service IP (e.g. 10.0.0.10).
- Kubelet uses kube-dns Service IP instead of 169.254.20.10, i.e. `--cluster-dns=10.0.0.10`.
- Add a new node-local-dns Service, which also selects kube-dns endpoints (actually almost identical
  to kube-dns Service specification). IP address of this new Service (e.g. 10.0.0.50) will be set to
  upstream of the node-local-dns Pod, i.e. `forward . 10.0.0.50 { ... }` in Corefile.
- Now the most important part: use NOTRACK rule to provide failover from node-local dns to kube-dns.
  The rule here is `-d 10.0.0.10 --dport 53 -j NOTRACK`. Here is how it works: recall that Kubernetes
  uses DNAT to change service IP to endpoint IP. If the rule doesn't exist, then everything works as
  before, i.e. Pod query goes to 10.0.0.10, then NATed to kube-dns Pod. If the rule exists, then
  contrack is disabled and the request will go to node-local dns agent, since it listens on this
  address.

There is a few caveats:
- An external agent must query for dns records on 169.254.20.10:53 and follow some threshold to either
  install or remove the NOTRACK rules.
- The proposal only works in kube-proxy iptables mode.

**Alternatives**

- When topology-aware service routing is available, node-local dns agent can leverage that feature.
- Running kube-dns as Daemonset will consume too many resources.
- For HA setup, adding multiple DNS server entries in `resolv.conf` doesn't always work because
  client behavior is unpredictable, e.g. it may send DNS queries to all DNS servers.

*References*

- [node-local dns cache KEP link](https://github.com/kubernetes/enhancements/blob/8e70bb6d374f911e87c2f6e1fa31ec80f12451b5/keps/sig-network/0030-nodelocal-dns-cache.md)
- [node-local dns cache to beta KEP link](https://github.com/kubernetes/enhancements/blob/8e70bb6d374f911e87c2f6e1fa31ec80f12451b5/keps/sig-network/20190424-NodeLocalDNS-beta-proposal.md)
- https://strongarm.io/blog/linux-stateless-firewall/
- https://distracted-it.blogspot.com/2015/05/iptables-firewall-rules-for-busy.html

## 20181024 - topology-aware service routing

- *Date: 06/23/2019, v1.15, design*
- *Date: 06/23/2019, v1.17, alpha*

Topology-aware service routing allows routing of service endpoints based on user specified topology,
instead of randomly choosing service endpoints. The KEP proposes two API changes:
- Add `topologyKeys:string` field to Service Spec.
- Add a new API object `PodLocator` (not finalized yet in v1.15).

And three component changes:
- Add `PodLocator Controller`: populate PodLocator object.
- Kube-proxy change: understand topology and program iptables/ipvs rules accordingly.
- DNS change: understand topology and write headless A record accordingly.

For example, the following API defines a service where local endpoints are preferred; if not found,
then use endpoints in the same zone (with the client). If still not found, then it will fail the
request.

```yaml
kind: Service
metadata:
  name: service-local
spec:
  topologyKeys: ["kubernetes.io/hostname", "topology.kubernetes.io/zone"]
```

The `PodLocator` is a new API to locate Pod: each Pod will have a corresponding `PodLocator`. The
primary reason for having the API is to make pod/node topology information more discoverable. Any
component interested in Pod topology just need to watch `PodLocator` and act accordingly, instead
of watching all Pods and Nodes. A PodLocator Controller will be added to keep `PodLocator` updated.

```go
// PodLocator represents information about where a pod exists in arbitrary space.  This is useful for things like
// being able to reverse-map pod IPs to topology labels, without needing to watch all Pods or all Nodes.
type PodLocator struct {
    metav1.TypeMeta
    // +optional
    metav1.ObjectMeta

    // NOTE: Fields in this resource must be relatively small and relatively low-churn.

    IPs []PodIPInfo // being added for dual-stack support
    NodeName string
    NodeLabels map[string]string
}
```

*Original design on 03/03/2018, v1.9*

The proposal aims to solve a couple of issues, including the above node-local service design, by
providing a new `ServicePolicy` API. Users can specify routing policy, for example, when a pod
accssing the service, only route traffic to the node, or rack, or zone, where the pod is running.
The policy generalizes node local to any user defined topology. The feature is in design phase.
For example, the following example creates a service policy which restrict all traffic to service
with label `app:bar` will be routed only to backends that satisfy both same region and same switch
as kube-proxy:

```yaml
kind: ServicePolicy
metadata:
  name: service-policy-example-1
  namespace: foo
spec:
  serviceSelector:
    matchLabels:
      app: bar
  topology:
    key: kubernetes.io/region
    mode: required
---
kind: ServicePolicy
metadata:
  name: service-policy-example-2
  namespace: foo
spec:
  serviceSelector:
    matchLabels:
      app: bar
  topology:
    key: kubernetes.io/switch
    mode: required
```

The proposal is moved to KEP, and `ServicePolicy` is removed due to its complexity.

*References*

- [topology-aware service routing KEP link](https://github.com/kubernetes/enhancements/blob/6861b7279948db44b58b8056450bc45102ea60bb/keps/sig-network/0033-service-topology.md)
- https://github.com/kubernetes/enhancements/issues/536
- https://github.com/kubernetes/community/pull/1551

## 20190125 - ingress api group

- *Date: 12/09/2019, v1.17, beta*

Ingress has been in beta status for many years, and is the last API that's not migrated from
extension API group to its own API group. The General goal of the KEP is to:
- move ingress from extension API group to networking API group
- graduate the Ingress API with bug fixes to GA

For the purpose, the KEP includes a bunch of changes:
- Add path as a prefix and make regex support optional, i.e. `ingress.spec.rules.http.paths.pathType`
  with values set to one of `ImplementationSpecific`, `Exact` and `Prefix`.
- Fix API field naming: `spec.backend` should be called `spec.defaultBackend`.
- Hostname wildcard matching, i.e. `spec.rules.host` supports wildcard matching.
- Formalize the Ingress class annotation into a field and an associated `IngressClass` resource.
- Add support for non-Service Backend types, i.e. `ingress.spec.backend.resource`.

*References*

- [ingress API group KEP link](https://github.com/kubernetes/enhancements/blob/c71c21d2f0f4875ce8f84663190c61bd2beb64e2/keps/sig-network/20190125-ingress-api-group.md)
- https://github.com/kubernetes/enhancements/issues/758

## 20190423 - service lb finalizer

- *Date: 11/03/2019, v1.16, beta*
- *Date: 12/09/2019, v1.17, stable*

The KEP is simple: a finalizer is added to service with `type=LoadBalaner`, to ensure cloud resources
are deleted before Service object is removed from Kubernetes. The finalizer logic is implemented in
service controller.

It's important to note that the finalizer takes place not just when Service is being deleted, it also
takes effect when updating Service from `type=LoadBalancer` to other types.

Upgrade is easy: upon starting new service-controller, it will add the finalizer to all existing
Services with `type=LoadBalancer`. For downgrade, there is compatibility issue between different
versions of Kubernetes. If a cluster is downgraded from a newer Kubernetes, and there are Services
with the finalizer, then such Services can never be deleted since there's no service lb finalizer in
previous Kubernetes. The KEP includes a "removal logic" that can remove service finalizer, but if
it's a n+2 upgrade, then users have to remove the finalizer themselves.

*References*

- [service lb finalizer KEP link](https://github.com/kubernetes/enhancements/blob/c71c21d2f0f4875ce8f84663190c61bd2beb64e2/keps/sig-network/20190423-service-lb-finalizer.md)

## 20190603 - endpointslice api

- *Date: 09/22/2019, v1.16, alpha*
- *Date: 03/30/2020, v1.18, beta*

In current endpoint API, one `Endpoint` object contains all individual endpoints of a `Service`.

```go
// Endpoints is a collection of endpoints that implement the actual service.  Example:
//   Name: "mysvc",
//   Subsets: [
//     {
//       Addresses: [{"ip": "10.10.1.1"}, {"ip": "10.10.2.2"}],
//       Ports: [{"name": "a", "port": 8675}, {"name": "b", "port": 309}]
//     },
//     {
//       Addresses: [{"ip": "10.10.3.3"}],
//       Ports: [{"name": "a", "port": 93}, {"name": "b", "port": 76}]
//     },
//  ]
```

However, this leads to performance problems in Kubernetes. Whenever a single pod in a service is
added/updated/deleted, the whole Endpoints object (even when the other endpoints didn't change) is
re-computed, written to storage (etcd) and sent to all watchers (e.g. kube-proxy). In addition,
etcd maximum storage size (1.5MB) limits the number of endpoints a service can have (around 5000
endpoints).

The new EndpointSlice API aims to:
- address existing performance problems
- leave room for future extension, e.g.
  - IPv4/IPv6 dual stack, stored in EndpointSlice.Endpoints[].Addresses
  - dynamic endpoints subsetting, i.e. assign partial list of endpoints to a group of nodes,
    instead of distributing all endpoints to all nodes

Now with EndpointSlice, one Service will map to multiple EndpointSlice. By default, the maximum
number of endpoints per EndpointSlice is 100, with configurable range from 1 to 1000.

The new API (alpha) is written in a new API group `discovery`. Following is a short digest:

```go
type EndpointSlice struct {
	metav1.TypeMeta
	metav1.ObjectMeta
	AddressType *AddressType
	Endpoints   []Endpoint
	Ports       []EndpointPort
}

// AddressType represents the type of address referred to by an endpoint.
type AddressType string

const (
	AddressTypeIP = AddressType("IP")
)

// Endpoint represents a single logical "backend" implementing a service.
type Endpoint struct {
	Addresses []string
	Conditions EndpointConditions
	Hostname *string
	TargetRef *api.ObjectReference
	Topology map[string]string
}

// EndpointConditions represents the current condition of an endpoint.
type EndpointConditions struct {
	Ready *bool
}

// EndpointPort represents a Port used by an EndpointSlice.
type EndpointPort struct {
	Name *string
	Protocol *api.Protocol
	Port *int32
}
```

Note that:
- similar to Endpoint, port information is not part of the endpoint struct; endpoints with the same
  port information should be grouped into the same endpointslice.
- the topology contains arbitrary topology information associated with the endpoint, e.g.
  - `kubernetes.io/hostname`: the value indicates the hostname of the node where the endpoint is located
  - `topology.kubernetes.io/zone`: the value indicates the zone where the endpoint is located
  - `topology.kubernetes.io/region`: the value indicates the region where the endpoint is located
- for the beta API, a new label `endpointslice.kubernetes.io/managed-by` is added to each EndpointSlice
  object and the value is set via endpoint-controller when creating the object; the reason for adding
  the label is because EndpointSlice API is very extensible and there might be other controller
  interested in managing its own EndpointSlice object.

The Enpointslice API contains a new endpointslice-controller component in kube-controller-manager,
which wil co-exist with endpoint-controller for multiple releases.

*References*

- [endpointslice API KEP link](https://github.com/kubernetes/enhancements/blob/26dc9a946876b32f3f2b41a58edf4e35a2751f9f/keps/sig-network/20190603-EndpointSlice-API.md)

## 20191227 - app protocol

- *Date: 03/31/2020, v1.18, stable*

This is a small KEP to add AppProtocol to Kubernetes Service and Endpoint API Object, thus each
individual service and endpoint port can be associated with an application protocol, which is less
confusing to users.

AppProtocol is already part of the EndpointSlice API, thus adding the field in Service and Endpoint
only occur minimal changes.

```go
// ServicePort represents the port on which the service is exposed
type ServicePort struct {
    ...
    // The application protocol for this port.
    // This field follows standard Kubernetes label syntax.
    // Un-prefixed names are reserved for IANA standard service names (as per
    // RFC-6335 and http://www.iana.org/assignments/service-names).
    // Non-standard protocols should use prefixed names such as
    // mycompany.com/my-custom-protocol.
    // +optional
    AppProtocol *string
}

// EndpointPort is a tuple that describes a single port.
type EndpointPort struct {
    ...
    // The application protocol for this port.
    // This field follows standard Kubernetes label syntax.
    // Un-prefixed names are reserved for IANA standard service names (as per
    // RFC-6335 and http://www.iana.org/assignments/service-names).
    // Non-standard protocols should use prefixed names such as
    // mycompany.com/my-custom-protocol.
    // +optional
    AppProtocol *string
}
```

For example:

```yaml
apiVersion: v1
kind: Service
...
spec:
  ports:
    - name: ssh
      port: 22
      protocol: tcp
      appProtocol: tcp
    - name: http
      port: 80
      appProtocol: http
    - name: https
      port: 443
      appProtocol: http
```

- [app protocol KEP link](https://github.com/kubernetes/enhancements/blob/000b16193b2e9833cd21884e58aaa05a03f11ef6/keps/sig-network/20191227-app-protocol.md)

# Feature & Design

## (large) networking

- *Date: 09/23/2018, v1.11*

The proposal provides design space for four fundamental networking model in Kubernetes, i.e.
- Container-to-Container communications
- Pod-to-Pod communications
- Pod-to-Service communications
- External-to-internal communications

*References*

- [networking design doc](https://github.com/kubernetes/community/blob/8080061fb6377a20e44d6890352f6ea27796cf10/contributors/design-proposals/network/networking.md)

## (large) kubernetes dns specification

- *Date: 11/26/2017, v1.8*

The proposal defines how kuberntes DNS should work. Implementations other than kube-dns can
implement the specification. For example, the specification defines what answer must be returned
in terms of headless service. Below is a brief summary:

- Schema version: a TXT record about specification schema version, e.g.
  ```
  QUERY SECTION
  dns-version.cluster.local.
  ANSWER SECTION
  28800 IN TXT "1.0.0"
  ```
- ClusterIP service
  - A Record, e.g.
    ```
    QUERY SECTION
    kubernetes.default.svc.cluster.local.
    ANSWER SECTION
    4 IN A 10.3.0.1
    ```
  - SRV Record (only for named port), e.g.
    ```
    QUERY SECTION
    _https._tcp.kubernetes.default.svc.cluster.local.
    ANSWER SECTION
    30 IN SRV 10 100 443 kubernetes.default.svc.cluster.local.
    ```
  - PTR Record (note IP is reversed), e.g. (Use `dig -x` to check PTR)
    ```
    QUERY SECTION
    1.0.3.10.in-addr.arpa.
    ANSWER SECTION
    14 IN PTR kubernetes.default.svc.cluster.local.
    ```
- Headleass service (no ClusterIP)
  - A Record, return A record for each ready endponts of a headless service, as well as A record for each endpont, e.g.
    ```
    QUERY SECTION
    headless.default.svc.cluster.local. IN A
    ANSWER SECTION
    headless.default.svc.cluster.local. 4 IN A 10.3.0.1
    headless.default.svc.cluster.local. 4 IN A 10.3.0.2
    headless.default.svc.cluster.local. 4 IN A 10.3.0.3

    QUERY SECTION
    my-pet-1.headless.default.svc.cluster.local. IN A
    ANSWER SECTION
    my-pet-1.headless.default.svc.cluster.local. 4 IN A 10.3.0.1
    ```
  - SRV Record (only for named port), return SRV record for each ready endpoint, port, protocol of a headless service, e.g.
    ```
    QUERY SECTION
    _https._tcp.headless.default.svc.cluster.local. IN SRV
    ANSWER SECTION
    _https._tcp.headless.default.svc.cluster.local. 4 IN SRV 10 100 443 my-pet-1.headless.default.svc.cluster.local.
    _https._tcp.headless.default.svc.cluster.local. 4 IN SRV 10 100 443 my-pet-2.headless.default.svc.cluster.local.
    _https._tcp.headless.default.svc.cluster.local. 4 IN SRV 10 100 443 my-pet-3.headless.default.svc.cluster.local.
    ```
  - PTR Record (note IP is reversed), this is similar to ClusterIP service, but since we don't have IP for headless service,
    PTR only exists for pods.
- ExternalName seervice
  - Given a Service named `<service>` in Namespace `<ns>` with ExternalName `<extname>`, a CNAME record named
    `<service>.<ns>.svc.<zone>` pointing to `<extname>` must exist.

*References*

- [specification as of kubernetes v1.8](https://github.com/kubernetes/dns/blob/7d0bfdc04b9a1f659becb7b184f53b1df7c996de/docs/specification.md)

## (large) network policy

- *Date: 09/23/2018, v1.11, stable*

The proposal introduces a `NetworkPolicy` objects, which select groups of pods and define how those
pods should be allowed to communicate with each other (both ingress and egress). For example:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: test-network-policy
  namespace: default
spec:
  podSelector:
    matchLabels:
      role: db
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - ipBlock:
        cidr: 172.17.0.0/16
        except:
        - 172.17.1.0/24
    - namespaceSelector:
        matchLabels:
          project: myproject
    - podSelector:
        matchLabels:
          role: frontend
    ports:
    - protocol: TCP
      port: 6379
  egress:
  - to:
    - ipBlock:
        cidr: 10.0.0.0/24
    ports:
    - protocol: TCP
      port: 5978
```

- isolates "role=db" pods in the "default" namespace for both ingress and egress traffic (if they weren’t already isolated)
- allows connections to TCP port 6379 of "role=db" pods in the "default" namespace from any pod in the "default" namespace with the label "role=frontend"
- allows connections to TCP port 6379 of "role=db" pods in the "default" namespace from any pod in a namespace with the label "project=myproject"
- allows connections to TCP port 6379 of "role=db" pods in the "default" namespace from IP addresses that are in CIDR 172.17.0.0/16 and not in 172.17.1.0/24
- allows connections from any pod in the "default" namespace with the label "role=db" to CIDR 10.0.0.0/24 on TCP port 5978

Notes about cidr based network policy. cidr based network policy is targeted at 1.8. At kubernetes
1.7, user can create a network policy with two types of policies:
- one is a pod label selector which selects pods in policy's namespace
- the other is a namespace label selector to select a namespace (i.e. all pods in the namespace).

Selected pods will be allowed to access targeting pods. The cidr network policy adds a third type,
i.e. to allow access targeting pods from specific cidr, e.g.

```yaml
kind: NetworkPolicy
apiVersion: networking.k8s.io/v1
metadata:
  name: sample-policy
spec:
  podSelector:
    matchlabels: {"role": "db"}
  ingress:
    - from:
        - cidrs: [ "192.168.5.0/24", "10.0.5.2/24" ]
```

The policy API is not decided yet as of v1.7; as mentioned in the issue, to achieve higher
flexibility, we can use:

```yaml
kind: NetworkPolicy
apiVersion: networking.k8s.io/v1
metadata:
  name: allow-except-from-private
spec:
  ingress:
  - cidrSelector:
    - type: Deny
      cidr: 10.0.0.0/8
    - type: Deny
      cidr: 192.168.0.0/16
    - type: Deny
      cidr: 172.16.0.0/12
    - type: Allow
      cidr: 0.0.0.0/0
```

*References*

- [network policy design doc (a bit outdated)](https://github.com/kubernetes/community/blob/8080061fb6377a20e44d6890352f6ea27796cf10/contributors/design-proposals/network/network-policy.md)
- https://kubernetes.io/docs/concepts/services-networking/network-policies/
- https://kubernetes.io/docs/tasks/administer-cluster/declare-network-policy/
- https://github.com/kubernetes/kubernetes/issues/49978

## (medium) command execution portforwarding

- *Date: 09/23/2018, v1.11*

The proposal aims to provide ssh-like experience in Kubernetes, i.e. execute command in container,
port forward from remote pod into local environment.

The proposal excludes the option to use SSH, because:
- there is no real user when using namespace/pod/container to identify a container
- there is length limit for user name

Therefore, Kubernetes uses streaming protocol to provide ssh-like experience; tools that expect to
use SSH won't work, but the protocol should suffice for most workload.

Kubelet uses `nsenter` to execute command in container, instead of using docker.

Requests go through client -> master -> kubelet -> container, there are room for imporvements:
- now with cri, kubelet is no longer a bottleneck: master can talk to container runtime directly
- master is still a bottleneck; we can solve the problem by providing a proxy which retrieves an
  authorization token from the master

*References*

- [command execution port forwarding design doc](https://github.com/kubernetes/community/blob/8080061fb6377a20e44d6890352f6ea27796cf10/contributors/design-proposals/network/command_execution_port_forwarding.md)

## (medium) external source ip preservation

- *Date: 03/03/2018, v1.9*

Problem statement from proposal:

> The current implementation requires that the cloud loadbalancer balances traffic across all
> Kubernetes worker nodes, and this traffic is then equally distributed to all the backend pods for
> that service. Due to the DNAT required to redirect the traffic to its ultimate destination, the
> return path for each session MUST traverse the same node again. To ensure this, the node also
> performs a SNAT, replacing the source ip with its own.

To simply put, SNAT is required because we are actually proxying request from one node to another.

```
          client
             \ ^
              \ \
               v \
   node 1 <--- node 2
    | ^   SNAT
    | |   --->
    v |
 endpoint
```

To solve the problem, for loadbalancer, we must remove the extra hop between two nodes. There are
two approaches mentioned in the proposal:
- Traffic Steering using LB programming: that is, service controller will be aware of pod topology
  and dynamically program LB backend nodes
- Traffic Steering using Health Checks: LB still keep all backend nodes, but kube-proxy will listen
  on a health check nodeport and if there is no local pod, 503 will be returned to LB thus it will
  not send requests to the node

Second approach is preferable since it involves less changes and is significantly faster. To support
this, there are two visible changes to the API:
- Add `service.alpha.kubernetes.io/external-traffic` annotation, with two values `Local` and
  `Cluster` to allow users to choose proxy mode. The annotation is changed to `service.spec.externalTrafficPolicy`
  field in v1.7 (to beta).
- Add `service.alpha.kubernetes.io/healthcheck-nodeport` to specify the nodeport where kube-proxy
  will listen The annotation is changed to `service.spec.healthCheckNodePort` field in v1.7 (to beta).

There's caveat when using `Local` option, see below comment from `service.spec.externalTrafficPolicy`:

```go
// externalTrafficPolicy denotes if this Service desires to route external
// traffic to node-local or cluster-wide endpoints. "Local" preserves the
// client source IP and avoids a second hop for LoadBalancer and Nodeport
// type services, but risks potentially imbalanced traffic spreading.
// "Cluster" obscures the client source IP and may cause a second hop to
// another node, but should have good overall load-spreading.
```

External traffic policy only works for service type `LoadBalancer` and `NodePort`. Implementation-wise,
all code in `proxier.go` will respecet this setting. For example, if option `Local` is used, then
SNAT (masq) will not be added, local endpoint chain will be setup, etc. If there is no local service,
packet will be dropped.

*References*

- [external lb source ip preservation design doc](https://github.com/kubernetes/community/blob/8080061fb6377a20e44d6890352f6ea27796cf10/contributors/design-proposals/network/external-lb-source-ip-preservation.md)
- [loadbalancer source ip preservation](https://kubernetes.io/docs/tasks/access-application-cluster/create-external-load-balancer/#preserving-the-client-source-ip)
- [understand source ip in Kubernetes](https://kubernetes.io/docs/tutorials/services/source-ip/)

## (small) service external name

- *Date: 10/12/2016, v1.4*

The feature supports referencing external services using CNAME, e.g. we can create a service named
`oracle` and with field `service.spec.externalName` set to `oracle-1.testdev.mycompany.com`; then
when pods access service `oracle` inside kubernetes, a CNAME `oracle-1.testdev.mycompany.com` will
be returned. It is admin's responsibility to make sure pod can resolve the CNAME. Typically, pods
are able to resolve such CNAME as it will use hosts' resolve.conf.

In kubernetes, when a service with `type == ExternalName` is created, dns pod will receive the
information and update its backend with a CNAME entry. In this setup, no virtual IP or proxying
is involved - only a CNAME is created in dns.

*References*

- [service external name design doc](https://github.com/kubernetes/kubernetes/blob/v1.4.0/docs/proposals/service-external-name.md)
- https://github.com/kubernetes/features/issues/33

## (small) traffic shaping with kubenet and cni

- *Date: 09/23/2018, v1.11, alpha*

kubenet (superceded by cni) support traffic shaping using linux `tc`. To use traffic shaping, make
sure Kubernetes is started with kubenet network plugin, i.e. `--network-plugin="kubenet"`, then add
annotation to pod object, e.g.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-for-shaping
  annotations:
    kubernetes.io/ingress-bandwidth: 1M
    kubernetes.io/egress-bandwidth: 1M
spec:
  containers:
    - name: container
      image: ddysher/nginx:1.13-net
      ports:
        - containerPort: 80
```

In v1.12, Kubernetes added support for traffic shaping with cni.

- [support traffic shaping for kubelet cni doc](https://github.com/kubernetes/community/blob/8080061fb6377a20e44d6890352f6ea27796cf10/contributors/design-proposals/network/support_traffic_shaping_for_kubelet_cni.md)
- [cni bandwidth plugin](https://github.com/containernetworking/plugins/tree/a8ad12dd7a3f4f913cd2fe0f33b61205e4875681/plugins/meta/bandwidth)
- https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/network-plugins/
- https://github.com/kubernetes/kubernetes/pull/63194

## (small) configurable nodeport ip range

- *Date: 03/04/2018, v1.10*

By default, kube-proxy accepts everything from NodePort without any filter. It can be a problem for
nodes which have both public and private NICs, and people only want to provide a service in private
network and avoid exposing any internal service on the public IPs. The implmentation is simple, for
example, in iptables mode, there is a rule at last of KUBE-SERVICES chain, which captures all traffic:

```
-A KUBE-SERVICES -m comment --comment "kubernetes service nodeports; NOTE: this must be the last rule in this chain" -m addrtype --dst-type LOCAL -j KUBE-NODEPORTS
```

Now with this feature, we add something similar to the following, where the ip address `192.168.8.53`
is the one we want to accept traffic.

```
-A KUBE-SERVICES -m comment --comment "kubernetes service nodeports; NOTE: this must be the last rule in this chain" -m addrtype --dst-type LOCAL -d 192.168.8.53 -j KUBE-NODEPORTS
```

*References*

- [nodeport ip range design doc](https://github.com/kubernetes/community/blob/bc455cc55778bf16252a050d9b8013897afd9748/contributors/design-proposals/network/nodeport-ip-range.md)

## (small) configurable resolv.conf

- *Date: 03/04/2018, v1.10, beta*
- *Date: 06/16/2019, v1.14, stable*

As of Kubernetes 1.9, it's not possible to have per pod DNS config: all Pods use cluster wide DNS.
The feature allows user to configure DNS settings of a Pod, e.g.

```yaml
# Pod spec
apiVersion: v1
kind: Pod
metadata: {"namespace": "ns1", "name": "example"}
spec:
  ...
  dnsPolicy: Custom
  dnsParams:  # changed to dnsConfig in stable API
    nameservers: ["1.2.3.4"]
    search:
    - ns1.svc.cluster.local
    - my.dns.search.suffix
    options:
    - name: ndots
      value: 2
    - name: edns0
```

The above API has changed a little bit in stable API:
- Options of `dnsPolicy` are `ClusterFirstWithHostNet`, `ClusterFirst`, `Default` or `None`
- The field `dnsParams` changes to `dnsConfig`

*References*

- [pod resolve conf design doc](  https://github.com/kubernetes/community/blob/bad95e7723049158128c96620993de83cab42321/contributors/design-proposals/network/pod-resolv-conf.md)

## (small) hostname alias

- *Date: 08/07/2018, v1.11, stable*

In 1.7, users can add these custom entries with the `HostAliases` field in PodSpec. Modification not
using `HostAliases` is not suggested because the file is managed by Kubelet and can be overwritten
during Pod creation/restart.

For the following yaml:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hostaliases-pod
spec:
  restartPolicy: Never
  hostAliases:
  - ip: "127.0.0.1"
    hostnames:
    - "foo.local"
    - "bar.local"
  - ip: "10.1.2.3"
    hostnames:
    - "foo.remote"
    - "bar.remote"
  containers:
  - name: cat-hosts
    image: busybox
    command:
    - cat
    args:
      - "/etc/hosts"
```

Kubernetes generates the following /etc/hosts:

```
$ kubectl logs hostaliases-pod
# Kubernetes-managed hosts file.
127.0.0.1 localhost
::1 localhost ip6-localhost ip6-loopback
fe00::0 ip6-localnet
fe00::0 ip6-mcastprefix
fe00::1 ip6-allnodes
fe00::2 ip6-allrouters
10.244.135.10 hostaliases-pod
127.0.0.1 foo.local
127.0.0.1 bar.local
10.1.2.3  foo.remote
10.1.2.3  bar.remote
```

## (deprecated) node-local service

- *Date: 05/21/2017, v1.6, design*
- *Date: 03/03/2018, v1.9, closed*

The goal is to provide a new service type which when requested, only send traffic to local service
endpoint. This works best for daemonset. [Here](https://groups.google.com/d/msg/kubernetes-dev/cK0djP-0ajY/HGeQ_oz0BAAJ)
is a typical use case.

The feature is generalized to the following feature: topology aware services routing.

*References*

- [proposal from author's branch](https://github.com/Clarifai/kubernetes/blob/dfb222f29a0c2365c92d73367cee5cbd9272b8e0/docs/proposals/node-local-services.md)
- https://github.com/kubernetes/kubernetes/issues/28610

## (deprecated) full service discovery

- *Date: 09/23/2018, v1.11, design*

Problem statement from proposal:

> To consume a service, a developer needs to know the full URL and a description of the API.
> Kubernetes contains the host and port information of a service, but it lacks the scheme and the
> path information needed if the service is not bound at the root. In this document we propose some
> standard kubernetes service annotations to fix these gaps. It is important that these annotations
> are a standard to allow for standard service discovery across Kubernetes implementations.

The proposal includes some standard annotations:

```yaml
...
"objects" : [ {
  "apiVersion" : "v1",
  "kind" : "Service",
  "metadata" : {
    "annotations" : {
      "api.service.kubernetes.io/protocol" : "REST",
      "api.service.kubernetes.io/scheme" "http",
      "api.service.kubernetes.io/path" : "cxfcdi",
      "api.service.kubernetes.io/description-path" : "cxfcdi/swagger.json",
      "api.service.kubernetes.io/description-language" : "SwaggerJSON"
    },
...
```

Note that the proposal is merged but not implemented (not sure about the status).

*References*

- [full service discovery design doc](https://github.com/kubernetes/community/blob/8080061fb6377a20e44d6890352f6ea27796cf10/contributors/design-proposals/network/service-discovery.md)

# Implementation

## how ip-per-pod works

*Date: 01/19/2015*

Kubernetes uses `container mode` of Docker network to share network namespace among the containers
in a pod and also make the network persistent until the pod is deleted.

For example, if you define your container A in kubernetes to map 80 to 8001 on the host, that port
map will not be applied to the container A; instead it will be mapped on a container named
kubernetes/pause, so even A is broken or down, that port map will not be lost. Of course, that also
means kubernetes started A like this:
```
docker run ... --net=container:NAME_or_ID_of_pause
```

Under the hood, docker uses linux network namespace to group containers with a single IP.

## how service with udp proxy works

*Date: 12/15/2014*

A service proxy runs on every node.

When a service is created, kubernetes master assigns a portal net for it, e.g. `10.0.0.1:1234`. The
master stores that information, which is then observed by all of the service proxy instances in the
cluster.

When a service proxy sees a new portal, it opens a new random port on its node, establishes an
iptables redirect from the portal to this new port, and starts accepting connections on the random
port (i.e. if there are a lot of services, proxy will listen on a lot of random port).

When a client pod connects to the service using `10.0.0.1:1234` or DNS, iptable rule will redirect the
connection to `localhost:random_port`. When proxier on the node (the same node as connecting pod)
recevies connection from the random_port, it queries load balancer for the next endpoint, and proxy
traffic between the connecting pod and endpoint pod.

- https://github.com/GoogleCloudPlatform/kubernetes/issues/1107
- https://github.com/GoogleCloudPlatform/kubernetes/pull/1402

## how dns works v1

*Date: 01/24/2015*

The DNS pod that runs holds 3 containers - skydns, etcd (which skydns uses), and a kubernetes-to-skydns
bridge called kube2sky. The kube2sky process watches the kubernetes master for changes in Services,
and then writes the information to etcd, which skydns reads. This etcd instance is not linked to
any other etcd clusters that might exist, including the kubernetes master.

When a container's dns policy is `ClusterFirst`, it will be started with `--dns` and `--dns-search`
option (see docker cli docs). The `--dns` will be the dns service's ip address, and `--dns-search`
wil be the one configured by user, e.g. `kubernetes.local`. To access a service, request can be sent
to:
```
http://service-name.namespace.kubernetes.local:service-port
```

## how dns works v2

*Date: 09/29/2016, v1.3*

As of kubernetes 1.3, skydns is no longer a separate pod of its own. Instead, skydns is running as
part of KubeDNS. Previously, the dns addons runs an etcd instance to serve as skydns backend, and
skydns is running as another service; then there is a kube2sky that bridges kubernetes service to
skydns DNS record.

Now KubeDNS is a standalone binary (see cmd/kube-dns) which includes skydns as a library. skydns no
longer uses etcd as its backend; instead, KubeDNS itself is the backend of skydns (newer skydns
supports custom backend; custom backend needs to satisfy library interface, namely Records() and
ReverseRecord() method). The resulting Pod has three containers: kubedns, dnsmasq and healthz,
where dnsmasq is just a cache.

## how dns works v3, with coredns

- *Date: 02/28/2018, v1.9*
- *Date: 03/31/2018, v1.10, beta*
- *Date: 05/08/2019, v1.13, stable*

In Kubernetes 1.9, replacing kube-dns with CoreDNS is an alpha feature. The benefits of using CoreDNS
is its extensibility based on its plugin system. [This blog post](https://coredns.io/2017/05/08/custom-dns-entries-for-kubernetes/)
has some use cases. All use cases narrow down to the scenario of adding custom dns entries into
Kubernetes, either it's just one rewrite DNS or a new DNS database.

*References*

- [proposal](https://github.com/kubernetes/community/blob/bc455cc55778bf16252a050d9b8013897afd9748/contributors/design-proposals/network/coredns.md)

## how network related controllers works

**endpoint controller (07/01/2018, v1.11)**

Endpoint controller exists since the first commit of Kubernetes. It watches for Service & Pod objects,
and populates the Endpoints API object; that is, endpoint controller joins Services & Pods. Proxier
(iptables, ipvs, etc) only cares about Service & Endpoints, instead of Pods. Endpoint abstractions
are useful in different aspects:
- Endpoint and Pod is not 1:1 mapping; instead, Endpoint consists of IP & Port
- Endpoint controller can help filter unready pods, terminating pods, etc
- Endpoint doesn't have to be associated with Pod, e.g. we can create endpoints for external services

**service controller, aka public IPs (04/29/2015)**

Service controller watches all service objects from apiserver. For each service that has
`CreateExternalLoadBalancer` flag, it creates the external load balancer. It also makes sure that
service update/delete is handled properly.

In gce, the external load balancer works by adding all nodes to a target poll, then forward all
traffic to the nodes through some load balance policy. E.g. if the service is 10.2.2.2, and expose
ports 80, 8080; then service controller will create a loadbalancer with a public ip, say 104.12.12.12,
and forward traffic from the IP to one of the nodes with the same port. The public IP of the load
balancer will be added to the field `publicIPs` of the service. Service controller then updates the
service to API server.

In every node, kube-proxy will notice the update and create iptable rules for the public IP (load
balancer's IP) just as it creates rules for portal IP. For the above example, suppose node has ip
address 105.21.21.21. When user requests 104.12.12.12:8080, the request will be forwarded to node
105.21.21.21:8080 by external load balancer. As kube-proxy has installed iptable rules, the traffic
will be routed to a random port opened by the proxy (see above 'How Services v2 works'). Once
kube-proxy gets the request, it then forwards the request to desired backend pod. In the whole
process, nothing is listening on 105.21.21.21:8080, the redirection all happens in kernel's ip stack.

Note that there are two different type of iptables, one for node port and one for service, i.e.
```
user request from 104.12.12.12:8080 (loadbalancer) -> 105.21.21.21:8080 -> random port on the node
```

```
pod calls 10.2.2.2:8080 (service) -> random port on the node
```

**route controller (03/05/2017, v1.5)**

The routeController configures routes for hosts in the cloud provider; it is entirely cloud specific.
The hosts get their CIDRs from node controller. The route simply tells cloud provider: "For this
CIDR, route it to this node".

## how network plugin works

*Date: 07/26/2016, v1.3*

**Overview**

The kubelet has a single default network plugin, and a default network common to the entire cluster.
It probes for plugins when it starts up, remembers what it found, and executes the selected plugin
at appropriate times in the pod lifecycle (this is only true for docker, as rkt manages its own CNI
plugins). Currently, there are three: `exec`, `cni` and `kubenet`. Network plugin interface has
several methods: `Init(), Name(), SetUpPod(), TearDownPod(), Status()`. For `SetUpPod()`, it is
called after infra container of the pod has been created but before the other containers of the pod
are launched.

Kubelet uses `--network-plugin` option to decide which plugin to use. It's important to note that
network plugin is _**only used when running docker**_. For other runtimes, e.g. cri-o, network is
managed directly in runtime itself (communicated with Kubelet via cri).

**exec plugin**

exec plugin defines its own rules for how plugin handles pod network lifecycle, i.e. four actions:
init, setup, teardown, status. Exec plugin is implemented as a standalone binary. It is deprecated
in favor of cni plugin.

**cni plugin**

cni plugin also defines rules for how plugin handles container network lifecycle; in kubernetes,
it is the infra container. At its core, cni is still a standalone binary, and its 'API' is
environment variables and command line flags, as well as a set of pre-defined directories like
`/etc/cni/net.d`. In kubelet code base, it imports libcni to setup env and flag, then exec cni
plugin, e.g. when SetUpPod() is called, cni plugin looks for cni config (see below for an example).
The config should be placed in `/etc/cni/net.d`. It then uses the config to set up the infra container.
e.g. use cni plugin with the following config sort of like using docker native bridge mode.

```json
{
 "name": "mynet",
 "type": "bridge",
 "bridge": "docker0",
 "isGateway": true,
 "ipMasq": true,
 "ipam": {
   "type": "host-local",
   "subnet": "172.17.0.1/16",
   "routes": [
     { "dst": "0.0.0.0/0" }
   ]
 }
}
```

**kubenet plugin**

kubenet implements basic `cbr0` using the bridge and host-local CNI plugins, i.e. kubenet depends on
cni plugin. It creates a Linux bridge named `cbr0` and creates a veth pair for each pod with the host
end of each pair connected to `cbr0`.

Since kubenet depends on cni, it will generate cni config for cni plugins, the default is:

```json
I0924 14:53:51.538758   26776 kubenet_linux.go:254] CNI network config set to {
  "cniVersion": "0.1.0",
  "name": "kubenet",
  "type": "bridge",
  "bridge": "cbr0",
  "mtu": 1500,
  "addIf": "eth0",
  "isGateway": true,
  "ipMasq": false,
  "hairpinMode": false,
  "ipam": {
    "type": "host-local",
    "subnet": "10.1.0.0/24",
    "gateway": "10.1.0.1",
    "routes": [
      { "dst": "0.0.0.0/0" }
    ]
  }
}
```

## how cluster cidr subnet manager works in flannel

*Date: 08/27/2016, v1.3*

Flannel uses etcd to aquire leases and network configurations. [This PR](https://github.com/coreos/flannel/pull/483)
makes it possible for flannel to use Kubernetes apiserver as source of network configuration (thus
it doesn't depend on an extra etcd in this case). In Kubernetes, cluster CIDR needs to be configured
in controller manager; once set, it will be responsible to calculate Node.Spec.PodCIDR for each node.

Flannel watches apiserver for node information, and once it reads Node.Spec.PodCIDR, it will use that
for the node's subnet. Other information like backend is currently set via Node.Annotation.

## how pod hostname/subdomain works

*Date: 05/03/2017, v1.6*

Pod hostname allows user to specify hostname and subdomain name for a pod, e.g. `pod-hostname.pod-subdomainname.default.svc.cluster.local`,
where `pod-hostname` and `pod-subdomainname` are specified from user, `default` is the pod namespace,
`svc` is a fixed construct, `cluster.local` is cluster domain.

Implementation is fairly easy. In kubelet, it will parse Pod.Spec, and if pod hostname and subdomain
are specified, it will add the information to pod's "/etc/hosts" file, which is mounted from host
machine, e.g. `/var/lib/kubelet/pods/f5fd585d-2f9d-11e7-bfdd-8825937fa049/etc-hosts`.

Note multiple pods can have the same hostname.domainname, even in the same namespace. Pod hostname
and subdomain is usually used in combination with headless service, since the FQDN is only accessible
from the pod itself, which is not very useful at its own. Once the headless service (with selector)
is created, endpoint controller will create endpoints for the service. For dns addon, it will create
an A record for every pod in the headless service; this record will be periodically updated. e.g.
for a service `x`, with pods `a` and `b`, it will create following DNS records: `a.x.ns.domain.` and
`b.x.ns.domain.`.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [KEPs](#keps)
  - [KEP-0007: pod-ready++](#kep-0007-pod-ready)
- [Feature & Design](#feature--design)
  - [networking](#networking)
  - [command execution portforwarding](#command-execution-portforwarding)
  - [kubernetes dns specification](#kubernetes-dns-specification)
  - [node-local service](#node-local-service)
  - [topology aware services routing](#topology-aware-services-routing)
  - [service external name](#service-external-name)
  - [full service discovery](#full-service-discovery)
  - [network policy](#network-policy)
  - [traffic shaping with kubenet and cni](#traffic-shaping-with-kubenet-and-cni)
  - [external source ip preservation](#external-source-ip-preservation)
  - [configurable nodeport ip range](#configurable-nodeport-ip-range)
  - [configurable resolv.conf](#configurable-resolvconf)
  - [hostname alias](#hostname-alias)
- [Workflow](#workflow)
  - [how ip-per-pod works](#how-ip-per-pod-works)
  - [service v2 with udp proxy](#service-v2-with-udp-proxy)
  - [service v2 with ipvs based service](#service-v2-with-ipvs-based-service)
  - [how dns works v1](#how-dns-works-v1)
  - [how dns works v2](#how-dns-works-v2)
  - [how dns works v3, with coredns](#how-dns-works-v3-with-coredns)
  - [how network related controllers works](#how-network-related-controllers-works)
  - [how network plugin works](#how-network-plugin-works)
  - [how cluster cidr subnet manager works in flannel](#how-cluster-cidr-subnet-manager-works-in-flannel)
  - [how pod hostname/subdomain works](#how-pod-hostnamesubdomain-works)
- [TODOs](#todos)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

> A collection of proposals, designs, features in Kubernetes network.

- [SIG-Network Community](https://github.com/kubernetes/community/tree/master/sig-network)
- [SIG-Network Proposals](https://github.com/kubernetes/community/blob/master/contributors/design-proposals/network)

# KEPs

## KEP-0007: pod-ready++

*Date: 09/07/2018, v1.11*

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

*References*

- [KEP link](https://github.com/kubernetes/community/blob/a5515a371e380886a56aaa5843df27f21d9e892e/keps/sig-network/0007-pod-ready%2B%2B.md)

# Feature & Design

## networking

*Date: 09/23/2018, v1.11*

The proposal provides design space for four fundamental networking model in Kubernetes, i.e.
- Container-to-Container communications
- Pod-to-Pod communications
- Pod-to-Service communications
- External-to-internal communications

*References*

- [design doc](https://github.com/kubernetes/community/blob/8080061fb6377a20e44d6890352f6ea27796cf10/contributors/design-proposals/network/networking.md)

## command execution portforwarding

*Date: 09/23/2018, v1.11*

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

- [design doc](https://github.com/kubernetes/community/blob/8080061fb6377a20e44d6890352f6ea27796cf10/contributors/design-proposals/network/command_execution_port_forwarding.md)

## kubernetes dns specification

*Date: 11/26/2017, v1.8*

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

## node-local service

*Date: 05/21/2017, v1.6*

The goal is to provide a new service type which when requested, only send traffic to local service
endpoint. This works best for daemonset. [Here](https://groups.google.com/d/msg/kubernetes-dev/cK0djP-0ajY/HGeQ_oz0BAAJ)
is a typical use case.

*Timeline*

- As of 06/08/2017, kubernetes 1.6 and 1.7-alpha, design

*References*

- [proposal from author's branch](https://github.com/Clarifai/kubernetes/blob/dfb222f29a0c2365c92d73367cee5cbd9272b8e0/docs/proposals/node-local-services.md)

## topology aware services routing

*Date: 03/03/2018, v1.9, design*

The proposal aims to solve a couple of issues, including the above node-local service design, by
providing a new ServicePolicy API. Users can specify routing policy, for example, when a pod
accssing the service, only route traffic to the node, or rack, or zone, where the pod is running.
The policy generalizes node local to any user defined topology. The feature is in design phase.
For example, the following example creates a service policy which restrict all traffic to service
with label "app:bar" will be routed only to backends that satisfy both same region and same switch
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

*References*

- https://github.com/kubernetes/community/pull/1551

## service external name

*Date: 10/12/2016, v1.4*

The feature supports referencing external services using CNAME, e.g. we can create a service named
'oracle' and with field `service.spec.externalName` set to `oracle-1.testdev.mycompany.com`; then
when pods access service 'oracle' inside kubernetes, a CNAME `oracle-1.testdev.mycompany.com` will
be returned. It is admin's responsibility to make sure pod can resolve the CNAME. Typically, pods
are able to resolve such CNAME as it will use hosts' resolve.conf.

In kubernetes, when a service with 'type == ExternalName' is created, dns pod will receive the
information and update its backend with a CNAME entry. In this setup, no virtual IP or proxying
is involved - only a CNAME is created in dns.

*References*

- https://github.com/kubernetes/features/issues/33
- https://github.com/kubernetes/kubernetes/blob/v1.4.0/docs/proposals/service-external-name.md

## full service discovery

*Date: 09/23/2018, v1.11, design*

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

- [design doc](https://github.com/kubernetes/community/blob/8080061fb6377a20e44d6890352f6ea27796cf10/contributors/design-proposals/network/service-discovery.md)

## network policy

*Date: 09/23/2018, v1.11, ga*

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

*References*

- [design doc (a bit outdated)](https://github.com/kubernetes/community/blob/8080061fb6377a20e44d6890352f6ea27796cf10/contributors/design-proposals/network/network-policy.md)
- https://kubernetes.io/docs/concepts/services-networking/network-policies/
- https://kubernetes.io/docs/tasks/administer-cluster/declare-network-policy/
- https://github.com/kubernetes/kubernetes/issues/49978

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

## traffic shaping with kubenet and cni

*Date: 09/23/2018, v1.11, alpha*

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

- [design doc](https://github.com/kubernetes/community/blob/8080061fb6377a20e44d6890352f6ea27796cf10/contributors/design-proposals/network/support_traffic_shaping_for_kubelet_cni.md)
- [cni bandwidth plugin](https://github.com/containernetworking/plugins/tree/a8ad12dd7a3f4f913cd2fe0f33b61205e4875681/plugins/meta/bandwidth)
- https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/network-plugins/
- https://github.com/kubernetes/kubernetes/pull/63194

## external source ip preservation

*Date: 03/03/2018, v1.9*

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

To solve the problem, for loadbalancer, we must remove the extra hop between two nodes. Thre are
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

- [design doc](https://github.com/kubernetes/community/blob/8080061fb6377a20e44d6890352f6ea27796cf10/contributors/design-proposals/network/external-lb-source-ip-preservation.md)
- [loadbalancer source ip preservation](https://kubernetes.io/docs/tasks/access-application-cluster/create-external-load-balancer/#preserving-the-client-source-ip)
- [understand source ip in Kubernetes](https://kubernetes.io/docs/tutorials/services/source-ip/)

## configurable nodeport ip range

*Date: 03/04, k8s 1.10*

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

- [proposal](https://github.com/kubernetes/community/blob/bc455cc55778bf16252a050d9b8013897afd9748/contributors/design-proposals/network/nodeport-ip-range.md)

## configurable resolv.conf

*Date: 03/04/2018, v1.10, alpha*

As of Kubernetes 1.9, it's not possible to have per pod DNS config: all Pods use cluster wide DNS.
The feature allows user to configure DNS settings of a Pod, e.g.

```
# Pod spec
apiVersion: v1
kind: Pod
metadata: {"namespace": "ns1", "name": "example"}
spec:
  ...
  dnsPolicy: Custom
  dnsParams:
    nameservers: ["1.2.3.4"]
    search:
    - ns1.svc.cluster.local
    - my.dns.search.suffix
    options:
    - name: ndots
      value: 2
    - name: edns0
```

- [proposal](  https://github.com/kubernetes/community/blob/bad95e7723049158128c96620993de83cab42321/contributors/design-proposals/network/pod-resolv-conf.md)

## hostname alias

*Date: 08/07/2018, v1.11, ga*

In 1.7, users can add these custom entries with the HostAliases field in PodSpec. Modification not
using HostAliases is not suggested because the file is managed by Kubelet and can be overwritten
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

# Workflow

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

## service v2 with udp proxy

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

## service v2 with ipvs based service

*Date: 05/18/2017*

- For in cluster service, a dummy interface will be created on each host and all service cluster
  IPs will be attached to the dummy interface. An ipvs service will be created for each kubernetes
  service ip + port + protocol combination, with each kubernetes backend as ipvs real server.
- For node port, the same applies except 1. ipvs service ip is the node ip. 2. dummy interface is
  not used.
- For service external ip, it's similar to node ip: ipvs service ip is the external ip.
- For loadbalacner type, same as external ip.
- For node local type, ipvs will do the same as iptables, i.e. just forward local endpoints.

*Timeline*

- As of 06/08/2017, kubernetes 1.6 and 1.7-alpha, design and implementation
- As of 07/09/2018, kubernetes 1.11, GA

*References*

- https://github.com/kubernetes/community/pull/692
- https://kubernetes.io/blog/2018/07/09/ipvs-based-in-cluster-load-balancing-deep-dive/

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

*Date: 02/28/2018, v1.9*

In Kubernetes 1.9, replacing kube-dns with CoreDNS is an alpha feature. The benefits of using CoreDNS
is its extensibility based on its plugin system. [This blog post](https://coredns.io/2017/05/08/custom-dns-entries-for-kubernetes/)
has some use cases. All use cases narrow down to the scenario of adding custom dns entries into
Kubernetes, either it's just one rewrite DNS or a new DNS database.

*References*

- [proposal](https://github.com/kubernetes/community/blob/bc455cc55778bf16252a050d9b8013897afd9748/contributors/design-proposals/network/coredns.md)

*Update on 03/31/2018, v1.10*

- In Kubernetes 1.10, replacing kube-dns with CoreDNS is a beta feature.

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
plugins). Currently, there are three: exec, cni and kubenet. Network plugin interface has several
methods: Init(), Name(), SetUpPod(), TearDownPod(), Status(). For SetUpPod(), it is called after
infra container of the pod has been created but before the other containers of the pod are launched.

Kubelet uses `--network-plugin` option to decide which plugin to use. It's important to note that
network plugin is **only used** when running docker. For other runtimes, e.g. cri-o, network is
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
where 'pod-hostname' and 'pod-subdomainname' are specified from user, 'default' is the pod namespace,
'svc' is a fixed construct, 'cluster.local' is cluster domain.

Implementation is fairly easy. In kubelet, it will parse Pod.Spec, and if pod hostname and subdomain
are specified, it will add the information to pod's "/etc/hosts" file, which is mounted from host
machine, e.g. `/var/lib/kubelet/pods/f5fd585d-2f9d-11e7-bfdd-8825937fa049/etc-hosts`.

Note multiple pods can have the same hostname.domainname, even in the same namespace. Pod hostname
and subdomain is usually used in combination with headless service, since the FQDN is only accessible
from the pod itself, which is not very useful at its own. Once the headless service (with selector)
is created, endpoint controller will create endpoints for the service. For dns addon, it will create
an A record for every pod in the headless service; this record will be periodically updated. e.g.
for a service `x`, with pods a and b, it will create following DNS records: `a.x.ns.domain.` and,
`b.x.ns.domain.`.

# TODOs

- Multi-tenant networking: https://github.com/kubernetes/kubernetes/pull/15465

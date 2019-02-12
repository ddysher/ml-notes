<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Concepts](#concepts)
  - [Traffic Management](#traffic-management)
  - [Observability](#observability)
  - [Security](#security)
  - [Extensibility](#extensibility)
- [Architecture](#architecture)
  - [Envoy](#envoy)
  - [Istiod](#istiod)
  - [Mixer (deprecated)](#mixer-deprecated)
  - [Pilot (deprecated)](#pilot-deprecated)
  - [Citadel (deprecated)](#citadel-deprecated)
  - [Galley (deprecated)](#galley-deprecated)
- [Experiment (v0.1.6)](#experiment-v016)
  - [Installation](#installation)
  - [Components](#components)
  - [Tasks](#tasks)
- [Experiment (v0.2.2)](#experiment-v022)
  - [Installation](#installation-1)
  - [Components](#components-1)
  - [Tasks](#tasks-1)
- [Experiment (v1.6.5)](#experiment-v165)
  - [Installation](#installation-2)
  - [Debugging](#debugging)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

[Istio](https://istio.io) is an open platform to connect, manage, and secure microservices.

An istio service mesh is logically split into a data plane and a control plane.
- The data plane is composed of a set of intelligent proxies (Envoy) deployed as sidecars that mediate and control all network communication between microservices.
- The control plane is responsible for managing and configuring proxies to route traffic, as well as enforcing policies at runtime.

Following is a list of key features from istio:

- Dynamic Routing
- Load balancing
- Failure recovery
- Rich metrics and monitoring
- A/B testing
- Canary releases
- Rate limiting
- Access control
- Circuit breaker
- End-to-end authentication
- TLS termination
- HTTP/2 & gRPC proxying
- Health checks
- Fault injection
- Upgrade unencrypted traffic
- Gradual rollout
- Retries

# Concepts

## [Traffic Management](https://istio.io/latest/docs/concepts/traffic-management/)

Istio forms a service mesh where each application running in the mesh has an associated sidecar proxy
running. Apart from sidecar proxy, ingress/egress traffic in the cluster is also handled in istio.
This architecture allows istio to see all traffic in the mesh, thus istio can provide full-fleged
traffic management.

To be specific, istio can control service routing (content based, e.g. header), canary release,
spltting traffic load, timeout, retries, circuit breaker, etc. Pilot is the core for managing global
service information, each sidecar envoy will also maintain load balancing information based on the
information from pilot and periodic health-checks of other instances.

Simply put, pilot is responsible for high level rules, while envoy enforces the rules: routing,
active health check, passive health check (circuit breaker), loadbalance, etc; all of these are
handled in envoy. Envoy uses the sds, rds, cds API to retrieve configurations from pilot.

Note as of istio v1.5, all control plane components are merged into a single binary: istiod.

The core concepts in traffic management are list below; they are represented as CRDs in Kubernetes:
- VirtualService
- DestinationRule
- Gateway
- ServiceEntry
- WorkloadEntry
- Sidecar

**VirtualService (CRD)**

Virtual service defines a conceptual, virtual service, meaning it does not map to any particular
running instances, but instead, a set of instances that collectively make up a service. Virtual
service consumers only connect to virtual service, without knowing any instance details. In
addition, virtual service can be used to configure istio gateway, similar to virtual service
applied to the mesh; the main difference is that virtual service on istio gateway will only
propagate rules to edge envoy proxies.

Example use cases of virtual service include:
- Different versions of an application, e.g. in Kubernetes, a virtual service spans across multiple
  deployment (thus services), each contains a different version;
- Monolithic application to microservice migration, i.e. a virtual service exposes a single endpoint
  but under the hood, forward traffic to multiple different endpoints;
- Policy enforcement: virtual service has rich set of features that can be enforced via services.

Implementation-wise, the rules in virtual service are propagated from istiod to every envoy proxies.
Conceptually, the rules will apply to out-bound traffic of the consumers. For example, if we create
a virtual service for a service called `rating` with 2s delay, then it effectively says: for any
consumer that calls `rating` (including `rating` itself), add 2s delay to the request. The delay is
implemented in evey envoy proxy at the sending-side of the mesh.

E.g. send traffic to different versions based on user:

```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
  - reviews
  http:
  - match:
    - headers:
        end-user:
          exact: jason
    route:
    - destination:
        host: reviews
        subset: v2
  - route:
    - destination:
        host: reviews
        subset: v3
```

**DestinationRule (CRD)**

Destinatinon rule is another critical part of istio's routing functionality. It is used to configure
the receiving-side of the mesh, e.g. circuit breaker, loadbalancing (within subsets), etc.

> You can think of virtual services as how you route your traffic to a given destination, and then
> you use destination rules to configure what happens to traffic for that destination. Destination
> rules are applied after virtual service routing rules are evaluated, so they apply to the traffic's
> "real" destination.
>
> In particular, you use destination rules to specify named service subsets, such as grouping all a
> given service's instances by version. You can then use these service subsets in the routing rules
> of virtual services to control the traffic to different instances of your services.

Implementation-wise, the rules in destination rules are propagated from istiod to every envoy proxies.
For example, in circuit breaker, all the instances that forms a cluster will share the budget.

E.g. three different subsets for the `my-svc` destination service, with different load balancing policie:

```yaml
apiVersion: networking.istio.io/v1alpha3
kind: DestinationRule
metadata:
  name: my-destination-rule
spec:
  host: my-svc
  trafficPolicy:
    loadBalancer:
      simple: RANDOM
  subsets:
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
    trafficPolicy:
      loadBalancer:
        simple: ROUND_ROBIN
  - name: v3
    labels:
      version: v3
```

**Gateway (CRD)**

Gateway manages inbound (ingress gateway) and outbout (egress gateway) traffic of the mesh. Gateway
is similar to Kubernetes ingress, but is much more feature-rich. The default gateway proxy from
istio support both kubernetes ingress/egress and istio gateway; however, the recommended approach is
to use gateway in favor of ingress.

Typically, using gateway in istio requires:
- deploy the actual proxies; the demo profile provides `istio-ingressgateway` and `istio-egressgateway`;
- create `Gateway` resource, which instruct the proxy about what hosts/port to take charge of;
- create `VirtualService` resource, which works similar for mesh internal routing, but applies to gateway.

Note the egress gateway (along with virtual service) is used to send traffic to external destinations
via selected nodes, either because we want more access control from a set of central nodes or only
these nodes can access external destinations. Apart from egress gateway, users can also use the
following approaches to access external network:
- configuring envoy to allow access to any external service.
- use a service entry (see below) to register an accessible external service inside the mesh (recommended).
- configuring the istio sidecar to exclude external IPs from its remapped IP table.

E.g. a gateway configuration selecting a gateway controller with HTTPS ingress traffic:

```yaml
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: ext-host-gwy
spec:
  selector:
    app: my-gateway-controller
  servers:
  - port:
      number: 443
      name: https
      protocol: HTTPS
    hosts:
    - ext-host.example.com
    tls:
      mode: SIMPLE
      serverCertificate: /tmp/tls.crt
      privateKey: /tmp/tls.key
```

**ServiceEntry (CRD)**

The service entry is used to manually add services into the mesh registry. Once added, they can be
treated as regular services in the mesh; this allows istio to manage traffics for services outside
of the mesh.

The use cases for service entry are:
- allow selective external destination access when outbound policy is set to REGISTRY_ONLY
- define timeout, fault injection, etc, for external destinations (via virtual service)
- add service entry for services running on virtual machines
- add service from other clusters to form a multi-cluster istio mesh

Once added, hosts defined in ServiceEntry can be used in VirtualService and DestinationRule.

E.g. declares a few external APIs accessed by internal applications over HTTPS:

```yaml
apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: external-svc-https
spec:
  hosts:
  - api.dropboxapi.com
  - www.googleapis.com
  - api.facebook.com
  location: MESH_EXTERNAL
  ports:
  - number: 443
    name: https
    protocol: TLS
  resolution: DNS
```

**WorkloadEntry (CRD)**

WorkloadEntry describes the properties of a non-Kubernetes workload such as VM or a bare metal
server as it is are onboarded into the mesh. A `WorkloadEntry` must be accompanied by an istio
`ServiceEntry` that selects the workload through the appropriate labels and provides the service
definition for a `MESH_INTERNAL` service (hostnames, port properties, etc.). A ServiceEntry object
can select multiple WorkloadEntries as well as Kubernetes Pods based on the label selector
specified in the ServiceEntry. Conceptually, WorkloadEntry is equivalent to Pod.

Note here, `MESH_INTERNAL` means any workload that's in the mesh, i.e. there is an envoy proxy
running as a sidecar with the application, whether it's running in Kubernetes or in VM.

E.g. a workload entry selected by a service entry (like pod selected by service in Kubernetes):

```yaml
apiVersion: networking.istio.io/v1alpha3
kind: WorkloadEntry
metadata:
  name: vm1
  namespace: ns1
spec:
  address: 1.1.1.1
  labels:
    app: foo
    instance-id: vm-78ad2
    class: vm
---
apiVersion: networking.istio.io/v1alpha3
kind: ServiceEntry
metadata:
  name: svc1
  namespace: ns1
spec:
  hosts:
  - svc1.internal.com
  ports:
  - number: 80
    name: http
    protocol: HTTP
  resolution: STATIC
  workloadSelector:
    labels:
      app: foo
```

**Sidecar (CRD)**

By default, Istio will program all sidecar proxies in the mesh with the necessary configuration
required to reach every workload instance in the mesh, as well as accept traffic on all the ports
associated with the workload. This is usually not desirable due to security and performance reasons.
The sidecar configuration is thus brought up to do the following:
- Fine-tune the set of ports and protocols that an Envoy proxy accepts.
- Limit the set of services that the Envoy proxy can reach.

E.g. all services in the `bookinfo` namespace can only reach services running in the same namespace
and the istio control plane:

```yaml
apiVersion: networking.istio.io/v1alpha3
kind: Sidecar
metadata:
  name: default
  namespace: bookinfo
spec:
  egress:
  - hosts:
    - "./*"
    - "istio-system/*"
```

## [Observability](https://istio.io/latest/docs/concepts/observability)

Istio has robust monitoring, tracing and logging, as well as custom dashboard which provides
visibility into application performance. All these features let you more effectively set, monitor,
and enforce SLOs on services. As mentiond above, istio has all the data from mesh, thus allowing
it to show every piece of traffic in the mesh, e.g. traffic flow.

The main features of observability are:
- Metrics: istio generates a set of service metrics based on the four "golden signals" of monitoring (latency, traffic, errors, and saturation).
  - Proxy-level metrics: metrics specifically about envoy, e.g. `envoy_cluster_upstream_rq_completed`
  - Service-level metrics: metrics for service communications. istio defines a set of [default metrics](https://istio.io/latest/docs/reference/config/policy-and-telemetry/metrics/)
    (prefixed with `istio_`) and labels for each metric, and custom metrics can be added via configurations.
  - Control plane metrics: metrics about istio itself.
- Distributed traces: envoy proxies automatically generate trace spans on behalf of the applications they proxy, but it require that the applications forward the appropriate request context.
- Access logs: access logs provide a way to monitor and understand behavior from the perspective of an individual workload instance; access logs are queried via envoy proxies.

## [Security](https://istio.io/latest/docs/concepts/security)

Istio provides the underlying secure communication channel, and manages authentication, authorization,
and encryption of service communication at scale.

Authentication has two policies:
- Peer Authentication: authn for peer-to-peer communication
- Request authentication: authn for external request

Peer's identity come from platform service account, e.g. kubernetes service account; istio sidecar
will automatically use service account to acquire certificate from istiod. External request's
identity uses OIDC with JWT, operator needs to configure RequestAuthentication with correct issuer.

Every envoy proxy runs an authorization engine, which is configured by istiod a single CRD API.
Authorization is enabled implicitly, and can be applied to HTTP and TCP traffic.

**PeerAuthentication (CRD)**

A default `STRICT` policy for `foo` namespace:

```yaml
apiVersion: "security.istio.io/v1beta1"
kind: "PeerAuthentication"
metadata:
  name: "example-policy"
  namespace: "foo"
spec:
  mtls:
    mode: STRICT
```

For workload specific peer authentication, corresponding destination rule is required.

**RequestAuthentication (CRD)**

A request authentication policy that requires end-user JWT for the ingress gateway:

```yaml
apiVersion: "security.istio.io/v1beta1"
kind: "RequestAuthentication"
metadata:
  name: "jwt-example"
  namespace: istio-system
spec:
  selector:
    matchLabels:
      istio: ingressgateway
  jwtRules:
  - issuer: "testing@secure.istio.io"
    jwksUri: "https://raw.githubusercontent.com/istio/istio/release-1.6/security/tools/jwt/samples/jwks.json"
```

**AuthorizationPolicy (CRD)**

Allows two sources, the `cluster.local/ns/default/sa/sleep` service account and the `dev` namespace,
to access the workloads with the `app: httpbin` and `version: v1` labels in the `foo` namespace when
requests sent have a valid JWT token.

```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
 name: httpbin
 namespace: foo
spec:
 selector:
   matchLabels:
     app: httpbin
     version: v1
 action: ALLOW
 rules:
 - from:
   - source:
       principals: ["cluster.local/ns/default/sa/sleep"]
   - source:
       namespaces: ["dev"]
   to:
   - operation:
       methods: ["GET"]
   when:
   - key: request.auth.claims[iss]
     values: ["https://accounts.google.com"]
```

## [Extensibility](https://istio.io/latest/docs/concepts/wasm/)

**EnvoyFilter (CRD)**

Istio leverages envoy + wasm for extensibility: users can use a lot of envoy built-in filters for
extra functionalities (like rate limiting, etc), and if necessary, can use Wasm to build custom
filters. The extensibility is provided in case istio **control plane** is not able to provide the
functionality via its abstraction, thus we can use envoy filter to program **data plane** directly.
The extensibility is mostly used for policy enforcement.

Pay attention:
- EnvoyFilter CRD will maintain backward compatibility, but the compatibility of config data depends on envoy.
- EnvoyFilter is namespaced, and there is a root namespace under which EnvoyFilter can take effect to all workloads.
- Multiple EnvoyFilters can exists in a namespace and all patches will be processed sequentially (based on creation time).

**Platform Support**

Istio is platform-independent and designed to run in a variety of environments, including those
spanning Cloud, on-premise, Kubernetes, Mesos, and more. You can deploy Istio on Kubernetes, or on
Nomad with Consul, etc.

# Architecture

- *Date: 08/07/2017, v0.1.6*
- *Date: 11/04/2018, v1.0.3*
- *Date: 07/27/2029, v1.6.5*

## Envoy

Istio uses an extended version of the Envoy proxy to mediate all inbound and outbound traffic for all
services in the service mesh. Envoy is deployed as a sidecar to the relevant service in the same
Kubernetes pod. This allows istio to extract a wealth of signals about traffic behavior as attributes,
which in turn can be used in Mixer to enforce policy decisions, and be sent to monitoring systems to
provide information about the behavior of the entire mesh.

## Istiod

In v1.5, all components (mixer, citadel, pilot, galley, injector) are merged into a single component
istiod, which means istiod provides service discovery, configuration and certificate management.

## Mixer (deprecated)

Mixer is responsible for enforcing access control and usage policies across the service mesh and
collecting telemetry data from the Envoy proxy and other services. The proxy extracts request level
attributes, which are sent to Mixer for evaluation. Mixer is a single binary: mixerserver.

Core concepts in Mixer:
- Aspect: define high-level configuration, i.e. what to do. For example, an aspect for rate limiting.
  ```yaml
  rules:
  - aspects:
    - kind: quotas
      params:
        quotas:
        - descriptorName: RequestCount
          maxAmount: 1
          expiration: 1s
  ```
- Adapter: do the real work.
  ```yaml
  adapters:
  - name: myMetricsCollector
    kind: metrics
    impl: prometheus
  ```
- Attribute: request properties, e.g. request.ip
- Selector: selects underline service to apply rules

At 0.1, Mixer is called for every request, which is very slow. 0.2 has plan to cache Mixer response
in envoy sidecar so that not all requests go to Mixer (depends on cache hit rate); also, request to
will be sent to zipkin for tracing. 0.3 will further improve mixer <-> envoy communication protocol,
ref: [google group](https://groups.google.com/forum/#!topic/istio-users/B1NA44QXi9g).

- https://istio.io/docs/concepts/policy-and-control/mixer.html
- https://istio.io/docs/concepts/policy-and-control/mixer-config.html

## Pilot (deprecated)

Pilot is responsible for collecting and validating configuration and propagating it to the various
istio components. It abstracts environment-specific implementation details from Mixer and Envoy,
providing them with an abstract representation of the user's services that is independent of the
underlying platform. In addition, traffic management rules (i.e. generic layer-4 rules and layer-7
HTTP/gRPC routing rules) can be programmed at runtime via Pilot. For overall design on pilot,
ref [design](https://github.com/istio/pilot/blob/5b0f451f41de81448b132f4ee7e8843cea6d823d/doc/design.md).

**istioctl**

istioctl is the commandline tool for istio. It is used to manipulate policies and rules, plus a few
other functionalities like injecting sidecar, etc.

**agent**

Pilot agent is a proxy built from envoy which can be ran as one of:
- sidecar: running along side with every pod in kubernetes. It is injected into pod with `istioctl kube-inject` (will be replaced with PodPreset).
- ingress: handles ingress traffic
- egress: handles egress traffic

For ingress and egress role, pilot agent is running as standalone pods. For sidecar role, it is
running along side with application container. Following is an example pod with injected proxy sidecar:

```yaml
spec:
  containers:
  - image: istio/examples-bookinfo-productpage-v1
    imagePullPolicy: IfNotPresent
    name: productpage
    ports:
    - containerPort: 9080
    resources: {}
  - args:
    - proxy
    - sidecar
    - -v
    - "2"
    env:
    - name: POD_NAME
      valueFrom:
        fieldRef:
          fieldPath: metadata.name
    - name: POD_NAMESPACE
      valueFrom:
        fieldRef:
          fieldPath: metadata.namespace
    - name: POD_IP
      valueFrom:
        fieldRef:
          fieldPath: status.podIP
    image: docker.io/istio/proxy_debug:0.1
```

**discovery**

discovery provides sds, cds, rds for envoy.

## Citadel (deprecated)

Citadel (istio-auth) provides strong service-to-service and end-user authentication using mutual TLS,
with built-in identity and credential management. Istio auth provides three main functionalities:
- identity: workloads are given a strong identity aross the lifetime of any workload. identity is
  not a random string like service name; for kubernetes, istio uses service account as workload
  identity.
- communication security: service-to-service communication is secured through client side envoy and
  server side envoy. The two envoys are communicating with tls, while sidecar envoy and service use
  local TCP.
- istio auth provides a per-cluster CA (Certificate Authority) to automate key and certificate
  management. It distribute key and certificate pair for each service account and rotate/revoke keys
  when necessary.

## Galley (deprecated)

Galley validates user authored Istio API configuration on behalf of the other Istio control plane
components. Over time, Galley will take over responsibility as the top-level configuration ingestion,
processing and distribution component of Istio. It will be responsible for insulating the rest of
the Istio components from the details of obtaining user configuration from the underlying platform
(e.g. Kubernetes).

# Experiment (v0.1.6)

*Date: 08/07/2017, v0.1.6*

## Installation

**Get istio**

Using the following command to get istio and copy required binary to PATH.

```
$ curl -L https://github.com/istio/istio/releases/download/0.1.6/istio-0.1.6-linux.tar.gz | tar xz
$ cp bin/istioctl ~/code/workspace/bin
```

**Start local kubernetes**

For istio version 0.1.6, we use kubernetes release 1.6.7.

```
# Use 'git fetch -t' if tag doesn't exist.
$ git checkout v1.6.7
$ ALLOW_PRIVILEGED=Y ALLOW_SECURITY_CONTEXT=Y KUBE_ENABLE_CLUSTER_DNS=true ENABLE_RBAC=true ./hack/local-up-cluster.sh
```

**Install minimalistic istio**

Following command will install deployments: "istio-mixer", "istio-pilot", "istio-ingress" and
"istio-egress", as well as corresponding configmaps and services. Note we need to make two changes:
- "istio-ingress" service uses LoadBalancer type; for local kubernetes, we change this to NodePort
- change all RoleBinding to ClusterRoleBinding and add "default" namespace to them

This is minimalistic istio, meaning no "istio-auth", no metrics collection, no zipkin integration, etc.
These are optional components; we'll start from simple installation.

```
# Create roles and rolebindings for istio components.
$ kubectl create -f install/kubernetes/istio-rbac-beta.yaml

# Install istio without enabling istio auth.
$ kubectl create -f install/kubernetes/istio.yaml

# Resulting artifacts.
$ kubectl get pods -o wide --all-namespaces
NAMESPACE     NAME                             READY     STATUS    RESTARTS   AGE       IP          NODE
default       istio-egress-815883402-88z9w     1/1       Running   0          4m        10.1.89.6   127.0.0.1
default       istio-ingress-1054723629-wg34f   1/1       Running   0          4m        10.1.89.5   127.0.0.1
default       istio-mixer-2450814972-sbw2t     1/1       Running   0          4m        10.1.89.4   127.0.0.1
default       istio-pilot-1836659236-6bzrp     2/2       Running   0          4m        10.1.89.3   127.0.0.1
kube-system   kube-dns-3664836949-7pxpn        3/3       Running   0          4m        10.1.89.2   127.0.0.1

$ kubectl get svc -o wide --all-namespaces
NAMESPACE     NAME            CLUSTER-IP   EXTERNAL-IP   PORT(S)                       AGE       SELECTOR
default       istio-egress    10.0.0.249   <none>        80/TCP                        4m        istio=egress
default       istio-ingress   10.0.0.223   <nodes>       80:31318/TCP,443:30524/TCP    4m        istio=ingress
default       istio-mixer     10.0.0.72    <none>        9091/TCP,9094/TCP,42422/TCP   4m        istio=mixer
default       istio-pilot     10.0.0.11    <none>        8080/TCP,8081/TCP             4m        istio=pilot
default       kubernetes      10.0.0.1     <none>        443/TCP                       5m        <none>
kube-system   kube-dns        10.0.0.10    <none>        53/UDP,53/TCP                 5m        k8s-app=kube-dns
```

## Components

**Component details**

`istio-pilot` contains two containers: one started with `pilot apiserver`, the other started with
`pilot discovery`. The apiserver process exposes endpoints to CRUD istio config (as kubernetes TPR).
The discovery process implements envoy's SDS, CDS and RDS, which can be seen as propagating kubernetes
information to all envoy proxies. As we can see below, envoy proxies configure istio-pilot as its
source of discovery.

For example, querying `v1/registration` endpoint of istio-pilot in sds gives:

<details><summary>istio-pilot sds</summary><p>

```
$ curl 10.0.0.11:8080/v1/registration
[
  {
   "service-key": "istio-egress.default.svc.cluster.local",
   "hosts": [
    {
     "ip_address": "10.1.89.6",
     "port": 80
    }
   ]
  },
  {
   "service-key": "istio-ingress.default.svc.cluster.local|http",
   "hosts": [
    {
     "ip_address": "10.1.89.5",
     "port": 80
    }
   ]
  },
  {
   "service-key": "istio-ingress.default.svc.cluster.local|https",
   "hosts": [
    {
     "ip_address": "10.1.89.5",
     "port": 443
    }
   ]
  },
  {
   "service-key": "istio-mixer.default.svc.cluster.local|configapi",
   "hosts": [
    {
     "ip_address": "10.1.89.4",
     "port": 9094
    }
   ]
  },
  {
   "service-key": "istio-mixer.default.svc.cluster.local|prometheus",
   "hosts": [
    {
     "ip_address": "10.1.89.4",
     "port": 42422
    }
   ]
  },
  {
   "service-key": "istio-mixer.default.svc.cluster.local|tcp",
   "hosts": [
    {
     "ip_address": "10.1.89.4",
     "port": 9091
    }
   ]
  },
  {
   "service-key": "istio-pilot.default.svc.cluster.local|http-apiserver",
   "hosts": [
    {
     "ip_address": "10.1.89.3",
     "port": 8081
    }
   ]
  },
  {
   "service-key": "istio-pilot.default.svc.cluster.local|http-discovery",
   "hosts": [
    {
     "ip_address": "10.1.89.3",
     "port": 8080
    }
   ]
  },
  {
   "service-key": "kubernetes.default.svc.cluster.local|https",
   "hosts": [
    {
     "ip_address": "10.0.2.15",
     "port": 6443
    }
   ]
  }
 ]
```

</p></details></br>

The above is informational, it's not called by envoy. Below is a real query:

```
$ curl 10.0.0.11:8080/v1/registration/kubernetes.default.svc.cluster.local\|https
{
  "hosts": [
   {
    "ip_address": "10.0.2.15",
    "port": 6443
   }
  ]
}
```

This tells that sds in istio-pilot is "kubernetes service fqdn -> kubernetes endpoints". If we run a
deployment with two replicas and expose via a service, i.e.

```
kubectl run nginx --image=nginx:1.13.5-alpine --replicas=2
kubectl expose deployment nginx --port 8888
```

We'll get this from sds:

```
{
 "service-key": "nginx.default.svc.cluster.local",
 "hosts": [
  {
   "ip_address": "10.1.89.7",
   "port": 8888
  },
  {
   "ip_address": "10.1.89.8",
   "port": 8888
  }
 ]
}
```

Querying `v1/clusters` returns all clusters:

<details><summary>All clusters</summary><p>

```
$ curl 10.0.0.11:8080/v1/clusters
[
  {
   "service-cluster": "istio-proxy",
   "service-node": "10.0.2.15",
   "clusters": [
    {
     "name": "out.01b3502fc7b29750c3b185358aec68fcbb4b9cf6",
     "service_name": "istio-pilot.default.svc.cluster.local|http-discovery",
     "connect_timeout_ms": 1000,
     "type": "sds",
     "lb_type": "round_robin"
    },
    {
     "name": "out.96c4dfcd665fa0caf6f48ab026e4263d1d17bac2",
     "service_name": "istio-pilot.default.svc.cluster.local|http-apiserver",
     "connect_timeout_ms": 1000,
     "type": "sds",
     "lb_type": "round_robin"
    },
    {
     "name": "out.fd518f1d0ba070c47739cbf6b191f85eb1cdda3d",
     "service_name": "istio-ingress.default.svc.cluster.local|http",
     "connect_timeout_ms": 1000,
     "type": "sds",
     "lb_type": "round_robin"
    }
   ]
  },
  {
   "service-cluster": "istio-proxy",
   "service-node": "10.1.89.3",
   "clusters": [
    {
     "name": "out.01b3502fc7b29750c3b185358aec68fcbb4b9cf6",
     "service_name": "istio-pilot.default.svc.cluster.local|http-discovery",
     "connect_timeout_ms": 1000,
     "type": "sds",
     "lb_type": "round_robin"
    },
    {
     "name": "out.96c4dfcd665fa0caf6f48ab026e4263d1d17bac2",
     "service_name": "istio-pilot.default.svc.cluster.local|http-apiserver",
     "connect_timeout_ms": 1000,
     "type": "sds",
     "lb_type": "round_robin"
    },
    {
     "name": "out.fd518f1d0ba070c47739cbf6b191f85eb1cdda3d",
     "service_name": "istio-ingress.default.svc.cluster.local|http",
     "connect_timeout_ms": 1000,
     "type": "sds",
     "lb_type": "round_robin"
    }
   ]
  },
  {
   "service-cluster": "istio-proxy",
   "service-node": "10.1.89.4",
   "clusters": [
    {
     "name": "out.01b3502fc7b29750c3b185358aec68fcbb4b9cf6",
     "service_name": "istio-pilot.default.svc.cluster.local|http-discovery",
     "connect_timeout_ms": 1000,
     "type": "sds",
     "lb_type": "round_robin"
    },
    {
     "name": "out.96c4dfcd665fa0caf6f48ab026e4263d1d17bac2",
     "service_name": "istio-pilot.default.svc.cluster.local|http-apiserver",
     "connect_timeout_ms": 1000,
     "type": "sds",
     "lb_type": "round_robin"
    },
    {
     "name": "out.fd518f1d0ba070c47739cbf6b191f85eb1cdda3d",
     "service_name": "istio-ingress.default.svc.cluster.local|http",
     "connect_timeout_ms": 1000,
     "type": "sds",
     "lb_type": "round_robin"
    }
   ]
  },
  {
   "service-cluster": "istio-proxy",
   "service-node": "10.1.89.5",
   "clusters": [
    {
     "name": "out.01b3502fc7b29750c3b185358aec68fcbb4b9cf6",
     "service_name": "istio-pilot.default.svc.cluster.local|http-discovery",
     "connect_timeout_ms": 1000,
     "type": "sds",
     "lb_type": "round_robin"
    },
    {
     "name": "out.96c4dfcd665fa0caf6f48ab026e4263d1d17bac2",
     "service_name": "istio-pilot.default.svc.cluster.local|http-apiserver",
     "connect_timeout_ms": 1000,
     "type": "sds",
     "lb_type": "round_robin"
    },
    {
     "name": "out.fd518f1d0ba070c47739cbf6b191f85eb1cdda3d",
     "service_name": "istio-ingress.default.svc.cluster.local|http",
     "connect_timeout_ms": 1000,
     "type": "sds",
     "lb_type": "round_robin"
    }
   ]
  },
  {
   "service-cluster": "istio-proxy",
   "service-node": "10.1.89.6",
   "clusters": [
    {
     "name": "out.01b3502fc7b29750c3b185358aec68fcbb4b9cf6",
     "service_name": "istio-pilot.default.svc.cluster.local|http-discovery",
     "connect_timeout_ms": 1000,
     "type": "sds",
     "lb_type": "round_robin"
    },
    {
     "name": "out.96c4dfcd665fa0caf6f48ab026e4263d1d17bac2",
     "service_name": "istio-pilot.default.svc.cluster.local|http-apiserver",
     "connect_timeout_ms": 1000,
     "type": "sds",
     "lb_type": "round_robin"
    },
    {
     "name": "out.fd518f1d0ba070c47739cbf6b191f85eb1cdda3d",
     "service_name": "istio-ingress.default.svc.cluster.local|http",
     "connect_timeout_ms": 1000,
     "type": "sds",
     "lb_type": "round_robin"
    }
   ]
  },
  {
   "service-cluster": "istio-proxy",
   "service-node": "10.1.89.7",
   "clusters": [
    {
     "name": "out.01b3502fc7b29750c3b185358aec68fcbb4b9cf6",
     "service_name": "istio-pilot.default.svc.cluster.local|http-discovery",
     "connect_timeout_ms": 1000,
     "type": "sds",
     "lb_type": "round_robin"
    },
    {
     "name": "out.96c4dfcd665fa0caf6f48ab026e4263d1d17bac2",
     "service_name": "istio-pilot.default.svc.cluster.local|http-apiserver",
     "connect_timeout_ms": 1000,
     "type": "sds",
     "lb_type": "round_robin"
    },
    {
     "name": "out.fd518f1d0ba070c47739cbf6b191f85eb1cdda3d",
     "service_name": "istio-ingress.default.svc.cluster.local|http",
     "connect_timeout_ms": 1000,
     "type": "sds",
     "lb_type": "round_robin"
    }
   ]
  },
  {
   "service-cluster": "istio-proxy",
   "service-node": "10.1.89.8",
   "clusters": [
    {
     "name": "out.01b3502fc7b29750c3b185358aec68fcbb4b9cf6",
     "service_name": "istio-pilot.default.svc.cluster.local|http-discovery",
     "connect_timeout_ms": 1000,
     "type": "sds",
     "lb_type": "round_robin"
    },
    {
     "name": "out.96c4dfcd665fa0caf6f48ab026e4263d1d17bac2",
     "service_name": "istio-pilot.default.svc.cluster.local|http-apiserver",
     "connect_timeout_ms": 1000,
     "type": "sds",
     "lb_type": "round_robin"
    },
    {
     "name": "out.fd518f1d0ba070c47739cbf6b191f85eb1cdda3d",
     "service_name": "istio-ingress.default.svc.cluster.local|http",
     "connect_timeout_ms": 1000,
     "type": "sds",
     "lb_type": "round_robin"
    }
   ]
  }
 ]
```

</p></details></br>

Querying `v1/routes` returns all routes:

<details><summary>All routes</summary><p>

```
$ curl 10.0.0.11:8080/v1/routes
[
 {
  "route-config-name": "80",
  "service-cluster": "istio-proxy",
  "service-node": "10.0.2.15",
  "virtual_hosts": [
   {
    "name": "istio-ingress.default.svc.cluster.local|http",
    "domains": [
     "istio-ingress:80",
     "istio-ingress",
     "istio-ingress.default:80",
     "istio-ingress.default",
     "istio-ingress.default.svc:80",
     "istio-ingress.default.svc",
     "istio-ingress.default.svc.cluster:80",
     "istio-ingress.default.svc.cluster",
     "istio-ingress.default.svc.cluster.local:80",
     "istio-ingress.default.svc.cluster.local",
     "10.0.0.223:80",
     "10.0.0.223"
    ],
    "routes": [
     {
      "prefix": "/",
      "cluster": "out.fd518f1d0ba070c47739cbf6b191f85eb1cdda3d"
     }
    ]
   }
  ]
 },
 {
  "route-config-name": "80",
  "service-cluster": "istio-proxy",
  "service-node": "10.1.89.3",
  "virtual_hosts": [
   {
    "name": "istio-ingress.default.svc.cluster.local|http",
    "domains": [
     "istio-ingress:80",
     "istio-ingress",
     "istio-ingress.default:80",
     "istio-ingress.default",
     "istio-ingress.default.svc:80",
     "istio-ingress.default.svc",
     "istio-ingress.default.svc.cluster:80",
     "istio-ingress.default.svc.cluster",
     "istio-ingress.default.svc.cluster.local:80",
     "istio-ingress.default.svc.cluster.local",
     "10.0.0.223:80",
     "10.0.0.223"
    ],
    "routes": [
     {
      "prefix": "/",
      "cluster": "out.fd518f1d0ba070c47739cbf6b191f85eb1cdda3d"
     }
    ]
   }
  ]
 },
 {
  "route-config-name": "80",
  "service-cluster": "istio-proxy",
  "service-node": "10.1.89.4",
  "virtual_hosts": [
   {
    "name": "istio-ingress.default.svc.cluster.local|http",
    "domains": [
     "istio-ingress:80",
     "istio-ingress",
     "istio-ingress.default:80",
     "istio-ingress.default",
     "istio-ingress.default.svc:80",
     "istio-ingress.default.svc",
     "istio-ingress.default.svc.cluster:80",
     "istio-ingress.default.svc.cluster",
     "istio-ingress.default.svc.cluster.local:80",
     "istio-ingress.default.svc.cluster.local",
     "10.0.0.223:80",
     "10.0.0.223"
    ],
    "routes": [
     {
      "prefix": "/",
      "cluster": "out.fd518f1d0ba070c47739cbf6b191f85eb1cdda3d"
     }
    ]
   }
  ]
 },
 {
  "route-config-name": "80",
  "service-cluster": "istio-proxy",
  "service-node": "10.1.89.5",
  "virtual_hosts": [
   {
    "name": "istio-ingress.default.svc.cluster.local|http",
    "domains": [
     "istio-ingress:80",
     "istio-ingress",
     "istio-ingress.default:80",
     "istio-ingress.default",
     "istio-ingress.default.svc:80",
     "istio-ingress.default.svc",
     "istio-ingress.default.svc.cluster:80",
     "istio-ingress.default.svc.cluster",
     "istio-ingress.default.svc.cluster.local:80",
     "istio-ingress.default.svc.cluster.local",
     "10.0.0.223:80",
     "10.0.0.223"
    ],
    "routes": [
     {
      "prefix": "/",
      "cluster": "out.fd518f1d0ba070c47739cbf6b191f85eb1cdda3d"
     }
    ]
   }
  ]
 },
 {
  "route-config-name": "80",
  "service-cluster": "istio-proxy",
  "service-node": "10.1.89.6",
  "virtual_hosts": [
   {
    "name": "istio-ingress.default.svc.cluster.local|http",
    "domains": [
     "istio-ingress:80",
     "istio-ingress",
     "istio-ingress.default:80",
     "istio-ingress.default",
     "istio-ingress.default.svc:80",
     "istio-ingress.default.svc",
     "istio-ingress.default.svc.cluster:80",
     "istio-ingress.default.svc.cluster",
     "istio-ingress.default.svc.cluster.local:80",
     "istio-ingress.default.svc.cluster.local",
     "10.0.0.223:80",
     "10.0.0.223"
    ],
    "routes": [
     {
      "prefix": "/",
      "cluster": "out.fd518f1d0ba070c47739cbf6b191f85eb1cdda3d"
     }
    ]
   }
  ]
 },
 {
  "route-config-name": "80",
  "service-cluster": "istio-proxy",
  "service-node": "10.1.89.7",
  "virtual_hosts": [
   {
    "name": "istio-ingress.default.svc.cluster.local|http",
    "domains": [
     "istio-ingress:80",
     "istio-ingress",
     "istio-ingress.default:80",
     "istio-ingress.default",
     "istio-ingress.default.svc:80",
     "istio-ingress.default.svc",
     "istio-ingress.default.svc.cluster:80",
     "istio-ingress.default.svc.cluster",
     "istio-ingress.default.svc.cluster.local:80",
     "istio-ingress.default.svc.cluster.local",
     "10.0.0.223:80",
     "10.0.0.223"
    ],
    "routes": [
     {
      "prefix": "/",
      "cluster": "out.fd518f1d0ba070c47739cbf6b191f85eb1cdda3d"
     }
    ]
   }
  ]
 },
 {
  "route-config-name": "80",
  "service-cluster": "istio-proxy",
  "service-node": "10.1.89.8",
  "virtual_hosts": [
   {
    "name": "istio-ingress.default.svc.cluster.local|http",
    "domains": [
     "istio-ingress:80",
     "istio-ingress",
     "istio-ingress.default:80",
     "istio-ingress.default",
     "istio-ingress.default.svc:80",
     "istio-ingress.default.svc",
     "istio-ingress.default.svc.cluster:80",
     "istio-ingress.default.svc.cluster",
     "istio-ingress.default.svc.cluster.local:80",
     "istio-ingress.default.svc.cluster.local",
     "10.0.0.223:80",
     "10.0.0.223"
    ],
    "routes": [
     {
      "prefix": "/",
      "cluster": "out.fd518f1d0ba070c47739cbf6b191f85eb1cdda3d"
     }
    ]
   }
  ]
 },
 {
  "route-config-name": "8080",
  "service-cluster": "istio-proxy",
  "service-node": "10.0.2.15",
  "virtual_hosts": [
   {
    "name": "istio-pilot.default.svc.cluster.local|http-discovery",
    "domains": [
     "istio-pilot:8080",
     "istio-pilot",
     "istio-pilot.default:8080",
     "istio-pilot.default",
     "istio-pilot.default.svc:8080",
     "istio-pilot.default.svc",
     "istio-pilot.default.svc.cluster:8080",
     "istio-pilot.default.svc.cluster",
     "istio-pilot.default.svc.cluster.local:8080",
     "istio-pilot.default.svc.cluster.local",
     "10.0.0.11:8080",
     "10.0.0.11"
    ],
    "routes": [
     {
      "prefix": "/",
      "cluster": "out.01b3502fc7b29750c3b185358aec68fcbb4b9cf6"
     }
    ]
   }
  ]
 },
 {
  "route-config-name": "8080",
  "service-cluster": "istio-proxy",
  "service-node": "10.1.89.3",
  "virtual_hosts": [
   {
    "name": "istio-pilot.default.svc.cluster.local|http-discovery",
    "domains": [
     "istio-pilot:8080",
     "istio-pilot",
     "istio-pilot.default:8080",
     "istio-pilot.default",
     "istio-pilot.default.svc:8080",
     "istio-pilot.default.svc",
     "istio-pilot.default.svc.cluster:8080",
     "istio-pilot.default.svc.cluster",
     "istio-pilot.default.svc.cluster.local:8080",
     "istio-pilot.default.svc.cluster.local",
     "10.0.0.11:8080",
     "10.0.0.11"
    ],
    "routes": [
     {
      "prefix": "/",
      "cluster": "out.01b3502fc7b29750c3b185358aec68fcbb4b9cf6"
     }
    ]
   }
  ]
 },
 {
  "route-config-name": "8080",
  "service-cluster": "istio-proxy",
  "service-node": "10.1.89.4",
  "virtual_hosts": [
   {
    "name": "istio-pilot.default.svc.cluster.local|http-discovery",
    "domains": [
     "istio-pilot:8080",
     "istio-pilot",
     "istio-pilot.default:8080",
     "istio-pilot.default",
     "istio-pilot.default.svc:8080",
     "istio-pilot.default.svc",
     "istio-pilot.default.svc.cluster:8080",
     "istio-pilot.default.svc.cluster",
     "istio-pilot.default.svc.cluster.local:8080",
     "istio-pilot.default.svc.cluster.local",
     "10.0.0.11:8080",
     "10.0.0.11"
    ],
    "routes": [
     {
      "prefix": "/",
      "cluster": "out.01b3502fc7b29750c3b185358aec68fcbb4b9cf6"
     }
    ]
   }
  ]
 },
 {
  "route-config-name": "8080",
  "service-cluster": "istio-proxy",
  "service-node": "10.1.89.5",
  "virtual_hosts": [
   {
    "name": "istio-pilot.default.svc.cluster.local|http-discovery",
    "domains": [
     "istio-pilot:8080",
     "istio-pilot",
     "istio-pilot.default:8080",
     "istio-pilot.default",
     "istio-pilot.default.svc:8080",
     "istio-pilot.default.svc",
     "istio-pilot.default.svc.cluster:8080",
     "istio-pilot.default.svc.cluster",
     "istio-pilot.default.svc.cluster.local:8080",
     "istio-pilot.default.svc.cluster.local",
     "10.0.0.11:8080",
     "10.0.0.11"
    ],
    "routes": [
     {
      "prefix": "/",
      "cluster": "out.01b3502fc7b29750c3b185358aec68fcbb4b9cf6"
     }
    ]
   }
  ]
 },
 {
  "route-config-name": "8080",
  "service-cluster": "istio-proxy",
  "service-node": "10.1.89.6",
  "virtual_hosts": [
   {
    "name": "istio-pilot.default.svc.cluster.local|http-discovery",
    "domains": [
     "istio-pilot:8080",
     "istio-pilot",
     "istio-pilot.default:8080",
     "istio-pilot.default",
     "istio-pilot.default.svc:8080",
     "istio-pilot.default.svc",
     "istio-pilot.default.svc.cluster:8080",
     "istio-pilot.default.svc.cluster",
     "istio-pilot.default.svc.cluster.local:8080",
     "istio-pilot.default.svc.cluster.local",
     "10.0.0.11:8080",
     "10.0.0.11"
    ],
    "routes": [
     {
      "prefix": "/",
      "cluster": "out.01b3502fc7b29750c3b185358aec68fcbb4b9cf6"
     }
    ]
   }
  ]
 },
 {
  "route-config-name": "8080",
  "service-cluster": "istio-proxy",
  "service-node": "10.1.89.7",
  "virtual_hosts": [
   {
    "name": "istio-pilot.default.svc.cluster.local|http-discovery",
    "domains": [
     "istio-pilot:8080",
     "istio-pilot",
     "istio-pilot.default:8080",
     "istio-pilot.default",
     "istio-pilot.default.svc:8080",
     "istio-pilot.default.svc",
     "istio-pilot.default.svc.cluster:8080",
     "istio-pilot.default.svc.cluster",
     "istio-pilot.default.svc.cluster.local:8080",
     "istio-pilot.default.svc.cluster.local",
     "10.0.0.11:8080",
     "10.0.0.11"
    ],
    "routes": [
     {
      "prefix": "/",
      "cluster": "out.01b3502fc7b29750c3b185358aec68fcbb4b9cf6"
     }
    ]
   }
  ]
 },
 {
  "route-config-name": "8080",
  "service-cluster": "istio-proxy",
  "service-node": "10.1.89.8",
  "virtual_hosts": [
   {
    "name": "istio-pilot.default.svc.cluster.local|http-discovery",
    "domains": [
     "istio-pilot:8080",
     "istio-pilot",
     "istio-pilot.default:8080",
     "istio-pilot.default",
     "istio-pilot.default.svc:8080",
     "istio-pilot.default.svc",
     "istio-pilot.default.svc.cluster:8080",
     "istio-pilot.default.svc.cluster",
     "istio-pilot.default.svc.cluster.local:8080",
     "istio-pilot.default.svc.cluster.local",
     "10.0.0.11:8080",
     "10.0.0.11"
    ],
    "routes": [
     {
      "prefix": "/",
      "cluster": "out.01b3502fc7b29750c3b185358aec68fcbb4b9cf6"
     }
    ]
   }
  ]
 },
 {
  "route-config-name": "8081",
  "service-cluster": "istio-proxy",
  "service-node": "10.0.2.15",
  "virtual_hosts": [
   {
    "name": "istio-pilot.default.svc.cluster.local|http-apiserver",
    "domains": [
     "istio-pilot:8081",
     "istio-pilot",
     "istio-pilot.default:8081",
     "istio-pilot.default",
     "istio-pilot.default.svc:8081",
     "istio-pilot.default.svc",
     "istio-pilot.default.svc.cluster:8081",
     "istio-pilot.default.svc.cluster",
     "istio-pilot.default.svc.cluster.local:8081",
     "istio-pilot.default.svc.cluster.local",
     "10.0.0.11:8081",
     "10.0.0.11"
    ],
    "routes": [
     {
      "prefix": "/",
      "cluster": "out.96c4dfcd665fa0caf6f48ab026e4263d1d17bac2"
     }
    ]
   }
  ]
 },
 {
  "route-config-name": "8081",
  "service-cluster": "istio-proxy",
  "service-node": "10.1.89.3",
  "virtual_hosts": [
   {
    "name": "istio-pilot.default.svc.cluster.local|http-apiserver",
    "domains": [
     "istio-pilot:8081",
     "istio-pilot",
     "istio-pilot.default:8081",
     "istio-pilot.default",
     "istio-pilot.default.svc:8081",
     "istio-pilot.default.svc",
     "istio-pilot.default.svc.cluster:8081",
     "istio-pilot.default.svc.cluster",
     "istio-pilot.default.svc.cluster.local:8081",
     "istio-pilot.default.svc.cluster.local",
     "10.0.0.11:8081",
     "10.0.0.11"
    ],
    "routes": [
     {
      "prefix": "/",
      "cluster": "out.96c4dfcd665fa0caf6f48ab026e4263d1d17bac2"
     }
    ]
   }
  ]
 },
 {
  "route-config-name": "8081",
  "service-cluster": "istio-proxy",
  "service-node": "10.1.89.4",
  "virtual_hosts": [
   {
    "name": "istio-pilot.default.svc.cluster.local|http-apiserver",
    "domains": [
     "istio-pilot:8081",
     "istio-pilot",
     "istio-pilot.default:8081",
     "istio-pilot.default",
     "istio-pilot.default.svc:8081",
     "istio-pilot.default.svc",
     "istio-pilot.default.svc.cluster:8081",
     "istio-pilot.default.svc.cluster",
     "istio-pilot.default.svc.cluster.local:8081",
     "istio-pilot.default.svc.cluster.local",
     "10.0.0.11:8081",
     "10.0.0.11"
    ],
    "routes": [
     {
      "prefix": "/",
      "cluster": "out.96c4dfcd665fa0caf6f48ab026e4263d1d17bac2"
     }
    ]
   }
  ]
 },
 {
  "route-config-name": "8081",
  "service-cluster": "istio-proxy",
  "service-node": "10.1.89.5",
  "virtual_hosts": [
   {
    "name": "istio-pilot.default.svc.cluster.local|http-apiserver",
    "domains": [
     "istio-pilot:8081",
     "istio-pilot",
     "istio-pilot.default:8081",
     "istio-pilot.default",
     "istio-pilot.default.svc:8081",
     "istio-pilot.default.svc",
     "istio-pilot.default.svc.cluster:8081",
     "istio-pilot.default.svc.cluster",
     "istio-pilot.default.svc.cluster.local:8081",
     "istio-pilot.default.svc.cluster.local",
     "10.0.0.11:8081",
     "10.0.0.11"
    ],
    "routes": [
     {
      "prefix": "/",
      "cluster": "out.96c4dfcd665fa0caf6f48ab026e4263d1d17bac2"
     }
    ]
   }
  ]
 },
 {
  "route-config-name": "8081",
  "service-cluster": "istio-proxy",
  "service-node": "10.1.89.6",
  "virtual_hosts": [
   {
    "name": "istio-pilot.default.svc.cluster.local|http-apiserver",
    "domains": [
     "istio-pilot:8081",
     "istio-pilot",
     "istio-pilot.default:8081",
     "istio-pilot.default",
     "istio-pilot.default.svc:8081",
     "istio-pilot.default.svc",
     "istio-pilot.default.svc.cluster:8081",
     "istio-pilot.default.svc.cluster",
     "istio-pilot.default.svc.cluster.local:8081",
     "istio-pilot.default.svc.cluster.local",
     "10.0.0.11:8081",
     "10.0.0.11"
    ],
    "routes": [
     {
      "prefix": "/",
      "cluster": "out.96c4dfcd665fa0caf6f48ab026e4263d1d17bac2"
     }
    ]
   }
  ]
 },
 {
  "route-config-name": "8081",
  "service-cluster": "istio-proxy",
  "service-node": "10.1.89.7",
  "virtual_hosts": [
   {
    "name": "istio-pilot.default.svc.cluster.local|http-apiserver",
    "domains": [
     "istio-pilot:8081",
     "istio-pilot",
     "istio-pilot.default:8081",
     "istio-pilot.default",
     "istio-pilot.default.svc:8081",
     "istio-pilot.default.svc",
     "istio-pilot.default.svc.cluster:8081",
     "istio-pilot.default.svc.cluster",
     "istio-pilot.default.svc.cluster.local:8081",
     "istio-pilot.default.svc.cluster.local",
     "10.0.0.11:8081",
     "10.0.0.11"
    ],
    "routes": [
     {
      "prefix": "/",
      "cluster": "out.96c4dfcd665fa0caf6f48ab026e4263d1d17bac2"
     }
    ]
   }
  ]
 },
 {
  "route-config-name": "8081",
  "service-cluster": "istio-proxy",
  "service-node": "10.1.89.8",
  "virtual_hosts": [
   {
    "name": "istio-pilot.default.svc.cluster.local|http-apiserver",
    "domains": [
     "istio-pilot:8081",
     "istio-pilot",
     "istio-pilot.default:8081",
     "istio-pilot.default",
     "istio-pilot.default.svc:8081",
     "istio-pilot.default.svc",
     "istio-pilot.default.svc.cluster:8081",
     "istio-pilot.default.svc.cluster",
     "istio-pilot.default.svc.cluster.local:8081",
     "istio-pilot.default.svc.cluster.local",
     "10.0.0.11:8081",
     "10.0.0.11"
    ],
    "routes": [
     {
      "prefix": "/",
      "cluster": "out.96c4dfcd665fa0caf6f48ab026e4263d1d17bac2"
     }
    ]
   }
  ]
 }
]
```

</p></details></br>


To find how istio/envoy handles traffic. First look at configuration of an envoy instance. Then look
at `v1/routes` to see where traffic is sent (a cluster), then look at `v1/clusters` and `v1/registration`
to see what constitute the cluster.

**Envoy ingress/egress config**

At this point, we can take a look at configs in envoy. Below is ingress envoy config (under /etc/envoy
in istio-ingress pod):

<details><summary>Ingress Envoy</summary><p>

```
{
  "listeners": [
    {
      "address": "tcp://0.0.0.0:80",
      "filters": [
        {
          "type": "read",
          "name": "http_connection_manager",
          "config": {
            "codec_type": "auto",
            "stat_prefix": "http",
            "generate_request_id": true,
            "use_remote_address": true,
            "tracing": {
              "operation_name": "ingress"
            },
            "rds": {
              "cluster": "rds",
              "route_config_name": "80",
              "refresh_delay_ms": 1000
            },
            "filters": [
              {
                "type": "decoder",
                "name": "router",
                "config": {}
              }
            ],
            "access_log": [
              {
                "path": "/dev/stdout"
              }
            ]
          }
        }
      ],
      "bind_to_port": true
    }
  ],
  "admin": {
    "access_log_path": "/dev/stdout",
    "address": "tcp://0.0.0.0:15000"
  },
  "cluster_manager": {
    "clusters": [
      {
        "name": "zipkin",
        "connect_timeout_ms": 1000,
        "type": "strict_dns",
        "lb_type": "round_robin",
        "hosts": [
          {
            "url": "tcp://zipkin:9411"
          }
        ]
      },
      {
        "name": "rds",
        "connect_timeout_ms": 1000,
        "type": "strict_dns",
        "lb_type": "round_robin",
        "hosts": [
          {
            "url": "tcp://istio-pilot:8080"
          }
        ]
      }
    ],
    "sds": {
      "cluster": {
        "name": "sds",
        "connect_timeout_ms": 1000,
        "type": "strict_dns",
        "lb_type": "round_robin",
        "hosts": [
          {
            "url": "tcp://istio-pilot:8080"
          }
        ]
      },
      "refresh_delay_ms": 1000
    },
    "cds": {
      "cluster": {
        "name": "cds",
        "connect_timeout_ms": 1000,
        "type": "strict_dns",
        "lb_type": "round_robin",
        "hosts": [
          {
            "url": "tcp://istio-pilot:8080"
          }
        ]
      },
      "refresh_delay_ms": 1000
    }
  },
  "tracing": {
    "http": {
      "driver": {
        "type": "zipkin",
        "config": {
          "collector_cluster": "zipkin",
          "collector_endpoint": "/api/v1/spans"
        }
      }
    }
  }
}
```

</p></details></br>

As shown in the config, apart from zipkin, which is a well-defined service, there is nothing static
configured in ingress envoy; everything is dynamic, i.e. istio uses "rds" to discover routes, uses
"sds" to discover services of a cluster, uses "cds" to discover cluster. All discovery services run
in "istio-pilot" service. Config from egress envoy is the same (even though tracing name == "ingress"),
i.e.

<details><summary>Egress Envoy</summary><p>

```
{
  "listeners": [
    {
      "address": "tcp://0.0.0.0:80",
      "filters": [
        {
          "type": "read",
          "name": "http_connection_manager",
          "config": {
            "codec_type": "auto",
            "stat_prefix": "http",
            "generate_request_id": true,
            "tracing": {
              "operation_name": "ingress"
            },
            "rds": {
              "cluster": "rds",
              "route_config_name": "80",
              "refresh_delay_ms": 1000
            },
            "filters": [
              {
                "type": "decoder",
                "name": "router",
                "config": {}
              }
            ],
            "access_log": [
              {
                "path": "/dev/stdout"
              }
            ]
          }
        }
      ],
      "bind_to_port": true
    }
  ],
  "admin": {
    "access_log_path": "/dev/stdout",
    "address": "tcp://0.0.0.0:15000"
  },
  "cluster_manager": {
    "clusters": [
      {
        "name": "zipkin",
        "connect_timeout_ms": 1000,
        "type": "strict_dns",
        "lb_type": "round_robin",
        "hosts": [
          {
            "url": "tcp://zipkin:9411"
          }
        ]
      },
      {
        "name": "rds",
        "connect_timeout_ms": 1000,
        "type": "strict_dns",
        "lb_type": "round_robin",
        "hosts": [
          {
            "url": "tcp://istio-pilot:8080"
          }
        ]
      }
    ],
    "sds": {
      "cluster": {
        "name": "sds",
        "connect_timeout_ms": 1000,
        "type": "strict_dns",
        "lb_type": "round_robin",
        "hosts": [
          {
            "url": "tcp://istio-pilot:8080"
          }
        ]
      },
      "refresh_delay_ms": 1000
    },
    "cds": {
      "cluster": {
        "name": "cds",
        "connect_timeout_ms": 1000,
        "type": "strict_dns",
        "lb_type": "round_robin",
        "hosts": [
          {
            "url": "tcp://istio-pilot:8080"
          }
        ]
      },
      "refresh_delay_ms": 1000
    }
  },
  "tracing": {
    "http": {
      "driver": {
        "type": "zipkin",
        "config": {
          "collector_cluster": "zipkin",
          "collector_endpoint": "/api/v1/spans"
        }
      }
    }
  }
}
```

</p></details></br>

**Envoy <-> Istio concept**

Each kubernetes service is a cluster in envoy. Each kubernetes pod is the service-node parameter in envoy.

## Tasks

**Task1: Integrating Services into the Mesh**

The task creates two services (client and server) and investigates sidecar proxy.

<details><summary>Run Application</summary><p>

```
# Create applications.
$ kubectl apply -f <(istioctl kube-inject -f task1/apps.yaml)

# All existing pods.
$ kubectl get pods -o wide
NAME                             READY     STATUS    RESTARTS   AGE       IP           NODE
istio-egress-815883402-2vmhs     1/1       Running   0          16m       172.17.0.6   127.0.0.1
istio-ingress-1054723629-v2mjb   1/1       Running   0          16m       172.17.0.5   127.0.0.1
istio-mixer-2450814972-1fhmr     1/1       Running   0          16m       172.17.0.3   127.0.0.1
istio-pilot-1836659236-3ls9r     2/2       Running   0          16m       172.17.0.4   127.0.0.1
service-one-1736709432-pc2zg     2/2       Running   0          7m        172.17.0.7   127.0.0.1
service-two-3955561808-q0gsh     2/2       Running   0          7m        172.17.0.8   127.0.0.1

# Find the server and client pods. "service-one" is our client and "service-two"
# is our server.
$ CLIENT=$(kubectl get pod -l app=service-one -o jsonpath='{.items[0].metadata.name}')
$ SERVER=$(kubectl get pod -l app=service-two -o jsonpath='{.items[0].metadata.name}')

# Send a request from client. Note we are sending request from "app" container of
# the client; not the proxy sidecar.
$ kubectl exec -it ${CLIENT} -c app -- curl service-two:80 | grep x-request-id
x-request-id=cd30da12-ee24-9429-b188-2d494017c083

# From client log, we see that request goes through client sidecar proxy first.
# The endpoint "172.17.0.8:8080" is the server's pod IP:Port, NOT service.
$ kubectl logs ${CLIENT} proxy | grep cd30da12-ee24-9429-b188-2d494017c083
[2017-08-08T00:22:56.670Z] "GET / HTTP/1.1" 200 - 0 558 107 106 "-" "curl/7.47.0" "cd30da12-ee24-9429-b188-2d494017c083" "service-two" "172.17.0.8:8080"

# From server log, we see that request goes through server sidecar proxy first.
$ kubectl logs ${SERVER} proxy | grep cd30da12-ee24-9429-b188-2d494017c083
[2017-08-08T00:22:56.671Z] "GET / HTTP/1.1" 200 - 0 558 105 0 "-" "curl/7.47.0" "cd30da12-ee24-9429-b188-2d494017c083" "service-two" "127.0.0.1:8080"
```

</p></details></br>

Apart from the injected sidecar container, each pod also has init containers. One of them is used to
enable core dump (debug); the other is used to transparently redirect all inbound and outbound traffic
to the proxy. It is running as an init container because:
- iptables requires NET_CAP_ADMIN.
- The sidecar iptable rules are fixed and don’t need to be updated after pod creation.

Following is the iptable rules (code located at `pilot/docker/prepare_proxy.sh`). Note '-m owner'
module is used to differentiate traffic from envoy.

<details><summary>iptable rules</summary><p>

```
# Generated by iptables-save v1.6.0 on Tue Aug  8 00:57:06 2017
*mangle
:PREROUTING ACCEPT [54:2700]
:INPUT ACCEPT [54:2700]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [54:2700]
:POSTROUTING ACCEPT [54:2700]
COMMIT
# Completed on Tue Aug  8 00:57:06 2017
# Generated by iptables-save v1.6.0 on Tue Aug  8 00:57:06 2017
*nat
:PREROUTING ACCEPT [0:0]
:INPUT ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
:POSTROUTING ACCEPT [27:1620]
:ISTIO_OUTPUT - [0:0]
:ISTIO_REDIRECT - [0:0]
-A PREROUTING -m comment --comment "istio/install-istio-prerouting" -j ISTIO_REDIRECT
-A OUTPUT -p tcp -m comment --comment "istio/install-istio-output" -j ISTIO_OUTPUT
-A ISTIO_OUTPUT ! -d 127.0.0.1/32 -o lo -m comment --comment "istio/redirect-implicit-loopback" -j ISTIO_REDIRECT
-A ISTIO_OUTPUT -m owner --uid-owner 1337 -m comment --comment "istio/bypass-envoy" -j RETURN
-A ISTIO_OUTPUT -d 127.0.0.1/32 -m comment --comment "istio/bypass-explicit-loopback" -j RETURN
-A ISTIO_OUTPUT -m comment --comment "istio/redirect-default-outbound" -j ISTIO_REDIRECT
-A ISTIO_REDIRECT -p tcp -m comment --comment "istio/redirect-to-envoy-port" -j REDIRECT --to-ports 15001
COMMIT
# Completed on Tue Aug  8 00:57:06 2017
# Generated by iptables-save v1.6.0 on Tue Aug  8 00:57:06 2017
*filter
:INPUT ACCEPT [54:2700]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [54:2700]
COMMIT
# Completed on Tue Aug  8 00:57:06 2017
```

</p></details></br>

UPDATE: Re-run the application, below is the cluster state and sidecar config:

<details><summary>Cluster state</summary><p>

```
kubectl get pods -o wide --all-namespaces
NAMESPACE     NAME                             READY     STATUS    RESTARTS   AGE       IP           NODE
default       istio-egress-815883402-88z9w     1/1       Running   0          2h        10.1.89.6    127.0.0.1
default       istio-ingress-1054723629-wg34f   1/1       Running   0          2h        10.1.89.5    127.0.0.1
default       istio-mixer-2450814972-sbw2t     1/1       Running   0          2h        10.1.89.4    127.0.0.1
default       istio-pilot-1836659236-6bzrp     2/2       Running   0          2h        10.1.89.3    127.0.0.1
default       nginx-3417304539-4j8tz           1/1       Running   0          32m       10.1.89.8    127.0.0.1
default       nginx-3417304539-mrk1k           1/1       Running   0          32m       10.1.89.7    127.0.0.1
default       service-one-1736709432-0pldq     2/2       Running   0          5m        10.1.89.9    127.0.0.1
default       service-two-3955561808-9lch6     2/2       Running   0          5m        10.1.89.10   127.0.0.1
kube-system   kube-dns-3664836949-7pxpn        3/3       Running   0          2h        10.1.89.2    127.0.0.1

$ kubectl get svc
NAME            CLUSTER-IP   EXTERNAL-IP   PORT(S)                       AGE
istio-egress    10.0.0.249   <none>        80/TCP                        2h
istio-ingress   10.0.0.223   <nodes>       80:31318/TCP,443:30524/TCP    2h
istio-mixer     10.0.0.72    <none>        9091/TCP,9094/TCP,42422/TCP   2h
istio-pilot     10.0.0.11    <none>        8080/TCP,8081/TCP             2h
kubernetes      10.0.0.1     <none>        443/TCP                       2h
nginx           10.0.0.224   <none>        8888/TCP                      32m
service-one     10.0.0.24    <none>        80/TCP                        5m
service-two     10.0.0.217   <none>        80/TCP                        5m
```

</p></details></br>

<details><summary>Envoy sidecar config</summary><p>

```json
{
  "listeners": [
    {
      "address": "tcp://0.0.0.0:80",
      "filters": [
        {
          "type": "read",
          "name": "http_connection_manager",
          "config": {
            "codec_type": "auto",
            "stat_prefix": "http",
            "generate_request_id": true,
            "tracing": {
              "operation_name": "ingress"
            },
            "rds": {
              "cluster": "rds",
              "route_config_name": "80",
              "refresh_delay_ms": 1000
            },
            "filters": [
              {
                "type": "decoder",
                "name": "mixer",
                "config": {
                  "mixer_server": "istio-mixer:9091",
                  "mixer_attributes": {
                    "target.ip": "10.1.89.9",
                    "target.service": "service-one.default.svc.cluster.local",
                    "target.uid": "kubernetes://service-one-1736709432-0pldq.default"
                  },
                  "forward_attributes": {
                    "source.ip": "10.1.89.9",
                    "source.uid": "kubernetes://service-one-1736709432-0pldq.default"
                  },
                  "quota_name": "RequestCount"
                }
              },
              {
                "type": "decoder",
                "name": "router",
                "config": {}
              }
            ],
            "access_log": [
              {
                "path": "/dev/stdout"
              }
            ]
          }
        }
      ],
      "bind_to_port": false
    },
    {
      "address": "tcp://0.0.0.0:8080",
      "filters": [
        {
          "type": "read",
          "name": "http_connection_manager",
          "config": {
            "codec_type": "auto",
            "stat_prefix": "http",
            "generate_request_id": true,
            "tracing": {
              "operation_name": "ingress"
            },
            "rds": {
              "cluster": "rds",
              "route_config_name": "8080",
              "refresh_delay_ms": 1000
            },
            "filters": [
              {
                "type": "decoder",
                "name": "mixer",
                "config": {
                  "mixer_server": "istio-mixer:9091",
                  "mixer_attributes": {
                    "target.ip": "10.1.89.9",
                    "target.service": "service-one.default.svc.cluster.local",
                    "target.uid": "kubernetes://service-one-1736709432-0pldq.default"
                  },
                  "forward_attributes": {
                    "source.ip": "10.1.89.9",
                    "source.uid": "kubernetes://service-one-1736709432-0pldq.default"
                  },
                  "quota_name": "RequestCount"
                }
              },
              {
                "type": "decoder",
                "name": "router",
                "config": {}
              }
            ],
            "access_log": [
              {
                "path": "/dev/stdout"
              }
            ]
          }
        }
      ],
      "bind_to_port": false
    },
    {
      "address": "tcp://0.0.0.0:8081",
      "filters": [
        {
          "type": "read",
          "name": "http_connection_manager",
          "config": {
            "codec_type": "auto",
            "stat_prefix": "http",
            "generate_request_id": true,
            "tracing": {
              "operation_name": "ingress"
            },
            "rds": {
              "cluster": "rds",
              "route_config_name": "8081",
              "refresh_delay_ms": 1000
            },
            "filters": [
              {
                "type": "decoder",
                "name": "mixer",
                "config": {
                  "mixer_server": "istio-mixer:9091",
                  "mixer_attributes": {
                    "target.ip": "10.1.89.9",
                    "target.service": "service-one.default.svc.cluster.local",
                    "target.uid": "kubernetes://service-one-1736709432-0pldq.default"
                  },
                  "forward_attributes": {
                    "source.ip": "10.1.89.9",
                    "source.uid": "kubernetes://service-one-1736709432-0pldq.default"
                  },
                  "quota_name": "RequestCount"
                }
              },
              {
                "type": "decoder",
                "name": "router",
                "config": {}
              }
            ],
            "access_log": [
              {
                "path": "/dev/stdout"
              }
            ]
          }
        }
      ],
      "bind_to_port": false
    },
    {
      "address": "tcp://10.0.0.1:443",
      "filters": [
        {
          "type": "read",
          "name": "tcp_proxy",
          "config": {
            "stat_prefix": "tcp",
            "route_config": {
              "routes": [
                {
                  "cluster": "out.64a5722ae8d6cfbb7c8968b6de8ce26c7c7dd032",
                  "destination_ip_list": [
                    "10.0.0.1/32"
                  ]
                }
              ]
            }
          }
        }
      ],
      "bind_to_port": false
    },
    {
      "address": "tcp://10.0.0.223:443",
      "filters": [
        {
          "type": "read",
          "name": "tcp_proxy",
          "config": {
            "stat_prefix": "tcp",
            "route_config": {
              "routes": [
                {
                  "cluster": "out.085861efa91e0636afefc66e54e5bb33fe2239ff",
                  "destination_ip_list": [
                    "10.0.0.223/32"
                  ]
                }
              ]
            }
          }
        }
      ],
      "bind_to_port": false
    },
    {
      "address": "tcp://10.0.0.224:8888",
      "filters": [
        {
          "type": "read",
          "name": "tcp_proxy",
          "config": {
            "stat_prefix": "tcp",
            "route_config": {
              "routes": [
                {
                  "cluster": "out.95964e0bfcc3c12935c9d0eaad99ab72fcfd5126",
                  "destination_ip_list": [
                    "10.0.0.224/32"
                  ]
                }
              ]
            }
          }
        }
      ],
      "bind_to_port": false
    },
    {
      "address": "tcp://10.0.0.249:80",
      "filters": [
        {
          "type": "read",
          "name": "tcp_proxy",
          "config": {
            "stat_prefix": "tcp",
            "route_config": {
              "routes": [
                {
                  "cluster": "out.1b33d702979c352c8053a70beacf409f024e98eb",
                  "destination_ip_list": [
                    "10.0.0.249/32"
                  ]
                }
              ]
            }
          }
        }
      ],
      "bind_to_port": false
    },
    {
      "address": "tcp://10.0.0.72:42422",
      "filters": [
        {
          "type": "read",
          "name": "tcp_proxy",
          "config": {
            "stat_prefix": "tcp",
            "route_config": {
              "routes": [
                {
                  "cluster": "out.c585980af0793384480c7998912f77c2c410e26c",
                  "destination_ip_list": [
                    "10.0.0.72/32"
                  ]
                }
              ]
            }
          }
        }
      ],
      "bind_to_port": false
    },
    {
      "address": "tcp://10.0.0.72:9091",
      "filters": [
        {
          "type": "read",
          "name": "tcp_proxy",
          "config": {
            "stat_prefix": "tcp",
            "route_config": {
              "routes": [
                {
                  "cluster": "out.f576d95a3e0e7f57142daccfd0834b399ef96dfe",
                  "destination_ip_list": [
                    "10.0.0.72/32"
                  ]
                }
              ]
            }
          }
        }
      ],
      "bind_to_port": false
    },
    {
      "address": "tcp://10.0.0.72:9094",
      "filters": [
        {
          "type": "read",
          "name": "tcp_proxy",
          "config": {
            "stat_prefix": "tcp",
            "route_config": {
              "routes": [
                {
                  "cluster": "out.613663238fb620535d24aaf4ed1131d32b9e52e7",
                  "destination_ip_list": [
                    "10.0.0.72/32"
                  ]
                }
              ]
            }
          }
        }
      ],
      "bind_to_port": false
    },
    {
      "address": "tcp://10.1.89.9:8080",
      "filters": [
        {
          "type": "read",
          "name": "http_connection_manager",
          "config": {
            "codec_type": "auto",
            "stat_prefix": "http",
            "generate_request_id": true,
            "tracing": {
              "operation_name": "ingress"
            },
            "route_config": {
              "virtual_hosts": [
                {
                  "name": "inbound|8080",
                  "domains": [
                    "*"
                  ],
                  "routes": [
                    {
                      "prefix": "/",
                      "cluster": "in.8080",
                      "opaque_config": {
                        "mixer_control": "on",
                        "mixer_forward": "off"
                      }
                    }
                  ]
                }
              ]
            },
            "filters": [
              {
                "type": "decoder",
                "name": "mixer",
                "config": {
                  "mixer_server": "istio-mixer:9091",
                  "mixer_attributes": {
                    "target.ip": "10.1.89.9",
                    "target.service": "service-one.default.svc.cluster.local",
                    "target.uid": "kubernetes://service-one-1736709432-0pldq.default"
                  },
                  "forward_attributes": {
                    "source.ip": "10.1.89.9",
                    "source.uid": "kubernetes://service-one-1736709432-0pldq.default"
                  },
                  "quota_name": "RequestCount"
                }
              },
              {
                "type": "decoder",
                "name": "router",
                "config": {}
              }
            ],
            "access_log": [
              {
                "path": "/dev/stdout"
              }
            ]
          }
        }
      ],
      "bind_to_port": false
    },
    {
      "address": "tcp://0.0.0.0:15001",
      "filters": [],
      "bind_to_port": true,
      "use_original_dst": true
    }
  ],
  "admin": {
    "access_log_path": "/dev/stdout",
    "address": "tcp://0.0.0.0:15000"
  },
  "cluster_manager": {
    "clusters": [
      {
        "name": "in.8080",
        "connect_timeout_ms": 1000,
        "type": "static",
        "lb_type": "round_robin",
        "hosts": [
          {
            "url": "tcp://127.0.0.1:8080"
          }
        ]
      },
      {
        "name": "out.085861efa91e0636afefc66e54e5bb33fe2239ff",
        "service_name": "istio-ingress.default.svc.cluster.local|https",
        "connect_timeout_ms": 1000,
        "type": "sds",
        "lb_type": "round_robin"
      },
      {
        "name": "out.1b33d702979c352c8053a70beacf409f024e98eb",
        "service_name": "istio-egress.default.svc.cluster.local",
        "connect_timeout_ms": 1000,
        "type": "sds",
        "lb_type": "round_robin"
      },
      {
        "name": "out.613663238fb620535d24aaf4ed1131d32b9e52e7",
        "service_name": "istio-mixer.default.svc.cluster.local|configapi",
        "connect_timeout_ms": 1000,
        "type": "sds",
        "lb_type": "round_robin"
      },
      {
        "name": "out.64a5722ae8d6cfbb7c8968b6de8ce26c7c7dd032",
        "service_name": "kubernetes.default.svc.cluster.local|https",
        "connect_timeout_ms": 1000,
        "type": "sds",
        "lb_type": "round_robin"
      },
      {
        "name": "out.95964e0bfcc3c12935c9d0eaad99ab72fcfd5126",
        "service_name": "nginx.default.svc.cluster.local",
        "connect_timeout_ms": 1000,
        "type": "sds",
        "lb_type": "round_robin"
      },
      {
        "name": "out.c585980af0793384480c7998912f77c2c410e26c",
        "service_name": "istio-mixer.default.svc.cluster.local|prometheus",
        "connect_timeout_ms": 1000,
        "type": "sds",
        "lb_type": "round_robin"
      },
      {
        "name": "out.f576d95a3e0e7f57142daccfd0834b399ef96dfe",
        "service_name": "istio-mixer.default.svc.cluster.local|tcp",
        "connect_timeout_ms": 1000,
        "type": "sds",
        "lb_type": "round_robin"
      },
      {
        "name": "zipkin",
        "connect_timeout_ms": 1000,
        "type": "strict_dns",
        "lb_type": "round_robin",
        "hosts": [
          {
            "url": "tcp://zipkin:9411"
          }
        ]
      },
      {
        "name": "rds",
        "connect_timeout_ms": 1000,
        "type": "strict_dns",
        "lb_type": "round_robin",
        "hosts": [
          {
            "url": "tcp://istio-pilot:8080"
          }
        ]
      }
    ],
    "sds": {
      "cluster": {
        "name": "sds",
        "connect_timeout_ms": 1000,
        "type": "strict_dns",
        "lb_type": "round_robin",
        "hosts": [
          {
            "url": "tcp://istio-pilot:8080"
          }
        ]
      },
      "refresh_delay_ms": 1000
    },
    "cds": {
      "cluster": {
        "name": "cds",
        "connect_timeout_ms": 1000,
        "type": "strict_dns",
        "lb_type": "round_robin",
        "hosts": [
          {
            "url": "tcp://istio-pilot:8080"
          }
        ]
      },
      "refresh_delay_ms": 1000
    }
  },
  "tracing": {
    "http": {
      "driver": {
        "type": "zipkin",
        "config": {
          "collector_cluster": "zipkin",
          "collector_endpoint": "/api/v1/spans"
        }
      }
    }
  }
}
```

</p></details></br>

As seen from the config, each service in kubernetes forms a cluster. If we add one more deployment, e.g.

```
kubectl run nginx-nginx --image=nginx:1.13.5-alpine --replicas=2
kubectl expose deployment nginx-nginx --port 9999
```

We will see a new revision of the config with "nginx-nginx" in cluster manager.

**Task2: Enabling Ingress Traffic**

Create application httpbin and test ingress traffic. istio implements ingress controller using envoy.

```
# Create application.
$ kubectl create -f <(istioctl kube-inject -f task2/httpbin.yaml)
$ kubectl create -f task2/ingress.yaml

# Inspect current pods and services.
$ kubectl get pods --all-namespaces
NAMESPACE     NAME                             READY     STATUS    RESTARTS   AGE
default       httpbin-1665208910-x81ds         2/2       Running   0          9m
default       istio-egress-815883402-qx5m6     1/1       Running   0          14m
default       istio-ingress-1054723629-9mmxz   1/1       Running   0          14m
default       istio-mixer-2450814972-bj11b     1/1       Running   0          14m
default       istio-pilot-1836659236-ctc2w     2/2       Running   0          14m
kube-system   kube-dns-3664836949-cfrcj        3/3       Running   0          14m

$ kubectl get svc
NAME            TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)                       AGE
httpbin         ClusterIP   10.0.0.77    <none>        8000/TCP                      9m
istio-egress    ClusterIP   10.0.0.196   <none>        80/TCP                        14m
istio-ingress   NodePort    10.0.0.171   <none>        80:30873/TCP,443:30636/TCP    14m
istio-mixer     ClusterIP   10.0.0.221   <none>        9091/TCP,9094/TCP,42422/TCP   14m
istio-pilot     ClusterIP   10.0.0.219   <none>        8080/TCP,8081/TCP             14m
kubernetes      ClusterIP   10.0.0.1     <none>        443/TCP                       14m

# Now query our applications through ingress node port.
$ curl http://localhost:30873/headers
xxx
```

Inspecting the log shows that all traffic hit ingress proxy; but only traffic in the ingress path
hit 'httpbin' pod's proxy sidecar. Note istio also supports secured ingress, by including tls in
ingress resource.

- https://istio.io/docs/tasks/ingress.html

**Task3: Enabling Egress Traffic**

Create application sleep and test egress traffic. By default, Istio-enabled services are unable to
access URLs outside of the cluster because iptables is used in the pod to transparently redirect all
outbound traffic to the sidecar proxy, which only handles intra-cluster destinations.

```
# Create application.
$ kubectl create -f <(istioctl kube-inject -f task3/sleep.yaml)
$ export SOURCE_POD=$(kubectl get pod -l app=sleep -o jsonpath={.items..metadata.name})

# Unable to access external services.
$ kubectl exec -it $SOURCE_POD -c sleep bash
root@sleep-1009184259-mj0s9:/# curl http://httpbin.org/headers

# Create ExternalName services and we'll be able to access external services.
$ kubectl create -f external-svc.yaml
$ kubectl exec -it $SOURCE_POD -c sleep bash
root@sleep-1009184259-mj0s9:/# curl http://externalbin/headers
{
  "headers": {
    "Accept": "*/*",
    "Connection": "close",
    "Host": "httpbin.org",
    "User-Agent": "curl/7.35.0",
    "X-B3-Sampled": "1",
    "X-B3-Spanid": "00007a0efb3f79f0",
    "X-B3-Traceid": "00007a0efb3f79f0",
    "X-Envoy-Expected-Rq-Timeout-Ms": "15000",
    "X-Istio-Attributes": "ChcKCXNvdXJjZS5pcBIKMTcyLjE3LjAuOAo5Cgpzb3VyY2UudWlkEitrdWJlcm5ldGVzOi8vc2xlZXAtMTAwOTE4NDI1OS1tajBzOS5kZWZhdWx0",
    "X-Ot-Span-Context": "00007a0efb3f79f0;00007a0efb3f79f0;0000000000000000;sr"
  }
}
```

Another approach is to have sidecar container bypass external IPs, so that services in the mesh can
call external services directly.

- https://istio.io/docs/tasks/egress.html

**Task4: Request Routing (no success)**

The basic idea is to create a resource 'RouteRule' (kubernetes TPR) and have pilot propagating
configurations to all pods. For example:

```yaml
apiVersion: config.istio.io/v1alpha2
kind: RouteRule
metadata:
  name: reviews-test-v2
  namespace: default
  ...
spec:
  destination:
    name: reviews
  match:
    request:
      headers:
        cookie:
          regex: ^(.*?;)?(user=jason)(;.*)?$
  precedence: 2
  route:
  - labels:
      version: v2
```

This will send requests from jason (based on header cookie) to version v2 of 'reviews' service.
Another example:

```yaml
destination: reviews.default.svc.cluster.local
precedence: 1
route:
- tags:
    version: v1
  weight: 50
- tags:
    version: v3
  weight: 50
```

This will send 50% requests to v1 and 50% requests to v3.

- https://istio.io/docs/tasks/request-routing.html
- https://istio.io/blog/canary-deployments-using-istio.html

**More tasks: Rate Limiting, Access Control, Metrics/Logs, Tracing**

- https://istio.io/docs/tasks/rate-limiting.html
- https://istio.io/docs/tasks/basic-access-control.html
- https://istio.io/docs/tasks/metrics-logs.html
- https://istio.io/docs/tasks/distributed-tracing.html

For tracing, note that code change is needed from application side to propagete well-defined headers.

# Experiment (v0.2.2)

*Date: 09/20/2017, v0.2.2*

## Installation

**Get istio**

Using the following command to get istio and copy required binary to PATH.

```
curl -L https://github.com/istio/istio/releases/download/0.2.2/istio-0.2.2-linux.tar.gz | tar xz
cp bin/istioctl ~/code/workspace/bin
```

**Start local kubernetes**

For istio version 0.2.2, we use kubernetes release 1.7.6.

```
# Use 'git fetch -t' if tag doesn't exist.
$ git checkout v1.7.6
$ ALLOW_PRIVILEGED=Y ALLOW_SECURITY_CONTEXT=Y KUBE_ENABLE_CLUSTER_DNS=true ENABLE_RBAC=true ./hack/local-up-cluster.sh
```

**Install minimalistic istio**

Made two changes to the default istio configs:
- Changed 'istio-ingress' service type to NodePort (use 32080 and 32443)
- Changed namespace from 'istio-system' to 'default' (including service, rolebinding, etc)

Then create istio system:

```console
# Install istio without enabling istio auth (rbac will be installed as well).
$ kubectl create -f istio-0.2.2/install/kubernetes/istio.yaml

# Resulting artifacts.
$ kubectl get pods --all-namespaces -o wide
NAMESPACE     NAME                             READY     STATUS    RESTARTS   AGE       IP           NODE
default       istio-egress-1567982705-rp2jb    1/1       Running   0          1m        172.17.0.6   127.0.0.1
default       istio-ingress-3729647984-9j1n8   1/1       Running   0          1m        172.17.0.5   127.0.0.1
default       istio-mixer-1897012944-s13tx     2/2       Running   0          1m        172.17.0.3   127.0.0.1
default       istio-pilot-3960925469-wf8l9     1/1       Running   0          1m        172.17.0.4   127.0.0.1
kube-system   kube-dns-3987527134-psl04        3/3       Running   0          2m        172.17.0.2   127.0.0.1

$ kubectl get svc --all-namespaces
NAMESPACE     NAME            TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)                                                  AGE
default       istio-egress    ClusterIP   10.0.0.191   <none>        80/TCP                                                   2m
default       istio-ingress   NodePort    10.0.0.164   <none>        80:32080/TCP,443:32443/TCP                               2m
default       istio-mixer     ClusterIP   10.0.0.154   <none>        9091/TCP,9093/TCP,9094/TCP,9102/TCP,9125/UDP,42422/TCP   2m
default       istio-pilot     ClusterIP   10.0.0.123   <none>        8080/TCP,8081/TCP                                        2m
default       kubernetes      ClusterIP   10.0.0.1     <none>        443/TCP                                                  2m
kube-system   kube-dns        ClusterIP   10.0.0.10    <none>        53/UDP,53/TCP                                            2m
```

**Create example application**

Create the bookinfo application.

```
$ kubectl apply -f <(istioctl kube-inject -f istio-0.2.2/samples/apps/bookinfo/bookinfo.yaml)
$ export GATEWAY_URL=$(kubectl get po -l istio=ingress -o 'jsonpath={.items[0].status.hostIP}'):$(kubectl get svc istio-ingress -o 'jsonpath={.spec.ports[0].nodePort}')
$ curl -o /dev/null -s -w "%{http_code}\n" http://${GATEWAY_URL}/productpage
```

<details><summary>Current cluster status</summary><p>

```
$ kubectl get pods --all-namespaces -o wide
NAMESPACE     NAME                             READY     STATUS    RESTARTS   AGE       IP            NODE
default       details-v1-4113811335-ff4gt      2/2       Running   0          38m       172.17.0.7    127.0.0.1
default       istio-egress-1567982705-rp2jb    1/1       Running   0          40m       172.17.0.6    127.0.0.1
default       istio-ingress-3729647984-9j1n8   1/1       Running   0          40m       172.17.0.5    127.0.0.1
default       istio-mixer-1897012944-s13tx     2/2       Running   0          40m       172.17.0.3    127.0.0.1
default       istio-pilot-3960925469-wf8l9     1/1       Running   0          40m       172.17.0.4    127.0.0.1
default       productpage-v1-453580229-mww27   2/2       Running   0          38m       172.17.0.11   127.0.0.1
default       ratings-v1-1946739047-p2px7      2/2       Running   0          38m       172.17.0.9    127.0.0.1
default       reviews-v1-3648490622-s6ft3      2/2       Running   0          38m       172.17.0.8    127.0.0.1
default       reviews-v2-348932222-vqm1p       2/2       Running   0          38m       172.17.0.10   127.0.0.1
default       reviews-v3-3278364722-7tgxc      2/2       Running   0          38m       172.17.0.12   127.0.0.1
kube-system   kube-dns-3987527134-psl04        3/3       Running   0          41m       172.17.0.2    127.0.0.1

$ kubectl get svc --all-namespaces
NAMESPACE     NAME            TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)                                                  AGE
default       details         ClusterIP   10.0.0.126   <none>        9080/TCP                                                 38m
default       istio-egress    ClusterIP   10.0.0.191   <none>        80/TCP                                                   41m
default       istio-ingress   NodePort    10.0.0.164   <none>        80:32080/TCP,443:32443/TCP                               41m
default       istio-mixer     ClusterIP   10.0.0.154   <none>        9091/TCP,9093/TCP,9094/TCP,9102/TCP,9125/UDP,42422/TCP   41m
default       istio-pilot     ClusterIP   10.0.0.123   <none>        8080/TCP,8081/TCP                                        41m
default       kubernetes      ClusterIP   10.0.0.1     <none>        443/TCP                                                  41m
default       productpage     ClusterIP   10.0.0.165   <none>        9080/TCP                                                 38m
default       ratings         ClusterIP   10.0.0.72    <none>        9080/TCP                                                 38m
default       reviews         ClusterIP   10.0.0.142   <none>        9080/TCP                                                 38m
kube-system   kube-dns        ClusterIP   10.0.0.10    <none>        53/UDP,53/TCP                                            41m

$ kubectl get ing --all-namespaces
NAMESPACE   NAME      HOSTS     ADDRESS   PORTS     AGE
default     gateway   *                   80        40m

$ kubectl describe ingress gateway
Name:                 gateway
Namespace:              default
Address:
Default backend:        default-http-backend:80 (<none>)
Rules:
  Host  Path    Backends
  ----  ----    --------
  ,*
        /productpage            productpage:9080 (<none>)
        /login                  productpage:9080 (<none>)
        /logout                 productpage:9080 (<none>)
        /api/v1/products        productpage:9080 (<none>)
        /api/v1/products/.*     productpage:9080 (<none>)
Annotations:
Events: <none>

$ kubectl get crd
NAME                                  AGE
attributemanifests.config.istio.io    2h
checknothings.config.istio.io         2h
deniers.config.istio.io               2h
destinationpolicies.config.istio.io   2h
egressrules.config.istio.io           2h
listcheckers.config.istio.io          2h
listentries.config.istio.io           2h
logentries.config.istio.io            2h
memquotas.config.istio.io             2h
metrics.config.istio.io               2h
noops.config.istio.io                 2h
prometheuses.config.istio.io          2h
quotas.config.istio.io                2h
reportnothings.config.istio.io        2h
routerules.config.istio.io            2h
rules.config.istio.io                 2h
stackdrivers.config.istio.io          2h
statsds.config.istio.io               2h
stdios.config.istio.io                2h
svcctrls.config.istio.io              2h
```

</p></details></br>

## Components

For pilot, only a single container's running, i.e. 'discovery'. Apart from cds, rds, sds, another
discovery service, lds, is also added to pilot. As before, envoy config does not contain any detailed
routes, clusters, etc, and in 0.2.2, no listeners as well. Both ingress and egress istio proxy has the
same config, e.g.

<details><summary>Ingress and Egress Envoy Config</summary><p>

```
 {
  "listeners": [],
  "lds": {
    "cluster": "lds",
    "refresh_delay_ms": 1000
  },
  "admin": {
    "access_log_path": "/dev/stdout",
    "address": "tcp://127.0.0.1:15000"
  },
  "cluster_manager": {
    "clusters": [
      {
        "name": "rds",
        "connect_timeout_ms": 1000,
        "type": "strict_dns",
        "lb_type": "round_robin",
        "hosts": [
          {
            "url": "tcp://istio-pilot:8080"
          }
        ]
      },
      {
        "name": "lds",
        "connect_timeout_ms": 1000,
        "type": "strict_dns",
        "lb_type": "round_robin",
        "hosts": [
          {
            "url": "tcp://istio-pilot:8080"
          }
        ]
      }
    ],
    "sds": {
      "cluster": {
        "name": "sds",
        "connect_timeout_ms": 1000,
        "type": "strict_dns",
        "lb_type": "round_robin",
        "hosts": [
          {
            "url": "tcp://istio-pilot:8080"
          }
        ]
      },
      "refresh_delay_ms": 1000
    },
    "cds": {
      "cluster": {
        "name": "cds",
        "connect_timeout_ms": 1000,
        "type": "strict_dns",
        "lb_type": "round_robin",
        "hosts": [
          {
            "url": "tcp://istio-pilot:8080"
          }
        ]
      },
      "refresh_delay_ms": 1000
    }
  }
}
```

</p></details></br>

Following is the start commands in a sidecar pod:

```
/usr/local/bin/envoy -c /etc/istio/proxy/envoy-rev0.json --restart-epoch 0 --drain-time-s 45 --parent-shutdown-time-s 60 --service-cluster istio-proxy --service-node sidecar~172.17.0.9~ratings-v1-1946739047-p2px7.default~default.svc.cluster.local
/usr/local/bin/pilot-agent proxy sidecar -v 2 --configPath /etc/istio/proxy --binaryPath /usr/local/bin/envoy --serviceCluster istio-proxy --drainDuration 45s --parentShutdownDuration 1m0s --discoveryAddress istio-pilot:8080 --discoveryRefreshDelay 30s --zipkinAddress zipkin:9411 --connectTimeout 10s --statsdUdpAddress istio-mixer:9125 --proxyAdminPort 15000
```

Let's try to dig through ingress's config chain, first find listener:

<details><summary>Listener</summary><p>

```
$ curl 172.17.0.4:8080/v1/listeners/istio-proxy/ingress~~istio-ingress-3729647984-9j1n8.default~default.svc.cluster.local
{
  "listeners": [
   {
    "address": "tcp://0.0.0.0:80",
    "name": "http_0.0.0.0_80",
    "filters": [
     {
      "type": "read",
      "name": "http_connection_manager",
      "config": {
       "codec_type": "auto",
       "stat_prefix": "http",
       "generate_request_id": true,
       "use_remote_address": true,
       "tracing": {
        "operation_name": "ingress"
       },
       "rds": {
        "cluster": "rds",
        "route_config_name": "80",
        "refresh_delay_ms": 30000
       },
       "filters": [
        {
         "type": "decoder",
         "name": "mixer",
         "config": {
          "mixer_attributes": {
           "destination.ip": "",
           "destination.uid": "kubernetes://istio-ingress-3729647984-9j1n8.default"
          },
          "forward_attributes": {
           "source.ip": "",
           "source.uid": "kubernetes://istio-ingress-3729647984-9j1n8.default"
          },
          "quota_name": "RequestCount"
         }
        },
        {
         "type": "decoder",
         "name": "router",
         "config": {}
        }
       ],
       "access_log": [
        {
         "path": "/dev/stdout"
        }
       ]
      }
     }
    ],
    "bind_to_port": true
   }
  ]
 }
```

</p></details></br>

Then find routes:

<details><summary>Routes</summary><p>

```
$ curl 172.17.0.4:8080/v1/routes/80/istio-proxy/ingress~~istio-ingress-3729647984-9j1n8.default~default.svc.cluster.local
{
  "virtual_hosts": [
   {
    "name": "*",
    "domains": [
     "*"
    ],
    "routes": [
     {
      "path": "/api/v1/products",
      "cluster": "out.304d4aa908c3ed9923066c887a9466a0755bd896",
      "opaque_config": {
       "mixer_check": "on",
       "mixer_forward": "on",
       "mixer_report": "on"
      }
     },
     {
      "path": "/login",
      "cluster": "out.304d4aa908c3ed9923066c887a9466a0755bd896",
      "opaque_config": {
       "mixer_check": "on",
       "mixer_forward": "on",
       "mixer_report": "on"
      }
     },
     {
      "path": "/logout",
      "cluster": "out.304d4aa908c3ed9923066c887a9466a0755bd896",
      "opaque_config": {
       "mixer_check": "on",
       "mixer_forward": "on",
       "mixer_report": "on"
      }
     },
     {
      "path": "/productpage",
      "cluster": "out.304d4aa908c3ed9923066c887a9466a0755bd896",
      "opaque_config": {
       "mixer_check": "on",
       "mixer_forward": "on",
       "mixer_report": "on"
      }
     },
     {
      "prefix": "/api/v1/products/",
      "cluster": "out.304d4aa908c3ed9923066c887a9466a0755bd896",
      "opaque_config": {
       "mixer_check": "on",
       "mixer_forward": "on",
       "mixer_report": "on"
      }
     }
    ]
   }
  ]
 }
```

</p></details></br>

This shows that ingress rules are converted to envoy rds. To find out the cluster in the route config
(out.304d4aa908c3ed9923066c887a9466a0755bd896); let's curl clusters endpoing:

```
$ curl 172.17.0.4:8080/v1/clusters/istio-proxy/ingress~~istio-ingress-3729647984-9j1n8.default~default.svc.cluster.local
{
  "clusters": [
   {
    "name": "out.304d4aa908c3ed9923066c887a9466a0755bd896",
    "service_name": "productpage.default.svc.cluster.local|http",
    "connect_timeout_ms": 1000,
    "type": "sds",
    "lb_type": "round_robin"
   },
   {
    "name": "mixer_server",
    "connect_timeout_ms": 1000,
    "type": "strict_dns",
    "lb_type": "round_robin",
    "hosts": [
     {
      "url": "tcp://istio-mixer:9091"
     }
    ],
    "features": "http2",
    "circuit_breakers": {
     "default": {
      "max_pending_requests": 10000,
      "max_requests": 10000
     }
    }
   }
  ]
 }
```

And to find the service backing the cluster, let's curl the sds endpoint:

```
$ curl 172.17.0.4:8080/v1/registration/productpage.default.svc.cluster.local\|http
{
  "hosts": [
   {
    "ip_address": "172.17.0.11",
    "port": 9080
   }
  ]
 }

$ kubectl get pods -o wide | grep 172.17.0.11
productpage-v1-453580229-mww27   2/2       Running   0          2h        172.17.0.11   127.0.0.1
```

The same approach applies to other proxies as well, i.e. egress, sidecar.

## Tasks

**Task4: Request Routing**

By default, all requests will round robin to all pods under review service:

<details><summary>Cluster and registration config</summary><p>

```
$ curl 172.17.0.4:8080/v1/clusters/istio-proxy/sidecar~172.17.0.11~productpage-v1-453580229-mww27.default~default.svc.cluster.local | grep -C 8 reviews
    "name": "out.777628d708f38f65d6b9837784a6922d2322f75f",
    "service_name": "istio-mixer.default.svc.cluster.local|http-health",
    "connect_timeout_ms": 1000,
    "type": "sds",
    "lb_type": "round_robin"
   },
   {
    "name": "out.7bbb18f93ae0827c3e6c0c398475422930c20a3e",
    "service_name": "reviews.default.svc.cluster.local|http",
    "connect_timeout_ms": 1000,
    "type": "sds",
    "lb_type": "round_robin"
   },
   {
    "name": "out.96c4dfcd665fa0caf6f48ab026e4263d1d17bac2",
    "service_name": "istio-pilot.default.svc.cluster.local|http-apiserver",
    "connect_timeout_ms": 1000,

$ curl 172.17.0.4:8080/v1/registration/reviews.default.svc.cluster.local\|http
{
  "hosts": [
   {
    "ip_address": "172.17.0.10",
    "port": 9080
   },
   {
    "ip_address": "172.17.0.12",
    "port": 9080
   },
   {
    "ip_address": "172.17.0.8",
    "port": 9080
   }
  ]
 }
```

</p></details></br>

Create the route rule to direct all requests to version v1:

<details><summary>Create route rule</summary><p>

```
$ istioctl create -f samples/apps/bookinfo/rules/route-rule-all-v1.yaml

$ istioctl get route-rules -o yaml
name: details-default
namespace: default
resourceVersion: "13038"
spec:
  destination:
    name: details
  precedence: 1
  route:
  - labels:
      version: v1
type: route-rule
---
name: productpage-default
namespace: default
resourceVersion: "13035"
spec:
  destination:
    name: productpage
  precedence: 1
  route:
  - labels:
      version: v1
type: route-rule
---
name: ratings-default
namespace: default
resourceVersion: "13037"
spec:
  destination:
    name: ratings
  precedence: 1
  route:
  - labels:
      version: v1
type: route-rule
---
name: reviews-default
namespace: default
resourceVersion: "13036"
spec:
  destination:
    name: reviews
  precedence: 1
  route:
  - labels:
      version: v1
type: route-rule
---
```

</p></details></br>

Below is the config for review v1 after creating the route:

```
$ curl 172.17.0.4:8080/v1/registration/reviews.default.svc.cluster.local\|http\|version=v1
{
  "hosts": [
   {
    "ip_address": "172.17.0.8",
    "port": 9080
   }
  ]
 }
```

From the output, we see that request will only be route to review version v1. Note request from
sidecar envoy to its service is configured as:

```
$ curl 172.17.0.4:8080/v1/clusters/istio-proxy/sidecar~172.17.0.11~productpage-v1-453580229-mww27.default~default.svc.cluster.local 2>/dev/null | grep -C 10 in.9080
{
  "clusters": [
   {
    "name": "in.9080",
    "connect_timeout_ms": 1000,
    "type": "static",
    "lb_type": "round_robin",
    "hosts": [
     {
      "url": "tcp://127.0.0.1:9080"
     }
    ]
   },
   {
```

Now create content based rules:

```
istioctl create -f samples/apps/bookinfo/rules/route-rule-reviews-test-v2.yaml
```

With this route rule defined, we can take a look at routes in productpage service:

<details><summary>Create route rule with content</summary><p>

```
$ curl 172.17.0.4:8080/v1/routes/9080/istio-proxy/sidecar~172.17.0.11~productpage-v1-453580229-mww27.default~default.svc.cluster.local
{
 "virtual_hosts": [
  {
   "name": "details.default.svc.cluster.local|http",
   "domains": [
    "details:9080",
    "details",
    "details.default:9080",
    "details.default",
    "details.default.svc:9080",
    "details.default.svc",
    "details.default.svc.cluster:9080",
    "details.default.svc.cluster",
    "details.default.svc.cluster.local:9080",
    "details.default.svc.cluster.local",
    "10.0.0.126:9080",
    "10.0.0.126"
   ],
   "routes": [
    {
     "prefix": "/",
     "cluster": "out.2f50c73ed6c7ec0db7e7658c9112bebcfefd9d5c"
    }
   ]
  },
  {
   "name": "productpage.default.svc.cluster.local|http",
   "domains": [
    "productpage:9080",
    "productpage",
    "productpage.default:9080",
    "productpage.default",
    "productpage.default.svc:9080",
    "productpage.default.svc",
    "productpage.default.svc.cluster:9080",
    "productpage.default.svc.cluster",
    "productpage.default.svc.cluster.local:9080",
    "productpage.default.svc.cluster.local",
    "10.0.0.165:9080",
    "10.0.0.165"
   ],
   "routes": [
    {
     "prefix": "/",
     "cluster": "out.4bdc5a0e59af7107a7189467360a720381024b5c"
    }
   ]
  },
  {
   "name": "ratings.default.svc.cluster.local|http",
   "domains": [
    "ratings:9080",
    "ratings",
    "ratings.default:9080",
    "ratings.default",
    "ratings.default.svc:9080",
    "ratings.default.svc",
    "ratings.default.svc.cluster:9080",
    "ratings.default.svc.cluster",
    "ratings.default.svc.cluster.local:9080",
    "ratings.default.svc.cluster.local",
    "10.0.0.72:9080",
    "10.0.0.72"
   ],
   "routes": [
    {
     "prefix": "/",
     "cluster": "out.9702f67ee1d22e953c7eedda548c846c3d813a4c"
    }
   ]
  },
  {
   "name": "reviews.default.svc.cluster.local|http",
   "domains": [
    "reviews:9080",
    "reviews",
    "reviews.default:9080",
    "reviews.default",
    "reviews.default.svc:9080",
    "reviews.default.svc",
    "reviews.default.svc.cluster:9080",
    "reviews.default.svc.cluster",
    "reviews.default.svc.cluster.local:9080",
    "reviews.default.svc.cluster.local",
    "10.0.0.142:9080",
    "10.0.0.142"
   ],
   "routes": [
    {
     "prefix": "/",
     "cluster": "out.9885ad2b8f51ba5a8ef1dbd5c35677a57e298b14",
     "headers": [
      {
       "name": "cookie",
       "value": "^(.*?;)?(user=jason)(;.*)?$",
       "regex": true
      }
     ]
    },
    {
     "prefix": "/",
     "cluster": "out.c7c42a0ffbf55f227c7c7c70637160bebc86e072"
    }
   ]
  }
 ]
}
```

</p></details></br>

Note the port is '9080'. This shows that sidecar proxy will conditionally proxy traffic from productpage
to revies service. If we do the percentage based proxy, we'll also see changes from this endpont.

**Task5: Rate Limiting (no success)**

Note, the tutorial on official website is for pre0.2, the way mixer rules are created have changed:

```
$ kubectl create -f tasks5/mixer-rule-ratings-ratelimit.yaml
```

To debug, follow https://github.com/istio/istio/blob/master/devel/README.md, and run local mixer https://github.com/istio/mixer/blob/master/doc/dev/development.md,
then change 'istio-mixer' to host ip in 'istio.yaml' installation yaml file. Reference: https://envoyproxy.github.io/envoy/intro/arch_overview/global_rate_limiting.html

**Task6: Access Control (no success)**

**Task7: Istio Auth**

Start over and run istio with auth enabled:

```
kubectl delete -f istio-0.2.2/install/kubernetes/istio.yaml
kubectl create -f istio-0.2.2/install/kubernetes/istio-auth.yaml

# A new pod istio-ca-{} is running
$ kubectl get pods
NAME                             READY     STATUS    RESTARTS   AGE
istio-ca-2547841328-mhz84        1/1       Running   0          4m
istio-egress-1567982705-6b4vt    1/1       Running   0          4m
istio-ingress-3729647984-z32dq   1/1       Running   0          4m
istio-mixer-1897012944-64qv1     2/2       Running   0          4m
istio-pilot-3960925469-jtds0     1/1       Running   0          4m

# The pod creates a lot of secrets
$ kubectl get secret
NAME                                        TYPE                                  DATA      AGE
default-token-8vx4z                         kubernetes.io/service-account-token   3         38m
istio-ca-service-account-token-1qc0m        kubernetes.io/service-account-token   3         4m
istio-egress-service-account-token-tr4fk    kubernetes.io/service-account-token   3         4m
istio-ingress-certs                         Opaque                                2         4m
istio-ingress-service-account-token-q2qhw   kubernetes.io/service-account-token   3         4m
istio-mixer-service-account-token-x2fqz     kubernetes.io/service-account-token   3         4m
istio-pilot-service-account-token-hhgwk     kubernetes.io/service-account-token   3         4m
istio.default                               istio.io/key-and-cert                 3         3m
istio.istio-ca-service-account              istio.io/key-and-cert                 3         3m
istio.istio-egress-service-account          istio.io/key-and-cert                 3         3m
istio.istio-ingress-service-account         istio.io/key-and-cert                 3         3m
istio.istio-mixer-service-account           istio.io/key-and-cert                 3         3m
istio.istio-pilot-service-account           istio.io/key-and-cert                 3         3m

$ kubectl get svc
NAME            TYPE           CLUSTER-IP   EXTERNAL-IP   PORT(S)                                                  AGE
istio-egress    ClusterIP      10.0.0.36    <none>        80/TCP                                                   4m
istio-ingress   LoadBalancer   10.0.0.80    <pending>     80:31537/TCP,443:30619/TCP                               4m
istio-mixer     ClusterIP      10.0.0.130   <none>        9091/TCP,9093/TCP,9094/TCP,9102/TCP,9125/UDP,42422/TCP   4m
istio-pilot     ClusterIP      10.0.0.219   <none>        8080/TCP,8081/TCP                                        4m
kubernetes      ClusterIP      10.0.0.1     <none>        443/TCP                                                  39m
```

As we can see, a new istio-ca pod is runnning which creates quite a few secrets. These secrets will
be mounted to applicatio pod, e.g.

```
volumeMounts:
- mountPath: /etc/istio/config
  name: istio-config
  readOnly: true
- mountPath: /etc/istio/proxy
  name: istio-envoy
- mountPath: /etc/certs/
  name: istio-certs
  readOnly: true
- mountPath: /var/run/secrets/kubernetes.io/serviceaccount
  name: default-token-8vx4z
  readOnly: true
```

Now if we create application and take a look at its listeners (as mentioned above, this is dynamically
generated from pilot), we'll see:

```
$ kubectl get pods -o wide
NAME                             READY     STATUS    RESTARTS   AGE       IP            NODE
details-v1-4113811335-trg2z      2/2       Running   0          2m        172.17.0.8    127.0.0.1
istio-ca-2547841328-mhz84        1/1       Running   0          8m        172.17.0.6    127.0.0.1
istio-egress-1567982705-6b4vt    1/1       Running   0          8m        172.17.0.7    127.0.0.1
istio-ingress-3729647984-z32dq   1/1       Running   0          8m        172.17.0.5    127.0.0.1
istio-mixer-1897012944-64qv1     2/2       Running   0          8m        172.17.0.3    127.0.0.1
istio-pilot-3960925469-jtds0     1/1       Running   0          8m        172.17.0.4    127.0.0.1
productpage-v1-453580229-6h30z   2/2       Running   0          2m        172.17.0.13   127.0.0.1
ratings-v1-1946739047-xbt38      2/2       Running   0          2m        172.17.0.9    127.0.0.1
reviews-v1-3648490622-b6w0c      2/2       Running   0          2m        172.17.0.10   127.0.0.1
reviews-v2-348932222-538tj       2/2       Running   0          2m        172.17.0.11   127.0.0.1
reviews-v3-3278364722-fp0q8      2/2       Running   0          2m        172.17.0.12   127.0.0.1
```

<details><summary>Listeners</summary><p>

```
$ curl 172.17.0.4:8080/v1/listeners/istio-proxy/sidecar~172.17.0.13~productpage-v1-453580229-6h30z.default~default.svc.cluster.local 2>/dev/null
{
  "listeners": [
   {
    "address": "tcp://0.0.0.0:15001",
    "name": "virtual",
    "filters": [],
    "bind_to_port": true,
    "use_original_dst": true
   },
   {
    "address": "tcp://0.0.0.0:80",
    "name": "http_0.0.0.0_80",
    "filters": [
     {
      "type": "read",
      "name": "http_connection_manager",
      "config": {
       "codec_type": "auto",
       "stat_prefix": "http",
       "generate_request_id": true,
       "tracing": {
        "operation_name": "ingress"
       },
       "rds": {
        "cluster": "rds",
        "route_config_name": "80",
        "refresh_delay_ms": 30000
       },
       "filters": [
        {
         "type": "decoder",
         "name": "mixer",
         "config": {
          "mixer_attributes": {
           "destination.ip": "172.17.0.13",
           "destination.service": "productpage.default.svc.cluster.local",
           "destination.uid": "kubernetes://productpage-v1-453580229-6h30z.default"
          },
          "forward_attributes": {
           "source.ip": "172.17.0.13",
           "source.uid": "kubernetes://productpage-v1-453580229-6h30z.default"
          },
          "quota_name": "RequestCount"
         }
        },
        {
         "type": "decoder",
         "name": "router",
         "config": {}
        }
       ],
       "access_log": [
        {
         "path": "/dev/stdout"
        }
       ]
      }
     }
    ],
    "bind_to_port": false
   },
   {
    "address": "tcp://0.0.0.0:8080",
    "name": "http_0.0.0.0_8080",
    "filters": [
     {
      "type": "read",
      "name": "http_connection_manager",
      "config": {
       "codec_type": "auto",
       "stat_prefix": "http",
       "generate_request_id": true,
       "tracing": {
        "operation_name": "ingress"
       },
       "rds": {
        "cluster": "rds",
        "route_config_name": "8080",
        "refresh_delay_ms": 30000
       },
       "filters": [
        {
         "type": "decoder",
         "name": "mixer",
         "config": {
          "mixer_attributes": {
           "destination.ip": "172.17.0.13",
           "destination.service": "productpage.default.svc.cluster.local",
           "destination.uid": "kubernetes://productpage-v1-453580229-6h30z.default"
          },
          "forward_attributes": {
           "source.ip": "172.17.0.13",
           "source.uid": "kubernetes://productpage-v1-453580229-6h30z.default"
          },
          "quota_name": "RequestCount"
         }
        },
        {
         "type": "decoder",
         "name": "router",
         "config": {}
        }
       ],
       "access_log": [
        {
         "path": "/dev/stdout"
        }
       ]
      }
     }
    ],
    "bind_to_port": false
   },
   {
    "address": "tcp://0.0.0.0:8081",
    "name": "http_0.0.0.0_8081",
    "filters": [
     {
      "type": "read",
      "name": "http_connection_manager",
      "config": {
       "codec_type": "auto",
       "stat_prefix": "http",
       "generate_request_id": true,
       "tracing": {
        "operation_name": "ingress"
       },
       "rds": {
        "cluster": "rds",
        "route_config_name": "8081",
        "refresh_delay_ms": 30000
       },
       "filters": [
        {
         "type": "decoder",
         "name": "mixer",
         "config": {
          "mixer_attributes": {
           "destination.ip": "172.17.0.13",
           "destination.service": "productpage.default.svc.cluster.local",
           "destination.uid": "kubernetes://productpage-v1-453580229-6h30z.default"
          },
          "forward_attributes": {
           "source.ip": "172.17.0.13",
           "source.uid": "kubernetes://productpage-v1-453580229-6h30z.default"
          },
          "quota_name": "RequestCount"
         }
        },
        {
         "type": "decoder",
         "name": "router",
         "config": {}
        }
       ],
       "access_log": [
        {
         "path": "/dev/stdout"
        }
       ]
      }
     }
    ],
    "bind_to_port": false
   },
   {
    "address": "tcp://0.0.0.0:9080",
    "name": "http_0.0.0.0_9080",
    "filters": [
     {
      "type": "read",
      "name": "http_connection_manager",
      "config": {
       "codec_type": "auto",
       "stat_prefix": "http",
       "generate_request_id": true,
       "tracing": {
        "operation_name": "ingress"
       },
       "rds": {
        "cluster": "rds",
        "route_config_name": "9080",
        "refresh_delay_ms": 30000
       },
       "filters": [
        {
         "type": "decoder",
         "name": "mixer",
         "config": {
          "mixer_attributes": {
           "destination.ip": "172.17.0.13",
           "destination.service": "productpage.default.svc.cluster.local",
           "destination.uid": "kubernetes://productpage-v1-453580229-6h30z.default"
          },
          "forward_attributes": {
           "source.ip": "172.17.0.13",
           "source.uid": "kubernetes://productpage-v1-453580229-6h30z.default"
          },
          "quota_name": "RequestCount"
         }
        },
        {
         "type": "decoder",
         "name": "router",
         "config": {}
        }
       ],
       "access_log": [
        {
         "path": "/dev/stdout"
        }
       ]
      }
     }
    ],
    "bind_to_port": false
   },
   {
    "address": "tcp://0.0.0.0:9093",
    "name": "http_0.0.0.0_9093",
    "filters": [
     {
      "type": "read",
      "name": "http_connection_manager",
      "config": {
       "codec_type": "auto",
       "stat_prefix": "http",
       "generate_request_id": true,
       "tracing": {
        "operation_name": "ingress"
       },
       "rds": {
        "cluster": "rds",
        "route_config_name": "9093",
        "refresh_delay_ms": 30000
       },
       "filters": [
        {
         "type": "decoder",
         "name": "mixer",
         "config": {
          "mixer_attributes": {
           "destination.ip": "172.17.0.13",
           "destination.service": "productpage.default.svc.cluster.local",
           "destination.uid": "kubernetes://productpage-v1-453580229-6h30z.default"
          },
          "forward_attributes": {
           "source.ip": "172.17.0.13",
           "source.uid": "kubernetes://productpage-v1-453580229-6h30z.default"
          },
          "quota_name": "RequestCount"
         }
        },
        {
         "type": "decoder",
         "name": "router",
         "config": {}
        }
       ],
       "access_log": [
        {
         "path": "/dev/stdout"
        }
       ]
      }
     }
    ],
    "bind_to_port": false
   },
   {
    "address": "tcp://10.0.0.10:53",
    "name": "tcp_10.0.0.10_53",
    "filters": [
     {
      "type": "read",
      "name": "tcp_proxy",
      "config": {
       "stat_prefix": "tcp",
       "route_config": {
        "routes": [
         {
          "cluster": "out.f8623c41b5eb88a22366307b5bf7722b8d1d67c6",
          "destination_ip_list": [
           "10.0.0.10/32"
          ]
         }
        ]
       }
      }
     }
    ],
    "bind_to_port": false
   },
   {
    "address": "tcp://10.0.0.130:42422",
    "name": "tcp_10.0.0.130_42422",
    "filters": [
     {
      "type": "read",
      "name": "tcp_proxy",
      "config": {
       "stat_prefix": "tcp",
       "route_config": {
        "routes": [
         {
          "cluster": "out.c585980af0793384480c7998912f77c2c410e26c",
          "destination_ip_list": [
           "10.0.0.130/32"
          ]
         }
        ]
       }
      }
     }
    ],
    "bind_to_port": false
   },
   {
    "address": "tcp://10.0.0.130:9091",
    "name": "tcp_10.0.0.130_9091",
    "filters": [
     {
      "type": "read",
      "name": "tcp_proxy",
      "config": {
       "stat_prefix": "tcp",
       "route_config": {
        "routes": [
         {
          "cluster": "out.f576d95a3e0e7f57142daccfd0834b399ef96dfe",
          "destination_ip_list": [
           "10.0.0.130/32"
          ]
         }
        ]
       }
      }
     }
    ],
    "bind_to_port": false
   },
   {
    "address": "tcp://10.0.0.130:9094",
    "name": "tcp_10.0.0.130_9094",
    "filters": [
     {
      "type": "read",
      "name": "tcp_proxy",
      "config": {
       "stat_prefix": "tcp",
       "route_config": {
        "routes": [
         {
          "cluster": "out.613663238fb620535d24aaf4ed1131d32b9e52e7",
          "destination_ip_list": [
           "10.0.0.130/32"
          ]
         }
        ]
       }
      }
     }
    ],
    "bind_to_port": false
   },
   {
    "address": "tcp://10.0.0.130:9102",
    "name": "tcp_10.0.0.130_9102",
    "filters": [
     {
      "type": "read",
      "name": "tcp_proxy",
      "config": {
       "stat_prefix": "tcp",
       "route_config": {
        "routes": [
         {
          "cluster": "out.31a308ff400a2540434fd723e6abf7a092c2ae2b",
          "destination_ip_list": [
           "10.0.0.130/32"
          ]
         }
        ]
       }
      }
     }
    ],
    "bind_to_port": false
   },
   {
    "address": "tcp://10.0.0.1:443",
    "name": "tcp_10.0.0.1_443",
    "filters": [
     {
      "type": "read",
      "name": "tcp_proxy",
      "config": {
       "stat_prefix": "tcp",
       "route_config": {
        "routes": [
         {
          "cluster": "out.64a5722ae8d6cfbb7c8968b6de8ce26c7c7dd032",
          "destination_ip_list": [
           "10.0.0.1/32"
          ]
         }
        ]
       }
      }
     }
    ],
    "bind_to_port": false
   },
   {
    "address": "tcp://10.0.0.36:80",
    "name": "tcp_10.0.0.36_80",
    "filters": [
     {
      "type": "read",
      "name": "tcp_proxy",
      "config": {
       "stat_prefix": "tcp",
       "route_config": {
        "routes": [
         {
          "cluster": "out.1b33d702979c352c8053a70beacf409f024e98eb",
          "destination_ip_list": [
           "10.0.0.36/32"
          ]
         }
        ]
       }
      }
     }
    ],
    "bind_to_port": false
   },
   {
    "address": "tcp://10.0.0.80:443",
    "name": "tcp_10.0.0.80_443",
    "filters": [
     {
      "type": "read",
      "name": "tcp_proxy",
      "config": {
       "stat_prefix": "tcp",
       "route_config": {
        "routes": [
         {
          "cluster": "out.085861efa91e0636afefc66e54e5bb33fe2239ff",
          "destination_ip_list": [
           "10.0.0.80/32"
          ]
         }
        ]
       }
      }
     }
    ],
    "bind_to_port": false
   },
   {
    "address": "tcp://172.17.0.13:9080",
    "name": "http_172.17.0.13_9080",
    "filters": [
     {
      "type": "read",
      "name": "http_connection_manager",
      "config": {
       "codec_type": "auto",
       "stat_prefix": "http",
       "generate_request_id": true,
       "tracing": {
        "operation_name": "ingress"
       },
       "route_config": {
        "virtual_hosts": [
         {
          "name": "inbound|9080",
          "domains": [
           "*"
          ],
          "routes": [
           {
            "prefix": "/",
            "cluster": "in.9080",
            "opaque_config": {
             "mixer_check": "on",
             "mixer_forward": "off",
             "mixer_report": "on"
            }
           }
          ]
         }
        ]
       },
       "filters": [
        {
         "type": "decoder",
         "name": "mixer",
         "config": {
          "mixer_attributes": {
           "destination.ip": "172.17.0.13",
           "destination.service": "productpage.default.svc.cluster.local",
           "destination.uid": "kubernetes://productpage-v1-453580229-6h30z.default"
          },
          "forward_attributes": {
           "source.ip": "172.17.0.13",
           "source.uid": "kubernetes://productpage-v1-453580229-6h30z.default"
          },
          "quota_name": "RequestCount"
         }
        },
        {
         "type": "decoder",
         "name": "router",
         "config": {}
        }
       ],
       "access_log": [
        {
         "path": "/dev/stdout"
        }
       ]
      }
     }
    ],
    "ssl_context": {
     "cert_chain_file": "/etc/certs/cert-chain.pem",
     "private_key_file": "/etc/certs/key.pem",
     "ca_cert_file": "/etc/certs/root-cert.pem",
     "require_client_certificate": true
    },
    "bind_to_port": false
   }
  ]
 }
```

</p></details></br>

The last few lines show the ssl context of the envoy sidecar. Envoy will use the certificates to
handle runtime traffic. To test, run:

```
$ kubectl exec productpage-v1-453580229-6h30z -c istio-proxy -- curl https://details:9080 -sS -k
curl: (35) gnutls_handshake() failed: Handshake failed

$ kubectl exec productpage-v1-453580229-6h30z -c istio-proxy -- curl https://details:9080 -sS --key /etc/certs/key.pem --cert /etc/certs/cert-chain.pem --cacert /etc/certs/root-cert.pem -k
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN">
<HTML>
  <HEAD><TITLE>Not Found</TITLE></HEAD>
  <BODY>
    <H1>Not Found</H1>
    `/' not found.
    <HR>
    <ADDRESS>
     WEBrick/1.3.1 (Ruby/2.3.4/2017-03-30) at
     details:9080
    </ADDRESS>
  </BODY>
</HTML>
```

# Experiment (v1.6.5)

## Installation

```
$ curl -L https://istio.io/downloadIstio | sh -
...

$ istioctl install --set profile=demo --set values.gateways.istio-ingressgateway.type=NodePort
Detected that your cluster does not support third party JWT authentication. Falling back to less secure first party JWT. See https://istio.io/docs/ops/best-practices/security/#configure-third-party-service-account-tokens for details.
✔ Istio core installed
✔ Istiod installed
✔ Egress gateways installed
✔ Ingress gateways installed
✔ Addons installed
```

Export Gateway information:

```
export INGRESS_HOST=$(kubectl get po -l istio=ingressgateway -n istio-system -o jsonpath='{.items[0].status.hostIP}')
export INGRESS_PORT=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="http2")].nodePort}')
export SECURE_INGRESS_PORT=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="https")].nodePort}')
export TCP_INGRESS_PORT=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="tcp")].nodePort}')
export GATEWAY_URL=$INGRESS_HOST:$INGRESS_PORT
```

Install the bookinfo example:

```
# Make sure sidecar is injected.
kubectl label namespace default istio-injection=enabled

# Create the application.
kubectl apply -f samples/bookinfo/platform/kube/bookinfo.yaml

# Create default gateway for external access.
kubectl apply -f samples/bookinfo/networking/bookinfo-gateway.yaml

# Create default set of destination rules each service (version).
kubectl apply -f samples/bookinfo/networking/destination-rule-all.yaml
```

To verify:

```
$ curl -s "http://${GATEWAY_URL}/productpage" | grep -o "<title>.*</title>"
<title>Simple Bookstore App</title>
```

To cleanup:

```
$ bash ./samples/bookinfo/platform/kube/cleanup.sh
...
```

## [Debugging](https://istio.io/latest/docs/ops/diagnostic-tools/proxy-cmd/)

istioctl provides two subcommands to facilitate debugging: `proxy-status` and `proxy-config`.

For example, after we created the routes to match user `jason` header, the route information is
synced from istiod to envoy proxy of `productpage` service. We can query the envoy config via:

<details><summary>istioctl proxy-config</summary><p>

```
$ istioctl proxy-config routes productpage-v1-7f4cc988c6-c7vwp --name 9080 -o json | jq
[
  {
    "name": "9080",
    "virtualHosts": [
      ...
      {
        "name": "reviews.default.svc.cluster.local:9080",
        "domains": [
          ...
        ],
        "routes": [
          {
            "match": {
              "prefix": "/",
              "caseSensitive": true,
              "headers": [
                {
                  "name": "end-user",
                  "exactMatch": "jason"
                }
              ]
            },
            "route": {
              "cluster": "outbound|9080|v2|reviews.default.svc.cluster.local",
              "timeout": "0s",
              ...
            },
            ...
          },
          {
            "match": {
              "prefix": "/"
            },
            "route": {
              "cluster": "outbound|9080|v1|reviews.default.svc.cluster.local",
              "timeout": "0s",
            }
            ...
          }
        ],
        "includeRequestAttemptCount": true
      }
    ],
    "validateClusters": false
  }
]
```

</p></details></br>

9080 is the port name that the `review` service runs.

The other set of commands include:

```
$ istioctl proxy-status
...

$ istioctl proxy-config listeners productpage-v1-7f4cc988c6-c7vwp -o json --address 0.0.0.0 --port 9080
...

$ istioctl proxy-config cluster productpage-v1-6c886ff494-7vxhs --fqdn reviews.default.svc.cluster.local -o json
...
```

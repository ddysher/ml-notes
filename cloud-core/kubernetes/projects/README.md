<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Application](#application)
  - [operator-framework](#operator-framework)
  - [service-catalog](#service-catalog)
  - [kubeapps](#kubeapps)
  - [kubecarrier](#kubecarrier)
  - [kruise](#kruise)
  - [application](#application)
  - [(deprecated) operatorkit](#deprecated-operatorkit)
  - [(deprecated) k8s-appcontroller](#deprecated-k8s-appcontroller)
- [Developer](#developer)
  - [draft](#draft)
  - [codegen](#codegen)
  - [metacontroller](#metacontroller)
- [Templating & Packaging](#templating--packaging)
  - [helm](#helm)
  - [kustomize](#kustomize)
  - [kpt](#kpt)
  - [(deprecated) ksonnet](#deprecated-ksonnet)
- [Scheduling](#scheduling)
  - [kube-batch](#kube-batch)
  - [volcano](#volcano)
- [Insight & Scaling](#insight--scaling)
  - [k8s-prometheus-adaptor](#k8s-prometheus-adaptor)
  - [addon-resizer](#addon-resizer)
  - [cluster autoscaler](#cluster-autoscaler)
  - [keda](#keda)
  - [kuberhealthy](#kuberhealthy)
  - [(deprecated) resorcerer](#deprecated-resorcerer)
- [Storage](#storage)
  - [external-storage](#external-storage)
  - [trident](#trident)
- [Network](#network)
  - [antrea](#antrea)
  - [multus-cni](#multus-cni)
  - [metallb](#metallb)
  - [keepalived-vip](#keepalived-vip)
  - [ip-masq-agent](#ip-masq-agent)
  - [ingress](#ingress)
  - [kube-router](#kube-router)
  - [external-dns](#external-dns)
  - [amazon-vpc-cni](#amazon-vpc-cni)
  - [cni-ipvlan-vpc-k8s](#cni-ipvlan-vpc-k8s)
  - [(deprecated) service-loadbalancer](#deprecated-service-loadbalancer)
  - [(deprecated) cni-genie](#deprecated-cni-genie)
- [Security](#security)
  - [audit2rbac](#audit2rbac)
  - [cert-manager](#cert-manager)
  - [kyverno](#kyverno)
  - [k-rail](#k-rail)
  - [polaris](#polaris)
  - [sealed-secrets](#sealed-secrets)
  - [kube-rbac-proxy](#kube-rbac-proxy)
  - [hierarchical namespaces controller](#hierarchical-namespaces-controller)
- [Node & Resource](#node--resource)
  - [gpushare](#gpushare)
  - [kubegpu](#kubegpu)
  - [virtual-kubelet](#virtual-kubelet)
  - [node problem detector](#node-problem-detector)
  - [krustlet](#krustlet)
- [Cluster & DR](#cluster--dr)
  - [kubespray](#kubespray)
  - [kops](#kops)
  - [kubeadm](#kubeadm)
  - [velero](#velero)
  - [clusterlint](#clusterlint)
  - [kargo vs. kops. vs kubeadm](#kargo-vs-kops-vs-kubeadm)
  - [metal3](#metal3)
  - [(deprecated) kaptaind](#deprecated-kaptaind)
  - [(deprecated) kismatic](#deprecated-kismatic)
- [Virtualization](#virtualization)
  - [kubevirt](#kubevirt)
  - [virtlet](#virtlet)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Application

## operator-framework

link: [operator-framework](./operator-framework)

## service-catalog

link: [service-catalog](./service-catalog)

## kubeapps

link: [kubeapps](./kubeapps)

## kubecarrier

*Date: 05/29/2020, v0.1.0*

[kubecarrier](https://github.com/kubermatic/kubecarrier) is a tool for managing services across
multi-cluster. It is claimed to be a complement to OLM as it can work with existing CRDs and already
installed Operators. It is also claimed to be a complement to KubeFed as it works on a higher-level
where application is assigned to a pre-determined cluster (management cluster), and application can
be distributed via KubeFed.

kuebcarrier workflow:
- installing kubecarrier in a management cluster;
- create `Account` with different roles in the management cluster, i.e. `tenant` to consume resources
  and `provider` to provide resources;
- registering new cluster to kubecarrier via `ServiceCluster`;
- create `CatalogEntrySet` CRD which points an underline CRD (e.g. represents a DB) in service cluster;
  - kubecarrier will create **a copy of the CRD & an internal CRD in the management cluster**
  - the internal CRD is a "public interface" and will be used to provide services to different account
- create `Catalog` CRD to actually share the DB to tenants.

## kruise

link: [kruise](./kruise)

## application

*Date: 09/12/2019*

[Application](https://github.com/kubernetes-sigs/application) is a project from sig-apps to provide
rich metadata to describe an aplication, which might contain Deployment/StatefulSet/Service, etc.
The application controller doesn't create any concrete resources, e.g. in the following example,
the controller won't create Service, Deployment and StatefulSet for users:

<details><summary>Application Example</summary><p>

```yaml
apiVersion: app.k8s.io/v1beta1
kind: Application
metadata:
  name: "wordpress-01"
  labels:
    app.kubernetes.io/name: "wordpress-01"
    app.kubernetes.io/version: "3"
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: "wordpress-01"
  componentKinds:
  - group: core
    kind: Service
  - group: apps
    kind: Deployment
  - group: apps
    kind: StatefulSet
  descriptor:
    type: "wordpress"
    version: "4.9.4"
    description: "WordPress is open source software you can use to create a beautiful website, blog, or app."
    ...
```

</p></details></br>

However, it does aggregate a bit information (only a little), primarily object status. In another
word, the CRD is mainly used to display application-level information.

## (deprecated) operatorkit

*Date: 07/28/2017*

OperatorKit aims to unify the effort for implementing operators. Scopes of the project includes:
- setup, configuration, and validation of a CLI framework
- common logging handlers
- setup of common clients such as for CRD APIs, kube-apiserver API, leader election and analytics
- code for easy leadership election management
- easy management of k8s resources, such as reconciliation loops for CRDs and utility function to set up common cluster resources possibly at a later stage
- boilerplate code for registering, validating and configuring CRD specs
- resource monitoring, providing utilities to handle channels, decoding, caching and error handling
- enforce and supply best practices for disaster recovery, e.g. if the operator is on a rebooting node
- allow easy exposure of APIs if the operator wants to export data

*References*

- [operatorkit design doc](https://docs.google.com/document/d/1NJhFcNezJyLM952eaYVcdfIQFQYWsAx4oTaA82-Frdk/edit)

## (deprecated) k8s-appcontroller

*Date: 09/12/2019*

[k8s-AppController](https://github.com/Mirantis/k8s-AppController/) is a *deprecated* project from
mirantis for managing complext deployment. The core datastructure is `Dependency` and `Definition`.
To some extend, the project is not a real application controller, but rather a workflow controller.

Dependency is used to define application dependencies, e.g. following yaml claims the dependency
between `pod/eventually-alive-pod` and `job/test-job`.

<details><summary>Dependency Example</summary><p>

```yaml
apiVersion: appcontroller.k8s/v1alpha1
kind: Dependency
metadata:
  name: dependency-1
parent: pod/eventually-alive-pod
child: job/test-job
```

</p></details></br>

To control startup sequence, we need to wrap native Kubernetes resources into `Definition`, e.g.
the following command convert native job resource into definition.

<details><summary>Definition Example</summary><p>

```yaml
$ cat job.yaml | docker run -i --rm mirantis/k8s-appcontroller:latest kubeac wrap
apiVersion: appcontroller.k8s/v1alpha1
kind: Definition
metadata:
  name: job-pi
job:
  apiVersion: batch/v1
  kind: Job
  metadata:
    name: pi
  spec:
    template:
      metadata:
        name: pi
      spec:
        containers:
        - name: pi
          image: perl:5.28-slim
          command: ["perl",  "-Mbignum=bpi", "-wle", "print bpi(2000)"]
        restartPolicy: Never
```

</p></details></br>

# Developer

## draft

*Date: 06/06/2017, no release*

[draft](https://github.com/Azure/draft) helps developers containerize applications, and helps with
development cycles, i.e. debug in local development then deploy applications to kubernetes. A typical
workflow:
- `draft create` to create containerized applications based on so-called packs
- `draft up` to deploy applications to kubernetes

draft has a server component running inside kubernetes, and a local daemon to interact with the
server (if configured to watch chanages). Once code changes, the daemon will send changes to server
component. The server component will build the docker image and pushes the image to a registry, as
well as instructing helm to install the Helm chart.

*References*

- http://blog.kubernetes.io/2017/05/draft-kubernetes-container-development.html
- [draft design doc](https://github.com/Azure/draft/blob/3fad7ef57ce9ed198649bef38023be3860792d24/docs/design.md)
- [draft installation](https://github.com/Azure/draft/blob/3fad7ef57ce9ed198649bef38023be3860792d24/docs/install.md)
- [draft getting started](https://github.com/Azure/draft/blob/3fad7ef57ce9ed198649bef38023be3860792d24/docs/getting-started.md)

## codegen

link: [codegen](./codegen)

## metacontroller

*Date: 06/01/2018*

[Metacontroller](https://github.com/GoogleCloudPlatform/metacontroller) is a controller for controller;
developyer only needs to write hooks for processing registered events (with CRDs), and metacontroller
handles the rest.

# Templating & Packaging

## helm

link: [helm](./helm)

## kustomize

link: [kustomize](./kustomize)

## kpt

link: [kpt](./kpt)

## (deprecated) ksonnet

*Date: 02/22/2018, v0.8.0*

Ksonnet has relatively good documentation, read following docs in order:
- https://ksonnet.io/docs/tutorial
- https://ksonnet.io/docs/concepts
- https://ksonnet.io/tour/welcome

*Reference*

- https://stackoverflow.com/questions/48867912/draft-vs-helm-vs-ksonnet-complementing-or-replacing
- https://blog.openshift.com/kubernetes-state-app-templating/

# Scheduling

## kube-batch

link: [kube-batch](./kube-batch)

## volcano

[volcano](https://volcano.sh) is built on top of kube-batch to provide batch scheduling. volcano's
scheduler is a direct copy of kube-batch, with the following additions:
- a new `Job` API (independent of core Kubernetes Job), allowing users to create a batch job directly from volcano
  - the `Job` API provides features like multiple PodTemplate, better ErrorHandling, etc
- a new admission controller component to validate Job resource
- a new controller component to reconcile status, including job-controller, podgroup-controller,
  queue-controller, garbagecollector-controller, etc
- few additional actions and plugins, compared to kube-batch

```
$ kubectl get pods -n volcano-system
NAME                                   READY   STATUS      RESTARTS   AGE
volcano-admission-5bd5756f79-9lj4t     1/1     Running     0          49m
volcano-admission-init-x2jlk           0/1     Completed   0          49m
volcano-controllers-687948d9c8-q8fkm   1/1     Running     0          49m
volcano-scheduler-79f569766f-rnwt6     1/1     Running     0          49m
```

# Insight & Scaling

## k8s-prometheus-adaptor

*Date: 01/14/2018*

The project is an implementation of Kubernetes custom metrics API, using the framework [here](https://github.com/kubernetes-incubator/custom-metrics-apiserver).
Basically, it registers itself as a third-party API service. Kubernetes core API server will proxy
request to it, i.e. client sends requst to endpoint `/apis/custom-metrics.metrics.k8s.io/v1beta1`
just like other standard requests; kubernetes API server then proxies the request to this adapter,
which translates the request to prometheus query language and return the metrics result.

*References*

- [deploy adaptor](https://github.com/DirectXMan12/k8s-prometheus-adapter/tree/master/deploy)

## addon-resizer

*Date: 08/06/2017, Kubernetes v1.7, no release*

[addon-resizer](https://github.com/kubernetes/autoscaler/tree/master/addon-resizer) is a container
which watches another container in a deployment, and vertically scales the dependent container up
and down (only one container).  It is usually deployed as a sidecar or as another deployment.
addon-resizer is also called nanny, i.e. babysitter.

**workflow**

addon-resizer polls kubernetes every configurable (default 10s) interval to decide if scaling is
needed for its dependent container. At each bookkeeping, it retrieves number of nodes from kubernetes,
and uses the information, along with command line flags, to estimate a resource requirements. If the
resource requirement is different from current value, it scales the container.

## cluster autoscaler

*Date: 08/06/2017, Kubernetes v1.7, project status beta*

[Cluster Autoscaler](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler) is a
standalone program that adjusts the size of a Kubernetes cluster to meet the current needs. It
assumes kubernetes nodes are running undera cloud provider node group. Cluster Autoscaler has
extensive documentation, ref [here](https://github.com/kubernetes/autoscaler/tree/cluster-autoscaler-0.6.0/cluster-autoscaler).

## keda

link: [keda](./keda)

## kuberhealthy

*Date: 06/22/2020, v2.2*

[KuberHealth](https://github.com/Comcast/kuberhealthy) is an operator to check Kubernetes health.
It contains a list of pre-defined "synthetic" checks and allows user to create their own checks.
The workflow in kuberhealthy is simple:
- user create a custom resource `khcheck` to define the check
- operator creates checker pod, which will in turn create "check resources", e.g. run a ds to check node status
- operator collectos the check status information and reports it via promethes metrics, influxdb, etc

## (deprecated) resorcerer

*Date: 08/06/2017, no release*

[resorcerer](https://github.com/openshift-demos/resorcerer) is an experimental implementation of
VPA, i.e. to scale container resource requirements. It is a daemonset running in kubernetes cluster,
use prometheus to retrieve container metrics, and provides rest API for users. resorcerer is very
simple, the core of it is three APIs:

```
GET /observation/$POD/$CONTAINER?period=$PERIOD
GET /recommendation/$POD/$CONTAINER
POST /adjustment/$POD/$CONTAINER cpu=$CPUSEC mem=$MEMINBYTES
```

Calling the first API will execute a pre-defined query against prometheus to observe container
resource usage. It will save the value in memory. The second API will simply return the usage data;
and the last apply the recommendation to kubernetes (according to how it is deployed, i.e.
deployment, standalone pod, etc).

# Storage

## external-storage

link: [external-storage](./external-storage)

## trident

link: [trident](./trident)

# Network

## antrea

*Date: 11/26/2019, v0.1*

[antrea](https://github.com/vmware-tanzu/antrea) is a Kubernetes network solution from VMWare, it
implements:
- Pod networking using OVS
- Network Security
- ClusterIP using OVS (planned)

For more information, refer to
- [archtecture guide](https://github.com/vmware-tanzu/antrea/blob/v0.1.0/docs/architecture.md)

## multus-cni

- *Date: 06/02/2018, v0.2*
- *Date: 12/13/2018, v3.1*

[multus-cni](https://github.com/intel/multus-cni) acts as a multi plugin in Kubernetes and provides
the multiple network interface support in a pod. Unlike cni-genie, in multus, networks are represented
as CRDs (using config file is also supported). Pods claim network using annotation as well. There is
ongoing effort to standardize network config CRD, ref [here](https://docs.google.com/document/d/1Ny03h6IDVy_e_vmElOqR7UdTPAG_RNydhVE1Kx54kFQ/edit#).

*Update on 12/13/2018, v3.1*

Now network plumbing working group has reached agreement on v1 version of multiple pod cni network:
- [v1 specification](https://docs.google.com/document/d/1Ny03h6IDVy_e_vmElOqR7UdTPAG_RNydhVE1Kx54kFQ/edit#)
- [v2 considerations](https://docs.google.com/document/d/1grqQ4Twqn0gnt2QraM-HVctT4HdyJgtZ-gqiGThCgaM/edit#)

multus-cni becomes the reference implementation of the standard, for more information, see:
- [multus-cni quick start](https://github.com/intel/multus-cni/blob/f157f424b5e6f806e83288335396212bd8d21ff2/doc/quickstart.md)
- [multus-cni how to use (detailed quick start)](https://github.com/intel/multus-cni/blob/f157f424b5e6f806e83288335396212bd8d21ff2/doc/how-to-use.md)

## metallb

*Date: 01/10/2018*

[MetalLB](https://github.com/google/metallb) is a load-balancer implementation for bare metal
Kubernetes clusters, using standard routing protocols (BGP). It consists of a controller to assign
load-balancer IP addresses (pre-configured), a daemonset of BGP speaker to peer with BGP router
outside of kubernetes cluster and announces assigned service IPs to the world.

## keepalived-vip

*Date: 04/07/2017*

[keepalived-vip](https://github.com/kubernetes/contrib/tree/master/keepalived-vip) is a project to
provide HA access to a service in baremtal environment; theoretically, it has nothing to do with
ingress; but can be used together with ingress to provider high-available ingress solution.

Workflow Senario:
- admin deploys keepalived containers on selected nodes; note the keepalived container will take a
  configmap as its input. The configmap is used to decide what services it will target.
- user creates pods (deployment) and servcie.
- user creates configmap to tell keepalived container to provide HA for the pods and service. The
  following configmap tells keepalived to use vip `10.4.0.50` for service `echoheaders` in namespace
  `default`
  ```yaml
  apiVersion: v1
  kind: ConfigMap
  metadata:
    name: vip-configmap
  data:
    10.4.0.50: default/echoheaders"
  ```

The above senario doesn't involve ingress. For ingress, we can deploy this keepalived vip and tell
it to use a vip for ingress controllers. However, in this case, traffic will first go to ingress,
then backend pods, which is two bounce.

A vip is given to a set of nodes; when user connects to the vip, traffic will be forwarded to backing
pods.

## ip-masq-agent

link: [ip-masq-agent](./ip-masq-agent)

## ingress

link: [ingress](./ingress)

## kube-router

link: [kube-router](./kube-router)

## external-dns

link: [external-dns](./external-dns)

## amazon-vpc-cni

A [CNI plugin](https://github.com/aws/amazon-vpc-cni-k8s/blob/v1.5.0/docs/cni-proposal.md) for amazon VPC.

Each EC2 instance can have multiple ENI (Elastic Network Interface), and each ENI can have multiple
secondary IP addresses. The primary IP address, i.e. the external node IP address, will be attached
to each ENI, and all the secondary IP addresses will be used as Pod IP. The CNI plugin is responsible
to allocate the IPs.

The network mode on each EC2 is similar to bridge CNI: a veth pair is created with one end attached
to pod network namespace, and the other end attached to host network namespace. Each veth is assigned
a secondary IP address.

The gateway inside each Pod is "169.254.1.1", which is a link-local address used to 'fool' Pod to
forward traffic to its internal veth interface. To do this, arp proxy is used to statically reply
the request "who has address 169.254.1.1", with the answer "eth0 (mac_address) has". There are also
a couple of ip/route rules setup at the host side.

To speed up IP allocation, a warm-up pool is maintained on each node.

## cni-ipvlan-vpc-k8s

This [CNI from Lyft](https://github.com/lyft/cni-ipvlan-vpc-k8s) is similar to amazon-vpc-cni, but
instead uses IPvlan L2 mode.

## (deprecated) service-loadbalancer

*Date: 05/13/2017, kubernetes v1.6, deprecated*

[service loadbalancer](https://github.com/kubernetes/contrib/tree/master/service-loadbalancer) is
deprecated in favor of ingress controller. At its core, service loadbalancer watches the api for
services and endpoints, and reload haproxy's configuration (can be other loadbalancer as well, like
F5). However, unlike ingress, there is no API for controlling its behavior, and it lacks a lot of
features seen in ingress.

## (deprecated) cni-genie

*Date: 08/19/2017*

[cni-genie](https://github.com/Huawei-PaaS/CNI-Genie) is a solution from huawei which enables:
- multiple cni plugins: user can choose which plugin to use when launching pod via annotation;
  typically, different network (or plugin) uses different cidr
- multiple IP addresses: user can request IP addresses from multiple cni
- select ideal network: cni-genie can help user choose a cni plugin to use based on information
  like per network load

Essentially, it is a proxy to underline cni.

*References*

- [high level design](https://github.com/Huawei-PaaS/CNI-Genie/blob/8a35c2c0fe05ecfd967be6952a9d5154bf071655/docs/HLD.md)
- [feature set](https://github.com/Huawei-PaaS/CNI-Genie/blob/8a35c2c0fe05ecfd967be6952a9d5154bf071655/docs/CNIGenieFeatureSet.md)

# Security

## audit2rbac

*Date: 06/03/2018*

[audit2rbac](https://github.com/liggitt/audit2rbac) converts advanced audit log (audit.Event) to
rbac rules (rbac.Role, rbac.RoleBinding, etc)

## cert-manager

*Date: 07/15/2020*

[cert-manager](https://github.com/jetstack/cert-manager) is a native Kubernetes certificate management
controller. It can help with issuing certificates from a variety of sources, such as Let's Encrypt,
HashiCorp Vault, Venafi, a simple signing key pair, or self signed. It will ensure certificates are
valid and up to date, and attempt to renew certificates at a configured time before expiry. One of
the primary use cases is automatically request certificates for ingress endpoints.

The concepts in cert-manager are (also created as CRDs in Kubernetes):
- Issuer
- ClusterIssuer
- Certificate
- CertificateRequest
- Challenge
- Order

The components in cert-manager are:

```
$ kubectl get pods -n cert-manager
NAME                                      READY   STATUS    RESTARTS   AGE
cert-manager-7747db9d88-tdlsq             1/1     Running   0          4h30m
cert-manager-cainjector-87c85c6ff-gtb72   1/1     Running   0          4h30m
cert-manager-webhook-64dc9fff44-j7568     1/1     Running   0          4h30m
```

Following is a brief steps when using cert-manager with ingress resource:
- install cert-manager & nginx-ingress controller
- assign a DNS name, e.g. `example.com` to `1.1.1.1`
- deploy a demo application serving an insecure connection
- create a let's encrypt `Issuer` defined in cert-manager, the core information includes,
  - `email`: a registered account address
  - `privateKeySecretRef`: secret to store key/cert pair
  - `solvers`: the solver which is used to solve tls [challenge](https://letsencrypt.org/docs/challenge-types/), i.e. http01, dns01
- deploy a TLS ingress resource, which points to the previous issuer via `cert-manager.io/issuer` label.

After the following steps, under the hood, cert-manager will create `Challenge` and `Order` CRDs
(end-user will never need to create the resources); it will automatically answer challenges from
let's encrypt, and save the issued key/cert pair in the named secret.

## kyverno

*Date: 12/14/2019*

[kyverno](https://github.com/nirmata/kyverno) is a policy engine designed for Kubernetes. The policy
engine is implemented as CRD and admission webhook controller. Users write CRD YAML configuration to
define policy, which can be:
- validation: define policy to validate resources
- mutation: contains actions that will be applied to matching resources
- generation: used to create default resources for a namespace

kyverno comes with its own set of rules configurations, using standard regex, json, etc.

## k-rail

*Date: 12/14/2019*

[k-rail](https://github.com/cruise-automation/k-rail/) is a policy engine designed for Kubernetes.
k-rail is implemented as an admission webhook, without using CRDs. It provides a set of built-in
policies, and extending policy requires writing Go program. The audit results can be fetched from
Kubernetes events, or directly from k-rail logs.

## polaris

*Date: 12/14/2019*

[polaris](https://github.com/FairwindsOps/polaris) is a Kubernetes validation tool: it runs a variety
of checks to ensure that Kubernetes pods and controllers are configured using best practices.

polaris contains three independent components:
- a dashboard to audit Kubernetes cluster
- an admission controller to ensure policy
- a command line to test YAML configuration

## sealed-secrets

*Date: 05/26/2020, v0.12.4*

[sealed-secrets](https://github.com/bitnami-labs/sealed-secrets) is a tool for managing one-way
encrypted secrets.

> Problem: "I can manage all my K8s config in git, except Secrets."
>
> Solution: Encrypt your Secret into a SealedSecret, which is safe to store - even to a public
> repository. The SealedSecret can be decrypted only by the controller running in the target cluster
> and nobody else (not even the original author) is able to obtain the original Secret from the
> SealedSecret.

The project contains a client side `kubeseal` and a controller running in the cluster. The controller
will reference a cert/key pair in a Kubernetes secret, and will use the key to encrypt/decrypt user
secrets. A new CRD called `SealedSecret` is created to manage `Secret`, similar to the relationship
of `Deployment` and `Pod`.

To use:

```
# install
$ helm install --namespace kube-system --name my-release stable/sealed-secrets

# create a secret file
$ echo "apiVersion: v1
kind: Secret
metadata:
  name: secret1
type: Opaque
data:
  username: YWRtaW4=            # echo -n 'admin' | base64
  password: MWYyZDFlMmU2N2Rm    # echo -n '1f2d1e2e67df' | base64
" > secret1.yaml

# seal it
$ kubeseal --format yaml --controller-name my-release-sealed-secrets < secret1.yaml > sealed-secret1.yaml

# then create sealed-secret
$ kubectl create -f sealed-secret1.yaml
sealedsecret.bitnami.com/secret1 created

# find the managed secret
$ kubectl get secret
NAME                  TYPE                                  DATA   AGE
default-token-7c9vz   kubernetes.io/service-account-token   3      20h
secret1               Opaque                                2      27s

$ kubectl get sealedsecrets.bitnami.com
NAME      AGE
secret1   27s

```

## kube-rbac-proxy

*Date: 04/30/2020, alpha*

[One-line introduction](https://github.com/brancz/kube-rbac-proxy):

> The kube-rbac-proxy is a small HTTP proxy for a single upstream, that can perform RBAC authorization
> against the Kubernetes API using SubjectAccessReview.

Motivation:

> I developed this proxy in order to be able to protect Prometheus metrics endpoints. In a scenario,
> where an attacker might obtain full control over a Pod, that attacker would have the ability to
> discover a lot of information about the workload as well as the current load of the respective
> workload. This information could originate for example from the node-exporter and kube-state-metrics.
> Both of those metric sources can commonly be found in Prometheus monitoring stacks on Kubernetes.

How does it work:

> On an incoming request, kube-rbac-proxy first figures out which user is performing the request.
> The kube-rbac-proxy supports using client TLS certificates, as well as tokens. In case of a client
> certificates, the certificate is simply validated against the configured CA. In case of a bearer
> token being presented, the authentication.k8s.io is used to perform a TokenReview.

> Once a user has been authenticated, again the authentication.k8s.io is used to perform a
> SubjectAccessReview, in order to authorize the respective request, to ensure the authenticated
> user has the required RBAC roles.

In general, kube-rbac-proxy runs as a reverse proxy sidecar alongside the component being protected.
There is no iptables magic: external system will call kube-rbac-proxy first, which will perform
authN/Z and proxy traffic to upstream (usually at localhost).

## hierarchical namespaces controller

- *Date: 2020/06/26*

The HNC subproject provides a mechanism to manage multiple namespaces into trees, to allow more
management capabilities around namespaces. The project is part of multi-tenancy working group, which
is sponsored by sig-auth. The motivation is:
- to manage policies across multiple namespaces
  - HNC has explicit configurations about what resources to deal with, and in what mode (propragate, ignore, etc)
  - an alternative approach is to use labels to manage all namespaces, ref: [namespace-configuration-operator](https://github.com/redhat-cop/namespace-configuration-operator)
- to allow teams to create namespaces themselves without having cluster-wide priviledges
  - HNC uses the concept of subnamespaces, and will create namespaces on behave of users
  - teams that wish to manage subnamespaces only need to be granted access to `subnamespaceanchor` CRD

The installed components are:

```
$ kubectl get crd
NAME                                   CREATED AT
hierarchyconfigurations.hnc.x-k8s.io   2020-06-26T04:52:28Z
hncconfigurations.hnc.x-k8s.io         2020-06-26T04:52:28Z
subnamespaceanchors.hnc.x-k8s.io       2020-06-26T04:52:28Z

$ kubectl get all -n hnc-system
NAME                                         READY   STATUS    RESTARTS   AGE
pod/hnc-controller-manager-cf545bf66-pr5gx   2/2     Running   0          56m

NAME                                             TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)    AGE
service/hnc-controller-manager-metrics-service   ClusterIP   10.0.0.219   <none>        8443/TCP   56m
service/hnc-webhook-service                      ClusterIP   10.0.0.154   <none>        443/TCP    56m

...
```

Here,
- `hncconfigurations` is a cluster scope config about how HNC behaves;
- `subnamespaceanchors` represents subnamespaces of a parent namespace; it is created under the parent namespace
- `hierarchyconfigurations` represents hierarchy of a namespace; it is created for each namespace

<details><summary>Few design considerations</summary><p>

> By default, HNC only propagates RBAC Roles and RoleBindings. However, you can configure HNC to
> propagate any other Kind of object, including custom resources. If you create objects of these
> kinds in a parent namespace, it will automatically be copied into any descendant namespaces as
> well. You cannot modify these propagated copies; HNC’s admission controllers will attempt to stop
> you from editing them, and if you bypass the controllers, HNC will overwrite them.
>
> Every propagated object in HNC is given the `hnc.x-k8s.io/inheritedFrom` label. The value of this
> label indicates the namespace that contains the original object. The HNC admission controller will
> prevent you from adding or removing this label, but if you manage to add it, HNC will likely
> promptly delete the object (believing that the source object has been deleted), while if you
> manage to delete it, HNC will simply overwrite the object anyway.
>
> While the hierarchy is defined in the `HierarchicalConfiguration` object, it is reflected on the
> namespaces themselves via HNC-managed labels.
>
> Any user (or service account) with the ability to create or update the hierarchical configuration
> of a namespace is known as an administrator of that namespace from HNC's perspective, even if they
> have no other permissions within that namespace. On the other hand, even if you create a root
> namespace (via kubectl create namespace foo), you are not an administrator of it (from HNC's
> perspective) unless you also have update permissions on the hierarchical config.
>
> Deleting namespaces is very dangerous, and deleting subnamespaces can result in entire subtrees of
> namespaces being deleted as well. Therefore, you may set the `allowCascadingDelete` field either
> on the child namespace, on its parent, or (if the parent is a subnamespace itself) on its parent,
> and so on.
>
> Changing parent of a namespace is dangerous. In general, to change the parent of your namespace N
> from A to B, you must have the following privileges:
> - You must be the admin of the highest namespace that will no longer be an ancestor of namespace N after this change, in order to confirm that you are happy to lose your privileges in namespace N.
> - You must be the admin of namespace B, in order to acknowledge that sensitive objects from B may be copied into namespace N.
>
> Conditions are reported as part of the status of the `HierarchicalConfiguration` object in each
> namespace, are summarized across the entire cluster in the status of the `HNCConfiguration` object,
> and are exposed via the hnc/namespace_conditions metric. Every condition contains a machine-readable
> code, a human-readable message, and an optional list of objects that are affected by the condition.
> For example:
> - The `CritCycle` condition is used if you somehow bypass the validating webhook and create a cycle.
> - The `CannotPropagate` condition indicates that an object in this namespace cannot be propagated
>   to other namespaces. This condition is displayed in the source namespace.

</p></details></br>

*References*

- [hnc how-to](https://github.com/kubernetes-sigs/multi-tenancy/blob/hnc-v0.4/incubator/hnc/docs/user-guide/how-to.md)
- [hnc concepts](https://github.com/kubernetes-sigs/multi-tenancy/blob/hnc-v0.4/incubator/hnc/docs/user-guide/concepts.md)

# Node & Resource

## gpushare

*Date: 05/02/2019*

Aliyun gpushare proposes a simple extension to allow 'share' GPU resource in Kubernetes cluster, it
consists of:
- [a modified device plugin](https://github.com/AliyunContainerService/gpushare-device-plugin) to report GPU memory (in MiB or GiB), apart from reporting number of GPU
- [a scheduler extender](https://github.com/AliyunContainerService/gpushare-scheduler-extender) that understands the extended GPU memory resource and allocate GPU accordingly

Pod requesting GPU memory will add the following resource:

```yaml
resources:
  limits:
    aliyun.com/gpu-mem: 16276
```

The extension doesn't resolve the following issues:
- application level isolation: the shema above is only used for scheduling, application should be
  aware of using only requested memory, which will be passed in as env into application pod.
- only GPU memory is added as extended resource, i.e. cuda cores are not considered.
- all available GPU memory is treated the same, i.e. it doesn't differentiate different type of GPU cards.

## kubegpu

link: [kubegpu](./kubegpu)

## virtual-kubelet

- *Date: 10/03/2018, v0.6*
- *Date: 02/14/2020, v1.2*

[virtual kubelet](https://github.com/virtual-kubelet/virtual-kubelet) registers to Kubernetes as a
'normal' node, but backed by other services. It is a Kubelet implementation that masquerades as a
kubelet for the purposes of connecting Kubernetes to other APIs. Despite the name `virtual-kubelet`,
it has nothing to do with vm-based virtualization (like kubevirt, virtlet); rather, it's best seen
as a complement to serverless system.

Following is a summary of how it works:
- virtual kubelet runs as a Pod in Kubernetes cluster. The Pod registers itself as a node, and
  watches for Pod scheduled to it. The virtual kubelet doesn't have an IP address.
- once a Pod is scheduled to it (using node selector from user), virtual-kubelet calls external
  provider (e.g. azure aci, hyper, aws fargate, etc) to create real containers.
- Pod status is updated to reflect the status from external provider.

The created pod/container is running in remote cluster, managed by cloud providers. virtual kubelet
it an API bridge between Kubernetes and cloud providers - the container for user application, once
started, has nothing to do with virtual kubelet. To use virtual-kubelet, users create Pod with
specific taint and node-selectors, then Kubernetes & virtual-kubelet will do the rest. It's possible
to create a multiple Pods, e.g. using Deployment, and assign them to virtual kubelet. virtual
kubelet will create equal number of containers in cloud providers.

virtual-kubelet is originated from Microsoft, and donated to CNCF as a sandbox project.

*Update on 02/14/2020, v1.2*

Cloud providers are moved out-of-tree, including:
- [Admiralty Multi-Cluster Scheduler](https://github.com/admiraltyio/multicluster-scheduler)
- Alibaba Cloud Elastic Container Instance (ECI)
- AWS Fargate
- Azure Batch
- Azure Container Instances (ACI)
- Kubernetes Container Runtime Interface (CRI)
- Huawei Cloud Container Instance (CCI)
- HashiCorp Nomad
- OpenStack Zun

*References*

- [how virtual-kubelet works](https://github.com/virtual-kubelet/virtual-kubelet/tree/v0.6.2#how-it-works)
- [azure aci provider (old)](https://github.com/virtual-kubelet/virtual-kubelet/blob/v0.6.2/providers/azure/README.md)
- [azure aci provider (new)](https://github.com/virtual-kubelet/azure-aci)
- [aws blog](https://aws.amazon.com/blogs/opensource/aws-fargate-virtual-kubelet/)

## node problem detector

*Date: 10/18/2017, v0.4.1*

[Node problem detector](https://github.com/kubernetes/node-problem-detector) surfaces node level
problems to kubernetes control plane. It consists of a npd and multple problem daemons. The problem
daemons are running as goroutine right now, but will be expanded to side car in the future. Node
problem detector is simple, but its design is comprehensive, ref [here](https://docs.google.com/document/d/1cs1kqLziG-Ww145yN6vvlKguPbQQ0psrSBnEqpy0pzE/edit).

## krustlet

[krustlet](https://github.com/deislabs/krustlet) is an implementation of Kubelet in Rust. Instead
of using container, it uses WebAssembly (WASM) to run Pod, and utilizes OCI artifacts as a registry
to store WASM artifacts.

# Cluster & DR

## kubespray

*Date: 04/26/2017, kargo v2.1.1*

[kargo](https://github.com/kubespray/kargo-cli) is a pure ansible playbook to deploy kubernetes,
with a lot of options. To ease deployment, kargo provides a cli tool: kargo-cli; so that user
doesn't have to interact with ansible directly.

*Update on 11/07/2018, v2.7.0*

kargo is moved to Kubernetes incubator and renamed [kubespray](https://github.com/kubernetes-incubator/kubespray).

*References*

- https://github.com/kubernetes-incubator/kargo/blob/v2.1.1/docs/getting-started.md

## kops

*Date: 04/26/2017, kops v1.5.3*

[Kops](https://github.com/kubernetes/kops) is the `kubectl` for clusters; common commands used in
kops are:

```
kops create cluster
kops update cluster
kops get clusters
kops delete cluster
```

Kops is written in go; unlike other tools, it doesn't depend on other management platform like
ansible. kops defines a specification similar to kubernetes, but the resource is NOT part of
kubernetes. Below is a very brief workflow:

- Run `kops create cluster`, a yaml file is created with keys like `apiVersion`, `kind`
- Run `kops update cluster`, the yaml file is parsed and applied to cloud, e.g. aws, gce.

*References*

- https://github.com/kubernetes/kops/blob/1.5.3/docs/aws.md
- https://github.com/kubernetes/kops/blob/1.5.3/docs/philosophy.md
- https://github.com/kubernetes/kops/blob/1.5.3/docs/boot-sequence.md

## kubeadm

*Date: 04/13/2020*

[kubeadm](https://github.com/kubernetes/kubeadm) is a tool built to create Kubernetes clusters.
Note kubeadm is not a complete solution for creating a cluster, it is meant to be used by other
tools. In addition, to use kubeadm, users need to do extra preparation, e.g. download kubelet,
setup CNI networking, etc.

The set of commands in kubeadm include:
- `kubeadm init` to bootstrap the initial Kubernetes control-plane node.
- `kubeadm join` to bootstrap a Kubernetes worker node or an additional control plane node, and join it to the cluster.
- `kubeadm upgrade` to upgrade a Kubernetes cluster to a newer version.
- `kubeadm reset` to revert any changes made to this host by kubeadm init or kubeadm join.

## velero

link: [velero](./velero)

## clusterlint

[clusterlint](https://github.com/digitalocean/clusterlint) is a project from DigitalOcean that
checks a Kubernetes cluster conforms to a set of best practices, include:
- security configurations
- webhook configurations
- resource configurations

The tool is mainly used before running an upgrade of DOKS, DigitalOcean Kubernetes Service.

## kargo vs. kops. vs kubeadm

Quick summary:
- Kargo runs on bare metal and most clouds, using Ansible as its substrate for provisioning and orchestration.
- Kops performs the provisioning and orchestration itself, and as such is less flexible in deployment platforms.
- Kubeadm's scope is limited to the local node filesystem and the Kubernetes API, and it is intended to be a
  composable building block of higher level tools.

For people with familiarity with Ansible, existing Ansible deployments or the desire to run a
Kubernetes cluster across multiple platforms, Kargo is a good choice. Kops, however, is more tightly
integrated with the unique features of the clouds it supports so it could be a better choice if you
know that you will only be using one platform for the foreseeable future.

## metal3

Metal3 (MetalKube) allows user to manage bare metal hosts for Kubernetes. Metal3 runs on Kubernetes
and is managed through Kubernetes interfaces. Under the hood, it will leverage projects like OpenStack
Ironic for host management.

Official Introduction:

> There are a number of great open source tools for bare metal host provisioning, including Ironic. [Metal3.io](https://metal3.io/)
> aims to build on these technologies to provide a Kubernetes native API for managing bare metal hosts
> via a provisioning stack that is also running on Kubernetes. We believe that Kubernetes Native
> Infrastructure, or managing your infrastructure just like your applications, is a powerful next
> step in the evolution of infrastructure management.
>
> The Metal3.io project is also building integration with the Kubernetes cluster-api project, allowing
> Metal3.io to be used as an infrastructure backend for Machine objects from the Cluster API.

Metal3 contains multiple components:
- [cluster-api-provider-metal3](https://github.com/metal3-io/cluster-api-provider-metal3)
- [baremetal-operator](https://github.com/metal3-io/baremetal-operator)

**cluster-api-provider-metal3**

The first component is cluster-api-provider-metal3, which is an implementation of the Machine
Actuator interface defined by the cluster-api project. This actuator reacts to changes to Machine
objects (CRD defined in cluster-api) and acts as a client of the BareMetalHost (CRD defined in
Metal3).

A full illustration of the architecture can be found [here](https://github.com/metal3-io/cluster-api-provider-metal3/blob/v0.3.1/docs/architecture.md).

**baremetal-operator**

The baremetal-operator is a controller for a new custom resource, BareMetalHost. This custom resource
represents an inventory of known (configured or automatically discovered) bare metal hosts. When a
Machine is created the Bare Metal Actuator will claim one of these hosts to be provisioned as a new
Kubernetes node. In response to BareMetalHost updates, the controller will perform bare metal host
provisioning actions as necessary to reach the desired state. The creation of the BareMetalHost
inventory can be done in two ways:
- Manually via creating BareMetalHost objects.
- Optionally, automatically created via a bare metal host discovery process.

The operator manages a set of tools for controlling the power on the host, monitoring the host status,
and provisioning images to the host. These tools run inside the pod with the operator, and do not
require any configuration by the user.

To simply put, it's the operator in charge of definitions of physical hosts, containing information
about how to reach the Out of Band management controller (reaching the server even if it's powered
down, either via dedicated or shared nic), URL of image to provision, plus other properties related
with hosts being used for provisioning instances.

## (deprecated) kaptaind

*Date: 09/14/2017*

[kaptaind](https://github.com/kaptaind/kaptaind) is a simple tool to backup & restore kubernetes
cluster snapshots. A broker component is running as api server, accepting export & import (i.e.
backup & restore) tasks. An agent is typically running in kubernetes cluster and asks for import
task. The export & import process is copy/past yaml files.

## (deprecated) kismatic

*Date: 04/26/2017, v 1.3.1*

[kismatic](https://github.com/apprenda/kismatic) is a set of production-ready defaults and best
practice tools for creating enterprise-tuned Kubernetes clusters. It is based on golang and ansible,
where ansible playbook is launched via golang (os.exec). kismatic installation flow:

```
$ kismatic install plan
$ kismatic install validate
$ kismatic install apply
```

- `plan`: kismatic creates a config yaml file
- `validate`: check hosts requirements
- `apply`: actually install kubernetes

Between 'plan' and 'validate', admin needs to provision hosts manually. kismatic is not just about
cluster deployment, it also does simple management, like installing kubedash, ingress. During
installation, kismatic does hosts validation, kubernetes smoke test.

*References*

- https://github.com/apprenda/kismatic/blob/v1.3.1/docs/INTENT.md
- https://github.com/apprenda/kismatic/blob/v1.3.1/docs/INSTALL.md
- https://github.com/apprenda/kismatic/blob/v1.3.1/docs/PLAN.md
- https://github.com/apprenda/kismatic/blob/v1.3.1/docs/PROVISION.md

# Virtualization

## kubevirt

link: [kubevirt](./kubevirt)

## virtlet

*Date: 10/03/2018, v1.4.0*

[virtlet](https://github.com/Mirantis/virtlet) is created from Mirantis.

virtlet is a Kubernetes CRI implementation for running VM workloads. It uses [criproxy](https://github.com/Mirantis/criproxy)
to proxy requests from kubelet to virtlet (in order to support multiple runtime). Note this can be
deprecated in favor of Kubernetes 1.12 new feature `RuntimeClass`.

Virtlet consists of the following components:
- virtlet manager - implements CRI interface for virtualization and image handling
- libvirt instance
- tapmanager which is responsible for managing VM networking
- vmwrapper which is responsible for setting up the environment for emulator
- emulator, currently qemu with KVM support (with possibility to disable KVM)

Note that virlet has only a single running component (deployed as daemonset):
- qemu and libvirt are installed in `virtlet-base` dockerfile
- virtlet manager and tapmanager are running as separate goroutines

Working with virtlet is similar to regular operations in Kubernetes, you create a Pod and request
virtlet as sandbox runtime, then a VM will be created via virtlet and its status is reported back
in Pod status, e.g. Pod IP is the VM's IP.

*References*

- [introduction and comparison to other similar projects](https://www.mirantis.com/blog/virtlet-run-vms-as-kubernetes-pods/)
- [virtlet architecture](https://github.com/Mirantis/virtlet/blob/v1.4.0/docs/architecture.md)
- [virtlet deployment](https://github.com/Mirantis/virtlet/blob/v1.4.0/deploy/real-cluster.md)

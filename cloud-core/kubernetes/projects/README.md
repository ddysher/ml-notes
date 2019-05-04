<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Networking](#networking)
  - [cni-genie](#cni-genie)
  - [multus-cni](#multus-cni)
  - [metallb](#metallb)
  - [keepalived-vip](#keepalived-vip)
  - [service-loadbalancer](#service-loadbalancer)
  - [ip-masq-agent](#ip-masq-agent)
  - [ingress](#ingress)
  - [kube-router](#kube-router)
  - [external-dns](#external-dns)
- [Security](#security)
  - [audit2rbac](#audit2rbac)
- [Storage](#storage)
  - [external-storage](#external-storage)
  - [trident](#trident)
- [Application](#application)
  - [service-catalog](#service-catalog)
- [Developer](#developer)
  - [draft](#draft)
- [codegen](#codegen)
  - [metacontroller](#metacontroller)
- [Insight](#insight)
  - [k8s-prometheus-adaptor](#k8s-prometheus-adaptor)
  - [addon-resizer](#addon-resizer)
  - [cluster autoscaler](#cluster-autoscaler)
- [Node & Resource](#node--resource)
  - [kubegpu](#kubegpu)
  - [gpushare (aliyun)](#gpushare-aliyun)
  - [node problem detector](#node-problem-detector)
- [Scheduling](#scheduling)
  - [resorcerer](#resorcerer)
- [Virtualization](#virtualization)
  - [kubevirt](#kubevirt)
  - [virtlet](#virtlet)
- [Cluster](#cluster)
  - [kismatic](#kismatic)
  - [kargo](#kargo)
  - [kops](#kops)
  - [kargo vs. kops](#kargo-vs-kops)
  - [kaptaind](#kaptaind)
- [Templating](#templating)
  - [helm](#helm)
  - [ksonnet](#ksonnet)
  - [Templates](#templates)
- [Nodeless](#nodeless)
  - [virtual-kubelet](#virtual-kubelet)
- [TODOs](#todos)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Networking

## cni-genie

*Date: 08/19/2017*

[cni-genie](https://github.com/Huawei-PaaS/CNI-Genie) is a solution from huawei which enables:
- multiple cni plugins: user can choose which plugin to use when launching pod via annotation;
  typically, different network uses different cidr
- multiple IP addresses: user can request IP addresses from multiple cni
- select ideal network: cni-genie can help user choose a cni plugin to use based on information
  like per network load

Essentially, it is a proxy to underline cnis.

*References*

- [high level design](https://github.com/Huawei-PaaS/CNI-Genie/blob/8a35c2c0fe05ecfd967be6952a9d5154bf071655/docs/HLD.md)
- [feature set](https://github.com/Huawei-PaaS/CNI-Genie/blob/8a35c2c0fe05ecfd967be6952a9d5154bf071655/docs/CNIGenieFeatureSet.md)

## multus-cni

*Date: 06/02/2018, v0.2*

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

## service-loadbalancer

*Date: 05/13/2017, k8s 1.6*

[service loadbalancer](https://github.com/kubernetes/contrib/tree/master/service-loadbalancer) is
deprecated in favor of ingress controller. At its core, service loadbalancer watches the api for
services and endpoints, and reload haproxy's configuration (can be other loadbalancer as well, like
F5). However, unlike ingress, there is no API for controlling its behavior, and it lacks a lot of
features seen in ingress.

## ip-masq-agent

link: [ip-masq-agent](./ip-masq-agent)

## ingress

link: [ingress](./ingress)

## kube-router

link: [kube-router](./kube-router)

## external-dns

link: [external-dns](./external-dns)

# Security

## audit2rbac

*Date: 06/03/2018*

[audit2rbac](https://github.com/liggitt/audit2rbac) converts advanced audit log (audit.Event) to
rbac rules (rbac.Role, rbac.RoleBinding, etc)

# Storage

## external-storage

link: [external-storage](./external-storage)

## trident

link: [trident](./trident)

# Application

## service-catalog

link: [service-catalog](./service-catalog)

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
- [design doc](https://github.com/Azure/draft/blob/3fad7ef57ce9ed198649bef38023be3860792d24/docs/design.md)
- [installation](https://github.com/Azure/draft/blob/3fad7ef57ce9ed198649bef38023be3860792d24/docs/install.md)
- [getting started](https://github.com/Azure/draft/blob/3fad7ef57ce9ed198649bef38023be3860792d24/docs/getting-started.md)

# codegen

link: [codegen](./codegen)

## metacontroller

*Date: 06/01/2018*

[Metacontroller](https://github.com/GoogleCloudPlatform/metacontroller) is a controller for controller;
developyer only needs to write hooks for processing registered events (with CRDs), and metacontroller
handles the rest.

# Insight

## k8s-prometheus-adaptor

*Date: 01/14/2018*

The project is an implementation of Kubernetes custom metrics API, using the framework [here](https://github.com/kubernetes-incubator/custom-metrics-apiserver).
Basically, it registers itself as a third-party API service. Kubernetes core API server will proxy
request to it, i.e. client sends requst to endpoint `/apis/custom-metrics.metrics.k8s.io/v1beta1`
just like other standard requests; kubernetes API server then proxies the request to this adapter,
which translate the request to prometheus query language and return the metrics result.

*References*
- [deploy adaptor](https://github.com/DirectXMan12/k8s-prometheus-adapter/tree/master/deploy)

## addon-resizer

*Date: 08/06/2017, Kubernetes v1.7, no release*

addon-resizer is a container which watches another container in a deployment, and vertically scales
the dependent container up and down (only one container).  It is usually deployed as a sidecar or as
another deployment. addon-resizer is also called nanny, i.e. babysitter.

**workflow**

addon-resizer polls kubernetes every configurable (default 10s) interval to decide if scaling is
needed for its dependent container. At each bookkeeping, it retrieves number of nodes from kubernetes,
and uses the information, along with command line flags, to estimate a resource requirements. If the
resource requirement is different from current value, it scales the container.

## cluster autoscaler

*Date: 08/06/2017, Kubernetes v1.7, project status beta*

Cluster Autoscaler is a standalone program that adjusts the size of a Kubernetes cluster to meet the
current needs. It assumes kubernetes nodes are running undera cloud provider node group. Cluster
Autoscaler has extensive documentation, ref [here](https://github.com/kubernetes/autoscaler/tree/cluster-autoscaler-0.6.0/cluster-autoscaler).

# Node & Resource

## kubegpu

link: [kubegpu](./kubegpu)

## gpushare (aliyun)

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

## node problem detector

*Date: 10/18/2017, v0.4.1*

[Node problem detector](https://github.com/kubernetes/node-problem-detector) surfaces node level
problems to kubernetes control plane. It consists of a npd and multple problem daemons. The problem
daemons are running as goroutine right now, but will be expanded to side car in the future. Node
problem detector is simple, but its design is comprehensive, ref [here](https://docs.google.com/document/d/1cs1kqLziG-Ww145yN6vvlKguPbQQ0psrSBnEqpy0pzE/edit).

# Scheduling

## resorcerer

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

# Virtualization

## kubevirt

link: [kubevirt](./kubevirt)

## virtlet

*Date: 10/03/2018, v1.4.0*

virtlet is created from Mirantis.

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
- [architecture](https://github.com/Mirantis/virtlet/blob/v1.4.0/docs/architecture.md)
- [deployment](https://github.com/Mirantis/virtlet/blob/v1.4.0/deploy/real-cluster.md)

# Cluster

## kismatic

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

## kargo

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

Kops is the `kubectl` for clusters; common commands used in kops are:

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

## kargo vs. kops

- Kargo runs on bare metal and most clouds, using Ansible as its substrate for provisioning and orchestration.
- Kops performs the provisioning and orchestration itself, and as such is less flexible in deployment platforms.

For people with familiarity with Ansible, existing Ansible deployments or the desire to run a
Kubernetes cluster across multiple platforms, Kargo is a good choice. Kops, however, is more tightly
integrated with the unique features of the clouds it supports so it could be a better choice if you
know that you will only be using one platform for the foreseeable future.

## kaptaind

*Date: 09/14/2017*

[kaptaind](https://github.com/kaptaind/kaptaind) is a simple tool to backup & restore kubernetes
cluster snapshots. A broker component is running as api server, accepting export & import (i.e.
backup & restore) tasks. An agent is typically running in kubernetes cluster and asks for import
task. The export & import process is copy/past yaml files.

# Templating

## helm

Helm is a tool for managing Kubernetes charts. Charts are packages of pre-configured Kubernetes
resources.

**Local Development**

- switch to helm repository and `make bootstrap` to install tools and vendors
- run `make build` to build binary
- run `./bin/tilter` to run a local tilter server which will talk to kubernetes cluster defined in ~/.kube/config
- run `export HELM_HOST=localhost:44134` to tell helm client to talk to this local tilter server
- use `./bin/helm` to start helm client

To test without actually installing chart, use `--dry-run` flag.

## ksonnet

*Date: 02/22/2018, v0.8.0*

Ksonnet has relatively good documentation, read following docs in order:
- https://ksonnet.io/docs/tutorial
- https://ksonnet.io/docs/concepts
- https://ksonnet.io/tour/welcome

*Reference*

- https://stackoverflow.com/questions/48867912/draft-vs-helm-vs-ksonnet-complementing-or-replacing

## Templates

A list of template projects

- https://blog.openshift.com/kubernetes-state-app-templating/

# Nodeless

## virtual-kubelet

*Date: 10/03/2018, 0.6.0*

virtual-kubelet is created from Microsoft.

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
started, has nothing to do with virtual kubelet.

It's possible to create a multiple Pods, e.g. using Deployment, and assign them to virtual kubelet.
virtual kubelet will create equal number of containers in cloud providers.

*References*
- [how it works](https://github.com/virtual-kubelet/virtual-kubelet/tree/v0.6.2#how-it-works)
- [azure aci provider](https://github.com/virtual-kubelet/virtual-kubelet/blob/v0.6.2/providers/azure/README.md)
- [aws blog](https://aws.amazon.com/blogs/opensource/aws-fargate-virtual-kubelet/)

# TODOs

- k8s-AppController (TODO: basic, P2)
  https://github.com/Mirantis/k8s-AppController/
- kube-lego (TODO: basic, P1)
  https://github.com/jetstack/kube-lego
- smith (TODO: basic, P1)
  https://github.com/atlassian/smith
- kuberesolver (TODO: basic, P1)
  https://github.com/sercand/kuberesolver
- rktlet (TODO: basic, P2)
  Bridge kubelet cri and rkt.
- kubegen (TODO: basic, P2)
  https://github.com/errordeveloper/kubegen
- brigade (TODO: basic, P2)

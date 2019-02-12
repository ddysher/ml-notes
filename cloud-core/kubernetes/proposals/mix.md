<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Feature & Design](#feature--design)
  - [cli: kubectl diff](#cli-kubectl-diff)
  - [cli: kubectl move to stage](#cli-kubectl-move-to-stage)
  - [cloud: support out-of-process and out-of-tree cloud providers](#cloud-support-out-of-process-and-out-of-tree-cloud-providers)
- [Kubernetes Releases](#kubernetes-releases)
  - [v1.18, 03/25/2020](#v118-03252020)
  - [v1.17, 12/09/2019](#v117-12092019)
  - [v1.16, 09/18/2019](#v116-09182019)
  - [v1.15, 06/19/2019](#v115-06192019)
  - [v1.14, 03/25/2019](#v114-03252019)
  - [v1.13, 12/08/2018](#v113-12082018)
  - [v1.12, 09/27/2018](#v112-09272018)
  - [v1.11, 06/27/2018](#v111-06272018)
  - [v1.10, 03/27/2018](#v110-03272018)
  - [v1.9, 12/15/2017](#v19-12152017)
  - [v1.8, 09/29/2017](#v18-09292017)
  - [v1.7, 06/30/2017](#v17-06302017)
  - [v1.6, 03/28/2017](#v16-03282017)
  - [v1.5, 12/13/2016](#v15-12132016)
  - [v1.4, 09/26/2016](#v14-09262016)
  - [References](#references)
- [Resources](#resources)
  - [sigs & ugs & wgs](#sigs--ugs--wgs)
  - [links & archives](#links--archives)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

> A collection of proposals, designs, features in various Kubernetes aspects.

# Feature & Design

## cli: kubectl diff

- *Date: 03/30/2020, v1.18, stable*

`kubectl diff` is a GA feature that enables diffing changes in Kubernetes objects, the diff works
by comparing the "live configuration in the current cluster state" vs. "future configuration if we
applied the yaml file". The "future configuration" is retrieved via applying request that is sent
with the `dryRun` flag.

*References*

- [kubectl diff KEP link](https://github.com/kubernetes/enhancements/blob/89c4310e3934fad5a1e339855b7c92c553fae597/keps/sig-cli/20200115-kubectl-diff.md)

## cli: kubectl move to stage

- *Date: 03/30/2020, v1.18, stable*

The kubectl code base locates in kubernetes/kubernetes repository, which posses some challenges.
The motivation to move kubectl to stage is:
- enable moving kubectl package to a dedicated repository kubernetes/kubectl
- remove tight coupling between kubectl and internal kubernetes code base
- external client depending on kubectl code doesn't have to depend on kubernetes repository as a whole

*References*

- [kubectl staging KEP link](https://github.com/kubernetes/enhancements/blob/000b16193b2e9833cd21884e58aaa05a03f11ef6/keps/sig-cli/kubectl-staging.md)

## cloud: support out-of-process and out-of-tree cloud providers

- *Date: 03/09/2018, v1.10, alpha*
- *Date: 06/16/2019, v1.14, beta*

As Kubernetes gains acceptance, more and more cloud providers will want to make it available. To do
that more easily, the community is working on extracting provider-specific binaries so that they can
be more easily replaced.

*References*

- [cloud refactoring design doc](https://github.com/kubernetes/community/blob/b5c1e2c14ef3c6384b52e3de908131e687029072/contributors/design-proposals/cloud-provider/cloud-provider-refactoring.md)
- [running cloud controller](https://github.com/kubernetes/website/blob/snapshot-initial-v1.9/docs/tasks/administer-cluster/running-cloud-controller.md)
- [developing cloud controller manager](https://github.com/kubernetes/website/blob/snapshot-initial-v1.9/docs/tasks/administer-cluster/developing-cloud-controller-manager.md)
- [keepalived cloud provider](https://github.com/munnerz/keepalived-cloud-provider/tree/0.0.1)

# Kubernetes Releases

## v1.18, 03/25/2020

Kuberentes release v1.18 contains equal number of graduated features and new features.

Major Themes:
- SIG-Node: Topology Manager moves to beta, which enables NUMA alignment of CPU and devices.
- SIG-API-Machinery: Serverside Apply to beta, which records changes to API objects.
- SIG-Network: A new type `IngressClass` is added, similar to `StorageClass`.
- SIG-CLI: Added a new `kubectl alpha debug` command, which uses Ephemeral Container to debug a running Pod.
- SIG-Windows: Windows CSI support introduces alpha

Graduated to Stable:
- Taint Based Eviction: Taints nodes with `NoExecute` when they become unready or unreachable.
- `kubectl diff`: Users can run a kubectl command to view the difference between a locally declared object configuration and the current state of a live object.
- CSI Block storage support: Use `volumeMode` to claim a raw block via Persistent Volume.
- API Server dry run: Add apiserver `dry-run` query-parameter so that requests can be validated and "processed" without actually being persisted.
- Pass Pod information in CSI calls
- Support Out-of-Tree vSphere Cloud Provider
- Support GMSA for Windows workloads
- Skip attach for non-attachable CSI volumes
- PVC cloning: Enable specifying an existing PVC as a DataSource parameter for creating a new PVC (Cloning)
- Moving kubectl package code to staging
- RunAsUserName for Windows
- AppProtocol for Services and Endpoints: Add `AppProtocol` field to ServicePort and EndpointPort
- Extending Hugepage Feature: Multi-size & container isolation
- client-go signature refactor to standardize options and context handling
- Node-local DNS cache: run a per-node DNS cache with upstream set to kube-dns

Major Changes
- EndpointSlice API (Beta)
- Moving kubectl package code to staging
- CertificateSigningRequest API
- Extending Hugepage Feature: Different sized hugepage & container isolation
- client-go signature refactor to standardize options and context handling

## v1.17, 12/09/2019

Kubernetes release v1.17 is a stability release, with many features graduated to stable and beta,
and introduces only a few new features.

Major Themes:
- SIG-Cloud-Provider: Cloud Provider labels reach general availability (stable)
- SIG-Storage: Volume snapshot moves to beta, which allows snapshot PV and restore from previous status.
- SIG-Storage: CSI Migration Beta

Graduated to Stable:
- Taint Node by Condition
- Configurable Pod Process Namespace Sharing: configure containers within a pod to share a common PID namespace
- Schedule DaemonSet Pods by kube-scheduler
- Dynamic Maximum Volume Count: maximum number of volume to mount per node
- Kubernetes CSI Topology Support: topology aware scheduling of volumes
- Provide Environment Variables Expansion in SubPath Mount
- Defaulting of Custom Resources
- Move Frequent Kubelet Heartbeats To Lease API
- Break Apart The Kubernetes Test Tarball
- Add Watch Bookmarks Support
- Behavior-Driven Conformance Testing
- Finalizer Protection For Service Loadbalancers
- Avoid Serializing The Same Object Independently For Every Watcher

Major Changes
- Add IPv4/IPv6 Dual Stack Support (Alpha)

Other Notable Features
- Topology Aware Routing of Services (Alpha)
- RunAsUserName for Windows

## v1.16, 09/18/2019

Kuberentes release v1.16 contains equal number of graduated features and new features.

Major Themes:
- SIG-API-Machinery: Custom Resources reach General Availability
- SIG-Instrumentation: Overhauled metrics
- SIG-Storage: Volume Extension, e.g. volume resizing, CSI changes, to beta

Major Changes:
- Windows Enhancements: GMSA (beta), kubeadm support (alpha), CSI support (alpha)
- EndpointSlices (Alpha): Greater scalability and extensibility
- Kubernetes API Changes: Deprecation of older APIs, e.g. extensions/v1beta1/xxx

## v1.15, 06/19/2019

Kubernetes release v1.15 focuses on Extensibility and Continuous Improvement.

Major Themes:
- Extensibility around core Kubernetes APIs
  - CustomResourceDefinition Webhook Conversion (beta): ability to convert between multiple CRD versions
  - CustomResourceDefinition OpenAPI Publishing (beta): publish CRD schema for client discovery
  - CustomResourceDefinition Pruning (beta): automatic removal of unknown fields in objects sent to a Kubernetes API
  - CustomResourceDefinition Defaulting (alpha): Defaults are set for unspecified field in an object sent to/read from API
  - Admission Webhook Reinvocation & Improvements (beta): reinvocation of admission webhook
- Cluster Lifecycle Stability and Usability Improvements
  - kubeadm HA setup to beta
  - kubeadm certificate management
- Continued improvement of CSI
  - Migration of in-tree volume plugins
  - Volume cloning (alpha)

Additional Notable Feature Updates:
- Support for go modules in Kubernetes Core
- Continued preparation on cloud provider extraction and code organization
- Kubectl get and describe now work with extensions
- Nodes now support third party monitoring plugins, aka, compute device assignment
- A new Scheduling Framework for schedule plugins is now Alpha
- ExecutionHook API designed to trigger hook commands in the containers for different use cases is now Alpha.
- Continued deprecation of extensions/v1beta1, apps/v1beta1, and apps/v1beta2 APIs

## v1.14, 03/25/2019

Kubernetes release v1.14 focuses on Extensibility and Supporting more workloads.

Major Themes:
- Production-level Support for Windows Nodes (GA)
  - Windows Server 2019 Node
  - Windows Networking
  - Many others
- Kubectl Changes
  - kustomize integration with `kubectl -k`: standard-alone kustomize binary is also available and added to kubectl when releasing kubernetes
  - new kubectl docs and logo
  - kubectl plugins become simpler and moved to stable
- Persistent Local Volumes are Now GA
- PID Limiting is Moving to Beta

Additional Notable Feature Updates
- Pod priority and preemption
- Pod Readiness Gates
- Harden the default RBAC discovery clusterrolebindings

## v1.13, 12/08/2018

Kubernetes 1.13 has been one of the shortest releases to date at 10 weeks. This release continues
to focus on stability and extensibility of Kubernetes.

Major Themes:
- Simplified Kubernetes Cluster Management with kubeadm in GA: bootstrapping, upgrade, pluggability and configurability
- Container Storage Interface (CSI) Goes GA: extensibility
- CoreDNS is Now the Default DNS Server for Kubernetes: extensibility, simplicity

Additional Notable Feature Updates:
- Support for 3rd party device monitoring plugins (alpha), aka, compute device assignment.
- Kubelet Device Plugin Registration (stable), aka, plugin watcher
- Topology Aware Volume Scheduling (stable)
- APIServer DryRun (beta): apply action moves from kubectl to apiserver
- `kubectl diff` (beta)
- Raw block device using persistent volume source (beta)

## v1.12, 09/27/2018

Kubernetes 1.12 continues to focus on internal improvements and graduating features to stable.

Major Themes:
- General Availability of Kubelet TLS Bootstrap
- Support for Azure Virtual Machine Scale Sets (VMSS) and Cluster-Autoscaler is Now Stable

Additional Notable Feature Updates:
- RuntimeClass for running multiple runtimes in a cluster (alpha)
- Snapshot/Restore functionality for Kubernetes and CSI (alpha)
- Topology aware dynamic provisioning (beta)
- Configurable pod process namespace sharing (beta)
- Taint node by condition (beta)
- Arbitrary/Custom Metrics in the Horizontal Pod Autoscaler (beta)
- Horizontal Pod Autoscaler to reach proper size faster (beta)
- Vertical Scaling of Pods (beta)
- Encryption at rest via KMS (beta): KMS includes Google Cloud KMS, Azure Key Vault, AWS DMS and Hashicorp Vault
- Kubelet server certificate bootstrap and rotation (beta)

## v1.11, 06/27/2018

Kubernetes 1.11 continues to advance maturity, scalability, and flexibility of Kubernetes.

Major Themes:
- IPVS-based in-cluster service load balancing graduates to stable
- CoreDNS for cluster DNS is promoted to stable
- Dynamic Kubelet configuration moves to beta: configure Kubelet using structured format via configmap (instead of flag)
- Custom resource definitions supporting multiple versions moves to beta
- Enhancement to CSI: raw block in CSI, new registration mechanism, etc

New Storage Features:
- Online resizing of Persistent Volumes (alpha)
- Dynamic maximum volume count (alpha)
- Storage object in use protection (stable)

## v1.10, 03/27/2018

Kubernetes v1.10 continues to advance maturity, extensibility, and pluggability of Kubernetes.

Major Themes:
- Storage - CSI and Local Storage move to beta, as well as storage object in use protection (beta)
- Security - External credential providers to alpha
- Networking - CoreDNS as a DNS provider to beta

## v1.9, 12/15/2017

Kubernetes v1.9 continues the evolution of an increasingly rich feature set, more robust stability,
and even greater community contributions.

Major Themes:
- Workloads API GA: aka, apps/v1 Workloads API
- Windows Support (beta): support Windows server
- Storage Enhancements with CSI (alpha)

Additional Notable Feature Updates:
- Custom Resource Definition Validation (beta)
- Hardware accelerator moves to alpha
- CoreDNS for cluster DNS (alpha)
- IPVS mode for kube-proxy (beta)

## v1.8, 09/29/2017

Kubernetes v1.8 represents a snapshot of many exciting enhancements and refinements underway.

Security:
- Graduates support for role based access control (RBAC) to stable
- Graduates support for Network Policy outbound traffic to beta
- Transport Layer Security (TLS) certificate rotation for the Kubelet graduates to beta

Workload:
- Promotes the core Workload APIs to beta
- Batch API CronJobs to beta
- Custom Resource Definitions remain in beta, with many extension features in progress

Notable New Features:
- Volume snapshots
- PV resizing
- Automatic taints
- Priority pods
- `kubectl` plugins

## v1.7, 06/30/2017

Kubernetes 1.7 is a milestone release that adds security, storage and extensibility features.

Security:
- Encrypted secrets (alpha)
- Network policy for pod-to-pod communication (stable)
- Node authorizer to limit kubelet access (alpha)
- Kubelet client/server TLS certificate rotation
- More customizable and extensible audit logs

Stateful Workloads:
- Automated updates to StatefulSets and enhances updates for DaemonSets
- Burst mode for scaling StatefulSets faster
- Local Storage (alpha)

Extensibility:
- API aggregation
- CRI enhancement

Additional Features:
- External admission controllers (alpha)
- Policy-based Federated Resource Placement (alpha)

## v1.6, 03/28/2017

Kubernetes 1.6 focuses on scale and automation, to help you deploy multiple workloads to multiple
users on a cluster.

Scale and Federation:
- Supports 5,000 node (150,000 pod) clusters
- `kubefed` command line utility graduated to beta

Security and Setup:
- RBAC graduates to beta: RBAC allows cluster administrators to selectively grant particular users
  or service accounts fine-grained access to specific resources on a per-namespace basis.
- kubeadm is now beta, with base features include RBAC setup, Bootstrap Token system and Certificates API.

Advanced Scheduling:
- Node affinity/anti-affinity (beta)
- Taints and tolerations (beta)
- Pod affinity and anti-affinity (beta)
- Multiple schedulers (beta)

Dynamic Storage Provisioning:
- StorageClass and dynamic volume provisioning are promoted to stable
- Addition of many volume plugins

Additional Features:
- Docker-CRI (beta)
- etcd v3
- Node Allocatable
- Out-of-tree cloud provider (alpha)
- Per-pod-eviction (alpha)
- Pod Injection Policy, aka, PodPreset (alpha)
- Custom metrics for HPA (alpha)
- Nvidia GPU support (alpha)

## v1.5, 12/13/2016

Kubernetes 1.5 release focuses on supporting production workloads.

Workload (stateful workload):
- StatefulSet (previously PetSet) moves to beta: no longer force deletes pods on unresponsible nodes
- PodDisruptionBudget moves to beta: `kubectl drain` will respect the budget policy

Cluster:
- Kubefed (alpha): introduces a new federation command (v1)
- HA Master (alpha)

Node:
- Windows server containers (alpha): support for Windows Server 2016 nodes
- Container Runtime Interface, aka, CRI (alpha)
- Node conformance test: a node passes conformance test is qualified to join a Kubernetes

## v1.4, 09/26/2016

Kubernetes 1.5 release makes Kubernetes easy to install, as well as easier to build, deploy and
manage distributed applications.

Cluster:
- kubeadm (alpha)
- certficate API for kubelet TLS bootstrap and a new discovery API (alpha)

Workload (stateful workload):
- ScheduledJob, aka, CronJob (alpha)
- Dynamic PVC Provisioning (beta)
- Curated helm charts

Cluster federation (v1):
- Federated ReplicaSets (beta)
- Federated Service (beta)
- Federated Ingress (alpha)

Container security support:
- Pod Security Policy (alpha)
- AppArmor (beta), configured via annotations

Infrastructure enhancements
- Pod Affinity/Anti-Affinity (alpha)
- Guaranteed Scheduling For Critical Add-On Pods
- PodDisruptionBudget (alpha)

## References

- https://kubernetes.io/blog/2020/03/25/kubernetes-1-18-release-announcement/
- https://kubernetes.io/blog/2019/12/09/kubernetes-1-17-release-announcement/
- https://kubernetes.io/blog/2019/09/18/kubernetes-1-16-release-announcement/
- https://kubernetes.io/blog/2019/06/19/kubernetes-1-15-release-announcement/
- https://kubernetes.io/blog/2019/03/25/kubernetes-1-14-release-announcement/
- https://kubernetes.io/blog/2018/12/03/kubernetes-1-13-release-announcement/
- [https://kubernetes.io/blog/2018/09/27/kubernetes-1.12-kubelet-tls-bootstrap-and-azure-...](https://kubernetes.io/blog/2018/09/27/kubernetes-1.12-kubelet-tls-bootstrap-and-azure-virtual-machine-scale-sets-vmss-move-to-general-availability/)
- https://kubernetes.io/blog/2018/06/27/kubernetes-1.11-release-announcement/
- https://kubernetes.io/blog/2018/03/26/kubernetes-1.10-stabilizing-storage-security-networking/
- https://kubernetes.io/blog/2017/12/kubernetes-19-workloads-expanded-ecosystem/
- https://kubernetes.io/blog/2017/09/kubernetes-18-security-workloads-and/
- https://kubernetes.io/blog/2017/06/kubernetes-1-7-security-hardening-stateful-application-extensibility-updates/
- https://kubernetes.io/blog/2017/03/kubernetes-1-6-multi-user-multi-workloads-at-scale/
- https://kubernetes.io/blog/2016/12/kubernetes-1-5-supporting-production-workloads/
- https://kubernetes.io/blog/2016/09/kubernetes-1-4-making-it-easy-to-run-on-kuberentes-anywhere/
- https://kubernetes.io/blog/2016/07/kubernetes-1-3-bridging-cloud-native-and-enterprise-workloads/
- http://blog.kubernetes.io/2018/03/first-beta-version-of-kubernetes-1-10.html

# Resources

## sigs & ugs & wgs

- sig-api-machinery
- sig-apps
- sig-architecture
- sig-auth
- sig-autoscaling
- ~sig-big-data~
- ~sig-cluster-ops~
- sig-cli
- sig-cloud-provider
- sig-cluster-lifecycle
- sig-contributor-experience
- sig-docs
- ~sig-openstack~
- sig-instrumentation
- sig-multicluster
- sig-network
- sig-node
- sig-pm
- sig-release
- sig-scalability
- sig-scheduling
- sig-service-catalog
- sig-storage
- sig-testing
- sig-ui
- sig-usability
- sig-windows
- ug-big-data
- ug-vmware-users
- ~wg-app-def~
- wg-apply
- ~wg-cluster-api~
- wg-component-standard
- ~wg-container-identity~
- wg-data-protection
- ~wg-kubeadm-adoption~
- wg-iot-edge
- wg-k8s-infra
- wg-lts
- wg-machine-learning
- wg-multitenancy
- wg-policy
- wg-resource-management
- wg-security-audit

## links & archives

A collection of Kubernetes resources:

- [Community](https://github.com/kubernetes/community)
- [Enhancements](https://github.com/kubernetes/enhancements)
- [LWKD (Last Week in Kubernetes Development)](http://lwkd.info/)
- [TGIK](https://github.com/heptio/tgik)
- [CNCF TOC](https://github.com/cncf/toc)
- https://github.com/jamiehannaford/what-happens-when-k8s

**Archives**

<details><summary>analysis of guestbook example</summary><p>

*Date: 09/01/2014, Running on GCE*

```
** Step Zero: Start kubernetes cluster on GCE.
   Just do hack/deb-build-and-up.sh, the script will create a master and 3 minions, with
   appropriate setup. In my case, it is:
   +---------------------+---------------+---------+----------------+----------------+
   | name                | zone          | status  | network-ip     | external-ip    |
   +---------------------+---------------+---------+----------------+----------------+
   | kubernetes-master   | us-central1-b | RUNNING | 10.240.75.164  | 146.148.53.128 |
   +---------------------+---------------+---------+----------------+----------------+
   | kubernetes-minion-1 | us-central1-b | RUNNING | 10.240.100.164 | 146.148.44.108 |
   +---------------------+---------------+---------+----------------+----------------+
   | kubernetes-minion-2 | us-central1-b | RUNNING | 10.240.125.81  | 146.148.39.143 |
   +---------------------+---------------+---------+----------------+----------------+
   | kubernetes-minion-3 | us-central1-b | RUNNING | 10.240.37.195  | 146.148.55.3   |
   +---------------------+---------------+---------+----------------+----------------+
   | kubernetes-minion-4 | us-central1-b | RUNNING | 10.240.57.41   | 146.148.37.231 |
   +---------------------+---------------+---------+----------------+----------------+
   There are different programs running on each machines:
   *master*
   + /usr/local/bin/apiserver
     # The address to listen to, normally, it's 127.0.0.1. Also, port is default to 8080.
     -address 127.0.0.1
     # The set of machines (minions) of the cluster
     -machines kubernetes-minion-3.c.solid-setup-685.internal,kubernetes-minion-4.c.solid-setup-685.internal,kubernetes-minion-1.c.solid-setup-685.internal,kubernetes-minion-2.c.solid-setup-685.internal
     # The etcd cluster, note kubernetes currently only let etcd running on master.
     # In theory, etcd cluster is independent of kubernetes cluster.
     -etcd_servers=http://10.240.75.164:4001
     # If non empty, and -cloud_provider is specified, a regular expression for matching
     # minion VMs (There can be VMs that are not running but not part of k8s cluster).
     -minion_regexp 'kubernetes-minion.*'
     # The cloud provider used.
     -cloud_provider=gce
     # The following two flags are not specified, but default value in k8s (apiserver.go).
     # "port=8080" is where k8s apiserver listen to incoming request, for example, list pods.
     # "minion_port=10250" is where kubelet of each minion listens to. Each k8s minion has
     # an instance of kubelet running, apiserver talk to these kubelet using port 10250.
     -port 8080
     -minion_port 10250
   + /usr/local/bin/etcd -peer-addr kubernetes-master:7001 -name kubernetes-master
   + /usr/local/bin/controller-manager -master=127.0.0.1:8080
   + /usr/local/bin/scheduler --master=127.0.0.1:8080 -master=127.0.0.1:8080

   *minions*
   + /usr/local/bin/kubelet
     # The etcd_servers flag points to master's etcd.
     -etcd_servers=http://10.240.75.164:4001
     # Listen to all interfaces of the minion.
     -address=0.0.0.0
     -config=/etc/kubernetes/manifests
     # Not specified, but default in k8s.
     -port=10250
   + /usr/local/bin/kube-proxy -etcd_servers=http://10.240.75.164:4001
   + /usr/bin/cadvisor -log_dir /
   + Docker container running cadvisor
   + Docker container running kubernetes/pause

** Step One: Turn up the redis master
   Use the redis-master.json configuration file to create a pod, the file describes
   a single pod running a redis key-value server in a container.

   $ cluster/kubecfg.sh -c example/guestbook/redis-master.json create pods
   Name                Image(s)            Host                                              Labels
   ----------          ----------          ----------                                        ----------
   redis-master-2      dockerfile/redis    kubernetes-minion-1.c.solid-setup-685.internal/   name=redis-master

   *Details on how pods are created:*
     - 1. kubecfg.sh accepts command line.
         As in the command line, the request is first go to the shell script cluster/kubecfg.sh.
         The script makes sure KUBERNETES_MASTER is properly set, then simply call
         kubecfg binary, which is generated from cmd/kubecfg.go.  So, instead of:
         $ cluster/kubecfg.sh list pods
         We can also use:
         $ kubecfg -h https://146.148.53.128 list pods

     - 2. kubecfg.go sends request.
         cmd/kubecfg.go first validates flags, urls, then create a k8s client, which is
         implemented under pkg/client. k8s client contains client side communication
         with the k8s master. For example, query k8s version using http://MASTERIP/version,
         list all k8s pods using http://MASTERIP/api/v1beta1/pods, create k8s pod using
         POST http://MASTERIP/api/v1beta1/pods/, etc.

         After validation, cmd/kubecfg.go starts sending request using either of the two
         methods: executeAPIRequest() || executeControllerRequest().  (Because there is
         REST API command interface and ReplicationController command interface). The
         ReplicationController is actually an abstraction above service, so ignore for
         now.

         The executeAPIRequest method dispatch request according to command line arg,
         i.e. get|list|create|delete|update. In this step, we mainly focus on create
         request. Note for now, k8s has the same code path for all storages, i.e.
         minions|pods|replicationControllers|services. They are named "obj", and have
         the dynamic type "interface{}".

         executeAPIRequest constructs request url using r = using s.Verb().Path().XXX,
         then constructs body using r.Body(readConfig(storage)), (storage = "pods").
         At last, send request using result := r.Do().

     - 3. apiserver.go gets request.
         cmd/apiserver.go first validates flags, then get cloud provider. (For GCE, cloud
         provider is registered at init() method of cloud provider package, see
         pkg/cloudprovider/gce/gce.go). The "cloud" object in apiserver.go is the type
         of pkg.cloudprovider.gce.GCECloud, which implements pkg.cloudprovider.Interface.

         The apiserver.go creates instance of HTTPPodInfoGetter.  HTTPPodInfoGetter is
         defined in pkg/client/podinfo.go (which is a little bit weired because client
         pkg is documented as communication between k8s master, but here, it is also used
         to communicate with k8s kubelet). HTTPPodInfoGetter implements PodInfoGetter,
         to access the kubelet over HTTP.

         Then apiserver.go creates a master object using master.New(), note that master
         object is also initialized in the New() method. (What is the client used in
         master object?).  The handler of apiserver is created using apiserver.Handle(),
         it is this method that creates http.mux, and installs REST routes, as well as
         some other supports like /logs, /version.  At last, apiserver starts serving
         request.

         Note that apiserver.Handle() returns default APIServer, and the handler is
         wrapped by RecoverPanics(). The actual server is the "mux", which we register
         different routes to it (pkg/apiserver/apiserver.go#InstallREST #InstallSupport).

         In this step, our request in step 2 is finally routed to pkg/apiserver/resthandler.go,
         the ServeHTTP() method. The request url is "POST /api/v1beta1/pods?labels=".
         ServeHTTP() calls handlerRESTStorage(), which dispatch according to REST method.
         In this case, the "POST" branch.

         In this branch, readBody first read out the content in request, which is json
         string, and create a new storage object using storage.New (here, the object is
         pkg/api/types.go#Pod). With this object, apiserver.go calls storage.Create(obj);
         since it's pod, the call goes to pkg/registry/pod/registry.go#Create. Note that
         New() creates an empty Pod struct, Create() creates the actual Pod.

         Inside storage.Create(), we see that pod.ID is assigned to the value from the
         redis-master.json file, which is "redis-master-2".  Then, Create returns two
         things: first, a channel returned from MakeAsync, second, a nil error message.
         api.MakeAsync returns a channel to caller immediately, and caller can use this
         channel to get result from the function passed in (the function passed in will
         return an object with interface{} type, MakeAsync return the object through
         channel). Therefore, rs.registry.CreatePod() is excuted asynchronously. So,
         back to resthandler.go, for this operations "out, err := storage.Create(obj)",
         "out" is a channel that will return the created Pod object.

         In the async function, rs.registry.CreatePod() goes to pkg/registry/etcd/etcd.go,
         where a new key is inserted into etcd, and then using rs.registry.GetPod(pod.ID)
         to get the pod (The new key is "/registry/pods/redis-master-2").

         There are other two methods after the async method:
           op := h.createOperation(out, sync, timeout)
           h.finishReq(op, w)
         By default, sync is false and timeout takes no effect.  h.CreateOperation creates
         a new operation. Note h.asyncOpWait=time.Millisecond*25 and h.ops come from
         pkg/apiserver/apiserver.go#NewAPIGroup. Operations is a pool of Operation with
         some lock management. NewOperation insert new operation into operations pool, and
         wait for the operation to finish (In this case, the "out" channel); it waits
         forever, and set finished=true to signal apiserver. Operations use util.Forever()
         to garbage collect all finished operations (created in operation.go#NewOperations).
         h.finishReq(op, w) check operation status, and write back result.

     - 4. scheduler.go schedule pods
         At this moment, Pod is set to etcd, but not scheduled (we can use list pods to
         see it, but docker hasn't run it yet). plugin/cmd/scheduler.go first creates a
         client to connect to k8s master (configFactory), and use configFactory.Create()
         to create a scheduler and all support functions (config). Then use this config,
         create a scheduler using "scheduler.New(config)", and run it.

         The Run() will execute pkg/scheduler.go#scheduleOne forever. It call NextPod()
         to get next pod to schedule, then use config.Algorithm to get next available
         minion (as host string). Then, it creates a binding object, api.Binding. Binding
         is written by a scheduler to cause a pod to be bound to a host. Then, the
         s.config.Binder.Bind(b) goes into Bind() in scheduler/factory/factory.go.
         b.Post().Path("binding").Body(binding) POST to url /api/v1beta1/bindings.

     - 5. apiserver.go gets request again
         Now, the request POST to apiserver again, but this time it is binding object.
         The same thing goes on as step 3 (The Create() method in binding/storage.go is
         called). The function in MakeAsync() calls ApplyBinding(binding) to do the
         binding, which goes into registry/etcd/etcd.go.  ApplyBinding simply call the
         assignPod() method with PodID and Host. assignPod() will update etcd keys for
         the pod (most importantly, the host entry in manifest).

     - 6. kubelet.go create containers
         Kubelet will reach out and do a watch on an etcd server. The etcd path that is
         watched is /registry/hosts/$(hostname -f); it will also act on file, HTTP
         endpoint, and HTTP server.

         Kubelet first creates docker and cadvisor client to interact & inspect containers.
         It then creates a *PodConfig* struct. This is an important struct in kubelet, it
         contains a map of (source -> pod name -> pod object). Here, source includes file,
         HTTP endpoint, HTTP server, and etcd server ('source' means where does k8s get
         the definition of the pod). With this PodConfig struct, kubelet creates File, URL,
         Etcd client if available (creates HTTP server at last). Each source will run
         forever in a goroutine, and send pod events via 'updates' channel. *Note* here,
         the 'updates' channel is per source, which is different from what the kubelet is
         waiting on. The per source 'updates' channel is created and listened by Mux, see
         Mux in pkg/util/config/config.go. Mux collects all these 'updates' channel and
         send to the updates 'channel' listened by kubelet.

         Kubelet then run this function forever (also in a goroutine):
           func() { k.Run(cfg.Updates()) }
         cfg.Updates() returns a channel of type PodUpdate (the channel is actually
         created at pkg/kubelet/config/config.go#NewPodConfig()). Run() method takes the
         channel, and start syncloop using the channel.

         syncLoop is the main loop for processing changes, see its comment for details.
         Inside syncLoop, it waits on "updates" event, and loops forever. The syncLoop
         handlers create/update pods immediately after updates channel sends data.

         The update channel is created at cmd/kubelet.go:
           cfg := kconfig.NewPodConfig(kconfig.PodConfigNotificationSnapshotAndUpdates)
         Shortly after its creation, cmd/kubelet.go checks for config (file source),
         manifestURL (HTTP endpoint source) and etcd (etcd source). Each of which will
         send Pod updates to it's own "update" channel, and merged to this 'updates',
         as stated above. Here, we use etcd source, which is located at
         pkg/kubelet/config/etcd.go#NewSourceEtcd().  It has a gorountines to monitor
         etcd keys, and send Pod information to "updates" channel whenever it detects
         changes (The key is constructed at EtcdKeyForHost, for example,
         "/registry/hosts/kubernetes-minion-3.c.solid-setup-685.internal/kubelet").
         The etcd key, as indicated at step 5, is created via apiserver (e.g. see the
         makeContainerKey() method defined in pkg/registry/etcd/etcd.go, called from
         ApplyBinding).

         With the above procedures, kubelet notices a new Pod is assigned to this
         machine, it calls "func (kl *Kubelet) SyncPods(pods []Pod) error" to actually
         create the Pod and Containers using docker client. Note in SyncPod will create
         network container (kubernetes/pause). This container has network setting, all
         containers in this Pod share the same network setting with this net container.

     - 7. etcd contents for now.
     {
       "action": "get",
       "node": {
         "dir": true,
         "key": "/",
         "nodes": [
           {
             "createdIndex": 3,
             "dir": true,
             "key": "/registry",
             "modifiedIndex": 3,
             "nodes": [
               {
                 "createdIndex": 5,
                 "dir": true,
                 "key": "/registry/hosts",
                 "modifiedIndex": 5,
                 "nodes": [
                   {
                     "createdIndex": 5,
                     "dir": true,
                     "key": "/registry/hosts/kubernetes-minion-1.c.solid-setup-685.internal",
                     "modifiedIndex": 5,
                     "nodes": [
                       {
                         "createdIndex": 5,
                         "key": "/registry/hosts/kubernetes-minion-1.c.solid-setup-685.internal/kubelet",
                         "modifiedIndex": 5,
                         "value": "{\"kind\":\"ContainerManifestList\",\"creationTimestamp\":null,\"apiVersion\":\"v1beta1\",\"items\":[{\"version\":\"v1beta1\",\"id\":\"redis-master-2\",\"volumes\":null,\"containers\":[{\"name\":\"master\",\"image\":\"dockerfile/redis\",\"ports\":[{\"hostPort\":6379,\"containerPort\":6379,\"protocol\":\"TCP\"}],\"env\":[{\"name\":\"SERVICE_HOST\",\"key\":\"SERVICE_HOST\",\"value\":\"kubernetes-minion-1.c.solid-setup-685.internal\"}]}]}]}"
                       }
                     ]
                   }
                 ]
               },
               {
                 "createdIndex": 3,
                 "dir": true,
                 "key": "/registry/pods",
                 "modifiedIndex": 3,
                 "nodes": [
                   {
                     "createdIndex": 3,
                     "key": "/registry/pods/redis-master-2",
                     "modifiedIndex": 3,
                     "value": "{\"kind\":\"Pod\",\"id\":\"redis-master-2\",\"creationTimestamp\":\"2014-08-31T17:23:41Z\",\"resourceVersion\":3,\"apiVersion\":\"v1beta1\",\"labels\":{\"name\":\"redis-master\"},\"desiredState\":{\"manifest\":{\"version\":\"v1beta1\",\"id\":\"redis-master-2\",\"volumes\":null,\"containers\":[{\"name\":\"master\",\"image\":\"dockerfile/redis\",\"ports\":[{\"hostPort\":6379,\"containerPort\":6379,\"protocol\":\"TCP\"}]}]},\"status\":\"Running\",\"host\":\"kubernetes-minion-1.c.solid-setup-685.internal\",\"restartpolicy\":{\"type\":\"RestartAlways\"}},\"currentState\":{\"manifest\":{\"version\":\"\",\"id\":\"\",\"volumes\":null,\"containers\":null},\"status\":\"Waiting\",\"restartpolicy\":{}}}"
                   }
                 ]
               }
             ]
           }
         ]
       }
       }

     - Summary
         Commandline request first goes from kubecfg to apiserver, where a new
         "registry/pod" entry is created. Scheduler will watch for Pod changes, and
         here, notice a new Pod is created. It will find a minion to run the Pod,
         and create a binding object to bind the Pod to the minion. The creation
         of binding object is sent from scheduler to apiserver (this round is to
         make sure scheduler is pluggable). apiserver gets the request, and create
         a new "registry/host/$minion/kubelet" key. kubelet on that minion watches
         for this key, and do the actual creation of Pod and containers.

** Step Two: Turn up the redis master service
   A Kubernetes 'service' is a named load balancer that proxies traffic to one or
   more containers. The services in a Kubernetes cluster are discoverable inside
   other containers via environment variables. Services find the containers to load
   balance based on pod labels. The pod that you created in Step One has the label
   name=redis-master. The selector field of the service determines which pods will
   receive the traffic sent to the service. Use the file redis-master-service.json.

   $ cluster/kubecfg.sh -c examples/guestbook/redis-master-service.json create services
   Name                Labels              Selector            Port
   ----------          ----------          ----------          ----------
   redismaster                             name=redis-master   10000

   This will cause all pods to see the redis master apparently running on localhost:10000.
   Once created, the service proxy on each minion is configured to set up a proxy on
   the specified port (in this case port 10000).

   Service is a named abstraction of software service (for example, mysql) consisting
   of local port (for example 3306) that the proxy listens on, and the selector that
   determines which pods will answer requests sent through the proxy.

   *Details on how services work:*
   - 1. apiserver gets request
       As step 1, kubecfg sends request to apiserver, which then goes to "POST" branch
       in handleRESTStorage() of resthandler.go. storage.New() creates a new service
       object, and storage.Create(obj) creates the actual object and returns a channel.
       In pkg/registry/service/storage.go, the Create() method handles the creations.

       The creation actually also just create etcd key for the service (so now we have
       a new key in etcd "/registry/services/specs/redismaster").

   - 2. master (apiserver) updates service endpoint
       The master object insides apiserver run endpoints.SyncServiceEndpoints() forever
       (initialized from master.go). It reads out all services from etcd, and loops
       through all of them. Since there is no service before, it's a no-op, but now, the
       sync procedure gets the new service. For the new service, it first lists all
       pods that match the service's selector. Then, for each pod, creates an endpoint
       for the pod. Note that redis master pod is running on minion-1 (hostname:
       kubernetes-minion-1.c.solid-setup-685.internal, gce network ip: 10.240.100.164,
       k8s ip: 10.244.1.1), and there is also a net container associated with this pod
       (ip 10.244.1.3).  When getting the endpoint address, the net container's IP is
       used as the Pod IP; therefore, the endpoint address is "10.244.1.3:6379" (the
       key in etcd is registry/services/endpoints/redismaster).

       Note that for all Pods, there is a corresponding Pause image (net container)
       for the endpoint. The redis master containers themselves do not have any
       network settings, it's all insides the corresponding network container. The
       net container's IP address is externally shown as PodIP.

   - 3. minion proxy watches request for the endpoint
       The proxier runs independent of master, it also notices that new service is
       created and endpoint is created (through two different OnUpdate() methods).

       For the service part, it goes to pkg/proxy/proxier.go, where it adds a new
       service "redismater", and then starts listening  on local port 10000, using
       net.Listen("tcp", ":1000").

       For the endpoint part, it goes to pkg/proxy/roundrobin.go; this is the place
       that load balance request to the service across differnt Pods (or, endpoint).
       The OnUpdate() updates the pool of endpoints for use.

   - 4. proxy accepts request
       Proxy will accept all connections from within the minion. For example, if a
       container wants to get data from redis server, it doesn't connect to the
       standard 6379 port. Rather, it use environment variable to connect. The env
       variable is actually set to the service port, here 10000. So the container
       talks to localhost's 10000 port. The proxy will handle the connection, see
       proxier.go#AcceptHandler. Also, the pod load balance is performed in this
       method.

       Proxy also watch on services and endpoints, see pkg/proxy/config/api.go, the
       runService and runEndpoints methods. They use client to call Watch on service
       and endpoint, then start looping forever waiting on changes on them. The
       client will create a new StreamWatcher (pkg/watch/iowatcher.go) to watch on
       server response. apiserver, on the other hand, will start a server, see
       pkg/apiserver/watch.go#ServeHTTP() or HandleWS(). It waits on ResultChan(),
       which is implemented by pkg/tools/etcd_tools_watch.go.

** Following steps have similar code path
* example: cluster components bring up status for GCE (06/19/2015)
  When cluster is up, master instance's layout will be:
Under /etc/kubernetes
/.../addons - contains manifest (rc, service definitions) for addons, there is a script 'kube-addons.sh' to create and keep them running.
/.../admission-controls - create admission control plugins
/.../kube-addons.sh,kube-addon-update.sh,kube-master-addons.sh - manages kube addons
/.../manifests - These are Pod definitions for various kubernetes components (self hosting). A kubelet binary will be running to create these Pods from the manifest files.

Under /srv is the files managed by salt, e.g. cluster roles, certificates, etc.

In each node, there is /var/lib/kubelet/ and /var/lib/kube-proxy/ where credentials for node are stored.

master $ ps aux | grep kube
root      3070  0.0  0.0  18024  3080 ?        S    Jun17   0:00 /bin/bash /etc/kubernetes/kube-addons.sh
root      5377  1.4  1.1 138296 41964 ?        Sl   Jun17  46:44 /usr/local/bin/kubelet --enable-debugging-handlers=false --cloud_provider=gce --config=/etc/kubernetes/manifests --allow_privileged=False --v=2 --cluster_dns=10.0.0.10 --cluster_domain=cluster.local --configure-cbr0=true --cgroup_root=/ --system-container=/system
root      5554  0.0  0.0   3172   184 ?        Ss   Jun17   0:00 /bin/sh -c /usr/local/bin/kube-controller-manager --master=127.0.0.1:8080 --cluster_name=kubernetes --cluster-cidr=10.244.0.0/16 --allocate-node-cidrs=true --cloud_provider=gce  --service_account_private_key_file=/srv/kubernetes/server.key --v=2 1>>/var/log/kube-controller-manager.log 2>&1
root      5566  0.0  0.0   3172   140 ?        Ss   Jun17   0:00 /bin/sh -c /usr/local/bin/kube-apiserver --address=127.0.0.1 --etcd_servers=http://127.0.0.1:4001 --cloud_provider=gce   --admission_control=NamespaceLifecycle,NamespaceExists,LimitRanger,SecurityContextDeny,ServiceAccount,ResourceQuota --service-cluster-ip-range=10.0.0.0/16 --client_ca_file=/srv/kubernetes/ca.crt --basic_auth_file=/srv/kubernetes/basic_auth.csv  --cluster_name=kubernetes --tls_cert_file=/srv/kubernetes/server.cert --tls_private_key_file=/srv/kubernetes/server.key --secure_port=443 --token_auth_file=/srv/kubernetes/known_tokens.csv  --v=2   --allow_privileged=False 1>>/var/log/kube-apiserver.log 2>&1
root      5567  0.3  0.7  33116 27292 ?        Sl   Jun17  10:00 /usr/local/bin/kube-controller-manager --master=127.0.0.1:8080 --cluster_name=kubernetes --cluster-cidr=10.244.0.0/16 --allocate-node-cidrs=true --cloud_provider=gce --service_account_private_key_file=/srv/kubernetes/server.key --v=2
root      5582  0.8  7.3 297504 277468 ?       Sl   Jun17  26:36 /usr/local/bin/kube-apiserver --address=127.0.0.1 --etcd_servers=http://127.0.0.1:4001 --cloud_provider=gce --admission_control=NamespaceLifecycle,NamespaceExists,LimitRanger,SecurityContextDeny,ServiceAccount,ResourceQuota --service-cluster-ip-range=10.0.0.0/16 --client_ca_file=/srv/kubernetes/ca.crt --basic_auth_file=/srv/kubernetes/basic_auth.csv --cluster_name=kubernetes --tls_cert_file=/srv/kubernetes/server.cert --tls_private_key_file=/srv/kubernetes/server.key --secure_port=443 --token_auth_file=/srv/kubernetes/known_tokens.csv --v=2 --allow_privileged=False
root      5616  0.0  0.0   3172   184 ?        Ss   Jun17   0:00 /bin/sh -c /usr/local/bin/kube-scheduler --master=127.0.0.1:8080 --v=2 1>>/var/log/kube-scheduler.log 2>&1
root      5625  0.1  0.3  18464 14768 ?        Sl   Jun17   6:13 /usr/local/bin/kube-scheduler --master=127.0.0.1:8080 --v=2

root      2938  0.9  1.3 146352 50996 ?        Sl   Jun17  97:42 /usr/local/bin/kubelet --api_servers=https://kubernetes-master --enable-debugging-handlers=true --cloud_provider=gce --config=/etc/kubernetes/manifests --allow_privileged=False --v=2 --cluster_dns=10.0.0.10 --cluster_domain=cluster.local --configure-cbr0=true --cgroup_root=/ --system-container=/system
root      2981  0.2  0.4  84360 16816 ?        Sl   Jun17  30:55 /usr/local/bin/kube-proxy --master=https://kubernetes-master --kubeconfig=/var/lib/kube-proxy/kubeconfig --v=2
```

</p></details></br>

<details><summary>thockin mentor</summary><p>

```
<thockin> #1550  #1549  #1513 (is bigger)  #1488 (is cleanup)  #1442  #1366
          (is bigger and needed)  #1353  not-filed: a JobController  #1261
          (very important)    [16:42]
<thockin> just scanning the issue list - some of those are small, some are
          bigger, and some are critical.  Getting DNS running is important.
          We need it soon.  [16:43]
<thockin> #1565 is another minor one that is probably easy to fix  [16:45]
<thockin> #1277 and #1278 are still there.  #1319 is a big deal  [16:47]
<thockin> should keep you busy for months :)

(Minor)  #1488 To linewrap or not to linewrap
(Fixed)  #1565 Error message during integration test
(Fixed)  #1550 Container port is is not an int
(Fixed)  #1549 Put etcdctl on the master
(Ignore) #1442 dev-build-and-push leaves stale go files
(Big)    #1277 Kube-proxy scaling/perf
(Big)    #1278 Kube-proxy error logging and handling
(Bigger) #1513 Real container ssh
(Bigger) #1366 Minion controller is needed to remove pods from unhealthy and vanished minions
(Giant)  #1319 Run a Docker registry with the master (!)
(Giant)  #1261 Proposal: Internal Dynamic DNS service

Use pod.status.NodeIP for logLocation instead of pod.spec.NodeName

// Volumes is an interface for managing cloud-provisioned volumes
// TODO: Allow other clouds to implement this
type Volumes interface {
	// Attach the disk to the specified instance
	// instanceName can be empty to mean "the instance on which we are running"
	// Returns the device (e.g. /dev/xvdf) where we attached the volume
	AttachDisk(instanceName string, volumeName string, readOnly bool) (string, error)
	// Detach the disk from the specified instance
	// instanceName can be empty to mean "the instance on which we are running"
	DetachDisk(instanceName string, volumeName string) error

	// Create a volume with the specified options
	CreateVolume(volumeOptions *VolumeOptions) (volumeName string, err error)
	DeleteVolume(volumeName string) error
}
```

</p></details></br>

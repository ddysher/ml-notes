<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [KEPs](#keps)
  - [KEP-0009: efficient node heartbeat](#kep-0009-efficient-node-heartbeat)
  - [KEP-0014: runtime class](#kep-0014-runtime-class)
- [Feature & Design](#feature--design)
  - [container and pod resource limits consideration](#container-and-pod-resource-limits-consideration)
  - [container runtime interface (cri)](#container-runtime-interface-cri)
  - [dynamic kubelet settings](#dynamic-kubelet-settings)
  - [kubelet eviction](#kubelet-eviction)
  - [pod resource management in kubelet](#pod-resource-management-in-kubelet)
  - [node allocatable resources](#node-allocatable-resources)
  - [troubleshooting running pods](#troubleshooting-running-pods)
  - [configurable pod process namespace sharing](#configurable-pod-process-namespace-sharing)
  - [windows support](#windows-support)
  - [plugin watcher](#plugin-watcher)
- [Workflow](#workflow)
  - [how does kubelet's method call flow](#how-does-kubelets-method-call-flow)
  - [what are kubelet's managers/agents](#what-are-kubelets-managersagents)
  - [how kubelet image gc works](#how-kubelet-image-gc-works)
  - [how kubelet container gc works](#how-kubelet-container-gc-works)
  - [how nodecontroller works](#how-nodecontroller-works)
  - [summary of various plugins](#summary-of-various-plugins)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

> A collection of proposals, designs, features in Kubernetes node.

- [SIG-Node Community](https://github.com/kubernetes/community/tree/master/sig-node)

# KEPs

## KEP-0009: efficient node heartbeat

*Date: 09/08/2018, v1.11, design*

Right now node heartbeat is done via updating Node API object, which poses significant load on etcd.
The goal of the proposal is to reduce etcd size by making node heartbeat cheaper.

A new API object `Lease` will be introdued in `coordination.k8s.io` group. With this new API in
place, we will change Kubelet so that:
- Kubelet is periodically computing NodeStatus every 10s (at it is now), but that will be independent
  from reporting status
- Kubelet is reporting NodeStatus if:
  - there was a meaningful change in it (initially we can probably assume that every change is
    meaningful, including e.g. images on the node)
  - or it didn’t report it over last node-status-update-period seconds (initially, this will be
    40s, then change to 1min or even longer)
- Kubelet creates and periodically updates its own Lease object and frequency of those updates is
  independent from NodeStatus update frequency.

The key point here is that both `Lease` and `Node` will be updated via Kubelet, and both are treated
as a signal of node being healthy. Separate the update can significantly reduce etcd load, since if
we only use `Node` API, we will update all fields, even though some of them are not very important,
e.g. pulling a new image will change `Node` object, resulting a full update in etcd.

*References*

- [KEP link](https://github.com/kubernetes/community/blob/baabac7525462911bac0dab87237d9a55a93f3f2/keps/sig-node/0009-node-heartbeat.md)

## KEP-0014: runtime class

*Date: 09/08/2018, v1.11, design*

The KEP adds a new API object `RuntimeClass`, which is a new cluster-scoped resource that surfaces
container runtime properties to the control plane. RuntimeClasses are assigned to pods through a
runtimeClass field on the PodSpec. This provides a new mechanism for supporting multiple runtimes
in a cluster and/or node. The Goal is to:
- Provide a mechanism for surfacing container runtime properties to the control plane
- Support multiple runtimes per-cluster, and provide a mechanism for users to select the desired runtime

Specific problems are identified in the KEP that will be addressed in the future, e.g.
- accounting for runtime overhead, i.e. how to calculate node resource usage now that we have multiple runtime
- scheduling to nodes that support the runtime (heterogenous cluster)
- surfacing which optional features are supported by different runtimes

Following is an example from KEP:

```yaml
kind: RuntimeClass
apiVersion: node.k8s.io/v1alpha1
metadata:
    name: native  # equivalent to 'legacy' for now
spec:
    runtimeHandler: runc
---
kind: RuntimeClass
apiVersion: node.k8s.io/v1alpha1
metadata:
    name: gvisor
spec:
    runtimeHandler: gvisor
----
kind: RuntimeClass
apiVersion: node.k8s.io/v1alpha1
metadata:
    name: kata-containers
spec:
    runtimeHandler: kata-containers
----
# provides the default sandbox runtime when users don't care about which they're getting.
kind: RuntimeClass
apiVersion: node.k8s.io/v1alpha1
metadata:
  name: sandboxed
spec:
  runtimeHandler: gvisor
```

Now user can choose which runtime to use via `pod.spec.runtimeClassName`:

```yaml
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: sandboxed-nginx
spec:
  replicas: 2
  selector:
    matchLabels:
      app: sandboxed-nginx
  template:
    metadata:
      labels:
        app: sandboxed-nginx
    spec:
      runtimeClassName: sandboxed   #   <----  Reference the desired RuntimeClass
      containers:
      - name: nginx
        image: nginx
        ports:
        - containerPort: 80
          protocol: TCP
```

Implementatin wise, Kubelet will watch for all `RuntimeClass` and pod requests. Once resolved, it
will pass `RuntimeClass.spec.runtimeHandler` to CRI, which is responsible to interpret different
runtime class.

Note that Kubelet only talks to one CRI implementation, it is up to CRI to manage various runtime.
For example, Mirantis has a [cri-proxy](https://github.com/Mirantis/criproxy) designed to support
multiple CRI implementation.

*References*

- [KEP link](https://github.com/kubernetes/community/blob/a5515a371e380886a56aaa5843df27f21d9e892e/keps/sig-node/0014-runtime-class.md)

# Feature & Design

## container and pod resource limits consideration

1. We could make it easy to add new resources. Kubelet needs to understand each individual resource's
   characteristics, for isolation, QoS, overcommitment, etc.
2. We generally break down the problem of whether a pod will fit on a node into 2 problems:
   1. How to determine the available capacity of a node;
   2. How to determine how much capacity a pod will consume.

*References*

- https://github.com/kubernetes/kubernetes/issues/168

## container runtime interface (cri)

*Date: 09/30/2016, v1.4*

CRI is still under development in Kubernetes 1.4. Previously, Kubelet defines a following runime
interface (shortened):

```go
type Runtime interface {
  ...
  // Status returns error if the runtime is unhealthy; nil otherwise.
  Status() error
  // GetPods returns a list of containers grouped by pods. The boolean parameter
  // specifies whether the runtime returns all containers including those already
  // exited and dead containers (used for garbage collection).
  GetPods(all bool) ([]*Pod, error)
  ...
  KillPod(pod *api.Pod, runningPod Pod, gracePeriodOverride *int64) error
  ...
  GetContainerLogs(pod *api.Pod, containerID ContainerID, logOptions *api.PodLogOptions, stdout, stderr io.Writer) (err error)
  // Delete a container. If the container is still running, an error is returned.
  DeleteContainer(containerID ContainerID) error
  // ContainerCommandRunner encapsulates the command runner interfaces for testability.
  ContainerCommandRunner
  // ContainerAttach encapsulates the attaching to containers for testability
  ContainerAttacher
  // ImageService provides methods to image-related methods.
  ImageService
}
```

Every runtime must implement the runtime; however, this is not ideal:
- Not every container runtime supports the concept of pods natively
- High-level interface discourages code sharing and reuse among runtimes
- Pod Spec is evolving rapidly

Therefore, it is refined so that container runtime only takes care of container operations, kubelet
will be responsible to do other tasks, e.g. enforce restart policy, etc. Following is the re-designed
Container Runtime Interface:

```go
// PodSandboxManager contains basic operations for sandbox.
type PodSandboxManager interface {
    Create(config *PodSandboxConfig) (string, error)
    Delete(id string) (string, error)
    List(filter PodSandboxFilter) []PodSandboxListItem
    Status(id string) PodSandboxStatus
}

// ContainerRuntime contains basic operations for containers.
type ContainerRuntime interface {
    Create(config *ContainerConfig, sandboxConfig *PodSandboxConfig, PodSandboxID string) (string, error)
    Start(id string) error
    Stop(id string, timeout int) error
    Remove(id string) error
    List(filter ContainerFilter) ([]ContainerListItem, error)
    Status(id string) (ContainerStatus, error)
    Exec(id string, cmd []string, streamOpts StreamOptions) error
}

...

// RuntimeService interface should be implemented by a container runtime.
// The methods should be thread-safe.
type RuntimeService interface {
    RuntimeVersioner
    ContainerManager
    PodSandboxManager
    ContainerStatsManager

    // UpdateRuntimeConfig updates runtime configuration if specified
    UpdateRuntimeConfig(runtimeConfig *runtimeapi.RuntimeConfig) error
    // Status returns the status of the runtime.
    Status() (*runtimeapi.RuntimeStatus, error)
}

// ImageService contains image-related operations.
type ImageService interface {
    List() ([]Image, error)
    Pull(image ImageSpec, auth AuthConfig) error
    Remove(image ImageSpec) error
    Status(image ImageSpec) (Image, error)
    Metrics(image ImageSpec) (ImageMetrics, error)
}

type ContainerMetricsGetter interface {
    ContainerMetrics(id string) (ContainerMetrics, error)
}
```

Container Runtime Interface (CRI) is a plugin interface which enables kubelet to use a wide variety
of container runtimes, without the need to recompile. CRI consists of a protocol buffers and gRPC
API, and libraries, with additional specifications and tools under active development. CRI is being
released as alpha in Kubernetes 1.5.

Kubelet has three options to locate cri implementation:
- container-runtime
- container-runtime-endpoint
- image-service-endpoint

Before starting a pod, kubelet calls `RuntimeService.RunPodSandbox` to create the environment. This
includes setting up networking for a pod (e.g., allocating an IP). Once the PodSandbox is active,
individual containers can be created/started/stopped/removed independently. To delete the pod,
kubelet will stop and remove containers before stopping and removing the PodSandbox.

*References*

- http://blog.kubernetes.io/2016/12/container-runtime-interface-cri-in-kubernetes.html
- https://github.com/kubernetes/community/blob/master/contributors/devel/container-runtime-interface.md
- https://kubernetes.io/docs/tasks/debug-application-cluster/crictl/

**[cri networking](https://github.com/kubernetes/community/blob/master/contributors/devel/kubelet-cri-networking.md)**

Kubelet no longer manages network: CRI implementation should take care of pod networking, i.e,
setting up network via `RunPodSandbox`, tear down network via `StopPodSandbox`, etc. Therefore,
CRI implementation is free to use any network specification like CNI, CNM, etc.

For example, in cri-o, admin is required to [setup cni properly](https://github.com/kubernetes-sigs/cri-o/tree/release-1.11/contrib/cni).

**[container metrics](https://github.com/kubernetes/community/blob/master/contributors/devel/cri-container-stats.md)**

Historically Kubelet relied on the cAdvisor library to retrieve container metrics such as CPU and
memory usage. These metrics are then aggregated and exposed through Kubelet's Summary API for the
monitoring pipeline (and other components) to consume. Any container runtime (e.g., docker and rkt)
integrated with Kubernetes needed to add a corresponding package in cAdvisor to support tracking
container and image file system metrics.

Now with cri, Kubelet can retrieve the metrics directly from runtime, following is the metrics API
defined in CRI:

```go
// ContainerStats returns stats of the container. If the container does not
// exist, the call returns an error.
rpc ContainerStats(ContainerStatsRequest) returns (ContainerStatsResponse) {}
// ListContainerStats returns stats of all running containers.
rpc ListContainerStats(ListContainerStatsRequest) returns (ListContainerStatsResponse) {}
```

**[streaming requests](https://docs.google.com/document/d/1OE_QoInPlVCK9rMAx9aybRmgFiVjHpJCHI9LrfdNM_s/edit#heading=h.7xbz74srei0)**

Before CRI, Kubelet handles all exec/attach/port-forward requests; for every request, it opens
a connection to runtime and proxies request/response. Now with CRI, Kubelet will only initialize
connection with CRI, apiserver will use CRI endpoint directly when communicating with client.

**[cri logging](https://github.com/kubernetes/community/blob/baabac7525462911bac0dab87237d9a55a93f3f2/contributors/design-proposals/node/kubelet-cri-logging.md)**

To fully manage disk and support diverse runtime, Kubelet will involve in managing container logs.
There are two basic requirements proposed in the doc:
- Enforce where the container logs should be stored on the host filesystem. Both kubelet and the
  log collector can interact with the log files directly.
- Ask the runtime to decorate the logs in a format that kubelet understands. This way runtime can
  leverage existing `kubectl logs`.

## dynamic kubelet settings

*Date: 08/12/2016, v1.3*

The proposal aims at simplying kubelet configs. Right now, kubelet is configured via flags, which
causes problems like versioning, on-the-fly change, etc. The proposal tries to solve the problem
via dynamic kubelet settings.

Specifically, master kubelet (kubelet running on master node) is started with minimal config to
start apiserver, scheduler, etc, with on-disk configs, i.e. manifests. Then user creates configMaps
for kubelet configs, either global config for all kubelet or per kubelet config. kubelet then starts
a sync loop to sync config changes.

*References*

- [issue discussion](https://github.com/kubernetes/kubernetes/pull/29459)
- [design proposal](https://github.com/kubernetes/community/blob/baabac7525462911bac0dab87237d9a55a93f3f2/contributors/design-proposals/node/dynamic-kubelet-configuration.md)

*Update on 03/09/2018, v1.9, alpha*

As of 1.9, the feature is [alpha](https://github.com/kubernetes/website/blob/snapshot-initial-v1.9/docs/tasks/administer-cluster/reconfigure-kubelet.md).

## kubelet eviction

*Date: 10/08/2016, v1.4*

The proposal discusses how to evict pods when node resources are low. All information are obtained
via cadvisor. The nodefs is basically rootfs, which is '/' in normal cases. imagefs is where images
are stored, which is also '/' if no specific imagefs are used, e.g. in a host using only one disk
partition:

```
RootFs {Device:/dev/sda4 Mountpoint:/ Capacity:237744676864 Available:196717707264 Usage:28926615552 Labels:[docker-images root] Inodes:0xc8217ed648 InodesFree:0xc8217ed650}
ImageFs {Device:/dev/sda4 Mountpoint:/ Capacity:237744676864 Available:196717707264 Usage:28926615552 Labels:[docker-images root] Inodes:0xc8217ed7a8 InodesFree:0xc8217ed7b0}
```

There is a eviction manager in kubelet which get all required information from cadvisor, and do a
summary calculation. Based on the calculation, it evicts pods according to eviction policy. Source
code resides in `pkg/kubelet/eviction`. Note that kubelet eviction deprecates image gc and container
gc.

*References*

- [kubelet eviction proposal](https://github.com/kubernetes/kubernetes/blob/385fb81407a561292460585afc556783dcd6eaf8/docs/proposals/kubelet-eviction.md)
- [resource qos](https://github.com/kubernetes/kubernetes/blob/5562715ae5e4a231c6b6ff81392dc845d621f703/docs/design/resource-qos.md)

## pod resource management in kubelet

*Date: 10/09/2016, v1.4*

The proposal proposes a unified cgroup hierarchy with pod level cgroups for better resource management.
Motivations are outlined in the design doc; basically, pod level cgroups accounts several infra level
resource usage to pod instead of node itself, and enables better resource share in pod, etc. As of now,
cgroups are per container instead of pod.

Implementation-wise, there is a top level cgroups for Burstable and BestEffort Pods, and Guaranteed Pods
fall under root cgroups.

*References*

- [pod resource management proposal](https://github.com/kubernetes/kubernetes/blob/c02db86f2e2ea1b1405787968ddf99bcd80ca798/docs/proposals/pod-resource-management.md)
- [updated pod resource management proposal](https://github.com/kubernetes/community/blob/5323d141feb5bf8994adf67b623b27465d2fe4b9/contributors/design-proposals/node/pod-resource-management.md)

## node allocatable resources

*Date: 04/04/2017, v1.6*

This proposal introduces the concept of `Allocatable` which identifies the amount of compute resources
available to user pods. Specifically, the kubelet will provide a few knobs to reserve resources for
OS system daemons and kubernetes daemons. The feature is enabled in 1.6.

*References*

- [node allocatable resources](https://github.com/kubernetes/community/blob/4aa88115d15845bb18ade8e483225af141135672/contributors/design-proposals/node-allocatable.md)

## troubleshooting running pods

*Date: 05/07/2017, v1.7*

This proposal seeks to add first class support for troubleshooting by creating a mechanism to execute
a shell or other troubleshooting tools inside a running pod without requiring that the associated
container images include such tools.

*References*

- [pod troubleshooting proposal](https://github.com/verb/kubernetes/blob/7b939b781eea8e06460f380abedb2e1170a49c84/docs/proposals/pod-troubleshooting.md)

*Update on 03/08/2018, v1.10*

The feature is still under discussion during k8s 1.9 development cycle and will not make it to k8s
1.10. The implementation plan is updated in the proposal. The new plan is to extend '/exec' endpoint
for debugging; if it's a debugging request, kubelet will run a sidecar container based on input
parameter.

- [updated pod troubleshooting proposal](https://github.com/kubernetes/community/blob/88553fdf661a3645e419bd3fb654dbe1d8480333/contributors/design-proposals/node/troubleshoot-running-pods.md)

## configurable pod process namespace sharing

*Date: 03/09/2018, v1.10, alpha*

Adding support for PID namespace is easy at first glance; however, sharing PID namespace in a pod
breaks the assumption in docker that container has init process 1; with PID namespace, PID 1 always
goes to infra container. The feature was enabled by default in 1.7, but because of issue, it was
disabled in 1.8.

*References*

- [design proposal](https://github.com/kubernetes/community/blob/b5c1e2c14ef3c6384b52e3de908131e687029072/contributors/design-proposals/node/pod-pid-namespace.md)
- https://github.com/kubernetes/kubernetes/issues/48937
- https://www.ianlewis.org/en/almighty-pause-container

*update on 08/05/2018, v1.11, alpha*

Due to the above reasons, a new key 'ShareProcessNamespace' is added to pod spec "Pod.Spec.SecurityContext",
where each Pod can individually enable sharing PID namespace within Pod. The feature is scheduled
for beta in v1.12.

## windows support

*Date 03/09/2018, v1.9, beta*

Support for windows container is beta in k8s 1.9.

*References*

- https://github.com/kubernetes/website/blob/snapshot-initial-v1.9/docs/getting-started-guides/windows/index.md

## plugin watcher

*Date: 08/05/2018, v1.11, alpha*

In Kubelet, resource registration has different approaches:
- for device plugin, it will find kubelet gRPC server in a canonical path and call its register method
- for csi, kubelet discovers csi drivers with path: /var/lib/kubelet/plugins/[SanitizedCSIDriverName]/csi.sock

The proposal aims to solve the problem and standarizes plugin discovery mechanism. The preferred
approach is: Kubelet watches new plugins under a canonical path through inotify, specifically:
- Kubelet will have a new module, PluginWatcher, which will probe a canonical path recursively
- On detecting a socket creation, Watcher will try to get plugin identity details using a gRPC client on the discovered socket and the RPCs of a newly introduced Identity service.
- Plugins must implement Identity service RPCs for initial communication with Watcher.

*References*

- https://github.com/kubernetes/community/pull/2369

# Workflow

## how does kubelet's method call flow

*Date: 04/13/2015, v1.0*

Kubelet only cares pods whose node name is set to it's name, see `pkg/kubelet/config`, `cmd/kubelet/kubelet.go#main()`.

```go
cmd/kubelet/app/server.go#Run() -> Create KubeletConfig
cmd/kubelet/app/server.go#RunKubelet()
  createAndInitKubelet()
    pkg/kubelet/kubelet.go#NewMainKubelet() -> Create Kubelet
  startKubelet()
pkg/kubelet/kubelet.go#Run()
```

## what are kubelet's managers/agents

*Date: 04/13/2015, v1.0*

- volumePluginMgr: see storage
- networkPlugin: see network
- containerGC: Garbage collect containers in a separate goroutine. `pkg/kubelet/container_gc.go`
- imageManager: Image manager meant to manage lifecycle of all images, currently, it just do image
  garbage collection based on disk threshhold. `pkg/kubelet/image_manager.go`
- containerManager: containerManager helps create container, get container status, etc. It also
  works with pod concepts, e.g. GetPodStatus. `pkg/kubelet/dockertools/manager.go`
- podManager: Pod manager stores and manages access to the pods. It manages pods from all sources
  (http, apiserver, file, etc). Kind of a local cache with some functions. `pkg/kubelet/pod_manager.go`
- statusManager: statusManager Updates pod statuses to apiserver. It only updates pod status when
  necessary. Kubelet call SetPodStatus for each pod, which triggers status manager to update pod
  status. `pkg/kubelet/status_manager.go`
- podWorkers: podWorkers is called in every sync period. Every sync period, kubelet's main SyncPods
  method will call podWorkers.UpdatePod(pod, xxx) for each known pod. podWorkers spawns different
  goroutines to do the update. statusManager is called inside per pod worker for each pod. `pkg/kubelet/pod_workers.go`
- dockerCache: A cache of pods.

## how kubelet image gc works

*Date: 10/31/2015, v1.0*

There is an image manager started by kubelet that loops forever. Every 5min, it does a garbage
collection of the images. Image policy defines two threshold: high and low. When disk usage
(reported from cadvisor) is larger than high threshold, image gc is triggered and image manager
will try to free disk space down to low threshold. Otherwise, no action is taken. If GC is
required, image manager will list and record all images on the host; then delete from last used
images until
1. no image to delete;
2. enough space has been freed.

## how kubelet container gc works

*Date: 10/31/2015, v1.0*

Kubelet will start a thread for container eviction, the thread runs every 1min. Deleting containers
depends on docker container name constructed by kubernetes,

```
k8s_cds-executor.9f546c57_cds-executor-qnrn6_default_c0e39f35-7d89-11e5-967d-5254dc082878_25d46755
parts: 0:k8s 1:cds-executor.9f546c57 2:cds-executor-qnrn6 3:default 4:c0e39f35-7d89-11e5-967d-5254dc082878 5:25d46755
nameParts: 0:cds-executor 1:9f546c57
containerName: cds-executor
hash: 9f546c57
podFullName:  cds-executor-qnrn6_default
podUID: c0e39f35-7d89-11e5-967d-5254dc082878
 ```

EvictUnit is the unit for eviction, it consists of (podUID and containerName), i.e. all possible
historical containers of a Pod. Note since kubernetes adds a lot of info to container name, there's
no conflict wrt docker. Kubernetes will delete containers specifying by MaxPerPodContainer and
MaxContainers.

## how nodecontroller works

*Date: 08/03/2018, v1.11*

Following is a list of NodeCondition:
- Ready
- OutOfDisk
- MemoryPressue
- DiskPressure
- PIDPressure
- NetworkUnavailable

Each condition can be one of the three conditions:
- True
- False
- Unknown

Under normal cases, node status will be updated by corresponding kubelet. Node controller has two
goroutines to manage node status & pod eviction: monitorNodeStatus & doEvictionPass.
- monitorNodeStatus: Node controller only cares about Ready Condition. If NodeReady condition was
  last set longer ago than gracePeriod, it updates the condition to Unknown (regardless of its
  current value) in the master; other conditions are set to Unknown as well.
- monitorNodeStatus: If Ready condition is False *or* Unknown (False is set via kubelet, Unknown is
  set by node controller itself as mentioned above), monitorNodeStatus updates all pods status to
  Unknown, and adds node to a evictor queue to start evicting pods on this node, see below.
- doEvictionPass: The goroutine evicts all pods in target node. It sets reason and message in the
  pod object, and send DELETE request to kubernetes. If node comes back later, then node is removed
  from evictor by monitorNodeStatus. The delete request sent to Kubernetes will follow normal Pod
  deletion flow, i.e. update pods.deletionTimestamp, start grace period, etc.

Note about interaction with application controllers, e.g. replicaset. For application controllers,
Pods that are considered a managed replica based on the following method:

```go
func IsPodActive(p *v1.Pod) bool {
  return v1.PodSucceeded != p.Status.Phase &&
    v1.PodFailed != p.Status.Phase &&
    p.DeletionTimestamp == nil
}
```

From the method, we see that since pod is deleted and pod.DeletionTimestamp is not nil, replicaset
will consider bringing up new pod.

Note about parameters, currently (by default):
- Lack of NodeStatus update for <node-monitor-grace-period> (default: 40s) results in NodeController
  marking node as NotReady (pods are no longer scheduled on that node)
- Lack of NodeStatus updates for <pod-eviction-timeout> (default: 5m) results in NodeController
  starting pod evictions from that node

## summary of various plugins

*Date: 09/23/2018, v1.11*

Kubernetes has a bounch of plugins, due to legacy reasons, they are not consistent in various
aspects. NB. there is a plugin watcher proposal (see above) to unify the registration mechanism,
but it's still under development as of v1.11.

**device plugin, v1beta1**

- communication: gRPC between kubelet and device plugin
- registration: kubelet & plugin both have sockets: plugin finds kubelet socket and call register
  method to register itself; default kubelet socket path is `/var/lib/kubelet/device-plugins/` and
  plugin socket path will be passed to kubelet during registration

**container runtime interface (cri), v1alpha2**

- communication: gRPC between kubelet and cri plugin
- registration: kubelet accepts commandline flags about location of cri endpoints

**container network interface (cni)**

- communication: binary invocation
- registration: for cri & cni, kubelet doesn't manage network; for docker, kubelet uses `--cni-config-dir` and `--cni-bin-dir`
  to locate cni plugins

**container storage interface (csi)**

- communication: gRPC between kubelet and csi plugin
- registration: kubelet locates driver at `/var/lib/kubelet/plugins/[SanitizedCSIDriverName]/csi.sock`

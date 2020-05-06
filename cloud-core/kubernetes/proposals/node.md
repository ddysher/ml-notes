<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [KEPs](#keps)
  - [20170523 - cpu manager](#20170523---cpu-manager)
  - [20180101 - runtime class](#20180101---runtime-class)
  - [20180101 - runtime class scheduling](#20180101---runtime-class-scheduling)
  - [20190212 - ephemeral containers](#20190212---ephemeral-containers)
  - [20180718 - efficient node heartbeat](#20180718---efficient-node-heartbeat)
  - [20180911 - compute device assignment](#20180911---compute-device-assignment)
  - [20190129 - hugepages support](#20190129---hugepages-support)
  - [20190129 - pid limiting](#20190129---pid-limiting)
  - [20190130 - topology manager](#20190130---topology-manager)
  - [20190221 - liveness holdoff, aka, startup probe](#20190221---liveness-holdoff-aka-startup-probe)
  - [20190226 - pod overhead](#20190226---pod-overhead)
  - [20190920 - pod pid namespace sharing](#20190920---pod-pid-namespace-sharing)
- [Feature & Design](#feature--design)
  - [(large) container runtime interface (cri)](#large-container-runtime-interface-cri)
  - [(large) dynamic kubelet configuration](#large-dynamic-kubelet-configuration)
  - [(large) kubelet eviction](#large-kubelet-eviction)
  - [(large) pod resource management in kubelet](#large-pod-resource-management-in-kubelet)
  - [(medium) accelerator monitoring](#medium-accelerator-monitoring)
  - [(medium) cri dockershim checkpoint](#medium-cri-dockershim-checkpoint)
  - [(medium) cri windows support](#medium-cri-windows-support)
  - [(medium) plugin watcher](#medium-plugin-watcher)
  - [(small) pod lifecycle event generator](#small-pod-lifecycle-event-generator)
  - [(small) projected volume, aka, all-in-one volume](#small-projected-volume-aka-all-in-one-volume)
  - [(small) downward api annotations](#small-downward-api-annotations)
  - [(small) downward api resources limits requests](#small-downward-api-resources-limits-requests)
  - [(small) envvar configmap](#small-envvar-configmap)
  - [(small) node allocatable resources](#small-node-allocatable-resources)
  - [(moved) troubleshooting running pods](#moved-troubleshooting-running-pods)
  - [(design pattern) container and pod resource limits consideration](#design-pattern-container-and-pod-resource-limits-consideration)
- [Implementation](#implementation)
  - [how does kubelet's method call flow](#how-does-kubelets-method-call-flow)
  - [what are kubelet's managers/agents](#what-are-kubelets-managersagents)
  - [how kubelet image gc works](#how-kubelet-image-gc-works)
  - [how kubelet container gc works](#how-kubelet-container-gc-works)
  - [how nodecontroller works](#how-nodecontroller-works)
  - [summary of various plugin registration](#summary-of-various-plugin-registration)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

> A collection of proposals, designs, features in Kubernetes node.

- [SIG-Node KEPs](https://github.com/kubernetes/enhancements/blob/master/keps/sig-node)
- [SIG-Node Proposals](https://github.com/kubernetes/community/blob/master/contributors/design-proposals/node)
- [SIG-Node Community](https://github.com/kubernetes/community/tree/master/sig-node)

# KEPs

## 20170523 - cpu manager

- *Date: 09/28/2017, v1.8, alpha*
- *Date: 06/14/2018, v1.10, beta*

There is no CPU affinity in kubernetes, thus if a Pod requesting 1 or more CPUs, it will context
switch to different CPUs. This results in bad cache hits, introducing latencies in kernel process
scheduler, etc.

The goal of the proposal is:
> if you are a Guaranteed pod with 1 or more cores of cpu (integer), the system will try to make
> sure that the pod gets its cpu quota primarily from reserved core(s), resulting in fewer context
> switches and higher cache affinity.

The affinity is per container, not per pod. Implementation-wise, a new CPU manager component is used
to manage cpuset and reconcile the settings. It maintains CPU topology and allocates CPUs per request
from kubelet. It passes the result to kubelet which in turn passes to container runtime via CRI. The
CPU topology is read from cadvisor, which find the information from `/proc/cpuinfo`. Currently, there
are two policies:
- none: works like existing policy
- static: when exclusive CPUs are allocated for a container, those CPUs are removed from the allowed
  CPUs of every other container running on the node. Once allocated at pod admission time, an
  exclusive CPU remains assigned to a single container for the lifetime of the pod (until it becomes
  terminal.)

CPU Manager feature has reached beta in v1.10. It is enabled by default and the default option is
`none`, which is the existing behavior.

*References*

- [cpu manager KEP link](https://github.com/kubernetes/enhancements/blob/d7306177022e9af921e5f6196b0dd592d01e5c28/keps/sig-node/20170523-cpu-manager.md)
- [cpu manager design doc](https://github.com/kubernetes/community/blob/c4d900e55bf67ba87eb7e4c368a8486ff4ca3761/contributors/design-proposals/node/cpu-manager.md)
- https://github.com/kubernetes/kubernetes/pull/51929

## 20180101 - runtime class

- *Date: 09/08/2018, v1.11, design*
- *Date: 06/07/2019, v1.14, beta*

The KEP adds a new API object `RuntimeClass`, which is a new cluster-scoped resource that surfaces
container runtime properties to the control plane. RuntimeClasses are assigned to pods through a
runtimeClass field on the PodSpec. This provides a new mechanism for supporting multiple runtimes
in a cluster and/or node. The goal is to:
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

Implementation wise, Kubelet will watch and cache all `RuntimeClass` resources. When a new pod is
created, Kubelet will try to resolve pod request against local cache. Once resolved, it will pass
`RuntimeClass.Spec.RuntimeHandler` to CRI (via RunPodSandboxRequest), which is then responsible to
interpret different runtime class. Pay attention that Kubelet only talks to one CRI implementation
registered upon start - it is up to the CRI implementation to understand `runtimehandler` and manages
various runtime.

*Update on Kubernetes v1.14*

RuntimeClass reaches beta at Kubernetes v1.14, and all major CRI implementation (e.g. containerd,
cri-o) now supports `RuntimeHandler`, i.e. support running multiple container runtime based on
configuration.

The API changes from CRD to internal API, with slight modifications:

```yaml
apiVersion: node.k8s.io/v1beta1  # RuntimeClass is defined in the node.k8s.io API group
kind: RuntimeClass
metadata:
  name: myclass  # The name the RuntimeClass will be referenced by
  # RuntimeClass is a non-namespaced resource
handler: myconfiguration  # The name of the corresponding CRI configuration
```

*References*

- [runtime class KEP link](https://github.com/kubernetes/enhancements/blob/bd79505d22a96315a1abf1e70f49535822694116/keps/sig-node/runtime-class.md)
- https://github.com/kubernetes/enhancements/issues/585

## 20180101 - runtime class scheduling

- *Date: 06/08/2019, v1.14, design*
- *Date: 09/29/2019, v1.16, beta*

As of Kubernetes v1.14, RuntimeClass assumes the cluster is homogenous with regards to RuntimeClasses,
i.e. each node supports the same set of RuntimeClasses. For heterogeneous clusters, cluster operator
and Pod authors should agree on a set of labels and taints, such that Pod authors can set appropriate
labels and tolerations when using a RuntimeClass.

Runtime class scheduling aims at automating the process by adding a `Scheduling` field in `RuntimeClass`:

```go
type Scheduling struct {
    // nodeSelector lists labels that must be present on nodes that support this
    // RuntimeClass. Pods using this RuntimeClass can only be scheduled to a
    // node matched by this selector. The RuntimeClass nodeSelector is merged
    // with a pod's existing nodeSelector. Any conflicts will cause the pod to
    // be rejected in admission.
    // +optional
    NodeSelector map[string]string

    // tolerations adds tolerations to pods running with this RuntimeClass.
    // +optional
    Tolerations []corev1.Toleration
}
```

Cluster operator is responsible to create RuntimeClasss with correct `Scheduling`. A new RuntimeClass
admission controller (built-in, enabled by default) will merge the labels and tolerations to whichever
Pod using the RuntimeClass. Follow on, the scheduling process is the same as before, i.e. scheduler
goes through predicates and priority to select Node for the Pod.

**Alternatives**

There are some design choices that are excluded in the proposal:
- scheduler predicate
- native RuntimeClass reporting
- use SchedulerPolicy

Scheduler predicate means adding a predicate into scheduler, which is responsible to resolve RuntimeClass
and filter node that match Pod request.

Native RuntimeClass reporting means adding runtime class information into Node status. This is not
flexible as indicated in the proposal, since we would need another scheduling mechanism (instead of
simply use existing label, taints constructs).

SchedulerPolicy is yet another KEP, using which will make RuntimeClass much more complex.

*References*

- [runtime class scheduling KEP link](https://github.com/kubernetes/enhancements/blob/bd79505d22a96315a1abf1e70f49535822694116/keps/sig-node/runtime-class-scheduling.md)

## 20190212 - ephemeral containers

- *Date: 09/21/2019, v1.16, alpha*

Ephemeral Containers are implemented in the core API group. While the primary purpose use case is
debugging, it's intended as a general purpose construct for running a short-lived container in a pod,
e.g. running an automated security audits scripts for some pods. Ephemeral Containers supercedes the
previous "troubleshooting running pods" proposal.

The new API is added to Pod spec:

```go
type PodSpec struct {
	...
	// List of user-initiated ephemeral containers to run in this pod.
	// This field is alpha-level and is only honored by servers that enable the EphemeralContainers feature.
	// +optional
	// +patchMergeKey=name
	// +patchStrategy=merge
	EphemeralContainers []EphemeralContainer `json:"ephemeralContainers,omitempty" patchStrategy:"merge" patchMergeKey:"name" protobuf:"bytes,31,rep,name=ephemeralContainers"`
}

type PodStatus struct {
	...
	// Status for any Ephemeral Containers that running in this pod.
	// This field is alpha-level and is only honored by servers that enable the EphemeralContainers feature.
	// +optional
	EphemeralContainerStatuses []ContainerStatus `json:"ephemeralContainerStatuses,omitempty" protobuf:"bytes,12,rep,name=ephemeralContainerStatuses"`
}
```

A kubectl command `kubectl debug` will be added to allow easy troubleshooting (which is not part of
the KEP). In short, `kubectl exec` runs a process in a container, `kubectl debug` runs a container
in a pod.

```
kubectl debug -c debug-shell --image=debian target-pod -- bash
```

Following is a quick summary:

> An EphemeralContainer is a temporary container that may be added to an existing pod for user-initiated
> activities such as debugging. Ephemeral containers have no resource or  scheduling guarantees, and
> they will not be restarted when they exit or when a pod is removed or restarted. If an ephemeral
> container causes a pod to exceed its resource  allocation, the pod may be evicted.
>
> Ephemeral containers may not be added by directly updating the pod spec. They must be added via the
> pod's ephemeralcontainers subresource, and they will appear in the pod spec once added.

Ephemeral Containers have several characteristics and limitations:
- A new Pod subresource `/ephemeralcontainers` is added to CRUD Ephemeral Containers.
- Admission plugins will be updated to guard `/ephemeralcontainers`.
- When supported by a runtime, multiple clients can attach to a single ephemeral container (i.e.
  `kubectl attach`) and share the terminal.
- Resources are not allowed for Ephemeral Containers. Ephemeral Containers use spare resources already
  allocated to the pod. There are no limits on the number of Ephemeral Containers that can be created
  in a pod, but exceeding a pod's resource allocation may cause the pod to be evicted.
- Ephemeral Containers have no additional privileges above what is available to any `v1.Container`.
  It's the equivalent of configuring an shell container in a pod spec except that it is created on
  demand.
- Ephemeral Containers will not be restarted.
- Ephemeral Containers will not be killed automatically unless the pod is destroyed. Ephemeral Containers
  will stop when their command exits, such as exiting a shell.
- SecurityContext (Capabilities, Privileged, RunAsXXX, etc) is not allowed for ephemeral containers.
- Ephemeral Containers may not be modified or deleted (for alpha)
- Creative usage of Ephemeral Containers should be limited, for example, it might be tempting to use
  Ephemeral Containers to perform critical but asynchronous functions like backing up a production
  database, but this would be dangerous because Ephemeral Containers have no execution guarantees
  and could even cause the database pod to be evicted by exceeding its resource allocation.

*References*

- [ephemeral containers KEP link](https://github.com/kubernetes/enhancements/blob/26dc9a946876b32f3f2b41a58edf4e35a2751f9f/keps/sig-node/20190212-ephemeral-containers.md)

## 20180718 - efficient node heartbeat

- *Date: 09/08/2018, v1.11, design*
- *Date: 12/09/2019, v1.17, stable*

Right now node heartbeat is done via updating Node API object, which poses significant load on etcd.
The goal of the proposal is to reduce etcd size by making node heartbeat cheaper.

A new API object `Lease` will be introdued in the `coordination.k8s.io` group. There are quite a few
alternatives, e.g.
- Add a new API object named `Heartbeat`: This is intuitive, but lacks generalization. Conversely
  `Lease` is more common and can be used in other components as well.
- Use existing `Event` API: Event is already used in Kubernetes and it's relatively low priority
  API in Kubernetes. In addition, using Event is not ideal for some use cases, like deleting all
  events, just watching heartbeat event, etc.
- Split `Node` object: This is complicated and not a very generic solution.

Now with this new API in place, Kubelet will be changed so that:
- It periodically computes NodeStatus every 10s (at it is now), but that will be independent from
  reporting status.
- It reports NodeStatus if:
  - there was a meaningful change in it,
  - or it didn’t report it over last `node-status-update-period` seconds (initially, this will be 40s).
- It creates and periodically updates its own `Lease` object and frequency of those updates is
  independent from NodeStatus update frequency (initially, this will be 10s).

The key point here is that both `Lease` and `Node` will be updated via Kubelet, and both are treated
as a signal of node being healthy. Separating the update can significantly reduce etcd load. As
mentioned above, if we only use `Node` API, we will update all fields, even though some of them are
not very important, e.g. pulling a new image will change `Node` object, resulting a full update in
etcd.

Starting from v1.14, we'll find node lease objects in dedicated namespace:

```
$ kubectl get lease --namespace kube-node-lease
NAME       HOLDER     AGE
minikube   minikube   4m29s
```

*References*

- [efficient node heartbeat KEP link](https://github.com/kubernetes/enhancements/blob/bd79505d22a96315a1abf1e70f49535822694116/keps/sig-node/0009-node-heartbeat.md)

## 20180911 - compute device assignment

- *Date: 07/28/2019, v1.15, beta*

The core of the KEP is to provide external agents a "Pod(Container)-to-Devices mapping", i.e. which
container is using which device. The target use case is to ease metrics observation for device
vendors. Kubelet is changed to expose a gRPC endpoint:

```
$ sudo ls /var/lib/kubelet/pod-resources
kubelet.sock
```

Summary for alternative approaches:
- Using existing kubelet gRPC service: not flexible
- Add field to Pod status: since device binding is just local information, it doesn't justify API change
- Use the Kubelet Device Manager Checkpoint file: requires additional implementation like versioning
- Add a field to the Pod Spec (Before starting the pod, the kubelet writes the assigned Spec.ComputeDevices
  back to the pod spec, and wait for Pod updates): similar to Pod status, device binding doesn't justify
  API change; in addition, setting pod spec introduces pod startup latency

*References*

- [compute device assignment KEP link](https://github.com/kubernetes/enhancements/blob/abdc87efbe04b1a83ec5c4f220d7af465ec4d458/keps/sig-node/compute-device-assignment.md)

## 20190129 - hugepages support

- *Date: 09/28/2017, v1.8, alpha*
- *Date: 06/23/2018, v1.10, beta*

The proposal enables kubernetes to support hugepages, and has a relatively narrow scope to only
support huge page allocated at boot time or by manual dynamic allocation. Features like kubelet
dynamic hugepage allocation and NUMA aware allocation are out of scope. To the end, node spec
becomes something similar to:

```yaml
# No huge page.
apiVersion: v1
kind: Node
metadata:
  name: node1
...
status:
  allocatable:
    cpu: "8"
    ephemeral-storage: "216272059649"
    hugepages-1Gi: "0"
    hugepages-2Mi: "0"
    memory: 16174764Ki
    pods: "110"
  capacity:
    cpu: "8"
    ephemeral-storage: 234670204Ki
    hugepages-1Gi: "0"
    hugepages-2Mi: "0"
    memory: 16277164Ki
    pods: "110"
---
# 1024 x 2Mi huge page.
apiVersion: v1
kind: Node
metadata:
  name: node1
...
status:
  allocatable:
    cpu: "8"
    ephemeral-storage: "216272059649"
    hugepages-1Gi: "0"
    hugepages-2Mi: 2Gi
    memory: 14077612Ki
    pods: "110"
  capacity:
    cpu: "8"
    ephemeral-storage: 234670204Ki
    hugepages-1Gi: "0"
    hugepages-2Mi: 2Gi
    memory: 16277164Ki
    pods: "110"
...
```

Note in the above output, node allocatable is different depending on how many huge pages are allocated.
Pre-allocated huge pages reduce the amount of allocatable memory on a node. The node will treat
pre-allocated huge pages similar to other system reservations and reduce the amount of memory it
reports.

A pod must make a request to consume pre-allocated huge pages using the resource `hugepages-<hugepagesize>`
whose quantity is a positive amount of memory in bytes, e.g. for 2Mi hugepage, it's valid to claim
4Mi but invalid to claim 3Mi hugepages.

Also, hugepage request and limit must match - no hugepages overcommit is allowed. Initially, a pod
may not consume multiple huge page sizes in a single pod spec; but the restriction can be relaxed
when use cases are presented in the community. Similar to other machine data, hugepage info is
retrieved via cadvisor, which in turn read from `/sys/kernel/mm/hugepages`. Below is a simple
script to pre-allocate huge page to test it out, source can be found [here](https://github.com/derekwaynecarr/hugepages):

<details><summary>HugePage Test Script</summary><p>

```shell
set -o errexit
#set -o pipefail
set -u
set -x

# The script must be run as a root.
# Input:
#
# Environment Variables
# NR_HUGEPAGES - Number of 2MB huge pages to allocate on the machine.  Defaults to 0
#

NR_HUGEPAGES=${NR_HUGEPAGES:-"0"}

allocate_huge_pages() {
    echo "$NR_HUGEPAGES" > /proc/sys/vm/nr_hugepages
}

verify_huge_pages() {
    nr_huge_pages=$(cat /proc/sys/vm/nr_hugepages)
    if [ "$NR_HUGEPAGES" -eq "$nr_huge_pages" ]
    then
        echo "huge pages allocated."
    else
        echo "huge pages not allocated."
        exit 1
    fi
}

exit_if_allocation_not_needed() {
    nr_huge_pages=$(cat /proc/sys/vm/nr_hugepages)
    if [ "$NR_HUGEPAGES" -eq "$nr_huge_pages" ]
    then
      echo "huge pages already allocated.  skipping allocation"
      exit 0
    fi
}

restart_kubelet() {
    echo "Sending SIGTERM to kubelet"
    if pidof kubelet &> /dev/null; then
        pkill -SIGTERM kubelet
    fi
}

post_allocation_sequence() {
    # Restart the kubelet for it to pick up the huge pages.
    restart_kubelet
}

main() {
    # Exit if installation is not required (for idempotency)
    exit_if_allocation_not_needed
    # Allocate the huge pages
    allocate_huge_pages
    # Verify the huge pages are allocated.
    verify_huge_pages
    # Perform post allocation steps
    post_allocation_sequence
}

main "$@"
```

</p></details></br>

Resource enforcement is done using `hugetlb` cgroup, i.e. control how many hugetlb pages pod can
allocate. Check `/proc/cgroups` to see if `hugetlb` cgroup is available, if not, then it's possible
it is not enabled via kernel config `CONFIG_CGROUP_HUGETLB`, see `/proc/config.gz`.

There are two approaches to use hugepage, one is `hugetlbfs`, the other is `shmget`. Using `hugetlbfs`,
pod needs to use volume/volumemounts with medium=hugepages.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: example
spec:
  containers:
  ...
    volumeMounts:
    - mountPath: /hugepages
      name: hugepage
    resources:
      requests:
        hugepages-2Mi: 1Gi
      limits:
        hugepages-2Mi: 1Gi
  volumes:
  - name: hugepage
    emptyDir:
      medium: HugePages
```

*Update on 09/24/2018*

Another [downstream implementation from intel](https://github.com/intelsdi-x/kubernetes/pull/55/files),
which uses new volumes API:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: test-hugepages-volume-pod
spec:
  containers:
  - image:  gcr.io/google_containers/test-webserver
    name: test-container
    volumeMounts:
    - mountPath: /hugepages
      name: test-volume
  volumes:
  - name: test-volume
    hugePages:
      pageSize: "2M"
      size: "200M"
      minSize: "100M"
```

*Update on 03/30/2020*

As mentioned above, there are certain limitations in the initial design proposal, follow up designs
overcome the limitations, specifically:
- Support container isolation of hugepages (previously at pod level)
- Support multi size hugepages at host level
- Support multi size hugepages at container level

For example, following is a Pod requesting multi size hugepages:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: example
spec:
  containers:
...
    volumeMounts:
    - mountPath: /hugepages-2Mi
      name: hugepage-2Mi
    - mountPath: /hugepages-1Gi
      name: hugepage-1Gi
    resources:
      requests:
        hugepages-2Mi: 1Gi
        hugepages-1Gi: 2Gi
      limits:
        hugepages-2Mi: 1Gi
        hugepages-1Gi: 2Gi
  volumes:
  - name: hugepage-2Mi
    emptyDir:
      medium: HugePages-2Mi
  - name: hugepage-1Gi
    emptyDir:
      medium: HugePages-1Gi
```

*References*

- [hugepages KEP link](https://github.com/kubernetes/enhancements/blob/000b16193b2e9833cd21884e58aaa05a03f11ef6/keps/sig-node/20190129-hugepages.md)
- [hugepages design doc](https://github.com/kubernetes/community/blob/c4d900e55bf67ba87eb7e4c368a8486ff4ca3761/contributors/design-proposals/resource-management/hugepages.md)
- https://github.com/kubernetes/enhancements/issues/1539
- https://lwn.net/Articles/499255/
- https://www.kernel.org/doc/Documentation/cgroup-v1/hugetlb.txt

## 20190129 - pid limiting

- *Date: 06/09/2019, v1.14, alpha & beta*

PID limiting proposes to limit PID usages per Pod, which includes:
- Pod-to-Pod Isolation
- Node-to-Pod Isolation

Pod-to-Pod isolation means isolating PID usages across Pods, which is acheived via adding a new flag
`pod-max-pids` in Kubelet: if this flag is set, then Pod's PID cgroups will include the limit; if
not set, then Node's allocatable PIDs will be set. For example, if the value is 300, then each Pod
can't use more than 300 processes.

However, since PIDs can be overcommitted, Pod-to-Pod isolation can't protect node components (e.g.
Kubelet, Docker) from running out of PIDs. Therefore, similar to cpu and memory, the Node-to-Pod
isolation is proposed to fix the problem by reserving certain amount of PIDs to system components.
That is, if `pod-max-pids` is not set, then allocatable PIDs (usually much larger, e.g. 30000) will
be added to top PID cgroups parenting all Pods, i.e. the top `kubepods` cgroups level.

*References*

- [pid limiting KEP link](https://github.com/kubernetes/enhancements/blob/bd79505d22a96315a1abf1e70f49535822694116/keps/sig-node/20190129-pid-limiting.md)
- https://kubernetes.io/blog/2019/04/15/process-id-limiting-for-stability-improvements-in-kubernetes-1.14/

## 20190130 - topology manager

- *Date: 08/20/2019, v1.15, design*
- *Date: 03/30/2020, v1.18, beta*

Topology manager is a new component in Kubelet that helps to find the best **socket affinity** for
containers based on inputs from other components like cpu manager and device manager. It's important
to note that topology manager, as outlined in the KEP, only takes care of socket affinity, i.e.
choosing the best socket to run a container. This means that inter-device connectivity (e.g. nvidia
Nvlink), HugePages, CNI are out of scope for this KEP. However, the authors makes sure that the
design will not block implementation of those features in the future.

The implementation is a *two phase topology coherence protocol*, the brief workflow is:
- Topology manager implements the Kubelet admission interface, i.e. Kubelet will call `Admit` method
  on topology manager before actually running a Pod.
- In side of the `Admit` method, topology manager will call `GetTopologyHints` of each `HintProvider`
  (for each container). Current HintProvider includes [cpu manager](https://github.com/kubernetes/kubernetes/blob/release-1.16/pkg/kubelet/cm/cpumanager/topology_hints.go)
  and [device manager](https://github.com/kubernetes/kubernetes/pull/80570). The device plugin API
  has been updated to include [topology information](https://github.com/kubernetes/kubernetes/blob/9a5b87a58b33b4a8e97ad0bf157c569060431f60/pkg/kubelet/apis/deviceplugin/v1beta1/api.proto#L100)
  when reporting device.
- When starting the container, Kubelet will call cpu manager and device manager to allocate cpu and
  device, which will then call `GetAffinity` method of topology manager to make the decision. This
  is why the protocol is called "two phase" - topology manager first calls cpu/device manager, which
  then calls topology manager.

*References*

- [topology manager KEP link](https://github.com/kubernetes/enhancements/blob/f701ae66b466a9c8e6789b7c5135924949617ea7/keps/sig-node/0035-20190130-topology-manager.md)
- https://github.com/kubernetes/enhancements/issues/693

## 20190221 - liveness holdoff, aka, startup probe

- *Date: 09/29/2019, v1.16, alpha*

The KEP proposes a new probe: startup probe, to holdoff all other probes until the Container starts.
The startup probe has the same structure as other probes. In addition, the `ContainerStatus` struct
will include a `Started` boolean to indicate the status. The main use case is to allow slow starting
containers that require a significant amount of time (one to several minutes) to start.

If this probe fails, the Pod will be restarted, just as if the livenessProbe failed. In the following
example, the container has 5min to start:

```yaml
ports:
- name: liveness-port
  containerPort: 8080
  hostPort: 8080

livenessProbe:
  httpGet:
    path: /healthz
    port: liveness-port
  failureThreshold: 1
  periodSeconds: 10

startupProbe:
  httpGet:
    path: /healthz
    port: liveness-port
  failureThreshold: 30
  periodSeconds: 10
```

An alternative proposal is to include a field `InitializationFailureThreshold` in liveness probe and
readiness probe, but this makes the API a bit complicated.

*References*

- [liveness holdoff KEP link](https://github.com/kubernetes/enhancements/blob/13a778c6a4a84dbde9e691e8dcf930a6eaa7ca51/keps/sig-node/20190221-livenessprobe-holdoff.md)

## 20190226 - pod overhead

- *Date: 06/07/2019, v1.14, design*
- *Date: 03/25/2020, v1.18, beta*

Historically, Kubernetes only supports linux container based runtimes. Now with the introduction of
RuntimeClass (as well as standardization like CRI, OCI), a Kubernetes cluster can have multiple
runtimes, and quite a few of them have non-negligible overhead. For example, for VM-based runtime,
the memory overhead can be several hundred megabytes.

Pod overhead proposes to include such overhead information into Pod spec, which is automatically
injected using RuntimeController admission controller, who finds the information from RuntimeClass
object. Cluster admin is responsible to set this overhead value in RuntimeClass.

The KEP touches many components in Kubernetes:
- Add the new API (.Overhead) to the pod spec and RuntimeClass
- Update the RuntimeClass admission controller to merge the overhead into the pod spec
- Update the ResourceQuota admission controller to account for overhead
- Update the scheduler to account for overhead
- Update the kubelet (admission, eviction, cgroup limits) to handle overhead

This is related to [pod resource management in kubelet](#pod-resource-management-in-kubelet) in
turns of linux containers.

To use the PodOverhead feature, you need a RuntimeClass that defines the overhead field. As an
example, you could use the following RuntimeClass definition with a virtualizing container runtime
that uses around 120MiB per Pod for the virtual machine and the guest OS:

```yaml
kind: RuntimeClass
apiVersion: node.k8s.io/v1beta1
metadata:
  name: kata-fc
handler: kata-fc
overhead:
  podFixed:
    memory: "120Mi"
    cpu: "250m"
```

Workloads which are created which specify the `kata-fc` RuntimeClass handler will take the memory
and cpu overheads into account for resource quota calculations, node scheduling, as well as Pod
cgroup sizing.

Consider running the given example workload, test-pod:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  runtimeClassName: kata-fc
  containers:
  - name: busybox-ctr
    image: busybox
    stdin: true
    tty: true
    resources:
      limits:
        cpu: 500m
        memory: 100Mi
  - name: nginx-ctr
    image: nginx
    resources:
      limits:
        cpu: 1500m
        memory: 100Mi
```

At admission time the RuntimeClass admission controller updates the workload's PodSpec to include
the overhead as described in the RuntimeClass. If the PodSpec already has this field defined, the
Pod will be rejected. In the given example, since only the RuntimeClass name is specified, the
admission controller mutates the Pod to include an overhead.

After the RuntimeClass admission controller, you can check the updated PodSpec:

```shell
$ kubectl get pod test-pod -o jsonpath='{.spec.overhead}'
map[cpu:250m memory:120Mi]
```

*References*

- [pod overhead KEP link](https://github.com/kubernetes/enhancements/blob/bd79505d22a96315a1abf1e70f49535822694116/keps/sig-node/20190226-pod-overhead.md)
- https://github.com/kubernetes/enhancements/issues/688

## 20190920 - pod pid namespace sharing

- *Date: 03/09/2018, v1.10, alpha*
- *Date: 10/04/2018, v1.12, beta*
- *Date: 12/09/2019, v1.17, stable*

Use cases of pod PID namespace sharing:
- signaling between containers, which is useful for side cars (e.g. for signaling a daemon process after rotating logs)
- easier troubleshooting of pods
- addressing Docker's zombie problem by reaping orphaned zombies in the infra container

Adding support for PID namespace is easy at first glance; however, sharing PID namespace in a pod
breaks the assumption in docker that container has init process 1 - with PID namespace, PID 1 always
goes to infra container, specifically:
- The main container process no longer has PID 1
- Processes are visible to other containers in the pod
- Container filesystems are visible to other containers in the pod through the /proc/$pid/root magic symlink

The feature was enabled by default in 1.7, but because of these issues, it was disabled in 1.8. In
v1.12, a new boolean field `ShareProcessNamespace` is added to internal Pod spec `Pod.Spec.SecurityContext`,
and to v1 spec `Pod.Spec`. Now each Pod can individually enable sharing PID namespace within Pod.

*References*

- [pod pid namespace KEP link](https://github.com/kubernetes/enhancements/blob/1bad2ecb356323429a6ac050f106af4e1e803297/keps/sig-node/20190920-pod-pid-namespace.md)
- [pod pid namespace design proposal](https://github.com/kubernetes/community/blob/b5c1e2c14ef3c6384b52e3de908131e687029072/contributors/design-proposals/node/pod-pid-namespace.md)
- https://github.com/kubernetes/kubernetes/issues/48937
- https://www.ianlewis.org/en/almighty-pause-container

# Feature & Design

## (large) container runtime interface (cri)

- *Date: 09/30/2016, v1.4*
- *Date: 04/04/2020, v1.18, alpha*

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

The [cri api](https://github.com/kubernetes/cri-api) has been promoted to a top-level project.

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

*References*

- [container runtime interface design doc](https://github.com/kubernetes/community/blob/f784eb4ab861bd46e1919c502325ce1714ba920b/contributors/design-proposals/node/container-runtime-interface-v1.md)
- http://blog.kubernetes.io/2016/12/container-runtime-interface-cri-in-kubernetes.html
- https://kubernetes.io/docs/tasks/debug-application-cluster/crictl/
- https://github.com/kubernetes/community/blob/master/contributors/devel/container-runtime-interface.md
- https://github.com/kubernetes/cri-api

## (large) dynamic kubelet configuration

- *Date: 08/12/2016, v1.3, design*
- *Date: 03/09/2018, v1.9, alpha*
- *Date: 12/16/2018, v1.13, beta*

The proposal aims at simplying kubelet configs. Right now, kubelet is configured via flags, which
causes problems like versioning, on-the-fly change, etc. The proposal tries to solve the problem
via dynamic kubelet configuration

Specifically, master kubelet (kubelet running on master node) is started with minimal config to
start apiserver, scheduler, etc, with on-disk configs, i.e. manifests; then user creates configMaps
for kubelet configs, either global config for all kubelet or per kubelet config; kubelet then starts
a sync loop to sync config changes.

The node API object is updated to include a `configSource`, which includes a reference to configmap
in the same kubernetes cluster. The field can be extended to include other fields as well.

```yaml
spec:
  configSource:
    configMap:
      name: CONFIG_MAP_NAME
      namespace: kube-system
      kubeletConfigKey: kubelet
```

*Update on 06/26/2019, v1.15, beta*

As of v1.15, Kubelet can be configured via three approaches:
- flags
- dynamic configuration
- local config file

Flags takes precedence over dynamic configuration, which takes precedence over local config file.
As mentioned above, to use dynamic configuration, users need to update node spec to include the
`configSource` field, and pass `--dynamic-config-dir` for config checkpoint; to use local config
file, users need to pass `--config` file about the location of the config file. Both approaches use
the same config format, which is defined in `pkg/kubelet/apis/config/`.

*References*

- [dynamic kubelet configuration proposal](https://github.com/kubernetes/community/blob/57d8f190f6e9c0d64af74456a13bf13f6bd45750/contributors/design-proposals/node/dynamic-kubelet-configuration.md)
- https://github.com/kubernetes/kubernetes/pull/29459
- https://kubernetes.io/blog/2018/07/11/dynamic-kubelet-configuration/

## (large) kubelet eviction

- *Date: 10/08/2016, v1.4*

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

## (large) pod resource management in kubelet

- *Date: 10/09/2016, v1.4*

The proposal proposes a unified cgroup hierarchy with pod level cgroups for better resource management.
Motivations are outlined in the design doc; basically, pod level cgroups accounts several infra level
resource usage to pod instead of node itself, and enables better resource share in pod, etc. As of now,
cgroups are per container instead of pod.

Implementation-wise, there is a top level cgroups for Burstable and BestEffort Pods for each cgroup
subsystem, and Guaranteed Pods fall under root cgroups, e.g.

```
$ ls /sys/fs/cgroup/cpu/kubepods/besteffort/
...
$ ls /sys/fs/cgroup/cpu/kubepods/burstable/
...
```

*References*

- [pod resource management proposal](https://github.com/kubernetes/kubernetes/blob/c02db86f2e2ea1b1405787968ddf99bcd80ca798/docs/proposals/pod-resource-management.md)
- [updated pod resource management proposal](https://github.com/kubernetes/community/blob/5323d141feb5bf8994adf67b623b27465d2fe4b9/contributors/design-proposals/node/pod-resource-management.md)

## (medium) accelerator monitoring

- *Date: 12/15/2018, v1.13*

As of Kubernetes v1.9.0, alpha support for accelerator monitoring is added to Kubernetes kubelet API.
(Now only Nvidia GPU monitoring is supported). If we query kubelet stats endpoint `curl localhost:10255/stats/summary`,
we'll be able to see GPU usage for containers. Note it won't show up unless GPU is attached to
containers.

In short, cadvisor is updated to expose GPU information using NVIDIA Management Library (NVML). Below
is the new API added:

```go
// ContainerStats holds container-level unprocessed sample stats.
type ContainerStats struct {
    ...
	// Stats pertaining to CPU resources.
	// +optional
	CPU *CPUStats `json:"cpu,omitempty"`
	// Stats pertaining to memory (RAM) resources.
	// +optional
	Memory *MemoryStats `json:"memory,omitempty"`
	// Metrics for Accelerators. Each Accelerator corresponds to one element in the array.
	Accelerators []AcceleratorStats `json:"accelerators,omitempty"`
    ...
}

// AcceleratorStats contains stats for accelerators attached to the container.
type AcceleratorStats struct {
	// Make of the accelerator (nvidia, amd, google etc.)
	Make string `json:"make"`

	// Model of the accelerator (tesla-p100, tesla-k80 etc.)
	Model string `json:"model"`

	// ID of the accelerator.
	ID string `json:"id"`

	// Total accelerator memory.
	// unit: bytes
	MemoryTotal uint64 `json:"memoryTotal"`

	// Total accelerator memory allocated.
	// unit: bytes
	MemoryUsed uint64 `json:"memoryUsed"`

	// Percent of time over the past sample period (10s) during which
	// the accelerator was actively processing.
	DutyCycle uint64 `json:"dutyCycle"`
}
```

*References*

- [accelerator monitoring proposal](https://github.com/kubernetes/community/blob/57d8f190f6e9c0d64af74456a13bf13f6bd45750/contributors/design-proposals/node/accelerator-monitoring.md)

## (medium) cri dockershim checkpoint

- *Date: 12/15/2018, v1.13*

In cri, kubelet passes pod sandbox configurations to container runtime only during sandbox creation.
Afterwards, it uses a reference ID from container runtime (part of cri protocol) to manage pod.
The proposal proposes that dockershim, the docker implementation of cri, should checkpoint sandbox
information itself, this is needed due to:
- Kubelet only passes sandbox id when deleting sandbox; however, sandbox configuration is needed
  in dockershim to manage networking with cni. Therefore, it is necessary to checkpoint sandbox
  configs for later use.
- Checkpointing configuration in dockershim makes the system more reliable in case of docker daemon
  crashes, or when user deletes underline sandbox, i.e. infra container, directly from docker.

The new internal kubelet workflow:

```
RunPodSandbox creates checkpoint:
() --> Pull Image --> Create Sandbox Container --> (Create Sandbox Checkpoint) --> Start Sandbox Container --> Set Up Network --> ()

RemovePodSandbox removes checkpoint:
() --> Remove Sandbox --> (Remove Sandbox Checkpoint) --> ()
```

Following is a sandbox checkpoint for dns pod's infra container. Note the id here is docker contaienr
id, not pod id.

```
$ sudo cat /var/lib/dockershim/sandbox/3b1bb0665c026c7598cf1fed545b67aeaa9ca758445e221dca0b2df9a88c2652 | jq
{
  "version": "v1",
  "name": "kube-dns-596fbb8fbd-trx8d",
  "namespace": "kube-system",
  "data": {
    "port_mappings": [
      {
        "protocol": "udp",
        "container_port": 10053,
        "host_port": 0
      },
      {
        "protocol": "tcp",
        "container_port": 10053,
        "host_port": 0
      },
      {
        "protocol": "tcp",
        "container_port": 10055,
        "host_port": 0
      },
      {
        "protocol": "udp",
        "container_port": 53,
        "host_port": 0
      },
      {
        "protocol": "tcp",
        "container_port": 53,
        "host_port": 0
      },
      {
        "protocol": "tcp",
        "container_port": 10054,
        "host_port": 0
      }
    ]
  },
  "checksum": 2794709719
}
```

*References*

- [cri dockershim checkpoint proposal](https://github.com/kubernetes/community/blob/57d8f190f6e9c0d64af74456a13bf13f6bd45750/contributors/design-proposals/node/cri-dockershim-checkpoint.md)

## (medium) cri windows support

- *Date 03/09/2018, v1.9, beta*
- *Date 06/09/2019, v1.14, stable*

The proposal (cri: windows container configuration) is straightforward: oci specification defines
platform specific configurations, including linux, windows, solaris, etc. However, kubelet runtime
only supports linux, which means configurations like resources in pod spec will not be translated
into oci configs when starting windows container. The proposal aims to solve the problem by changing
kubelet runtime to be more modular and respect platform specific configs.

When setting appropriate networking, Pods from Windows and Linux container can access each other.
To properly schedule Pods, user must add correct node selector in Pod spec, or use taints & tolerations.

*References*

- [cri windows proposal](https://github.com/kubernetes/community/blob/57d8f190f6e9c0d64af74456a13bf13f6bd45750/contributors/design-proposals/node/cri-windows.md)
- [v1.9 getting started guide](https://github.com/kubernetes/website/blob/snapshot-initial-v1.9/docs/getting-started-guides/windows/index.md)
- [v1.13 getting started guide](https://github.com/kubernetes/website/blob/release-1.13/content/en/docs/getting-started-guides/windows/_index.md)

## (medium) plugin watcher

- *Date: 08/05/2018, v1.11, alpha*
- *Date: 12/16/2018, v1.13, stable*

In Kubelet, resource registration has different approaches:
- for device plugin, plugin will find kubelet gRPC server in a canonical path and call its register method
- for csi, kubelet discovers csi drivers with path: `/var/lib/kubelet/plugins/[SanitizedCSIDriverName]/csi.sock`

The proposal aims to solve the problem and standarizes plugin discovery mechanism. The preferred
approach is: Kubelet watches new plugins under a canonical path through inotify, specifically:
- Kubelet will have a new module, PluginWatcher, which will probe a canonical path recursively
- On detecting a socket creation, Watcher will try to get plugin identity details using a gRPC client on the discovered socket and the RPCs of a newly introduced Identity service.
- Plugins must implement Identity service RPCs for initial communication with Watcher.

*References*

- [plugin watcher proposal](https://github.com/kubernetes/community/blob/f784eb4ab861bd46e1919c502325ce1714ba920b/contributors/design-proposals/node/plugin-watcher.md)
- https://github.com/kubernetes/community/pull/2369
- https://github.com/kubernetes/kubernetes/pull/73891

## (small) pod lifecycle event generator

- *Date: 09/15/2017*

In terms of pod lifecycle, Kubelet has two high-level responsibilities:
- watches API server for pod spec changes
- lists/polls container runtime for pod stats

Using the two information, Kubelet is able to reconcile Pod status. However, before PLEG, Kubelet
uses one worker (goroutine) per pod to poll container runtime, which introduces non-negligible
overhead.

The goal of the proposal is to solve the problem by refactoring the internals of Kubelet. Instead
of polling pod per worker (goroutine), Kubelet will run a single worker to poll container runtime,
and generates events for other components in Kubelet to consume.

Kubelet includes a generic PLEG which wil relist all containers, it will also leverage two kind of
event stream:
- container runtime based event stream
- cgroups (cAdvisor) based event stream

*References*

- [pod lifecycle event generator design doc](https://github.com/kubernetes/community/blob/073f16e29bf3ed95793248624472b172a8153384/contributors/design-proposals/node/pod-lifecycle-event-generator.md)

## (small) projected volume, aka, all-in-one volume

- *Date: 12/15/2018, v1.13*

The proposal describes a new volume type that can project secrets, configmaps, and downward API items.
The volume aims to solve the problem where users must use multiple volumes in order to mount those
item into the same directory in containser, e.g.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: volume-test
spec:
  containers:
  - name: container-test
    image: busybox
    volumeMounts:
    - name: mysecret
      mountPath: "/secrets"
      readOnly: true
    - name: podInfo
      mountPath: "/podinfo"
      readOnly: true
    - name: config-volume
      mountPath: "/config"
      readOnly: true
  volumes:
  - name: mysecret
    secret:
      secretName: jpeeler-db-secret
      items:
        - key: username
          path: my-group/my-username
  - name: podInfo
    downwardAPI:
      items:
        - path: "labels"
          fieldRef:
            fieldPath: metadata.labels
        - path: "annotations"
          fieldRef:
            fieldPath: metadata.annotations
  - name: config-volume
    configMap:
      name: special-config
      items:
        - key: special.how
          path: path/to/special-key
```

vs.

```
apiVersion: v1
kind: Pod
metadata:
  name: volume-test
spec:
  containers:
  - name: container-test
    image: busybox
    volumeMounts:
    - name: all-in-one
      mountPath: "/projected-volume"
      readOnly: true
  volumes:
  - name: all-in-one
    projected:
      sources:
      - secret:
          name: mysecret
          items:
            - key: username
              path: my-group/my-username
      - downwardAPI:
          items:
            - path: "labels"
              fieldRef:
                fieldPath: metadata.labels
            - path: "cpu_limit"
              resourceFieldRef:
                containerName: container-test
                resource: limits.cpu
      - configMap:
          name: myconfigmap
          items:
            - key: config
              path: my-group/my-config
```

*References*

- [all-in-one volume proposal](https://github.com/kubernetes/community/blob/57d8f190f6e9c0d64af74456a13bf13f6bd45750/contributors/design-proposals/node/all-in-one-volume.md)

## (small) downward api annotations

- *Date: 12/15/2018, v1.13*

The proposal extends Kubernetes downwards API to allow passing annotation as environment variable
to container. Below is the common usage of downward API:

```yaml
# use downward API
env:
  - name: POD_IP
    valueFrom:
      fieldRef:
        fieldPath: status.podIP
  - name: POD_NAME
    valueFrom:
      fieldRef:
        fieldPath: metadata.name
  - name: POD_NAMESPACE
    valueFrom:
      fieldRef:
        fieldPath: metadata.namespace
```

With the proposal, we are able to use annotation (and labels) as well:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-ann-env
  annotations:
    spec.pod.beta.kubernetes.io/statefulset-index: "1"
spec:
  containers:
  - name: nginx
    image: nginx:1.13
    env:
    - name: STATEFULSET_INDEX
      valueFrom:
        fieldRef:
          fieldPath: metadata.annotations['spec.pod.beta.kubernetes.io/statefulset-index']
```

*References*

- [annotations downward api proposal](https://github.com/kubernetes/community/blob/57d8f190f6e9c0d64af74456a13bf13f6bd45750/contributors/design-proposals/node/annotations-downward-api.md)

## (small) downward api resources limits requests

- *Date:12/15/2018, v1.13*

Currently the downward API (via environment variables and volume plugin) only supports exposing a
Pod's name, namespace, annotations, labels and its IP. This document explains the need and design
to extend them to expose resources (e.g. cpu, memory) limits and requests. The motivation is to
allow applications to understand its resource constraints, e.g. java heap, golang maxproc, etc.

The proposal has detailed descriptions of different approaches. The current implementation of this
proposal will focus on the API with magic keys approach, i.e.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: kubernetes-downwardapi-volume-example
spec:
  containers:
  - name: client-container
    image: nginx:1.13
    resources:
      requests:
        memory: "64Mi"
        cpu: "250m"
      limits:
        memory: "128Mi"
        cpu: "500m"
    volumeMounts:
    - name: podinfo
      mountPath: /etc/downwards
      readOnly: false
  volumes:
  - name: podinfo
    downwardAPI:
      items:
      - path: "cpu_limit"
        resourceFieldRef:
          containerName: client-container
          resource: limits.cpu
          divisor: "1m"
      - path: "memory_limit"
        resourceFieldRef:
          containerName: client-container
          resource: limits.memory
```

Inside container, we'll see:

```
$ kubectl exec -it kubernetes-downwardapi-volume-example sh
# ls /etc/downwards
cpu_limit  memory_limit
# cat /etc/downwards/cpu_limit
500
# cat /etc/downwards/memory_limit
134217728
```

*References*

- [downward api resources limits requests proposal](https://github.com/kubernetes/community/blob/57d8f190f6e9c0d64af74456a13bf13f6bd45750/contributors/design-proposals/node/downward_api_resources_limits_requests.md)

## (small) envvar configmap

- *Date: 12/16/2018, v1.13*

The proposal aims to:
- allow using an entire configmap as environment variable in a container
- avoid conflict when using multiple configs with the same key (using `prefix` field)

The container struct as been extended to include a new type `EnvFromSource`:

```go
type Container struct {
    ...
	// +optional
	EnvFrom []EnvFromSource
	// +optional
	Env []EnvVar
    ...
}
```

```go
// EnvFromSource represents the source of a set of ConfigMaps
type EnvFromSource struct {
	// An optional identifier to prepend to each key in the ConfigMap.
	// +optional
	Prefix string
	// The ConfigMap to select from.
	//+optional
	ConfigMapRef *ConfigMapEnvSource
	// The Secret to select from.
	//+optional
	SecretRef *SecretEnvSource
}
```

For example, following is the configmap:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: etcd-env-config
data:
  number_of_members: "1"
  initial_cluster_state: new
  initial_cluster_token: DUMMY_ETCD_INITIAL_CLUSTER_TOKEN
  discovery_token: DUMMY_ETCD_DISCOVERY_TOKEN
  discovery_url: http://etcd_discovery:2379
  etcdctl_peers: http://etcd:2379
  duplicate_key: FROM_CONFIG_MAP
  REPLACE_ME: "a value"
```

The pod using this configmap:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: config-env-example
spec:
  containers:
  - name: etcd
    image: openshift/etcd-20-centos7
    ports:
    - containerPort: 2379
      protocol: TCP
    - containerPort: 2380
      protocol: TCP
    env:
    - name: duplicate_key
      value: FROM_ENV
    - name: expansion
      value: $(REPLACE_ME)
    envFrom:
    - configMapRef:
        name: etcd-env-config
```

The env result in container:

```
number_of_members="1"
initial_cluster_state="new"
initial_cluster_token="DUMMY_ETCD_INITIAL_CLUSTER_TOKEN"
discovery_token="DUMMY_ETCD_DISCOVERY_TOKEN"
discovery_url="http://etcd_discovery:2379"
etcdctl_peers="http://etcd:2379"
duplicate_key="FROM_ENV"
expansion="a value"
REPLACE_ME="a value"
```

*References*

- [envvar configmap proposal](https://github.com/kubernetes/community/blob/57d8f190f6e9c0d64af74456a13bf13f6bd45750/contributors/design-proposals/node/envvar-configmap.md)

## (small) node allocatable resources

- *Date: 04/04/2017, v1.6*

This proposal introduces the concept of `Allocatable` which identifies the amount of compute resources
available to user pods. Specifically, the kubelet will provide a few knobs to reserve resources for
OS system daemons and kubernetes daemons. The feature is enabled in 1.6.

*References*

- [node allocatable resources](https://github.com/kubernetes/community/blob/4aa88115d15845bb18ade8e483225af141135672/contributors/design-proposals/node-allocatable.md)

## (moved) troubleshooting running pods

- *Date: 05/07/2017, v1.7, design*
- *Date: 03/08/2018, v1.10, design*
- *Date: 09/21/2019, v1.15, moved to KEP*

This proposal seeks to add first class support for troubleshooting by creating a mechanism to
execute a shell or other troubleshooting tools inside a running pod without requiring that the
associated container images include such tools.

The feature is still under discussion during v1.9 development cycle and will not make it to v1.10.
The implementation plan is updated in the proposal. The new plan is to extend '/exec' endpoint for
debugging; if it's a debugging request, kubelet will run a sidecar container based on input
parameter.

In v1.15, the troubleshooting running pods proposal has moved to the Ephemeral Containers KEP.

*References*

- [pod troubleshooting proposal](https://github.com/verb/kubernetes/blob/7b939b781eea8e06460f380abedb2e1170a49c84/docs/proposals/pod-troubleshooting.md)
- [updated pod troubleshooting proposal](https://github.com/kubernetes/community/blob/88553fdf661a3645e419bd3fb654dbe1d8480333/contributors/design-proposals/node/troubleshoot-running-pods.md)

## (design pattern) container and pod resource limits consideration

1. We could make it easy to add new resources. Kubelet needs to understand each individual resource's
   characteristics, for isolation, QoS, overcommitment, etc.
2. We generally break down the problem of whether a pod will fit on a node into 2 problems:
   1. How to determine the available capacity of a node;
   2. How to determine how much capacity a pod will consume.

*References*

- https://github.com/kubernetes/kubernetes/issues/168

# Implementation

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

Note about interaction with workload controllers, e.g. replicaset. For workload controllers, Pods
that are considered a managed replica based on the following method:

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

## summary of various plugin registration

*Date: 09/23/2018, v1.11*

Kubernetes has a bounch of plugins, due to legacy reasons, they are not consistent in many aspects.
There is a plugin watcher proposal (see above) to unify the registration mechanism, but it's under
development as of v1.11.

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

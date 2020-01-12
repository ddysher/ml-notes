<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Feature & Design](#feature--design)
  - [cpu manager](#cpu-manager)
  - [device plugin, or device manager](#device-plugin-or-device-manager)
  - [hugepages support](#hugepages-support)
  - [resource quota scoping](#resource-quota-scoping)
  - [resource class](#resource-class)
  - [node performance isolation](#node-performance-isolation)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

> A collection of proposals, designs, features in Kubernetes resource management

- [Resource Management Proposals](https://github.com/kubernetes/community/tree/master/contributors/design-proposals/resource-management)
- [Resource Management Working Group](https://github.com/kubernetes/community/tree/master/wg-resource-management)
- [SIG-Node Community (Partially)](https://github.com/kubernetes/community/tree/master/sig-node)

# Feature & Design

## cpu manager

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

- [cpu manager design doc](https://github.com/kubernetes/community/blob/c4d900e55bf67ba87eb7e4c368a8486ff4ca3761/contributors/design-proposals/node/cpu-manager.md)
- https://github.com/kubernetes/kubernetes/pull/51929

## device plugin, or device manager

- *Date: 09/16/2017, v1.8, alpha*
- *Date: 06/23/2018, v1.10, beta*
- *Date: 08/05/2018, v1.11, beta*

**Proposal**

At their core, device plugins are simple gRPC servers that may run in a container deployed through
the pod mechanism or in bare metal mode. These servers implement the gRPC interface defined later
in this design document and once the device plugin makes itself known to kubelet, kubelet will
interact with the device through two simple functions:
- A ListAndWatch function for the kubelet to Discover the devices and their properties as well as notify of any status change (device became unhealthy).
- An Allocate function which is called before creating a user container consuming any exported devices.

Implementation-wise, Kubelet will list & watch device plugins via `ListAndWatch`, and maintains an
in-memory copy of all healthy devices. Kubelet is responsible to choose the appropriate devices once
containers are created but not started, and then passes device ID to `Allocate` function.

On failure cases:
- If device fails, device plugin will signal kubelet about the failed device and kubelet will fail
  pod using the device
- If device plugin fails, kubelet will remove device capacities in the node, but leave pods with
  devices allocated by this plugin running
- If kubelet fails, device plugin will know about it and try to reconnect to kubelet. Pods will keep
  running. When Kubelet fails or restarts it should know what are the devices that are owned by the
  different containers and be able to rebuild a list of available devices (via checkpointing)

**Useful discussions**

- https://github.com/kubernetes/community/pull/695#discussion_r120757506
- https://github.com/kubernetes/community/pull/695#discussion_r120844914
- https://github.com/kubernetes/community/pull/695#issuecomment-309584406
- https://github.com/kubernetes/community/pull/695#issuecomment-313809312
- https://github.com/kubernetes/community/pull/695#discussion_r128643002
- https://github.com/kubernetes/community/pull/695#discussion_r128644479
- https://github.com/kubernetes/community/pull/695#discussion_r130189486
- https://github.com/kubernetes/community/pull/695#discussion_r131023702
- https://github.com/kubernetes/community/pull/695#discussion_r131029049
- https://github.com/kubernetes/community/pull/695#discussion_r132128470
- https://github.com/kubernetes/community/pull/695#discussion_r132131179
- http://bit.ly/2xNxIzw
- http://bit.ly/2psMXKK

*Update on 08/05/2018, v1.11, beta*

Device plugin registration changes from device registration to kubelet probing model, for more detail,
see plugin watcher proposal in `node.md`.

*References*

- [device plugin design doc](https://github.com/kubernetes/community/blob/c4d900e55bf67ba87eb7e4c368a8486ff4ca3761/contributors/design-proposals/resource-management/device-plugin.md)
- https://docs.google.com/document/d/1LHeTPx_fWA1PdZkHuALPzYxR0AYXUiiXdo3S0g2VSlo/edit
- https://github.com/kubernetes/community/pull/695

## hugepages support

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

*References*

- [hugepages design doc](https://github.com/kubernetes/community/blob/c4d900e55bf67ba87eb7e4c368a8486ff4ca3761/contributors/design-proposals/resource-management/hugepages.md)
- https://lwn.net/Articles/499255/
- https://www.kernel.org/doc/Documentation/cgroup-v1/hugetlb.txt

## resource quota scoping

*Date: 06/23/2018, v1.10, stable*

The proposal first identifies a couple use cases:
- Improve resource quota to also include request & limit, to give cluster admin more control over
  how resources are allocated
- Separate quota for different QoS and promote fair-use. For example, right now if we have quota in
  a namespace, then all pods must have request/limit set. However, in practice, the cluster-admin
  wants to control the impact of best-effort pods to the cluster, but not restrict the ability to
  run best-effort pods altogether
- Quota end-users separately based on long-running vs. bounded-duration compute resources. This is
  similar to the above use case

The design choice is:
- extend quota `cpu,memory` to `cpu,memory,requests.cpu,limits.cpu,etc`
- add quota scope `Terminating,NonTerminating,BestEffort,NonBestEffort,etc`

An alternative design to quota scope is to use labels. Using labels is more flexible, but makes it
hard for cluster admin to reason about quota usage since he/she must know semantics of all labels.

*References*

- [resource quota scoping design doc](https://github.com/kubernetes/community/blob/d3879c1610516ca26f2d6c5e1cd3f4d392fb35ec/contributors/design-proposals/resource-management/resource-quota-scoping.md)

## resource class

*Date: 09/29/2017, v1.8, design*

**Proposal**

The proposal introduces two API objects:
- `ComputeResource` API object that represents a type of physical compute resource with a unique set
  of common properties.
- `ResourceClass` API object that maps from the physical ComputeResources matching certain specified
  property constraints to a portable name, with which cluster admins can further define the associated
  resource policies such as quota and limitRange.

For example:

```yaml
kind: ComputeResource
metadata:
  name: node-1-gpu-12h8x
spec:
  nodeName: node-1
  resourceName: nvidia.com/gpu
  properties:
    gpuType: K80
    memory: 8G
---
kind: ResourceClass
metadata:
  name: nvidia.high.mem
spec:
  labelSelector:
  - matchExpressions:
    - key: "Kind"
      operator: "In"
      values:
      - "nvidia-gpu"
    - key: "memory"
      operator: "GtEq"
      values:
      - "30G"
```

Kubelet is responsible to create ComputeResource for node-level resource, and a special controller
or scheduler is responsible to create cluster-level ComputeResource. ComputeResource works
closesly with device plugin API.

ComputeResource is proposed to be `nodeName-resourceName-propertyHash` to make is unique and
deterministic. However, property might change, in such case, ComputeResource name will change.
The proposal suggests that we do not simply drain the node or evict the pod, rather, Kubelet keeps
the old ComputeResource as long as there are pod consuming it, and only transit to new name when
compute resource is free.

The scheduler needs to watch for ComputeResource objects and ResourceClass objects, and caches
the binding information between the ResourceClass and the matching ComputeResource objects to
serve container resource request expressed through ResourceClass names.

Note that two ResourceClass can potentially select the same ComputeResource, which complicates
scheduling. There are few solutions to this problem:
- Disallow overlapping ResourceClass, that is, no two ResourceClass can select the same
  ComputeResource; however, this is very inflexible since compute resources tend to have very
  different properties and it's useful to provide different ResourceClass even for a single
  ComputeResource
- Use metadata constraint, e.g. label & selector. Similar to the above approach, this is not flexible.
- Proposed solution: add a `Priority` field in ResourceClass, scheduler will use matching class
  with the highest priority when choosing a class.

To maintain and propagate ComputeResource to ResourceClass binding information, the scheduler will
need to record this information in a newly introduced PodSpec field. For example, if a Node has two
ComputeResource CR1 and CR2, and there are two ResourceClass RC1 and RC2 - both RC1 and RC2 select
the two ComputeResource. When scheduling a Pod, scheduler needs to bind ComputeResource and
ResourceClass (e.g. CR1 with RC2), then set PodSpec to inform Kubelet to mount device CR1.

The proposal chooses to keep resource quota at its current meaning, i.e., a resource quota limits
how much resource can be requested by all of the pods in their container specs in a given namespace.
This is to simplify migration:

```yaml
# original quota
kind: ResourceQuota
metadata:
  name: gpu-quota-example
spec:
  Hard:
    nvidia.com/gpu: “100”
---
# 10% quota is tracked via ResourceClass, 90% is tracked via raw resource name
kind: ResourceQuota
metadata:
  name: gpu-quota-example
spec:
  Hard:
    nvidia.com/gpu: “90”
    gpu-silver: "6"
    gpu-gold: “
---
# quota after migration
kind: ResourceQuota
metadata:
  name: gpu-quota-example
spec:
  Hard:
    nvidia.com/gpu: “0”
    gpu-silver: "60"
    gpu-gold: “40”
```

For autoprovisioning, one important aspect is its interaction with cluster autoscaler:
- for node level resource, it is desirable to now the time to provision a resource, otherwise cluster
  autoscaler will keep creating nodes
- for cluster level resource, most components including cluster autoscaler, scheduler, need to filter
  the resource (e.g. scheduler doesn't consider node fitting for cluster level resource)

To solve the above problems, a provision config is proposed:

```go
ProvisionConfig {
    // CLUSTERLEVEL or NODELEVEL.
    // CLUSTERLEVEL resource can be ignored by scheduler, Kubelet, and
    // Cluster Autoscaler during their node resource fitness evaluation.
    ResourceType string
    // Resource specific node label keys attached on a node with the resource. The
    // value of such a node label indicates the expected quantity of the resource on the node.
    // It may contain multiple node label keys if the given ResourceClass matches multiple
    // kinds of node resources. E.g., we may have different node labels for different types
    // of GPU. A resource class matching all such GPUs should list all their node label keys.
    // Cluster autoscaler can use this field in combination with resource allocatable
    // to determine node readiness for the given resource, and the expected quantity
    // of the resource on the node.
    CapacityNodeLabelKeys []string
    // Represents latency upper bound for the resource to be exported on a new node.
    // Cluster Autoscaler can wait up to this bound before it considers the node not viable
    // for the resource.
    ProvisionSeconds int64
}
```

**Useful discussions**

- https://github.com/Kubernetes/community/pull/782#issuecomment-313589838
- http://bit.ly/2NwIo0i
- http://bit.ly/2DqXQqc
- http://bit.ly/2NxQW77
- http://bit.ly/2DqXQqc

*References*

- [resource class design doc v1](https://github.com/vikaschoudhary16/community/blob/53c2a804aa6fc936baa2bf35e854c62737b58dba/contributors/design-proposals/resource-class.md)
- [resource class design doc v2](https://github.com/vikaschoudhary16/community/blob/814999c7493371a162322e7e23725e36279b128a/contributors/design-proposals/resource-class.md)
- https://github.com/kubernetes/community/pull/782
- https://docs.google.com/document/d/1666PPUs4Lz56TqKygcy6mXkNazde-vwA7q4e5H92sUc/edit

## node performance isolation

*Date: 09/24/2018, design*

Document Summary:
> This document outlines how the Kubernetes node enables performance isolation primitives across
> workloads. It documents near and longer term opportunities to support the ability to configure
> applications and nodes to run particular classes of workloads in a more optimal fashion.

To be specific, here `performance isolation primitives` can be features used to support performance
sensitive workloads like numa, hugetable, sr-iov, etc.

This proposal describes three types of node profile environments:
- standard node profiles: vanilla os and hardware, with default kubelet options
- tuned node profiles: optimized os and hardware to support particular class of workloads, e.g. [aws instance types](https://aws.amazon.com/ec2/instance-types/)
- hyper-tuned node profiles: optimized os and hardware, paired with an individual application

Kubernetes will prioritize effort in the standard + tuned node profile space.

**cpu**

The design chooses "Performance Isolation based on QoS Classes", that is, we isolate cpu via QoS
instead of new API fields. The rest of the section discusses two policies in the above `cpu manager`
proposal:
- dynamic cpu assignment: in this option, the kubelet initially lands pods on shared cores, and then
  places latency sensitive pods on dedicated cores based upon observed CPU load. Once the CPU load
  drops, the dedicated cores can be shared with other pods. This option would make it possible to
  turn off unused CPU sockets, and save money.
- static cpu assignment: in this option, the kubelet assigns G pods that made integral CPU requests
  to individual CPU cores, and excludes Bu pods and Be pods from operating on those cores.

Another option is to use "Differentiated latency within a QoS class". This option differs from the
above option primarily by having a separate application class field on the pod spec that states if
the workload is latency or batch style. In this manner, G/Bu/Be pods would still land on a shared
pool of cores as all other workloads unless they had identified themselves as latency sensitive.
This option is not used due to complexity and cognitive burden for users.

Yet another option is "Pre-allocating exclusive versus shared cores", that is, cpu resources are
configured into two different resources: `cpu` and `dedicated-cpu`, e.g. configuring the node into
exclusive cpu cores (1, 2, 3, 4) and shared cores (5, 6, 7, 8) based on operator configuration.
Users are responsible to request different cpu resources based on application requirement. The option
is not used due to complexity and confusion to users.

**memory**

The proposal mentioned quite a few use cases, but didn't provide any concrete solutions.

**huge pages**

The proposal chooses to make huge pages the first class resource in Kubernetes, since huge pages are
relatively common resource type. Refer to above `hugepages support` section for detailed design.

Another option is to have users use opaque resources to account for huge pages, and have isolation
and discovery semantics satisfied via an external isolator. The option is not used since as mentioned
above, huge pages is a relatively common resource type, and using opaque resources with external
isolator makes it complicated to use. Also, since it's possible for Kubelet to manage hugepages,
it's unreasonable to use opaque resources.

*References*

- https://docs.google.com/document/d/1dS1AhAEcfZf6jnWaKoYjdEew3mYyCXUmMXmyz_lW3DM/edit

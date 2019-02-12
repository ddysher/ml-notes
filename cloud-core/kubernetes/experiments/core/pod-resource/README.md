## Kubernetes Pod Resource Management (v1.6)

- [Node Allocatable](https://github.com/kubernetes/community/blob/5323d141feb5bf8994adf67b623b27465d2fe4b9/contributors/design-proposals/node/node-allocatable.md)
- [Pod Resource Management](https://github.com/kubernetes/community/blob/5323d141feb5bf8994adf67b623b27465d2fe4b9/contributors/design-proposals/node/pod-resource-management.md)

#### Notes on resources configurations

Allocatable concept and pod resource management aims at providing better resource
management capability in kubernetes, resulting in more stable node.

`kubepods` is the top level cgroup for all pods in kubernetes. For example, in a
system with 8 CPUs, `kubepods` will have cpu share set to 8196.

```
$ cat /sys/fs/cgroup/cpu/kubepods/cpu.shares
8196
```

However, since we have other cgroups as well, `8196` share doesn't guarantee that
if a pod request `500m`, it has cpu share equivalent of half core. Share is a
relative number, it only has meaning when compared to other processes. For example,
our system has a cgroup hierarchy `/sys/fs/cgroup/cpu/user`, which is kubepods'
sibling nodes in the cgroup hierarchy; it has `1024` share. This means kubepods
cgroup sandbox will get 8196/(8196+1024) of CPU time when system is busy. Suppose
we have another pod also requesting `500m`, then the two pods will share the CPU
time, meaning each will get ((8196/(8196+1024)) * 1/2), which is less than half
a core. Note this is true only when all processes are completing for a single
core - share is enforced on a particular core. Kernel can schedule process to
other core, so the pod can get half of a core if the system has multi core and
other cores are idle. The total time is capped by cfs_quota_us.

Kubernetes allows us to set node allocatable to reserve resource for system daemons,
e.g. if we pass `--kube-reserved=cpu=2`, then we'll get:

```
$ cat /sys/fs/cgroup/cpu/kubepods/cpu.shares
6144
```

The same applies to memory. Another experimental flag related to incompressible
resource is `--experimental-qos-reserved`, which will set memory limit to burstable
and guaranteed qos cgroup; otherwise, memory is unlimited for these two qos cgroups.

More on allocatable, for example:
 - node capacity is 32Gi
 - kube-reserved is 2Gi
 - system-reserved is 1Gi
 - eviction-hard is set to <100Mi.

Node allocatable is 28.9Gi; scheduler schedules pods using this number. Memory
cgroup limit is set to 29Gi to allow kubelet eviction - kubelet will start evicting
pods whenever pods consume more than 28.9Gi.

As of v1.6, only pod allocatable is enforced; `kube-reserved` and `system-reserved`
is not enforced, see `pkg/kubelet/apis/kubeconfig/v1alpha1/defaults.go`. Operator
must have a clear understanding of how many resources to reserve for kubernetes
daemons and system daemons; once `kube-reserved` and `system-reserved` is enforced,
the daemons will be CPU starved or OOM killed.

`kube-reserved` and `system-reserved` cgroups are expected to be created by users.
kubepods cgroups will be created by kubelet automatically if it is not already
there.

#### Run a Guaranteed pod

```
kubectl create -f pod-guranteed.yaml
```

Pod uid is `b2582f40-b413-11e7-ab99-08002722cb22`, we'll see root sandbox under
`/sys/fs/cgroup/cpu/kubepods`. Per proposal, guaranteed pods uses root cgroup,
therefore we'll see the following layout:

```
$ ll /sys/fs/cgroup/cpu/kubepods
total 0
drwxr-xr-x 2 root root 0 Oct 18 14:38 besteffort
drwxr-xr-x 3 root root 0 Oct 18 14:38 burstable
-rw-r--r-- 1 root root 0 Oct 18 14:38 cgroup.clone_children
-rw-r--r-- 1 root root 0 Oct 18 14:38 cgroup.procs
-rw-r--r-- 1 root root 0 Oct 18 14:38 cpu.cfs_period_us
-rw-r--r-- 1 root root 0 Oct 18 14:38 cpu.cfs_quota_us
-rw-r--r-- 1 root root 0 Oct 18 13:22 cpu.shares
-r--r--r-- 1 root root 0 Oct 18 14:38 cpu.stat
-rw-r--r-- 1 root root 0 Oct 18 14:38 notify_on_release
drwxr-xr-x 4 root root 0 Oct 18 14:50 podb2582f40-b413-11e7-ab99-08002722cb22
-rw-r--r-- 1 root root 0 Oct 18 14:38 tasks
```

There are two containers under `podb2582f40-b413-11e7-ab99-08002722cb22`, one is
nginx container and the other is pause container.

According to proposal, the value for pod level cpu and memory data is calculated as:

```
pod<UID>/cpu.shares = sum(pod.spec.containers.resources.requests[cpu])
pod<UID>/cpu.cfs_quota_us = sum(pod.spec.containers.resources.limits[cpu])
pod<UID>/memory.limit_in_bytes = sum(pod.spec.containers.resources.limits[memory])
```

And cpu conversion is:

```
cpu.shares = (cpu in millicores * 1024) / 1000
cpu.cfs_period_us = 100000 (i.e. 100ms)
cpu.cfs_quota_us = quota = (cpu in millicores * 100000) / 1000
```

e.g.

```
$ cat /sys/fs/cgroup/cpu/kubepods/podb2582f40-b413-11e7-ab99-08002722cb22/cpu.shares
512

$ cat /sys/fs/cgroup/cpu/kubepods/podb2582f40-b413-11e7-ab99-08002722cb22/cpu.cfs_period_us
100000

$ cat /sys/fs/cgroup/cpu/kubepods/podb2582f40-b413-11e7-ab99-08002722cb22/cpu.cfs_quota_us
50000

$ cat /sys/fs/cgroup/cpu/kubepods/podb2582f40-b413-11e7-ab99-08002722cb22/8bd6192d74b9c051cd3a418a87f73d40f7e8abb3fda408223087b81085dc2761/cpu.shares
512

$ cat /sys/fs/cgroup/cpu/kubepods/podb2582f40-b413-11e7-ab99-08002722cb22/c9e65416b81cb2645536e563e6cbd11ac024f1a002d0e80d7706018e83ede76a/cpu.shares
2
```

First item is derived from (100 * 1024) / 1000.

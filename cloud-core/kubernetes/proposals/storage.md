<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Feature & Design](#feature--design)
  - [volume provisioning and storageclass](#volume-provisioning-and-storageclass)
  - [configurable volume provisioning](#configurable-volume-provisioning)
  - [volume propagation, hostpath](#volume-propagation-hostpath)
  - [volume hostpath qualifiers](#volume-hostpath-qualifiers)
  - [volume mount options](#volume-mount-options)
  - [volume snapshot](#volume-snapshot)
  - [containerized mounter pod](#containerized-mounter-pod)
  - [local volume management](#local-volume-management)
  - [local storage capacity isolation](#local-storage-capacity-isolation)
  - [local persistent volume](#local-persistent-volume)
  - [raw block consumption in kubernetes](#raw-block-consumption-in-kubernetes)
  - [volume topology-aware scheduling](#volume-topology-aware-scheduling)
  - [growing persistent volume](#growing-persistent-volume)
  - [volume operation metrics](#volume-operation-metrics)
  - [exposing storage (pv/pvc) metrics via kubelet](#exposing-storage-pvpvc-metrics-via-kubelet)
  - [csi volume plugin](#csi-volume-plugin)
  - [storage object in use protection](#storage-object-in-use-protection)
  - [pod safety](#pod-safety)
  - [volume.subPath](#volumesubpath)
  - [flexvolume and dynamic flexvolume design](#flexvolume-and-dynamic-flexvolume-design)
  - [disk accounting](#disk-accounting)
- [Workflow](#workflow)
  - [kubelet volume setup](#kubelet-volume-setup)
  - [kubernetes storage components](#kubernetes-storage-components)
  - [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

> A collection of proposals, designs, features in Kubernetes storage.

- [SIG-Storage Community](https://github.com/kubernetes/community/tree/master/sig-storage)

# KEPs

## KEP-20190120: ExecutionHook

Volume snapshot support was introduced in Kubernetes v1.12 as an alpha feature.
In the alpha implementation of snapshots for Kubernetes, there is no snapshot consistency
guarantees beyond any guarantees provided by storage system (e.g. crash consistency).

This proposal is aimed to address that limitation by providing an `ExecutionHook`
in the `Container` struct. The snapshot controller will look up this hook before
taking a snapshot and execute it accordingly.

*References*

- https://github.com/kubernetes/enhancements/pull/705

# Feature & Design

## volume provisioning and storageclass

*Date: 10/13/2016, v1.4, design*

kubernetes 1.2 introduces an alpha feature: volume dynamic provisioning; then 1.3 introduces volume
selector to allow users to select volume. In 1.4, we want it to be more flexible. A new type
'StorageClass' is introduced so admins can define different flavors. When a new claim is created
with a specific class, PV controller will try to bind a PV; if there's no existing one, then a new
PV with specifc class is created, see proposals for detail.

*References*

- [design doc](https://github.com/kubernetes/kubernetes/blob/cfba438e418d79df4144a7bd5411bed681c504fb/docs/proposals/volume-provisioning.md)
- [provisioning example](https://github.com/kubernetes/kubernetes/blob/cfba438e418d79df4144a7bd5411bed681c504fb/examples/experimental/persistent-volume-provisioning/README.md)

For general introduction of dynamic provisioning, storageclass, PV/PVC, see above references. Here
we mainly target at clearing a little bit doubts.
- In 1.6, storageclass becomes stable. There can be multiple storageclass (i.e. provisioner) in a
  kubernetes cluster. There will be a default one (denoted by annotation), if user creates a PVC
  without specifying a storageclass name, i.e. pvc.spec.storageClassName, then the default storageclass
  will be used. This behavior is acheived via DefaultStorageClass admission controller.
- PersistentVolume also has attribute 'pv.spec.storageClassName'; it's possible to manually change
  this attribute to make the PV 'created' by corresponding provisioner.
- As mentioned in 'Kubernetes storage components: PV/PVC controller), the actual dynamic provisioning
  control logic resides in PV/PVC controller. To be specific, the claimWorker extracts PVC API object,
  get 'pvc.spec.storageClassName'; then uses the name to find the StorageClass API object (use cached
  lister). Once found, it uses storageclass.Provisioner (type: string) to find the  plugin. Controller
  keeps a map of provisioner name to plugin implementations; the map is constructed at controller
  start-up time, i.e. go init() method. At last, controller calls Provision() method of the plugin
  to dynamically create volume (it will also pass storageClass.Parameters to plugin).
- If a PV was dynamically provisioned for a new PVC, the loop will always bind that PV to the PVC.
- Note that a PVC with a non-empty selector can't have a PV dynamically provisioned for it.

*References*

- http://blog.kubernetes.io/2016/10/dynamic-provisioning-and-storage-in-kubernetes.html
- http://blog.kubernetes.io/2017/03/dynamic-provisioning-and-storage-classes-kubernetes.html
- https://kubernetes.io/docs/tasks/administer-cluster/change-default-storage-class/

*Update on 06/24/2018, v1.10, ga*

The feature reaches GA before v1.10.

If volume scheduling is enabled, dynamic provisioning is done in scheduler rather than PV controller.

## configurable volume provisioning

*Date: 07/16/2017, v1.7, design*

With storage class, user can request a specific storage class, and a dynamic provisioner can create
persistent volume of that storage class on the fly for the user. However, there's little control
from the user about the attributes of the new volume; also, amdin has to configure a lot of parameters
which can be tedious (e.g. create a lot of storage class for different type of volumes).

Configurable volum provisioning aims to solve the problem. The proposal also removes the restriction
in the initial volume provisioning proposal where `claim.Spec.Selector` and `claim.Spec.Class` are
mutually exclusive. Below is an example from the proposal.

```yaml
apiVersion: storage.k8s.io/v1beta1
kind: StorageClass
metadata:
  name: slow
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp2
  zones: us-east-1a, us-east-1b, us-east-1c, us-east-2a, us-east-2b, us-east-2c
selectorOptions:
  - key: failure-domain.beta.kubernetes.io/zone
    allowedValues:
      - us-east-1a
      - us-east-1b
      - us-east-1c
      - us-east-2a
      - us-east-2b
      - us-east-2c
    description: "Requested AWS availability zone"
  - key: encryption.beta.kubernetes.io/enabled
    defaultValue: "false"
    allowedValues:
      - "true"
      - "false"
    description: "Request volume encryption"
  - key: encryption.beta.kubernetes.io/key-id
    description: "ID of AWS encryption key"
---
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: myclaim
spec:
  class: slow
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1500Mi
  selector:
    matchLabels:
      encryption.beta.kubernetes.io/enabled: "false"
    matchExpressions:
      - key: failure-domain.beta.kubernetes.io/zone
        operator: In
        values:
          - us-east-1a
          - us-east-1b
          - us-east-1c
```

Note this proposal is closed due to lack of feature leader.

*References*

- https://github.com/kubernetes/community/pull/247
- https://github.com/kubernetes/features/issues/244

## volume propagation, hostpath

*Date: 05/23/2017, v1.6, design*

From proposal introduction:
> A proposal to add support for propagation mode in HostPath volume, which allows mounts within
> containers to visible outside the container and mounts after pods creation visible to containers.

What this means is that when user creates a priviledged pod with Hostpath volume, kubelet will make
it a shared mount. For example:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hostpath
spec:
  containers:
    - name: hostpath
      image: nginx:1.13
      securityContext:
        privileged: true
      volumeMounts:
        - mountPath: "/data"
          name: hostpath
  volumes:
    - name: hostpath
      hostPath:
        path: "/tmp/path"
```

If we create this privileged pod, then when kubelet mounts this directory, it will make `/data` a
shared bind mount, e.g. inside the container, we'll see:

```console
root@hostpath:/# mountpoint /data
/data is a mountpoint

root@hostpath:/# findmnt -o TARGET,PROPAGATION /data/
TARGET PROPAGATION
/data  shared
```

Under the hood, kubelet just mounts using docker ':rshared' option, i.e.

```console
$ docker run -itd --privileged -v /tmp/path:/data:rshared nginx:1.13
```

Now inside the container, when we do mount under '/data', we'll be able to see the content from
host, i.e.

```console
### From CONTAINER
root@5aa789be9d63:/# mount --bind /etc /data/etc
root@5aa789be9d63:/# ls /data/etc
adduser.conf            environment  init.d         logrotate.d    pam.d      rc5.d        shadow-
alternatives            fonts        iproute2       mke2fs.conf    passwd     rc6.d        shells
apt                     fstab        issue          motd           passwd-    rcS.d        skel
bash.bashrc             gai.conf     issue.net      mtab           profile    resolv.conf  staff-group-for-usr-local
bindresvport.blacklist  group        kernel         network        profile.d  rmt          subgid
cron.daily              group-       ld.so.cache    networks       protocols  rpc          subuid
debconf.conf            gshadow      ld.so.conf     nginx          rc0.d      securetty    systemd
debian_version          gshadow-     ld.so.conf.d   nsswitch.conf  rc1.d      security     terminfo
default                 host.conf    libaudit.conf  opt            rc2.d      selinux      timezone
deluser.conf            hostname     localtime      os-release     rc3.d      services     ucf.conf
dpkg                    hosts        login.defs     pam.conf       rc4.d      shadow       update-motd.d

### From HOST
$ ls /tmp/path/etc
adduser.conf            environment  init.d         logrotate.d    pam.d      rc5.d        shadow-
alternatives            fonts        iproute2       mke2fs.conf    passwd     rc6.d        shells
apt                     fstab        issue          motd           passwd-    rcS.d        skel
bash.bashrc             gai.conf     issue.net      mtab           profile    resolv.conf  staff-group-for-usr-local
bindresvport.blacklist  group        kernel         network        profile.d  rmt          subgid
cron.daily              group-       ld.so.cache    networks       protocols  rpc          subuid
debconf.conf            gshadow      ld.so.conf     nginx          rc0.d      securetty    systemd
debian_version          gshadow-     ld.so.conf.d   nsswitch.conf  rc1.d      security     terminfo
default                 host.conf    libaudit.conf  opt            rc2.d      selinux      timezone
deluser.conf            hostname     localtime      os-release     rc3.d      services     ucf.conf
dpkg                    hosts        login.defs     pam.conf       rc4.d      shadow       update-motd.d
```

*References*

- [design doc](https://github.com/kubernetes/community/blob/b7c4abc6fdb962785654ca50c26dc982bf87ea04/contributors/design-proposals/propagation.md)
- [concept](https://kubernetes.io/docs/concepts/storage/volumes/#mount-propagation)
- https://medium.com/kokster/kubernetes-mount-propagation-5306c36a4a2d

*Update on 06/21/2017, v1.6, design*

The above proposal has a problem: it makes too many hostPath shared mounts. In reality, user may
just want only one hostPath to be shared mount, and leave all other hostPath untouched. Futher, for
component like kubelet, you can't simply make mount like `/etc` shared, since that will shadow host'
`/etc`.

The API was later changed to a 'mountPropagation' field in Container.volumeMounts, with values:
None, HostToContainer and Bidirectional.

*References*

- [design doc](https://github.com/kubernetes/community/blob/d3879c1610516ca26f2d6c5e1cd3f4d392fb35ec/contributors/design-proposals/node/propagation.md)
- https://github.com/kubernetes/community/pull/659

*Update on 03/07/2018, v1.10, beta*

Mount namespace propagation is promoted to beta. This feature allows a container to mount a volume
as rslave so that host mounts can be seen inside the container, or as rshared so that any mounts
from inside the container are reflected in the host's mount namespace. The default for this feature
is rslave. Note the API follows previous changed design, i.e. a 'mountPropagation' field in
Container.volumeMounts.

## volume hostpath qualifiers

*Date: 06/07/2017, v1.6, design*

This is to solve the problem where if using host path in a pod and the host path doesn't exist,
docker will create the path. However, we might want more semantics, e.g. fail the pod if the path
doesn't exist, fail the pod if it exists but is not a block device, etc. The problem this proposal
is trying to solve is simple to understand, but pay attention to how it articulates various options
and concerns.

*References*

- [desing doc](https://github.com/kubernetes/community/blob/3853b8d5bcc42314c446620eba42c6e9b9c3ac41/contributors/design-proposals/volume-hostpath-qualifiers.md)

## volume mount options

*Date: 06/24/2018, v1.10, ga*

The proposal allows PV to specify mount options, which will be used by kubelet (for in-tree
plugins) to mount volume:

```
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv0003
spec:
  capacity:
    storage: 5Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Recycle
  mountOptions:
    - hard
    - nolock
    - nfsvers=3
  nfs:
    path: /tmp
    server: 172.17.0.2
```

One can also add mount option in StorageClass and the options will be added to dynamically
provisioned persistent volume:

```
kind: StorageClass
apiVersion: storage.k8s.io/v1
metadata:
  name: slow
provisioner: kubernetes.io/glusterfs
parameters:
  type: gp2
  mountOptions: "auto_mount"
```

While mount options enable more flexibility in how volumes are mounted, it can result in user
specifying options that are not supported or are known to be problematic when using inline volume
specs. Thus mountOptions as an API parameter will not be supported for inline volume specs.

## volume snapshot

*Date: 06/16/2017, v1.7, design*

The volume snapshot provides an API for users to issue snapshot request; all real snapshots operations
are done in plugins. There are two components here: a controller and a provisioner. The controllers
syncs actual state of world and desired state of world, which includes creating snapshot, deleting
snapshot. The provisioner is no different than other external provisioners (like nfs), except that
it accepts an annotation which specifies from which snapshot to create the volumes. This external
provisioner is a temporary solution before kubernetes fully supports snapshot. Once kubernetes
natively supports snapshot, it's likely there will be a new field in PVC: pvc.spec.fromSnapshot, and
existing volume plugins will be updated to indicate whether snapshot is supported.

*References*

- https://github.com/kubernetes-incubator/external-storage/pull/197
- https://github.com/rootfs/snapshot

*Update on 06/23/2018, v1.10, design*

Snapshot design and development now happen in external-storage repository. Two API objects are
proposed: `VolumeSnapshot` and `VolumeSnapshotData`; their relationship is similar to `PersistentVolumeClaim`
and `PersistentVolume`, that is, VolumeSnapshot represents a request to create snapshot and
VolumeSnapshotData holds the actual snapshot. On the other hand, VolumeSnapshot is namespaced and
VolumeSnapshotData is not. The overall workflow is:
- Start VolumeSnapshot controller and provisioner. The controller will craete VolumeSnapshot and
  VolumeSnapshotData using CRDs. Controller is responsible to create snapshot and provisioner is
  responsible to create volume based on snapshot.
- Create PV & PVC, make sure they are bound.
- Create VolumeSnapshot to request creating snapshot. The VolumeSnapshot must have a reference to
  the above PVC.
- After a while, controller finishes snapshot creation operation, then creates a VolumeSnapshotData
  object in API server. The VolumeSnapshotData has a reference to VolumeSnapshot as well as PVC;
  and user-created VolumeSnapshot is updated to reference the VolumeSnapshotData.
- At this point, snapshot operation is done. If we want to restore the snapshot, we need to create
  a StorageClass with the above provisioner. The create a PVC with annotation `snapshot.alpha.kubernetes.io/snapshot`
  with value set to the name of VolumeSnapshot. Once created, provisioner will create a PV using
  our snapshot.
- To delete snapshot, just delete VolumeSnapshot, the associated VolumeSnapshotData will be
  automatically deleted.

*References*

- [design doc](https://github.com/kubernetes-incubator/external-storage/blob/c0eb404503535ae313eb0acfcf9d14716333fbce/snapshot/doc/volume-snapshotting-proposal.md)
- [user guide](https://github.com/kubernetes-incubator/external-storage/blob/c0eb404503535ae313eb0acfcf9d14716333fbce/snapshot/doc/user-guide.md)
- [example](https://github.com/kubernetes-incubator/external-storage/blob/c0eb404503535ae313eb0acfcf9d14716333fbce/snapshot/doc/examples/hostpath/README.md)

## containerized mounter pod

*Date: 05/23/2017, v1.6, design*

Note this is not merged as of writing. The goal of this proposal is to allow kubernetes to
provision/attach/mount/unmount/detach/delete volumes in pod instead of on the host. For example,
currently, to mount a glusterfs volumes, we do all the setup on host (kubelet mounts everything);
but in certain os, such tools are not available.

The proposal aims to address this to allow pod to do all the work; so it is not a requirement to
have `mout.glusterfs` utility on host; rather, a daemonset pod contains the utility and will be
called via kubelet when mount/unmount, etc. For this to work properly, daemonset pod must be ran in
privileged mode, and certain directories (notably `/var/lib/kubelet`) must have 'shared' mount
propagation.

*References*

- [design doc](https://github.com/kubernetes/community/blob/eb4ec5c9c3d978eded6a3a303c69b8e002c085a2/contributors/design-proposals/storage/containerized-mounter-pod.md)
- https://github.com/kubernetes/community/pull/589

*Update on 06/24/2018, v1.10, design*

NOTE: As we expect that most volume plugins are going to be moved to CSI soon, all implementation of
this proposal will be guarded by alpha feature gate `MountContainers` which is never going leave
alpha. Whole implementation of this proposal is going to be removed when the plugins are fully moved
to CSI. With CSI, all mount/umount operations are handled in CSI driver.

## local volume management

*Date: 05/12/2017, v1.6, design*

**Proposal**

The proposal is an umbrella discussion about local volume management, including local ephemeral
storage, local persistent storage, log management, etc. Many of the contents are detailed in other
proposals.

**Useful dicsussions**

- https://github.com/kubernetes/community/pull/306#discussion_r98563618
- https://github.com/kubernetes/community/pull/306#discussion_r98578689
- https://github.com/kubernetes/community/pull/306#discussion_r98581788
- https://github.com/kubernetes/community/pull/306#discussion_r98582959
- https://github.com/kubernetes/community/pull/306#discussion_r99013874
- https://github.com/kubernetes/community/pull/306#discussion_r99372140
- https://github.com/kubernetes/community/pull/306#discussion_r99466735
- https://github.com/kubernetes/community/pull/306#discussion_r99982706
- https://github.com/kubernetes/community/pull/306#discussion_r99983006
- https://github.com/kubernetes/community/pull/306#discussion_r99983733
- https://github.com/kubernetes/community/pull/306#discussion_r100532545
- https://github.com/kubernetes/community/pull/306#discussion_r100663643
- https://github.com/kubernetes/community/pull/306#discussion_r101708608
- https://github.com/kubernetes/community/pull/306#discussion_r108078873
- https://github.com/kubernetes/community/pull/306#discussion_r109041116
- https://github.com/kubernetes/community/pull/306#discussion_r109095715
- https://github.com/kubernetes/community/pull/306#discussion_r109225341
- https://github.com/kubernetes/community/pull/306#discussion_r109965401
- https://github.com/kubernetes/community/pull/306#issuecomment-291944844
- https://github.com/kubernetes/community/pull/306#discussion_r111440816

**Unread discussions**

- https://github.com/kubernetes/community/pull/306#discussion_r98592676
- https://github.com/kubernetes/community/pull/306#discussion_r99467132

**Unapprehended discussions**

- https://github.com/kubernetes/community/pull/306#discussion_r109039478

**Terminologies**

- inline PV: inline PV is just like emptyDir, which has the same lifecycle as a Pod (therefore not
  actually persistent). inline PV is outlined in this proposal because emptyDir is created under
  primary partition (/var/lib/kubelet), but is often used to IO intensive workload. inline PV, on
  the other hand, is created under secondary partition; therefore, we can protect primary partition
  from overwhelming IOs.

*References*

- [design doc](https://github.com/kubernetes/community/blob/master/contributors/design-proposals/storage/local-storage-pv.md)
- https://github.com/kubernetes/community/pull/306
- https://github.com/kubernetes/kubernetes/issues/30799
- https://github.com/kubernetes/kubernetes/issues/7562

## local storage capacity isolation

*Date: 05/23/2017, v1.6, design*

**Overview**

As of kubernetes 1.7-alpha, local volume capacity isolation will be enforced on emptyDir and overlay.
For emptyDir, kubelet retrieves volume usage from cadvisor, and for each pod's emptyDir, kubelet
checks with its sizeLimit and evict the pod if any of the volume exceeds its limit. For overlay,
kubelet also uses information from cadvisor, but this time evict pod based on its `containerStat.Rootfs`,
which is defined as ContainerStats. As can be seen from the comment, this overlay/rootfs is actually
defined as pod's writable layer.

```go
// ContainerStats holds container-level unprocessed sample stats.
type ContainerStats struct {
  // Reference to the measured container.
  Name string `json:"name"`
  // The time at which data collection for this container was (re)started.
  StartTime metav1.Time `json:"startTime"`
  // Stats pertaining to CPU resources.
  // +optional
  CPU *CPUStats `json:"cpu,omitempty"`
  // Stats pertaining to memory (RAM) resources.
  // +optional
  Memory *MemoryStats `json:"memory,omitempty"`
  // Stats pertaining to container rootfs usage of filesystem resources.
  // Rootfs.UsedBytes is the number of bytes used for the container write layer.
  // +optional
  Rootfs *FsStats `json:"rootfs,omitempty"`
  // Stats pertaining to container logs usage of filesystem resources.
  // Logs.UsedBytes is the number of bytes used for the container logs.
  // +optional
  Logs *FsStats `json:"logs,omitempty"`
  // User defined metrics that are exposed by containers in the pod. Typically, we expect only one container in the pod to be exposing user defined metrics. In the event of multiple containers exposing metrics, they will be combined here.
  // +patchMergeKey=name
  // +patchStrategy=merge
  UserDefinedMetrics []UserDefinedMetric `json:"userDefinedMetrics,omitmepty" patchStrategy:"merge" patchMergeKey:"name"`
}
```

**Implementation**

In PR #44758, a new field 'sizeLimit' is added to EmptyDirVolumeSource, also two resource type are
added (name can change):
```go
ResourceStorageOverlay ResourceName = "storage.kubernetes.io/overlay"
ResourceStorageScratch ResourceName = "storage.kubernetes.io/scratch"
```

In PR #45686, eviction based on emptyDir and and overlay is added. For emptyDir, if size of emptyDir
used by pod is larger than `sizeLimit`, then kubelet evicts the pod. Usage stats is retrieved from
cadvisor. For overlay, the workflow is the same. The overlay eviction is based on limit, not request
(specifying overlay limit is the same as cpu and memory), e.g.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-limit
spec:
  containers:
  - name: nginx
    image: nginx:1.13
    resources:
      limits:
        storage.kubernetes.io/overlay: 128Mi
```

In PR #46456, local storage allocatable is added. As mentioned in disk accounting, overlay is calculated
from imageFs (if there is dedicated one); for docker, this is `/var/lib/docker`; the resource name is
`storage.kubernetes.io/overlay`, scratch is calculated from rootFs, and this is `/var/lib/kubelet`; the
resource name is `storage` (it's not the above `storage.kubernetes.io/scratch`).

```go
rootfs, err := kl.GetCachedRootFsInfo()
if err != nil {
  node.Status.Capacity[v1.ResourceStorage] = resource.MustParse("0Gi")
} else {
  for rName, rCap := range cadvisor.StorageScratchCapacityFromFsInfo(rootfs) {
    node.Status.Capacity[rName] = rCap
  }
}

if hasDedicatedImageFs, _ := kl.HasDedicatedImageFs(); hasDedicatedImageFs {
  imagesfs, err := kl.ImagesFsInfo()
  if err != nil {
    node.Status.Capacity[v1.ResourceStorageOverlay] = resource.MustParse("0Gi")
  } else {
    for rName, rCap := range cadvisor.StorageOverlayCapacityFromFsInfo(imagesfs) {
      node.Status.Capacity[rName] = rCap
    }
  }
}

scratchSpaceRequest := podRequest.StorageScratch
if allocatable.StorageOverlay == 0 {
  scratchSpaceRequest += podRequest.StorageOverlay
  //scratchSpaceRequest += nodeInfo.RequestedResource().StorageOverlay
  nodeScratchRequest := nodeInfo.RequestedResource().StorageOverlay + nodeInfo.RequestedResource().StorageScratch
  if allocatable.StorageScratch < scratchSpaceRequest+nodeScratchRequest {
    predicateFails = append(predicateFails, NewInsufficientResourceError(v1.ResourceStorageScratch, scratchSpaceRequest, nodeScratchRequest, allocatable.StorageScratch))
  }

} else if allocatable.StorageScratch < scratchSpaceRequest+nodeInfo.RequestedResource().StorageScratch {
  predicateFails = append(predicateFails, NewInsufficientResourceError(v1.ResourceStorageScratch, scratchSpaceRequest, nodeInfo.RequestedResource().StorageScratch, allocatable.StorageScratch))
}
if allocatable.StorageOverlay > 0 && allocatable.StorageOverlay < podRequest.StorageOverlay+nodeInfo.RequestedResource().StorageOverlay {
  predicateFails = append(predicateFails, NewInsufficientResourceError(v1.ResourceStorageOverlay, podRequest.StorageOverlay, nodeInfo.RequestedResource().StorageOverlay, allocatable.StorageOverlay))
}
```

*References*

- https://github.com/kubernetes/kubernetes/pull/44785
- https://github.com/kubernetes/kubernetes/pull/45686
- https://github.com/kubernetes/kubernetes/pull/46456

*Update on 03/07/2018, v1.10, beta*

The feature is promoted to beta at Kubernetes 1.10. Due to the complexity of supporting various
runtime setup, Kubernetes now only supports root partition, i.e. `/var/lib/kubelet`. The resource
name is "ephemeral-storage".

Ephemeral storage behaves just like other resources like cpu, memory. Kubelet reports total available
ephemeral storage and scheduler will do request/limit counting; if sum of all requests exceed
allocatable ephemeral storage, pod will stay pending. Kubelet checks three resource levels:
- emptydir size limit
- limit of each container
  - for shared partition, this is logs and container rootfs
  - for separate partition, this is only logs
- limit of pod
  - for shared partition, this is logs, emptydir and container rootfs
  - for separate partition, this is logs and emptydir

## local persistent volume

*Date: 05/23/2017, v1.6, design*

The overall goal of the proposal is to support local storage as persistent volume, for use cases like
distributed filesystems and databases, caching, etc.

- [design doc](https://github.com/kubernetes/community/blob/eb4ec5c9c3d978eded6a3a303c69b8e002c085a2/contributors/design-proposals/storage/local-storage-pv.md)

*Update on 06/23/2018, v1.10, beta*

The feature is promoted to beta at Kubernetes 1.10.

## raw block consumption in kubernetes

*Date: 07/01/2018, v1.11, alpha*

For alpha version, API changes include:
- a new 'VolumeMode' field in PV and PVC object
- a new 'VolumeDevices' field in Pod object

```yaml
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: myclaim
spec:
  storageClassName: local-fast
  volumeMode: Block
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 80Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: my-db
spec:
    containers:
    - name: mysql
      image: mysql
      volumeDevices:
      - name: my-db-data
        devicePath: /dev/xvda
    volumes:
    - name: my-db-data
      persistentVolumeClaim:
        claimName: raw-pvc
```

There is no API change in StorageClass, but it can be naturally extended to support block device.
kubelet implementation is similar to fs mounts, i.e. for filesystem, kubelet maintains the following
path:
```
Global mount path, e.g. var/lib/kubelet/plugins/kubernetes.io/{pluginName}/{volumePluginDependentPath}
Volume mount path, e.g. var/lib/kubelet/pods/{podUID}/volumes/{escapeQualifiedPluginName}/{volumeName}
```

The purpose of those mount points are that Kubernetes manages volume attach/detach status using
these mount points and number of references to these mount points. Similarly, for raw block device,
Kubelet also needs to do such management; but unlike filesystem, block volume doesn't have filesystem
thus can't be mounted. Instead, Kubelet creates a new symbolic link under the new global map path when
volume is attached to a Pod. Number of symbolic links are equal to the number of Pods which use the
same volume. Kubelet needs to manage both creation and deletion of symbolic links under the global
map path:
```
Global path: `/var/lib/kubelet/plugins/kubernetes.io/{pluginName}/volumeDevices/{volumePluginDependentPath}/{podUID}
Volume path: `/var/lib/kubelet/pods/{podUID}/volumeDevices/{escapeQualifiedPluginName}/{volumeName}
```

- [design doc](https://github.com/kubernetes/community/blob/bfebfa4d7b0c7469f5e1b9c89fe77e2469a43a84/contributors/design-proposals/storage/raw-block-pv.md)
- https://github.com/kubernetes/features/issues/351

## volume topology-aware scheduling

*Date: 03/07/2018, v1.10, beta*

This feature enables you to specify topology constraints on PersistentVolumes and have those
constraints evaluated by the scheduler. It also delays the initial PersistentVolumeClaim binding
until the Pod has been scheduled so that the volume binding decision is smarter and considers all
Pod scheduling constraints as well.

At the moment, this feature is most useful for local persistent volumes, but support for dynamic
provisioning is under development. This volume topology aware scheduling design is used mostly to
complement local storage, to make scheduler aware of volume topology; previously, PV&PVC
binding/unbinding is independent of scheduler.

Following is a rough summary:
- PersistentVolume object will be extended with a new `NodeAffinity` field of type `VolumeNodeAffinity`
  that specifies the constraints. It will closely mirror the existing NodeAffinity type used by
  Pods, but we will use a new type so that we will not be bound by existing and future Pod
  `NodeAffinity` semantics.
- A new StorageClass field `BindingMode` will be added to control the volume binding behavior.
  Available modes are `Immediate` and `WaitForFirstConsumer`. StorageClass will be required to get
  the new binding behavior, even if dynamic provisioning is not used (in the case of local storage).
  For the new behavior `WaitForFirstConsumer`, both binding decisions of:
  - Selecting a precreated PV with NodeAffinity
  - Dynamically provisioning a PV with NodeAffinity
  will be considered by the scheduler, so that all of a Pod's scheduling constraints can be evaluated
  at once, i.e. both binding and provisioning will be delayed.
- Bound PVC enforcement will be done in scheduler predicate as well as kubelet admission.
- To make dynamic provisioning aware of pod scheduling decisions, delayed volume binding must also
  be enabled. The scheduler will pass its selected node to the dynamic provisioner, and the provisioner
  will create a volume in the topology domain that the selected node is part of. The selected node is
  passed in via annotation 'annSelectedNode'.
- For the common use case, volumes will be provisioned in whatever topology domain the scheduler has
  decided is best to run the workload. Users may impose further restrictions by setting label/node
  selectors, and pod affinity/anti-affinity policies on their Pods. All those policies will be taken
  into account when dynamically provisioning a volume. While less common, administrators may want to
  further restrict what topology domains are available to a StorageClass. To support these administrator
  policies, an `AllowedTopology` field can also be specified in the StorageClass to restrict the
  topology domains for dynamic provisioning.
- There are no plans to bind multiple PVCs in one transaction. Since the scheduler is serialized, a
  partial binding failure should be a rare occurrence and would only be caused if there is a user or
  other external entity also trying to bind the same volumes.

Following is comment from scheduler_binder.go:
```go
// SchedulerVolumeBinder is used by the scheduler to handle PVC/PV binding
// and dynamic provisioning.  The binding decisions are integrated into the pod scheduling
// workflow so that the PV NodeAffinity is also considered along with the pod's other
// scheduling requirements.
//
// This integrates into the existing default scheduler workflow as follows:
// 1. The scheduler takes a Pod off the scheduler queue and processes it serially:
//    a. Invokes all predicate functions, parallelized across nodes.  FindPodVolumes() is invoked here.
//    b. Invokes all priority functions.  Future/TBD
//    c. Selects the best node for the Pod.
//    d. Cache the node selection for the Pod. (Assume phase)
//       i.  If PVC binding is required, cache in-memory only:
//           * Updated PV objects for prebinding to the corresponding PVCs.
//           * For the pod, which PVs need API updates.
//           AssumePodVolumes() is invoked here.  Then BindPodVolumes() is called asynchronously by the
//           scheduler.  After BindPodVolumes() is complete, the Pod is added back to the scheduler queue
//           to be processed again until all PVCs are bound.
//       ii. If PVC binding is not required, cache the Pod->Node binding in the scheduler's pod cache,
//           and asynchronously bind the Pod to the Node.  This is handled in the scheduler and not here.
// 2. Once the assume operation is done, the scheduler processes the next Pod in the scheduler queue
//    while the actual binding operation occurs in the background.
```

*References*

- [design doc](https://github.com/kubernetes/community/blob/e208e4dc74e690ea9c7d82cb67acece5f1f665fc/contributors/design-proposals/storage/volume-topology-scheduling.md)

*Update on 06/23/2018, v1.10, beta*

The feature is promoted to beta at Kubernetes 1.10.

## growing persistent volume

*Date: 07/16/2017, v1.7, design*

To use the feature, user is required to update PVC size (pvc.spec.resources.requests.storage), which
is previously an immutable field. Once the field is updated, a volume expand controller will perform
the expansion operation, calling specific plugin, which should implement `ExpandableVolumePlugin`
interface. To give admin control over volume expansion, a new field called `AllowVolumeExpand` will
be added to StorageClass.

Below is a few uesful discussions:
- How does resize work with external provisioner?
- How resize works for flex volume and local storage?
- Resize is triggered from PVC update, this delegates control to normal user, i.e. admin cannot control resize, is this the right model?
- Filesystem resize is required from kubelet, but how does kubelet know fs type?
- If underline device resize succeeds, but what if fs resize continuously fail?
- There is a force detach in attach/detach controller, what if force detach happens (pod is deleted) during FSResize? This could result in data corruption.
- https://github.com/kubernetes/community/pull/657#issuecomment-317064697

*References*

- [design doc](https://github.com/kubernetes/community/blob/eb4ec5c9c3d978eded6a3a303c69b8e002c085a2/contributors/design-proposals/storage/grow-volume-size.md)

*Update on 03/07/2018, v1.10, alpha*

Offline persistent volume resize is alpha in v1.9 and v1.10. Two related proposals are proposed: one
is online persistent volume resize, the other is flex volume resize support.
- https://github.com/kubernetes/community/pull/1535
- https://github.com/kubernetes/community/pull/1700

*Update on 12/10/2018, v1.13*

Offline resize: beta; online resize: alpha
- https://kubernetes.io/blog/2018/07/12/resizing-persistent-volumes-using-kubernetes/

## volume operation metrics

*Date: 03/07/2018, v1.10, ga*

Kubernetes 1.10 brings to general availability detailed metrics of what's going in inside the storage
systems, including metrics such as mount and unmount time, number of volumes in a particular state,
and number of orphaned pod directories. The metrics are exposed in prometheus format. The metrics
will be emitted using Prometheus format and available for collection from `/metrics` HTTP endpoint
of kubelet and controller-manager.

*References*

- [design doc](https://github.com/kubernetes/community/blob/e208e4dc74e690ea9c7d82cb67acece5f1f665fc/contributors/design-proposals/storage/volume-metrics.md)
- [cloudprovide storage metrics](https://github.com/kubernetes/community/blob/e208e4dc74e690ea9c7d82cb67acece5f1f665fc/contributors/design-proposals/cloud-provider/cloudprovider-storage-metrics.md)
- https://docs.google.com/document/d/1Fh0T60T_y888LsRwC51CQHO75b2IZ3A34ZQS71s_F0g

## exposing storage (pv/pvc) metrics via kubelet

*Date: 02/09/2017, v1.7, design*

As mentioned in 'disk accounting' section, kubelet exposes API endpoints for stats on a node, e.g.
```
https://localhost:10250/stats/summary
```

The data structure for the endpoint is:

```go
// Summary is a top-level container for holding NodeStats and PodStats.
type Summary struct {
  // Overall node stats.
  Node NodeStats `json:"node"`
  // Per-pod stats.
  Pods []PodStats `json:"pods"`
}
```

NodeStats holds node-level unprocessed sample stats, e.g. CPU, Network stats. PodStats holds pod-level
unprocessed sample stats, including its containers, volumes, etc.

```go
// PodStats holds pod-level unprocessed sample stats.
type PodStats struct {
  // Reference to the measured Pod.
  PodRef PodReference `json:"podRef"`
  // The time at which data collection for the pod-scoped (e.g. network) stats was (re)started.
  StartTime metav1.Time `json:"startTime"`
  // Stats of containers in the measured pod.
  // +patchMergeKey=name
  // +patchStrategy=merge
  Containers []ContainerStats `json:"containers" patchStrategy:"merge" patchMergeKey:"name"`
  // Stats pertaining to network resources.
  // +optional
  Network *NetworkStats `json:"network,omitempty"`
  // Stats pertaining to volume usage of filesystem resources.
  // VolumeStats.UsedBytes is the number of bytes used by the Volume
  // +optional
  // +patchMergeKey=name
  // +patchStrategy=merge
  VolumeStats []VolumeStats `json:"volume,omitempty" patchStrategy:"merge" patchMergeKey:"name"`
}

// VolumeStats contains data about Volume filesystem usage.
type VolumeStats struct {
  // Embedded FsStats
  FsStats
  // Name is the name given to the Volume
  // +optional
  Name string `json:"name,omitempty"`
}
```

However, the volume stats only contain volume name; there's no way of finding the desired metrics of
a PVC. Therefore, the proposal adds a reference field so we'll be able to see metrics of a PVC.

```go
// VolumeStats contains data about Volume filesystem usage.
type VolumeStats struct {
  // Embedded FsStats
  FsStats
  // Name is the name given to the Volume
  // +optional
  Name string `json:"name,omitempty"`
  // Reference to the PVC, if one exists
  // +optional
  PVCRef *PVCReference `json:"pvcRef,omitempty"`
}
```

Once we have the information, we can register the metrics in prometheus.

*References*

- https://github.com/kubernetes/kubernetes/pull/51553
- https://github.com/kubernetes/features/issues/363

## csi volume plugin

*Date: 02/28/2018, v1.9, alpha*

**Architecture**

Below is a reference architecture suggested by Kubernetes team; the actual architecture or deployment
strategy depends on admin. For example, in an extreme case, a single node cluster, all components can
ben ran in a single pod.
- A statefulset of size '1' with csi driver (from vendor), external provisioner (from kubernetes team)
  and external attacher (from kubernetes team). The three containers run in a Pod, and external
  provisioner/attacher communicate with the csi driver via unix socket, which is defined in csi
  specification. The socket can be mounted as hostpath or emptydir. All in all, the statefulset
  facilitates communication with the Kubernetes controllers, and is tasked to provision and attach
  volumes of respective driver.
- A deamonset with csi driver (from vendor), kubernetes csi helper (from kubernetes team). The
  daemonset facilitates communication with Kubelet.
- Kubelet runs on every node and is responsible for making csi calls, i.e. `NodePublishVolume` and
  `NodeUnpublishVolume`. Kubelet directly makes the call to csi driver; the driver is registered
  from csi helper, i.e. put a socket under a well-known path for kubelet to discover.

*References*

- [design doc](https://github.com/kubernetes/community/blob/9905391eee5ccc0afccd01001fc0abd2e70a4ca6/contributors/design-proposals/storage/container-storage-interface.md)

**Workflow**

For a complete workflow, see [walkthrough section in design doc](https://github.com/kubernetes/community/blob/9905391eee5ccc0afccd01001fc0abd2e70a4ca6/contributors/design-proposals/storage/container-storage-interface.md#example-walkthrough)

**Component: external provisioner**

[csi external provisioner](https://github.com/kubernetes-csi/external-provisioner) is a sidecar
container that watches Kubernetes PersistentVolumeClaim objects and triggers CreateVolume/DeleteVolume
against a CSI endpoint. It is basically a bridge between Kubernetes API and csi API, i.e. from
'PV, PVC, SC' to 'CreateVolume, DeleteVolume' call.

The external provisioner container runs in a statefulset, which also contains a csi driver container.

**Component: external attacher**

[csi external attacher](https://github.com/kubernetes-csi/external-attacher) is a sidecar container
that watches the new Kubernetes `VolumeAttachment` objects and triggers ControllerPublish/Unpublish
against a CSI endpoint. It is basically a bridge between Kubernetes API and csi API, i.e. from
'PV, Node, VA' to 'Attach/Detach' call. The

VolumeAttachment is created/deleted via Kubelet in-tree csi volume plugin. Attacher is much more
complex than provisioner; it deals with concurrency and has more API calls to csi to find volume
capabilities. Note, even though this is called the external attacher, its function is to call the
CSI API calls ControllerPublish and ControllerUnpublish. These calls most likely will occur in a
node which is not the one that will mount the volume. For this reason, many CSI drivers do not
support these calls, instead doing the attach/detach and mount/unmount both in the CSI NodePublish
and NodeUnpublish calls done by the kubelet at the node which is supposed to mount.

**Component: driver registrar**

[csi driver registrar](https://github.com/kubernetes-csi/driver-registrar) is a sidecar container that
- registers the CSI driver with kubelet
- adds the drivers custom NodeId to a label on the Kubernetes Node API Object.

For alpha, kubelet locates driver at `/var/lib/kubelet/plugins/[SanitizedCSIDriverName]/csi.sock`

The mechanism is mentioned in [kubelet-to-csi-driver-communication section](https://github.com/kubernetes/community/blob/9905391eee5ccc0afccd01001fc0abd2e70a4ca6/contributors/design-proposals/storage/container-storage-interface.md#kubelet-to-csi-driver-communication).

**Related CSI calls**

- CreateVolume/DeleteVolume: This RPC will be called by Kubernetes to provision a new volume on
  behalf of a user (to be consumed as either a block device or a mounted filesystem). DeleteVolume
  is a reverse of CreateVolume.
- ControllerPublishVolume/ControllerUnPublishVolume: Think of attach/detach. ControllerPublishVolume
  RPC will be called by Kubernetes when it wants to place a workload that uses the volume onto a
  node. The Plugin SHOULD perform the work that is necessary for making the volume available on the
  given node. The Plugin MUST NOT assume that this RPC will be executed on the node where the volume
  will be used. ControllerUnPublishVolume RPC is a reverse of ControllerPublishVolume.
- NodePublishVolume/NodeUnpublishVolume: Think of mount/umount. NodePublishVolume is called by
  Kubernetes when a workload that wants to use the specified volume is placed (scheduled) on a node.
  The Plugin SHALL assume that this RPC will be executed on the node where the volume will be used.
  NodePublishVolumeRequest contains a `target_path` at where the Plugin MUST make the volume
  available. NodeUnPublishVolume RPC is a reverse of NodePublishVolume.

*References*

- https://github.com/kubernetes-csi
- https://kubernetes-csi.github.io
- http://blog.kubernetes.io/2018/01/introducing-container-storage-interface.html

*Update on 03/07/2018, v1.10, beta*

The feature is promoted to beta at Kubernetes 1.10 release.

## storage object in use protection

*Date: 03/07/2018, v1.10, beta*

The feature contains two folds:
- Prevent deletion of Persistent Volume Claims that are used by a pod (beta)
- Prevent deletion of Persistent Volume that is bound to a Persistent Volume Claim (beta)

In previous versions of Kubernetes it was possible to delete storage that is in use by a pod, causing
massive problems for the pod. These features provide validation that prevents that from happening.
- For PVC protection, a new pvc protection controller is added which adds itself to PVC's finalizer.
  If a delete event happens and PVC is used by a Pod, pvc protection controller will do nothing
  (thus preventing the PVC from being deleted and PVC stays in 'Terminating' status); otherwise if
  PVC is not used by a pod, then pvc protection controller will remove the finalizer.
- For PV protection, a new pv protection controller is added which adds itself to PV's finalizer.
  If a delete event happens and PV is still bound to PVC, pv protection controller will do nothing
  (thus preventing the PV from being deleted and PV stays in 'Terminating' status); otherwise if PV
  is not bound, then pv protection controller will remove the finalizer.

*References*

- [design doc](https://github.com/kubernetes/community/blob/eb4ec5c9c3d978eded6a3a303c69b8e002c085a2/contributors/design-proposals/storage/postpone-pv-deletion.md)

## pod safety

*Date: 07/26/2018, v1.11, design*

**Overview**

The proposal discusses the pod execution guarantees, in what cases a cluster partition happens and
how to prevent/fix the partition.

**Background**

First off, a bit of background about pod execution and deletion.
- Pod termination is divided into the following steps:
  - A component requests the termination of the pod by issuing a DELETE to the pod resource with an
    optional grace period
    - If no grace period is provided, the default from the pod is leveraged
    - When the kubelet observes the deletion, it starts a timer equal to the grace period and performs
      the following actions:
      - Executes the pre-stop hook, if specified, waiting up to grace period seconds before continuing
      - Sends the termination signal to the container runtime (SIGTERM or the container image's STOPSIGNAL on Docker)
      - Waits 2 seconds, or the remaining grace period, whichever is longer
      - Sends the force termination signal to the container runtime (SIGKILL)
  - Once the kubelet observes the container is fully terminated, it issues a status update to the
    REST API for the pod indicating termination, then issues a DELETE with grace period = 0.
- Deleting a pod with grace period 0 is called force deletion and will update the pod with a
  `deletionGracePeriodSeconds` of 0, and then immediately remove the pod from etcd. Because all
  communication is asynchronous, force deleting a pod means that the pod processes may continue to
  run for an arbitrary amount of time. If a higher level component like the StatefulSet controller
  treats the existence of the pod API object as a strongly consistent entity, deleting the pod in
  this fashion will violate the at-most-one guarantee we wish to offer for StatefulSet.
- ReplicaSets and ReplicationControllers both attempt to preserve availability of their constituent
  pods over ensuring at most one (of a pod) semantics. So a replica set to scale 1 will immediately
  create a new pod when it observes an old pod has begun graceful deletion, and as a result at many
  points in the lifetime of a replica set there will be 2 copies of a pod's processes running
  concurrently. Only access to exclusive resources like storage can prevent that simultaneous
  execution. As described above, it is not safe to use persistent volumes that lack RWO guarantees
  with a replica set or deployment, even at scale 1.

**Goal**

This proposal covers the changes necessary to ensure:
- StatefulSet can ensure at most one semantics for each individual pet
- Other system components such as the node and namespace controller can safely perform their responsibilities without violating that guarantee
- An administrator or higher level controller can signal that a node partition is permanent, allowing the StatefulSet controller to proceed
- A fencing controller can take corrective action automatically to heal partitions

We will accomplish this by:
- Clarifying which components are allowed to force delete pods (as opposed to merely requesting termination)
- Ensuring system components can observe partitioned pods and nodes correctly
- Defining how a fencing controller could safely interoperate with partitioned nodes and pods to safely heal partitions
- Describing how shared storage components without innate safety guarantees can be safely shared on the cluster.

**Proposed changes**

- Avoid multiple instances of pods: a couple Kubernetes components are to be changed with regard to
  managing pods. For example, all existing controllers must be changed to only signal pod termination,
  and are not allowed to force delete pods.
- Fencing: a fencing controller is proposed to take actions in care of partition. It leverages a
  couple external APIs like cloud provider control plane, Hardware IPMI interface, etc.
- Storage Consistency: scheduler and kubelet must be aware of RWO volume and make sure a RWO volume
  can not be used by two pods simultaneously. Kubelet of a newer pod must wait the other pod
  terminates, before starting the new pods.

*References*

- [design doc](https://github.com/kubernetes/community/blob/2d2feabc33402ce4c2dacbef6830198fd5ba13a3/contributors/design-proposals/storage/pod-safety.md)

## volume.subPath

*Date: 04/04/2017, v1.6*

Sometimes, it is useful to share one volume for multiple uses in a single pod. The `volumeMounts.subPath`
property can be used to specify a sub-path inside the referenced volume instead of its root. Here is
an example of a pod with a LAMP stack (Linux Apache Mysql PHP) using a single, shared volume. The HTML
contents are mapped to its html folder, and the databases will be stored in its mysql folder:


```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-lamp-site
spec:
    containers:
    - name: mysql
      image: mysql:5.7
      volumeMounts:
      - mountPath: /var/lib/mysql
        name: site-data
        subPath: mysql
    - name: php
      image: php:7.2
      volumeMounts:
      - mountPath: /var/www/html
        name: site-data
        subPath: html
    volumes:
    - name: site-data
      persistentVolumeClaim:
        claimName: my-lamp-site-data
```

## flexvolume and dynamic flexvolume design

*Date: 10/26/2016, v1.4*

flexvolume is just another volume plugin, similar to gce, nfs, etc. During volume probe, a directory
is searched to find volume plugins, default path is `/usr/libexec/kubernetes/kubelet-plugins/volume/exec`.

Kubernetes defines a custom 'protocol' for communicating with the plugin (plugin is just a regular
binary). As of kubernetes 1.4, five methods needs be implemented, i.e. init, attach, detach, mount,
unmount. Eventually, flexvolume will be replaced by csi.

*Update on 10/27/2017, v1.8*

The updated proposal contains more methods: waitforattach, mountdevice, unmountdevice. Another
option, `--enable-controller-attach-detach` is introduced for the plugin to be called remotely,
e.g. calling attach method from master to attach a device to a node.

*Update on 06/24/2018, v1.10*

Adding new out-of-tree volume dynamically via flexvolume requires kubelet or controller manager
restart. To solve the problem, the proposal proposes to add a PluginProber interface which contains
Init() and Probe() methods; flexvolume will use inotify to find new volume plugin in search path.
The feature has been implemented and is superceded by csi.

*References*

- [example](https://github.com/kubernetes/kubernetes/tree/6d81e916a6c5e7c992f141018b7f262c818a638f/examples/volumes/flexvolume)
- [devel](https://github.com/kubernetes/community/blob/4377efa625d91ed8367bbc6a6672b7dff03dbd2b/contributors/devel/flexvolume.md)
- [dynamic flexvolume deployment design doc](https://github.com/kubernetes/community/blob/eb4ec5c9c3d978eded6a3a303c69b8e002c085a2/contributors/design-proposals/storage/flexvolume-deployment.md)

## disk accounting

*Date: 05/08/2017, v1.6*

**Proposal**

As of kubernetes 1.6, disk accounting has been landed in kubernetes; the above proposal is not
updated but the fundamental idea is correct. Below is a step by step analysis of the proposal, as
well as implementation based on k8s 1.7-alpha.

The proposal centers around four areas where disk can be consumed:
- Container images
- Container's writable layer
- Container's logs - when written to stdout/stderr and default logging backend in docker is used.
- Local volumes - hostPath, emptyDir, gitRepo, etc.

Then based on the four areas, the proposal discusses:
- Introduction (for every area)
- Improve disk accouting (for every area)

*References*

- [disk accounting proposal](https://github.com/kubernetes/community/blob/57d8f190f6e9c0d64af74456a13bf13f6bd45750/contributors/design-proposals/node/disk-accounting.md)
- https://github.com/kubernetes/kubernetes/issues/17331

**endpoints**

API endpoints are registered in `pkg/kubelet/server/stats/handler.go`, below is a short digest:

```console
curl -k https://localhost:10250/stats/summary
curl -k https://localhost:10250/stats/container
# first 'nginx' is pod name, second 'nginx' is container name
curl -k https://localhost:10250/stats/nginx/nginx
```

**kubelet**

In kubelet, a resource analyzer is created, which provides statistics on node resource consumption.
The resource analyzer contains a FsResourceAnalyzer and a SummaryProvider. Later in kubelet, it
starts the resource analyzer.

```go
// create a new resourceAnalyzer
klet.resourceAnalyzer = stats.NewResourceAnalyzer(klet, kubeCfg.VolumeStatsAggPeriod.Duration, klet.containerRuntime)

// Step 8: Start resource analyzer
kl.resourceAnalyzer.Start()
```

The first argument to method "NewResourceAnalyzer" receives StatsProvider: klet, short for kubelet,
see `pkg/kubelet/kubelet_cadvisor.go` for details. Basically, kubelet just delegates all the
implementation details to cadvisor.

```go
// Host methods required by stats handlers.
type StatsProvider interface {
  GetContainerInfo(podFullName string, uid types.UID, containerName string, req *cadvisorapi.ContainerInfoRequest) (*cadvisorapi.ContainerInfo, error)
  GetContainerInfoV2(name string, options cadvisorapiv2.RequestOptions) (map[string]cadvisorapiv2.ContainerInfo, error)
  GetRawContainerInfo(containerName string, req *cadvisorapi.ContainerInfoRequest, subcontainers bool) (map[string]*cadvisorapi.ContainerInfo, error)
  GetPodByName(namespace, name string) (*v1.Pod, bool)
  GetNode() (*v1.Node, error)
  GetNodeConfig() cm.NodeConfig
  ImagesFsInfo() (cadvisorapiv2.FsInfo, error)
  RootFsInfo() (cadvisorapiv2.FsInfo, error)
  ListVolumesForPod(podUID types.UID) (map[string]volume.Volume, bool)
  GetPods() []*v1.Pod
}
```

kubelet implementation of "StatsProvider" locates in `pkg/kubelet/kubelet_cadvisor.go"

**cadvisor (node disk)**

cadvisor implements an interface for kubelet to use; the interface is similar to StatsProvider. e.g.
in kubelet.ImagesFsInfo, kubelet simply calls kl.cadvisor.ImagesFsInfo().

```go
// Interface is an abstract interface for testability.
// It abstracts the interface to cAdvisor.
type Interface interface {
  Start() error
  DockerContainer(name string, req *cadvisorapi.ContainerInfoRequest) (cadvisorapi.ContainerInfo, error)
  ContainerInfo(name string, req *cadvisorapi.ContainerInfoRequest) (*cadvisorapi.ContainerInfo, error)
  ContainerInfoV2(name string, options cadvisorapiv2.RequestOptions) (map[string]cadvisorapiv2.ContainerInfo, error)
  SubcontainerInfo(name string, req *cadvisorapi.ContainerInfoRequest) (map[string]*cadvisorapi.ContainerInfo, error)
  MachineInfo() (*cadvisorapi.MachineInfo, error)
  VersionInfo() (*cadvisorapi.VersionInfo, error)
  // Returns usage information about the filesystem holding Docker images.
  ImagesFsInfo() (cadvisorapiv2.FsInfo, error)
  // Returns usage information about the root filesystem.
  RootFsInfo() (cadvisorapiv2.FsInfo, error)
  // Get events streamed through passedChannel that fit the request.
  WatchEvents(request *events.Request) (*events.EventChannel, error)
}
```

ImagesFsInfo/RootFsInfo works by passing request to cadvisor manager, located in
`vendor/github.com/google/cadvisor/manager/manager.go`. The manager is started in `cmd/kubelet/app/server.go#run`:

```go
kubeDeps.CAdvisorInterface, err = cadvisor.New(uint(s.CAdvisorPort), s.ContainerRuntime, s.RootDirectory)
```

s.CAdvisorPort, s.ContainerRuntime, s.RootDirectory are all configurations passed from user; for
defaults, see `pkg/apis/componentconfig/v1alpha1/defaults.go`. In particular, default value for
s.CAdvisorPort is 4194, s.ContainerRuntime is "docker", and default value for s.RootDirectory is
`/var/lib/kubelet`. As also discussed in "kubelet eviction" section (node.md), for a single partition
on '/', ImageFsInfo and RootFsInfo returned from cadvisor is:

```
RootFs {Device:/dev/sda4 Mountpoint:/ Capacity:237744676864 Available:196717707264 Usage:28926615552 Labels:[docker-images root] Inodes:0xc8217ed648 InodesFree:0xc8217ed650}
ImageFs {Device:/dev/sda4 Mountpoint:/ Capacity:237744676864 Available:196717707264 Usage:28926615552 Labels:[docker-images root] Inodes:0xc8217ed7a8 InodesFree:0xc8217ed7b0}
```

Below is the FsInfo type for the above output. For RootFs, what we pass to cadvisor is `/var/lib/kubelet`,
but since cadvisor only cares about fs, the RootFs for `/var/lib/kubelet` ended up to be "/". The
same case applies to ImageFs.

```
type FsInfo struct {
  // The block device name associated with the filesystem.
  Device string `json:"device"`
  // Path where the filesystem is mounted.
  Mountpoint string `json:"mountpoint"`
  // Filesystem usage in bytes.
  Capacity uint64 `json:"capacity"`
  // Bytes available for non-root use.
  Available uint64 `json:"available"`
  // Number of bytes used on this filesystem.
  Usage uint64 `json:"usage"`
  // Labels associated with this filesystem.
  Labels []string `json:"labels"`
  // Number of Inodes.
  Inodes *uint64 `json:"inodes,omitempty"`
  // Number of available Inodes (if known)
  InodesFree *uint64 `json:"inodes_free,omitempty"`
}
```

To verify, we can use a loop device and look at its output:

```
$ losetup -f
/dev/loop1
$ dd if=/dev/zero of=/tmp/store1 bs=512 count=1048576
1048576+0 records in
1048576+0 records out
536870912 bytes (537 MB, 512 MiB) copied, 1.15362 s, 465 MB/s
$ sudo losetup /dev/loop1 /tmp/store1
$ sudo mkfs.ext4 /dev/loop1
$ sudo mkdir /var/lib/kubelet
$ sudo mount -t ext4 /dev/loop1 /var/lib/kubelet
$ sudo umount /var/lib/kubelet/
$ sudo losetup -d /dev/loop1

# output:
RootFs {/dev/loop0 /var/lib/kubelet 511647744 473657344 413696 [] 0xc4210d6a98 0xc4210d6aa0}
ImagesFs {/dev/sda4 / 237744676864 194404442112 31239880704 [docker-images root] 0xc4210d6048 0xc4210d6050}
```

**cadvisor (container disk)**

For container disk information, handler calls "GetContainerInfo", which also gets passed to cadvisor;
cadvisor then returns metrics from in-memory cache. Regarding how disk information is collected, it
is an implementation detail of cadvisor.

# Workflow

## kubelet volume setup

*Date: 01/01/2015, v1.0*

**EmptyDir**

An emptyDir volume is created when a Pod is bound to a Node. It is empty when the first container
command starts. All Containers in the same pod can read and write the same files in the EmptyDir.
When a Pod is unbound, the data in the emptyDir is deleted forever.

Internally, kubelet sends requests to the emptyDir volume plugin to setup volume at a location
similar to (note the path is a normal directory, not a mountpoint):
```
/var/lib/kubelet/pods/4794c77e-7cc8-11e8-8338-2c4d54ed3845/volumes/kubernetes.io~empty-dir/myscratch
```

where:
- `/var/lib/kubelet/pods` is pre-defined path
- `4794c77e-7cc8-11e8-8338-2c4d54ed3845` is Pod UUID
- `volumes/kubernetes.io~empty-dir` is also pre-defined path
- `myscratch` is emptydir volume name

Once the path is created, kubelet passes the path as `HostPath` to container runtime to setup
container mount. Specifically, kubeGenericRuntimeManager (v1.10) is responsible to call container
runtime to pull image, create/start container, etc. kubeGenericRuntimeManager calls volume plugin
to find out the above path and passes it as `runtimeapi.Mount`; container runtime is responsible
to mount the path in host into container; in docker, it's the '-v' parameter. In container runtime,
the host path is bind-mounted into container. Using bind mounts, we can mount all, or even part of
an already-mounted filesystem to another location, and have the filesystem accessible from both
mount points at the same time.

**Persistent Volume**

The whole workflow for GCE disk is similar to emptyDir, excepts that the disk is first mounted into
a global path first, then bind mount to the above 'dir'.

## kubernetes storage components

*Date: 06/06/2017, v1.6*

**Components summary**

- PVC/PV Controller
  - Bind/Provision
  - Enforce reclaim policy: Delete/Recycle/Retain
- Attach/Detach Controller
  - Attach/Detach
- Kubelet Volume Manager
  - Attach/Detach
  - Mount/Unmount
- Volume Plugins
  - Storage provider specific logic

**Volume plugins**

All volume plugins locate at `kubernetes/pkg/volume`. Volume plugins must implement Mounter/Unmounter
interface, and optionally Attacher, Detacher, Provisioner, Deleter, Recycler interface.

For Mounter/Unmounter Interface (from slides):
- Mounter/Unmounter makes data source (volume, block device, network share, or something else) available as a directory on host’s root FS.
- Directory is then mounted into containers by kubelet.
- Methods in Mounter/Unmounter interface are always called from node (Kubelet binary).

Mount interface has a SetupAt(dir, fsGroup) method. This dir is where plugin should mount the volume.
For example, in emptyDir plugin, 'dir' equals to the following path for each volume:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-emptydir
spec:
  containers:
  - name: nginx
    image: nginx:1.13
    resources:
      limits:
        cpu: 150m
        memory: 150Mi
      requests:
        cpu: 100m
        memory: 100Mi
    volumeMounts:
    - name: storage
      mountPath: /data/storage
    - name: scratch
      mountPath: /data/scratch
  volumes:
  - name: storage
    emptyDir: {}
  - name: scratch
    emptyDir: {}
# dir: /var/lib/kubelet/pods/26ae077c-4b2b-11e7-9241-2c4d54ed3845/volumes/kubernetes.io~empty-dir/scratch
# dir: /var/lib/kubelet/pods/26ae077c-4b2b-11e7-9241-2c4d54ed3845/volumes/kubernetes.io~empty-dir/storage
```

For other block based volumes, e.g. gce_pd, rbd, plugin will first mount the volume to a global path
at its choice, at bind mount to given dir. Note this applies to block based volumes, and doesn't apply
to glusterfs, nfs, etc. For example, gce pd will be mounted at `globalPDPath` first, then will be
bind mounted to `dir`:

```
# globalPDPath: /var/lib/kubelet/plugins/kubernetes.io~gce-pd/mypdname
# dir: /var/lib/kubelet/pods/11053ab6-4ba7/volumes/kubernetes.io~pd/mongodb~volume
```

For Attacher/Detacher Interface (from slides):
- Make block device available on specified host.
- Attach & VolumesAreAttached methods called from master (kube controller binary).
  - Can optionally be configured to be called by node.
- WaitForAttach, MountDevice, & GetDeviceMountPath always called on node from Kubelet.

This interface is used for block device. Some block volume plugins do not implement this interface
and incoporate the logic in mount methods. The separation is important since if kubelet is down,
noone will be able to detach a volume, thus resulting a dangling volume.

For Provisioner/Deleter Interface (from slides):
- Create and delete new pieces of physical storage and the k8s PV object to represent it.
- Methods called from master (kube controller binary).

Recycler interface is deprecated in favor of delete + provision.

**PV/PVC controller**

PV controller is started via controller manager; it starts two main workers that periodically syncs
volume (PV) and claim (PVC):
```go
go wait.Until(ctrl.volumeWorker, time.Second, stopCh)
go wait.Until(ctrl.claimWorker, time.Second, stopCh)
```

volumeWorker and claimWorker have similar sync loop; they watch for new PV and PVC, and work on them
respectively. For PVC worker, it syncs both bound and unbound PVC; and if dynamic provisioning is
enabled, it will also provision new PV. For PV worker, it mainly syncs volume phase, status, etc.
They call volume plugin to fulfill request, and volume plugin makes storage provider specific calls.
PV/PVC controller will also satisfy volume reclaim policy - for retain policy, it does nothing; for
delete policy, it deletes the volume.

**Attach/Detach controller**

The component runs in controller manager and performs attach/detach operations. These operations used
to be done in Kubelet, but problem with the approach is that if Kubelet is down, volumes can never
be detached from the node. Therefore, the attach/detach controller is proposed to solve the problem,
which runs on master.

**Kubelet volume manager**

During kubelet startup, it calls `ProbeVolumePlugins` method to get all plugins, which is a list of
`volume.VolumePlugin`. It gets the list by calling individual plugin's `ProbeVolumePlugins` method.
Each volume plugin (empty_dir, nfs, etc) needs to implement interface `pkg/volume/plugins.go#VolumePlugin`.

VolumePlugin is able to access host information via volumeHost - the information is provided via kubelet.
The main ProbeVolumePlugins locates at `cmd/kubelet/app/plugins.go`. The list of plugins returned by
ProbeVolumePlugins are stored in KubeletConfig. Afterwards when the acutal kubelet structure is created
(and ran), a VolumePluginMgr is created to track registered plugins. When a new pod is created, kubelet
use methods in VolumePlugin to setup volume. In particular, VolumePlugin returns Builder, Cleaner to
do the job.

Update on 02/27/2017: Now VolumePlugin returns Mounter, Unmounter instead of Builder, Cleaner; but
essentially, they are the same).

*References*

- https://docs.google.com/presentation/d/1Yl5JKifcncn0gSZf3e1dWspd8iFaWObLm9LxCaXZJIk/edit

## References

- https://kubernetes.io/docs/concepts/storage/volumes/
- https://kubernetes.io/docs/concepts/storage/persistent-volumes/
- https://github.com/kubernetes-incubator/external-storage
- https://kubernetes.io/docs/tasks/administer-cluster/change-pv-reclaim-policy/
- https://kubernetes.io/docs/tasks/administer-cluster/limit-storage-consumption/

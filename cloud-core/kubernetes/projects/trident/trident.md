<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Architecture](#architecture)
  - [Trident API and etcd store](#trident-api-and-etcd-store)
  - [Launcher](#launcher)
- [Implementation](#implementation)
  - [External volume](#external-volume)
  - [Workflow](#workflow)
- [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

- *Date: 06/01/2017, project release v17.04*
- *Date: 10/20/2019, project release v19.07*

[Trident](https://github.com/NetApp/trident/) is an external kubernetes persistent volume provisioner
for NetApp ONTAP, SolidFire, and E-Series systems. Trident can be run independently and interacted
with via its REST API alone, but users will benefit the most from its functionality as an external
provisioner for Kubernetes storage.

# Architecture

## Trident API and etcd store

Trident itself uses an etcd to store volume, to store trident API objects and configurations. Each
of the user-manipulable API objects (backends, storage classes, and volumes) is defined by a JSON
configuration. These configurations can either be implicitly created from Kubernetes API objects or
they can be posted to the Trident REST API to create objects of the corresponding types.

Trident will keep the objects in sync between trident and kubernetes; thus, trident can be managed
directly via a REST API and indirectly via interactions with Kubernetes. Trident keeps track of
four principal object types: backends, storage pools, storage classes, and volumes; ref [here](https://github.com/NetApp/trident/tree/6de468e55ca3a7055db769648b9fb2a5edc9d32f#trident-objects)

## Launcher

Since trident uses an etcd, it needs to provide persistent storage for etcd. It does so by running
a launcher pod, before the real trident deployment. The launcher will run an ephemeral trident pod
which uses the same configuration that we will pass to real trident deployment. The ephemeral trident
pod serves the API backed with in-memory store. When this ephemeral pod starts running, launcher pod
sends request to it to create PV from netapp backend (the same netapp backend we'll use for future
applications). After this PV is created, the ephemeral pod is deleted and the real trident deployment
is created; the real trident deployment has a persistent volume claim which will claim the PV created
by the ephemeral trident pod, thus providing persistent storage for etcd.

*Update on 10/20/2019, v19.07*

Trident uses CRDs for managing state, etcd is no longer required in newer release. For existing
trident installation, trident will migrate data from etcd to CRDs for users.

Due to the architectural change, the complicated process in launcher Pod is also deprecated.

# Implementation

## External volume

As mentioned in external-storage (as of kubernetes 1.6): it is *important* to note that out-of-tree
provisioner is scoped to the volume supported in kubernetes API. For example, you can create an
out-of-tree provisioner for glusterfs, but not xxxfs, because xxxfs API object is not defined in
kubernetes. For trident, it is fully out-of-tree and doesn't require kubernetes API change. When
creating PV object, it creates either nfs volume source or iscsi volume source based on volume
config, i.e.

```go
driverType := p.orchestrator.GetDriverTypeForVolume(vol)
switch {
case driverType == dvp.SolidfireSANStorageDriverName ||
  driverType == dvp.OntapSANStorageDriverName ||
  driverType == dvp.EseriesIscsiStorageDriverName:
  iscsiSource = CreateISCSIVolumeSource(vol.Config)
  pv.Spec.ISCSI = iscsiSource
case driverType == dvp.OntapNASStorageDriverName:
  nfsSource = CreateNFSVolumeSource(vol.Config)
  pv.Spec.NFS = nfsSource
default:
  // Unknown driver for the frontend plugin or for Kubernetes.
  // Provisioned volume should get deleted.
  log.WithFields(log.Fields{
    "volume": vol.Config.Name,
    "type":   p.orchestrator.GetVolumeType(vol),
    "driver": driverType,
  }).Warn("Kubernetes frontend doesn't recognize this type of volume; ",
    "deleting the provisioned volume.")
  err = fmt.Errorf("Unrecognized volume type by Kubernetes")
  return
}
pv, err = p.kubeClient.Core().PersistentVolumes().Create(pv)
```

There are, however, useful attributes for these 'netapp device created volumes'. These volume
configuration parameters can be specified using PVC annotations, e.g. `trident.netapp.io/exportPolicy: exportPolicy`.
Trident's internal volume representation has such attribute, annotations are thus used to translate
between kubernetes API volume object and its internal API.

```go
// in trident/storage/volume.go

type VolumeConfig struct {
  Version         string            `json:"version"`
  Name            string            `json:"name"`
  InternalName    string            `json:"internalName"`
  Size            string            `json:"size"`
  Protocol        config.Protocol   `json:"protocol"`
  SnapshotPolicy  string            `json:"snapshotPolicy,omitempty"`
  ExportPolicy    string            `json:"exportPolicy,omitempty"`
  SnapshotDir     string            `json:"snapshotDirectory,omitempty"`
  UnixPermissions string            `json:"unixPermissions,omitempty"`
  StorageClass    string            `json:"storageClass,omitempty"`
  AccessMode      config.AccessMode `json:"accessMode,omitempty"`
  AccessInfo      VolumeAccessInfo  `json:"accessInformation"`
}
```

## Workflow

The workflow is the same as other dynamic provisioning, i.e. create storage class with `netapp.io/trident`
as provisioner, and create persistent volume claim with the class, e.g.

```yaml
apiVersion: storage.k8s.io/v1beta1
kind: StorageClass
metadata:
  name: basic
provisioner: netapp.io/trident
parameters:
  backendType: "__BACKEND_TYPE__"
---
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: basic
  annotations:
    volume.beta.kubernetes.io/storage-class: basic
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

The above example creates a storage class named `basic` using `netapp.io/trident` as provisioner.

*Update on 10/20/2019, v19.07*

Trident implements CSIl provisioner in new releases, which is more generic and feature-rich. CSI is
the default option for Kubernetes 1.14 and above. The upgrade guide provides detailed instructions,
to simply put, the legacy Trident volume must be upgraded from a NFS/iSCSI type to the CSI type, i.e.
from:

```yaml
$ kubectl describe pv default-pvc-2-a8486

Name:            default-pvc-2-a8486
Labels:          <none>
Annotations:     pv.kubernetes.io/provisioned-by: netapp.io/trident
                 volume.beta.kubernetes.io/storage-class: standard
Finalizers:      [kubernetes.io/pv-protection]
StorageClass:    standard
Status:          Bound
Claim:           default/pvc-2
Reclaim Policy:  Delete
Access Modes:    RWO
VolumeMode:      Filesystem
Capacity:        1073741824
Node Affinity:   <none>
Message:
Source:
    Type:      NFS (an NFS mount that lasts the lifetime of a pod)
    Server:    10.xx.xx.xx
    Path:      /trid_1907_alpha_default_pvc_2_a8486
    ReadOnly:  false
```

to

```yaml
$ kubectl describe pv default-pvc-2-a8486
Name:            default-pvc-2-a8486
Labels:          <none>
Annotations:     pv.kubernetes.io/provisioned-by: csi.trident.netapp.io
                 volume.beta.kubernetes.io/storage-class: standard
Finalizers:      [kubernetes.io/pv-protection]
StorageClass:    standard
Status:          Bound
Claim:           default/pvc-2
Reclaim Policy:  Delete
Access Modes:    RWO
VolumeMode:      Filesystem
Capacity:        1073741824
Node Affinity:   <none>
Message:
Source:
    Type:              CSI (a Container Storage Interface (CSI) volume source)
    Driver:            csi.trident.netapp.io
    VolumeHandle:      default-pvc-2-a8486
    ReadOnly:          false
    VolumeAttributes:      backendUUID=c5a6f6a4-b052-423b-80d4-8fb491a14a22
                           internalName=trid_1907_alpha_default_pvc_2_a8486
                           name=default-pvc-2-a8486
                           protocol=file
Events:                <none>
```

The Trident installation will contain csi orchastrator Deployment and node agent Daemonset:

```
$ tridentctl version

+----------------+----------------+
| SERVER VERSION | CLIENT VERSION |
+----------------+----------------+
| 19.07.1        | 19.07.1        |
+----------------+----------------+

$ kubectl get pods -n <trident-namespace>
NAME                          READY   STATUS    RESTARTS   AGE
trident-csi-426nx             2/2     Running   0          20m
trident-csi-b5cf8fd7c-fnq24   4/4     Running   0          20m
```

The deployment contains the following containers. The `csi-*` images are provided by Kubernetes.
- trident-main
- csi-provisioner (quay.io/k8scsi/csi-provisioner)
- csi-attacher (quay.io/k8scsi/csi-attacher)
- csi-snapshotter (quay.io/k8scsi/csi-snapshotter)

The daemonset contains the following containers. The `csi-*` images are provided by Kubernetes.
- trident-main
- driver-registrar (quay.io/k8scsi/csi-node-driver-registrar)

# References

- https://netapp-trident.readthedocs.io/en/stable-v19.07/kubernetes/deploying.html
- https://netapp-trident.readthedocs.io/en/stable-v19.07/dag/kubernetes/deploying_trident.html
- https://netapp-trident.readthedocs.io/en/stable-v19.07/kubernetes/upgrading.html

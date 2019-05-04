<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Trident API and etcd store](#trident-api-and-etcd-store)
- [Launcher](#launcher)
- [External volume](#external-volume)
- [Workflow](#workflow)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

*Date: 06/01/2017, release v17.04.1*

Trident is an external kubernetes persistent volume provisioner for NetApp ONTAP, SolidFire, and
E-Series systems. Trident can be run independently and interacted with via its REST API alone, but
users will benefit the most from its functionality as an external provisioner for Kubernetes storage.

# Trident API and etcd store

Trident itself uses an etcd to store volume, to store trident API objects and configurations. Each
of the user-manipulable API objects (backends, storage classes, and volumes) is defined by a JSON
configuration. These configurations can either be implicitly created from Kubernetes API objects or
they can be posted to the Trident REST API to create objects of the corresponding types.

Trident will keep the objects in sync between trident and kubernetes; thus, trident can be managed
directly via a REST API and indirectly via interactions with Kubernetes. Trident keeps track of
four principal object types: backends, storage pools, storage classes, and volumes; ref [here](https://github.com/NetApp/trident/tree/6de468e55ca3a7055db769648b9fb2a5edc9d32f#trident-objects)

# Launcher

Since trident uses an etcd, it needs to provide persistent storage for etcd. It does so by running
a launcher pod, before the real trident deployment. The launcher will run an ephemeral trident pod
which uses the same configuration that we will pass to real trident deployment. The ephemeral trident
pod serves the API backed with in-memory store. When this ephemeral pod starts running, launcher pod
sends request to it to create PV from netapp backend (the same netapp backend we'll use for future
applications). After this PV is created, the ephemeral pod is deleted and the real trident deployment
is created; the real trident deployment has a persistent volume claim which will claim the PV created
by the ephemeral trident pod, thus providing persistent storage for etcd.

# External volume

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

# Workflow

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

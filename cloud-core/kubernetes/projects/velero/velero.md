<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Design](#design)
  - [Basics](#basics)
  - [Hooks](#hooks)
  - [Plugins](#plugins)
  - [Misc](#misc)
- [Experiments (v1.4)](#experiments-v14)
  - [Installation](#installation)
  - [Backup & Restore](#backup--restore)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

[Velero](https://github.com/vmware-tanzu/velero) (formerly Heptio Ark) gives you tools to back up
and restore your Kubernetes cluster resources and persistent volumes. You can run Velero with a
public cloud platform or on-premises. Velero lets you:
- Take backups of your cluster and restore in case of loss.
- Migrate cluster resources to other clusters.
- Replicate your production cluster to development and testing clusters.

Velero consists of:
- A server that runs on your cluster
- A command-line client that runs locally

# Design

## Basics

Velero is simple in concept, namely, it consists of two main operations: backup and restore.

To back up, run:

```
$ velero backup create [name]

# or periodically:
$ velero schedule create [name]
```

The backup data is stored in two locations:
- an object storage
- volume snapshot (if enabled)

To restore, run:

```
$ velero restore create --from-backup [name]
```

Use case of Velero includes:
- Disaster recovery
- Cluster migration
- Upgrade backup

## Hooks

Velero allows user to perform custom actions both before and after a backup action via annotation
or velero.backup spec. For example:

```
kubectl annotate pod -n nginx-example -l app=nginx \
    pre.hook.backup.velero.io/command='["/sbin/fsfreeze", "--freeze", "/var/log/nginx"]' \
    pre.hook.backup.velero.io/container=fsfreeze \
    post.hook.backup.velero.io/command='["/sbin/fsfreeze", "--unfreeze", "/var/log/nginx"]' \
    post.hook.backup.velero.io/container=fsfreeze
```

## Plugins

Velero uses storage provider plugins to integrate with a variety of storage systems to support backup
and snapshot operations.

## Misc

About "Atomicity":

> Note that cluster backups are not strictly atomic. If Kubernetes objects are being created or
> edited at the time of backup, they might not be included in the backup. The odds of capturing
> inconsistent information are low, but it is possible.

About "Single source of truth":

> Velero treats object storage as the source of truth. It continuously checks to see that the
> correct backup resources are always present. If there is a properly formatted backup file in
> the storage bucket, but no corresponding backup resource in the Kubernetes API, Velero synchronizes
> the information from object storage to Kubernetes.
>
> This allows restore functionality to work in a cluster migration scenario, where the original
> backup objects do not exist in the new cluster.
>
> Likewise, if a backup object exists in Kubernetes but not in object storage, it will be deleted
> from Kubernetes since the backup tarball no longer exists.

About "Remapping":

> Velero supports multiple namespace remapping – for example, in a single restore, objects in
> namespace "abc" can be recreated under namespace "def", and the objects in namespace "123" under
> "456".

About "API Versions":

> Velero backs up resources using the Kubernetes API server’s preferred version for each group/resource.
> When restoring a resource, this same API group/version must exist in the target cluster in order
> for the restore to be successful.

# Experiments (v1.4)

## Installation

Installing Velero based on quick start guide yields the following info:

<details><summary>velero install</summary><p>

```
$  velero install \
>      --provider aws \
>      --plugins velero/velero-plugin-for-aws:v1.0.0 \
>      --bucket velero \
>      --secret-file ./credentials-velero \
>      --use-volume-snapshots=false \
>      --backup-location-config region=minio,s3ForcePathStyle="true",s3Url=http://minio.velero.svc:9000
CustomResourceDefinition/backups.velero.io: attempting to create resource
CustomResourceDefinition/backups.velero.io: created
CustomResourceDefinition/backupstoragelocations.velero.io: attempting to create resource
CustomResourceDefinition/backupstoragelocations.velero.io: created
CustomResourceDefinition/deletebackuprequests.velero.io: attempting to create resource
CustomResourceDefinition/deletebackuprequests.velero.io: created
CustomResourceDefinition/downloadrequests.velero.io: attempting to create resource
CustomResourceDefinition/downloadrequests.velero.io: created
CustomResourceDefinition/podvolumebackups.velero.io: attempting to create resource
CustomResourceDefinition/podvolumebackups.velero.io: created
CustomResourceDefinition/podvolumerestores.velero.io: attempting to create resource
CustomResourceDefinition/podvolumerestores.velero.io: created
CustomResourceDefinition/resticrepositories.velero.io: attempting to create resource
CustomResourceDefinition/resticrepositories.velero.io: created
CustomResourceDefinition/restores.velero.io: attempting to create resource
CustomResourceDefinition/restores.velero.io: created
CustomResourceDefinition/schedules.velero.io: attempting to create resource
CustomResourceDefinition/schedules.velero.io: created
CustomResourceDefinition/serverstatusrequests.velero.io: attempting to create resource
CustomResourceDefinition/serverstatusrequests.velero.io: created
CustomResourceDefinition/volumesnapshotlocations.velero.io: attempting to create resource
CustomResourceDefinition/volumesnapshotlocations.velero.io: created
Waiting for resources to be ready in cluster...
Namespace/velero: attempting to create resource
Namespace/velero: already exists, proceeding
Namespace/velero: created
ClusterRoleBinding/velero: attempting to create resource
ClusterRoleBinding/velero: created
ServiceAccount/velero: attempting to create resource
ServiceAccount/velero: created
Secret/cloud-credentials: attempting to create resource
Secret/cloud-credentials: created
BackupStorageLocation/default: attempting to create resource
BackupStorageLocation/default: created
Deployment/velero: attempting to create resource
Deployment/velero: created
Velero is installed! ⛵ Use 'kubectl logs deployment/velero -n velero' to view the status.
```

</p></details></br>

All running components (including a test minio):

```
$ kubectl get pods -n velero
NAME                     READY   STATUS      RESTARTS   AGE
minio-d787f4bf7-kkcw5    1/1     Running     0          8m54s
minio-setup-8wpld        0/1     Completed   0          8m54s
velero-944667869-ffksk   1/1     Running     0          6m
```

The `backupstroragelocations` resource is where the config information stored:

```
$ kubectl get backupstoragelocations -n velero default -o yaml
apiVersion: velero.io/v1
kind: BackupStorageLocation
metadata:
  creationTimestamp: "2020-06-24T00:01:31Z"
  generation: 2
  labels:
    component: velero
  name: default
  namespace: velero
  resourceVersion: "512"
  selfLink: /apis/velero.io/v1/namespaces/velero/backupstoragelocations/default
  uid: 86987062-8155-4314-becb-0a51fbf2810a
spec:
  config:
    region: minio
    s3ForcePathStyle: "true"
    s3Url: http://minio.velero.svc:9000
  objectStorage:
    bucket: velero
  provider: aws
status:
  lastSyncedTime: "2020-06-24T00:03:08.495697043Z"
```

## Backup & Restore

Running velero backup will create a `backup`:

<details><summary>Take backup</summary><p>

```
$ velero backup create nginx-backup --selector app=nginx
Backup request "nginx-backup" submitted successfully.
Run `velero backup describe nginx-backup` or `velero backup logs nginx-backup` for more details.

$ velero backup describe nginx-backup
Name:         nginx-backup
Namespace:    velero
Labels:       velero.io/storage-location=default
Annotations:  velero.io/source-cluster-k8s-gitversion=v1.17.4
              velero.io/source-cluster-k8s-major-version=1
              velero.io/source-cluster-k8s-minor-version=17

Phase:  Completed

Namespaces:
  Included:  *
  Excluded:  <none>

Resources:
  Included:        *
  Excluded:        <none>
  Cluster-scoped:  auto

Label selector:  app=nginx

Storage Location:  default

Velero-Native Snapshot PVs:  auto

TTL:  720h0m0s

Hooks:  <none>

Backup Format Version:  1

Started:    2020-06-24 08:11:50 +0800 CST
Completed:  2020-06-24 08:11:52 +0800 CST

Expiration:  2020-07-24 08:11:50 +0800 CST

Total items to be backed up:  6
Items backed up:              6

Velero-Native Snapshots: <none included>
```

The backup CRD:

```
$ kubectl get backup -n velero nginx-backup -o yaml
apiVersion: velero.io/v1
kind: Backup
metadata:
  annotations:
    velero.io/source-cluster-k8s-gitversion: v1.17.4
    velero.io/source-cluster-k8s-major-version: "1"
    velero.io/source-cluster-k8s-minor-version: "17"
  creationTimestamp: "2020-06-24T00:11:50Z"
  generation: 5
  labels:
    velero.io/storage-location: default
  name: nginx-backup
  namespace: velero
  resourceVersion: "675"
  selfLink: /apis/velero.io/v1/namespaces/velero/backups/nginx-backup
  uid: 708a8677-3c15-4afd-b4b9-bf55a1960024
spec:
  hooks: {}
  includedNamespaces:
  - '*'
  labelSelector:
    matchLabels:
      app: nginx
  storageLocation: default
  ttl: 720h0m0s
status:
  completionTimestamp: "2020-06-24T00:11:52Z"
  expiration: "2020-07-24T00:11:50Z"
  formatVersion: 1.1.0
  phase: Completed
  progress:
    itemsBackedUp: 6
    totalItems: 6
  startTimestamp: "2020-06-24T00:11:50Z"
  version: 1
```

</p></details></br>


Running Restore operation has a similar result:

<details><summary>Take restore</summary><p>

```
$ velero restore create --from-backup nginx-backup
Restore request "nginx-backup-20200624081814" submitted successfully.
Run `velero restore describe nginx-backup-20200624081814` or `velero restore logs nginx-backup-20200624081814` for more details.


$ kubectl get restore -n velero nginx-backup-20200624081814 -o yaml
apiVersion: velero.io/v1
kind: Restore
metadata:
  creationTimestamp: "2020-06-24T00:18:14Z"
  generation: 3
  name: nginx-backup-20200624081814
  namespace: velero
  resourceVersion: "824"
  selfLink: /apis/velero.io/v1/namespaces/velero/restores/nginx-backup-20200624081814
  uid: a04af403-811b-4512-912b-a1802f7dc0ec
spec:
  backupName: nginx-backup
  excludedResources:
  - nodes
  - events
  - events.events.k8s.io
  - backups.velero.io
  - restores.velero.io
  - resticrepositories.velero.io
  includedNamespaces:
  - '*'
status:
  phase: Completed
```

</p></details></br>

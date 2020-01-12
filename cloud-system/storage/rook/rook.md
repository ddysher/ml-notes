<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Components](#components)
  - [Operator](#operator)
  - [Agent](#agent)
  - [Ceph](#ceph)
  - [Custom Resources](#custom-resources)
- [Experiment](#experiment)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

- *Date: 03/10/2018, v0.7*
- *Date: 11/02/2019, v1.4*

Rook is an open source orchestrator for distributed storage systems running in Kubernetes (rook doesn't
support other platform like mesos). Rook turns distributed storage software into a self-managing,
self-scaling, and self-healing storage services. It does this by automating deployment, bootstrapping,
configuration, provisioning, scaling, upgrading, migration, disaster recovery, monitoring, and resource
management.

Rook is currently in alpha (v0.7) state and has focused initially on orchestrating Ceph on top of
Kubernetes (run Ceph in Kubernetes cluster). Rook plans to add support for other storage systems
beyond Ceph in future releases. Rook itself is not a storage system; it leverages existing storage
system and makes them easy to use in cloud native environment.

After v1, support for Ceph in Rook is stable, and the community adds many more storage backend in
Ceph, including CockroachDB, NFS, etc. The Rook framework itself is alpha, and each different storage
backend has different maturity level.

*References*

- https://github.com/rook/rook/tree/v0.7.1
- https://github.com/rook/rook/wiki/Rook-Integration-with-Orchestration-Platforms

# Components

## Operator

The Rook operator is a simple container that has all that is needed to bootstrap and monitor the
storage cluster (watch for rook.io/Cluster). The operator will start and monitor ceph monitor pods
and a daemonset for the OSDs, which provides basic RADOS storage. The operator manages CRDs for
pools, object stores (S3/Swift), and file systems (rook.io/Pool, rook.io/ObjectStore, rook.io/Filesystem)
by initializing the pods and other artifacts necessary to run the services.

## Agent

Agent is started by operator, and is running as daemonset. Each agent configures a Flexvolume plugin
that integrates with Kubernetes' volume controller framework. All storage operations required on the
node are handled such as attaching network storage devices, mounting volumes, and formating the
filesystem.

## Ceph

All ceph binaries are included in a single container 'rook'. Ceph is the only backend supported at
this moment (v0.7). Many of the Ceph concepts like placement groups and crush maps are hidden. Ceph
version is an environment variable in rook's Dockerfile, and is downloaded via apt-get.

## Custom Resources

All custom resources defined in Rook:
- rook.io/Cluster
- rook.io/Pool
- rook.io/ObjectStore
- rook.io/Filesystem

# Experiment

Following are the steps from official docs:
- Create rook operator, which in turn create rook agent daemonset
- Create a `rook.io/Cluster`, i.e. a storage cluster in rook. Operator listens on Cluster resource
  and start ceph components based on cluster.spec.
- Depending on what storage type we need, we can start creating Pool, ObjectStore and Filesystem.
  - For block storage, we create a Pool resource with a StorageClass, then we'll be able to claim PV
    of this storage class. The operator acts as the provisioner to dynamically create PVs; and agent
    is the flex volume plugin to attach and mount the volume.
  - For object store, we create a ObjectStore and rook will create RGW service in the cluster with
    the S3 API. We are then able to use the object store using RGW service.
  - For filesystem, we create s Filesystem and rook will create MDS service. Wecan use the filesystem
    via flexvolume syntax.

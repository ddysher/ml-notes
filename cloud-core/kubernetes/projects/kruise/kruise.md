<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Components](#components)
  - [Advanced StatefulSet](#advanced-statefulset)
  - [BroadcastJob](#broadcastjob)
  - [SidecarSet](#sidecarset)
  - [CloneSet](#cloneset)
  - [UnitedDeployment](#uniteddeployment)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

- *Date: 07/07/2019, v0.1*
- *Date: 05/29/2020, v0.5*

[kruise](https://github.com/openkruise/kruise) is a set of controllers to automate application
management in Kubernetes. It contains (as of v0.1) three controllers:
- Advanced StatefulSet
- BroadcastJob
- SidecarSet

As of v0.5, there are two additional controllers:
- CloneSet
- UnitedDeployment

All of the controllers run in a single StatefulSet.

# Components

## Advanced StatefulSet

Advanced StatefulSet provides two main additions to StatefulSet:
- MaxUnavailable rolling update strategy
- In-place pod update strategy

The main offering from Advanced StatefulSet is in-place update of container image, which works by
updating revision labels of `kruise.StatefulSet` and patching container image. Kubelet will restart
container whose image has been updated (kubelet will not restart the Pod). On the other hand, the
regular `StatefulSet` in Kubernetes will delete Pods first, then create new Pods.

## BroadcastJob

> This controller distributes a Pod on every node in the cluster. Like a DaemonSet, a BroadcastJob
> makes sure a Pod is created and run on all selected nodes once in a cluster. Like a Job, a
> BroadcastJob is expected to run to completion.

## SidecarSet

SidecarSet leverages the mutating webhook admission controllers to automatically inject a sidecar
container for every selected Pod when the Pod is created. Additional feature of SidecarSet incldues:
- In-place Sidecar container image upgrade: similar to Advanced Statefulset;
- Decoupled Sidecar container lifecycle management: updating container image in SidecarSet CRD will
  update all Pods that's been targetted via the SidecarSet; note this only applies to image, updating
  other fields is done lazily, i.e. only when Pods are recreated;
- Mounting Sidecar volumes;
- etc.

## CloneSet

CloneSet manages stateless applications similar to Deployment, but with many more features, include:
- Scale features
  - Support PVCs per Pod;
  - Selective Pod deletion;
  - etc.
- Update features
  - In-place update, similar to Advanced Statefulset;
  - Partition for update, i.e. the desired number of Pods in old revisions, defaults to 0;
  - Update sequence: `priority`, `scatter` strategy;
  - etc.

## UnitedDeployment

UnitedDeployment provisions one type of workload for each group with corresponding `NodeSelector`.
The underline workload type supported is `StatefulSet`. The following UnitedDeployment, once created,
will create 3 StatefulSets, with Pods of each StatefulSet running on specified Nodes:

<details><summary>Example</summary><p>

```yaml
apiVersion: apps.kruise.io/v1alpha1
kind: UnitedDeployment
metadata:
  name: sample
spec:
  replicas: 6
  revisionHistoryLimit: 10
  selector:
    matchLabels:
      app: sample
  template:
    statefulSetTemplate:
      metadata:
        labels:
          app: sample
      spec:
        template:
          metadata:
            labels:
              app: sample
          spec:
            containers:
            - image: nginx:alpine
              name: nginx
  topology:
    subsets:
    - name: subset-a
      nodeSelector:
        nodeSelectorTerms:
        - matchExpressions:
          - key: node
            operator: In
            values:
            - zone-a
      replicas: 1
    - name: subset-b
      nodeSelector:
        nodeSelectorTerms:
        - matchExpressions:
          - key: node
            operator: In
            values:
            - zone-b
      replicas: 50%
    - name: subset-c
      nodeSelector:
        nodeSelectorTerms:
        - matchExpressions:
          - key: node
            operator: In
            values:
            - zone-c
  updateStrategy:
    manualUpdate:
      partitions:
        subset-a: 0
        subset-b: 0
        subset-c: 0
    type: Manual
...
```

</p></details></br>

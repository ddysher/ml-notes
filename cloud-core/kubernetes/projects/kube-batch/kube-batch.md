<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Design](#design)
  - [APIs](#apis)
  - [Actions & Plugins](#actions--plugins)
  - [Others](#others)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

kube-batch is a batch scheduler for Kubernetes, providing mechanisms for applications to run batch
jobs on Kubernetes.

# Design

*Date: 09/15/2019, v0.5.0*

## APIs

The core design ideas in kube-batch coscheduling are:
- a new API (CRD) `PodGroup` to specify a group of Pods that needs to be batch-scheduled
- a new annotation `scheduling.k8s.io/group-name: <name>` on Pod to identify a Pod as part of a group
- a new scheduler (multi-scheduler) that implements batch scheduler capability (Pod needs to set `SchedulerName`)
- in newer design, a new API (CRD) `Queue` is proposed to hold a queue of `PodGroup`

**PodGroup**

Following is an example YAML:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: qj-1
spec:
  backoffLimit: 6
  completions: 6
  parallelism: 6
  template:
    metadata:
      annotations:
        scheduling.k8s.io/group-name: qj-1
    spec:
      containers:
      - image: busybox
        imagePullPolicy: IfNotPresent
        name: busybox
        resources:
          requests:
            cpu: "100m"
      restartPolicy: Never
      schedulerName: kube-batch
---
apiVersion: scheduling.incubator.k8s.io/v1alpha1
kind: PodGroup
metadata:
  name: qj-1
spec:
  minMember: 6
```

Note here:
- If `PodGroup` is not created, then all Pods will be Pending until `PodGroup` is created
- If we change `parallelism` to be smaller than `minMember`, say 3, then all 3 Pods will be Pending
- If we remove the annotation, then Pods do not belong to any `PodGroup` and will be immediately scheduled

**Queue**

Queue defines the queue to allocate resource for PodGroup; if queue does not exist, the PodGroup
will not be scheduled. There is not much documentation on Queue, the intention seems to enable
multi-tenant use cases. For example:

```yaml
apiVersion: scheduling.incubator.k8s.io/v1alpha1
kind: PodGroup
metadata:
  name: qj-1
spec:
  minMember: 6
  queue: demo
---
apiVersion: scheduling.incubator.k8s.io/v1alpha1
kind: Queue
metadata:
  name: demo
spec:
  weight: 1
```

## Actions & Plugins

kube-batch defines interfaces for `Action` and `Plugin` respectively. On each scheduling session
(default to 1s), all plugins are called via `OnSessionOpen` plugin interface method, then all
actions are executed in order via `Execute` action interface method. In short:
- action is the the actual process of scheduling Pods, including:
  - reclaim, allocate, backfill, prerempt
- plugin contains preprocessing logic such as gang, predicates, nodeorder, etc
  - e.g. commonly used default scheduler features such as node/pod affinity is defined in nodeorder

Following is a sample config:

```yaml
actions: "reclaim, allocate, backfill, preempt"
tiers:
- plugins:
  - name: priority
  - name: gang
  - name: conformance
- plugins:
  - name: drf
  - name: predicates
    arguments:
      predicate.MemoryPressureEnable: true
      predicate.DiskPressureEnable: true
      predicate.PIDPressureEnable: true
  - name: proportion
  - name: nodeorder
```

## Others

**Controller**

Each Pod in a group is managed by its own controller, if any. In the future, there might be a new
PodGroup controller to manage the group itself, e.g. to restart all pods in a group.

For other customized controllers (e.g. tf-operator) that wish to leverage batch scheduler, it is
responsible to create `PodGroup`, set Pod annotation, etc.

**Cluster-Autoscaler**

When Cluster-Autoscaler scale-out a new node, it leverages predicates in scheduler to check whether
the new node can be scheduled. But Coscheduling is not an implementation of predicates for now; so
it'll not work well together with Cluster-Autoscaler right now.

# Experimentation

Install helm v2:

```
$ helm init

$ kubectl create serviceaccount --namespace kube-system tiller
$ kubectl create clusterrolebinding tiller-cluster-rule --clusterrole=cluster-admin --serviceaccount=kube-system:tiller
$ kubectl patch deploy --namespace kube-system tiller-deploy -p '{"spec":{"template":{"spec":{"serviceAccount":"tiller"}}}}'
```

Deploy kube-batch:

```
$ helm install $GOPATH/src/github.com/kubernetes-sigs/kube-batch/deployment/kube-batch --namespace kube-system
$ kubectl create clusterrolebinding kube-batch-cluster-rule --clusterrole=cluster-admin --serviceaccount=default
```

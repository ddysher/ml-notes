<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [KEPs](#keps)
  - [production readiness review](#production-readiness-review)
  - [appropriate use of node-role labels](#appropriate-use-of-node-role-labels)
- [Feature & Design](#feature--design)
  - [arch: borg/mesos style](#arch-borgmesos-style)
  - [arch: kubernetes node (worker node, minion)](#arch-kubernetes-node-worker-node-minion)
  - [arch: kubernetes control plane (master)](#arch-kubernetes-control-plane-master)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# KEPs

## production readiness review

- *Date: 08/18/2019*

The KEP introduces a process and critiera for merging Kubernetes features. It is still under review,
with the following goals:
- Define production readiness criteria for alpha, beta, and GA features.
- Define a production readiness review gate and process for all features.
- Utilize existing tooling with prow to enforce the process.

*References*

- https://github.com/kubernetes/enhancements/pull/1193

## appropriate use of node-role labels

- *Date: 09/01/2019*
- *Date: 12/14/2019, v1.17, alpha*

Kubernetes introduced a label `node-role.kubernetes.io/master=` for the purpose of labeling a node
as master, which allows external tools to recognize the label and do their own processing, e.g. for
`kubeadm` to deploy master components. However, due to lack of review, many other Kubernetes core
components (within kubernetes/kubernetes) and related projects were introduced which depend on the
label, which is problematic. For example, an implementation uses `node-role.kubernetes.io/master=`
to determine if a certain pod should be scheduled on "master", but the usage of "master" is not the
same across different scenario. The correct way here is to define dedicated labels and add thses
labels to nodes of choices.

> The tldr is that the node role label is not going away, but its an implementation detail of the
> cluster topology and not something that Kubernetes components should imply behavior around in
> favor of more intent based labels (exclude-disruption, etc.). That said, the role of the node
> should be stable for the life of the node.

In short, the KEP clarifies that the `node-role.kubernetes.io/*` labels are not for internal use and
cannot be used to change Kubernetes behavior.

*References*

- [appropriate use of node-role labels KEP link](https://github.com/kubernetes/enhancements/blob/76bc70540550659b39afa8f8b41e04f921bdf257/keps/sig-architecture/2019-07-16-node-role-label-use.md)

# Feature & Design

## arch: borg/mesos style

*Date: 05/18/2017*

Borg style architecture

- a single logical API endpoint for clients, where some amount of processing is done on requests,
  such as admission control and applying defaults
- generic (non-application-specific) collection abstractions described declaratively
- generic controllers/state machines that manage the lifecycle of the collection abstractions and
  the containers spawned from them
- a generic scheduler

Mesos style architecture
- multiple application-centric framework
- every framework has its own set of APIs
- no standard set of collection abstractions, controller/state machine, or schedulers

Building mesos style framework on kubernetes
- Use API plugins to create API resources for your new application-specific collection abstraction(s)
- Implement controllers for the new abstractions (and for managing the lifecycle of the pods the controllers generate)
- Implement a scheduler with the application-specific scheduling logic

*References*

- [mesos style design doc](https://github.com/kubernetes/community/blob/460827bdbd253b20b966889bcc361375763e453c/contributors/devel/mesos-style.md)

## arch: kubernetes node (worker node, minion)

*Date: 09/01/2014*

**Docker**

The Kubernetes node has the services necessary to run Docker containers and be managed from the
master systems.

**Kubelet**

The Kubelet works in terms of a container manifest. A container manifest is a YAML file that describes
a pod. The Kubelet takes a set of manifests that are provided in various mechanisms and ensures that
the containers described in those manifests are started and continue running.

**Proxy**

Each node also runs a simple network proxy. This reflects services as defined in the Kubernetes API
on each node and can do simple TCP stream forwarding or round robin TCP forwarding across a set of
backends. A service is a configuration unit for the proxies that run on every worker node. It is
named and points to one or more pods.

## arch: kubernetes control plane (master)

*Date: 09/01/2014*

**etcd**

All persistent master state is stored in an instance of etcd. This provides a great way to store
configuration data reliably. With watch support, coordinating components can be notified very quickly
of changes.

**API Server**

This server serves up the main Kubernetes API.  It validates and configures data for 3 types of
objects: pods, services, and replicationControllers. Beyond just servicing REST operations, validating
them and storing them in etcd, the API Server does two other things:
- Schedules pods to worker nodes. Right now the scheduler is very simple.
- Synchronize pod information (where they are, what ports they are exposing) with the service configuration.

**Controller Manager Server**

The replicationController type described above isn't strictly necessary for Kubernetes to be useful.
It is really a service that is layered on top of the simple pod API.

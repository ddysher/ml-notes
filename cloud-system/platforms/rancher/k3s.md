<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Implementation](#implementation)
  - [Removing un-important features](#removing-un-important-features)
  - [Using sqlite3](#using-sqlite3)
- [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

*Date: 10/12/2019, v0.9.1*

k3s is a light-weight Kubernetes distribution from Rancher.
- Legacy, alpha, non-default features are removed
- Removed most in-tree plugins (cloud providers and storage plugins)
- Add sqlite3 as the default storage mechanism
- Wrapped in simple launcher that handles a lot of the complexity of TLS and options
- Replace Docker with Containerd

k3s also includes Flannel, CoreOS and a bit of Host utilities (iptables, socat, etc).

# Implementation

## Removing un-important features

Removing unimportant features (lagacy, alpha, non-default, etc), and in-tree plugins are done via
[forking kubernetes source](https://github.com/rancher/kubernetes). Rancher maintains the fork for
every Kubernetes release.

## Using sqlite3

Kubernetes uses etcd as the backend storage by default, and many places are hard-coded to use etcd.
To switch to sqlite3, Rancher creates a project called [kine](https://github.com/rancher/kine), which
runs a server endpoint. The server speaks [etcd server proto](https://github.com/etcd-io/etcd/tree/master/etcdserver/etcdserverpb),
and acts as an etcd backend to Kubernetes. The kine project will translate the requests into SQL
statements.

Note the `rancher/kine` project is replaced from `ibuildthecloud/kine` in go.mod.

# References

- https://rancher.com/press/2019-02-26-press-release-rancher-labs-introduces-lightweight-distribution-kubernetes-simplify/
- https://itnext.io/edge-focused-compact-kubernetes-with-micropaas-μpaas-k3s-k3os-and-rio-6f7d758e19f1

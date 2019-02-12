<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [CRI-O](#cri-o)
  - [Overview](#overview)
  - [Components](#components)
  - [Timeline](#timeline)
- [CRI-Containerd](#cri-containerd)
  - [Overview](#overview-1)
  - [Design](#design)
  - [Timeline](#timeline-1)
- [Comparison](#comparison)
  - [CRI-O vs. CRI-Containerd](#cri-o-vs-cri-containerd)
  - [CRI-O vs. rktlet](#cri-o-vs-rktlet)
  - [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# CRI-O

## Overview

Around kubernetes 1.4, a new container runtime interface is introduced in kubelet runtime to solve
problems like code reuse, simplify container runtime, etc. cri-o is previously called ocid, it
bridges oci standards and kubelet container runtime interface.

cri-o is a separate daemon running along side with kubelet, and implements kubelet runtime. kubelet
calls the daemon via protocol buffer; the daemon setups PodSandbox and Container via executing runc
binary, setup network using libcni (which execute cni plugin binary), and so on. cri-o also supports
other OCI-compliant runtime like Clear Container, etc.

*References*

- http://cri-o.io
- https://github.com/kubernetes-sigs/cri-o

## Components

CRI-O is made up of several components that are found in different GitHub repositories.
- [OCI compatible runtime](https://github.com/opencontainers/runtime-tools): cri-o supports any
  OCI-compliant runtime
- [containers/storage](https://github.com/containers/storage): used for managing layers and creating
  root file-systems for the containers in a pod: Overlayfs, devicemapper, AUFS and btrfs are
  implemented, with Overlayfs as the default driver.
- [containers/image](https://github.com/containers/image): used for pulling images from registries.
- [networking (CNI)](https://github.com/containernetworking/cni): used for setting up network for pods.
- [container monitoring (conmon)](https://github.com/kubernetes-sigs/cri-o/tree/master/conmon): used
  to monitor the containers, handle logging from the container process, serve attach clients and
  detects Out Of Memory (OOM) situations.
- security is provided by several core Linux capabilities

<p align="center"><img src="./assets/crio-architecture.png" height="360px" width="auto"></p>

## Timeline

- 07/22/2016, kubernetes v1.4, cri-o no release
- 03/10/2018, kubernetes v1.9, cri-o v1.9.9
  - cri-o reaches v1.0 around 10/2017
  - source code still lives in kuberentes incubator
- 09/08/2018, kubernetes v1.11, cri-o v1.11.2
  - cri-o graduates from kubernetes incubator
  - repository moves from kubernetes-incubator to https://github.com/kubernetes-sigs/cri-o

# CRI-Containerd

## Overview

cri-containerd is a containerd based implementation of Kubernetes container runtime interface (CRI).
It is used in Kubernetes to provide an alternative to docker, i.e.

- with docker:         kubelet -> docker-shim -> docker -> containerd -> oci container (runc)
- with cri-containerd: kubelet ->      cri-containerd   -> containerd -> oci container (runc)
- with cri plugin:     kubelet ->               containerd            -> oci container (runc)

cri-containerd repository location changes along time:
- from:    https://github.com/kubernetes-incubator/cri-containerd
- to:      https://github.com/containerd/cri-containerd
- then to: https://github.com/containerd/cri (just cri plugin)

## Design

Following is the design proposal from containerd:
- https://github.com/containerd/cri-containerd/blob/v1.0.0-beta.1/docs/proposal.md

## Timeline

- 03/18/2018, kubernetes v1.9, cri-containerd v1.0.0-beta
  - cri-containerd is transitioning from a standalone binary that talks to containerd, to a plugin
    within containerd. Once containerd loads cri plugin (type grpc), it can serve cri requests.
    The cri plugin runs inside of containerd, and uses containerd internal modules to handle requests.
- 12/19/2018, kubernetes v1.13, cri-containerd v1.11.1

# Comparison

## CRI-O vs. CRI-Containerd

cri-o directly talks to oci compliant runtime; while cri-containerd utilized containerd to talk
to such runtime. They are two different implementation of cri interface.

## CRI-O vs. rktlet

[rktlet](https://github.com/kubernetes-incubator/rktlet) is similar to cri-o, but target at rkt
integration with kubelet container runtime interface.

## References

- https://joejulian.name/post/kubernetes-container-engine-comparison

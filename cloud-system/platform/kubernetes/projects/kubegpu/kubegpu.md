<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Implementation](#implementation)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

*Date: 10/03/2018*

[KubeGPU](https://github.com/Microsoft/KubeGPU) is an experimental project (extension framework for
Kubernetes) that helps scheduling pod matching a set of constraint. The main focus is GPU devices.
For more information, ref [design](https://github.com/Microsoft/KubeGPU/blob/b7ed848485482342410d3b584b8b37cdb9859182/docs/kubegpu.md).

It consists of:
- crishim, which includes cri grpc service and a device advertiser
- custom scheduler, which replaces default scheduler
- plugins, the device-specific code to be used by the CRI shim/device advertiser and the custom device scheduler

# Implementation

Workflow:
- An advertiser loop to query the devices for parameters (resource quantities and other attributes)
  which are patched to the API server using node annotations.
- A scheduler which utilizes the node resources and attributes along with resource requests from the
  pod to:
  - a. Optional: Translate pod constraints/requests to device/resource requests
  - b. See which nodes satisfy all pod constraints
  - c. Allocate resources on the node to meet those constraints
  - d. Patch the pod annotation with resource allocation
- A CRI shim which uses the pod annotations to obtain resource allocation to assign devices to the
  container. The pod annotations are obtained by using a Kube Client.

**crishim**

The shim is a replacement for dockershim in Kubernetes. It implements entire docker service via
importing dockershim source code, with changes made to a few methods, e.g. CreateContainer. The shim
modifies the container configuration by using pod annotations. As an example, these annotations could
be provided by the scheduler which specify which devices are being used. However, the actual
modifications made to the container configuration are done inside the plugins.

```go
// implementation of runtime service -- have to implement entire docker service
type dockerExtService struct {
	dockershim.DockerService
	kubeclient *clientset.Clientset
	devmgr     *device.DevicesManager
}
```

There is also a device advertiser which advertises devices and other information to be used by the
scheduler. The advertisement is done by patching the node annotation on the API server.

**scheduler**

The custom scheduler is a replacement for default scheduler. It imports default scheduler code and
extends it with a new predicate to fit node with extended resources (devices). The chosen devices
are written as pod annotations to be consumed by the custom CRI shim.

**plugins**

Plugins are Golang plugin module, and are loaded from `crishim` and `scheduler`. It does the actual
device discovery and allocation.

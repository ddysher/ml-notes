<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
  - [Introduction](#introduction)
  - [Architecture](#architecture)
  - [Features](#features)
  - [Concepts](#concepts)
- [Design](#design)
  - [Plugins](#plugins)
  - [Shims](#shims)
- [Related Projects](#related-projects)
  - [containerd vs docker](#containerd-vs-docker)
  - [containerd vs oci,runc](#containerd-vs-ocirunc)
  - [containerd vs kubernetes,mesos,swarm](#containerd-vs-kubernetesmesosswarm)
- [Experiments (03/18/2018, v1.0.2)](#experiments-03182018-v102)
  - [Installation](#installation)
  - [Use command line client](#use-command-line-client)
  - [Use command line client (v1.3.2)](#use-command-line-client-v132)
  - [Use golang client](#use-golang-client)
- [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

## Introduction

- *Date: 03/19/2017, v0.2*
- *Date: 12/08/2017, v1.0*
- *Date: 01/22/2019, v1.3*

containerd is an industry-standard core container runtime with an emphasis on simplicity, robustness
and portability. It is available as a daemon for Linux and Windows, which can manage the complete
container lifecycle of its host system: image transfer and storage, container execution and supervision,
low-level storage and network attachments, etc.

## Architecture

Following is a detailed architecture of containerd:
- containerd has a layered design: API, Core, Backend, where
  - API provides high-level API for external systems
  - Core contains Services and Metadata: Services are low-level APIs providing access to Metadata
  - Backend is pluaggable for content store, snapshot, etc
- containerd runtime calls out containerd-shim, which in turn uses OCI runtime, e.g. runc, to start container

<p align="center"><img src="./assets/containerd-arch.png" height="400px" width="auto"></p>

## Features

- **Client**: containerd offers a full client package to help you integrate containerd into your platform.
- **Namespaces**: containerd offers a fully namespaced API so multiple consumers can all use a single
  containerd instance without conflicting with one another. Namespaces allow multi-tenancy within a
  single daemon.
- **Checkpoint and Restore**: containerd can support checkpoint clone and/or live migrate containers
  using [criu](https://criu.org/Main_Page).
- **Plugin**: containerd supports extending its functionality using most of its defined interfaces.
  This includes using a customized runtime, snapshotter, content store, and even adding gRPC interfaces.
- **OCI Distribution**: containerd integrates with [OCI distribution specification](https://github.com/opencontainers/distribution-spec).
- **OCI Runtime**: containerd fully supports [OCI runtime specification](https://github.com/opencontainers/runtime-spec).
- **OCI Image**: containerd fully supports [OCI image specification](https://github.com/opencontainers/image-spec).
  containerd allows you to use overlay or snapshot filesystems with your containers. It comes with
  builtin support for overlayfs and btrfs.

## Concepts

<p align="center"><img src="./assets/containerd-concepts.png" height="240px" width="auto"></p>

**Container**

In containerd, a container is a metadata object. Resources such as an OCI runtime specification,
image, root filesystem, and other metadata can be attached to a container.

**Task**

Taking a container object and turning it into a runnable process on a system is done by creating a
new Task from the container. A task represents the runnable object within containerd.

Pay attention to the design here: a container is a _metadata object_, while task is a _runnable
object_.

**Content**

Provides access to content addressable storage. All immutable content will be stored here, keyed
by content hash. The main implementation is `local`, which provices content using local filesystem.

**Snapshot**

Snapshot provides root filesystem for running containers, and supports operations like commit,
mount, view, etc. Implementation of snapshot includes native, overlayfs, aufs, devicemapper, etc.

> Manages filesystem snapshots for container images. This is analogous to the graphdriver in Docker
> today. Layers are unpacked into snapshots.

For example, a native implementation take snapshot using directory name:

```
# Start plugin in one terminal
$ go run ./main.go /var/run/mysnapshotter.sock /tmp/snapshots

# Use ctr in another
$ CONTAINERD_SNAPSHOTTER=customsnapshot ctr images pull docker.io/library/alpine:latest
$ tree -L 3 /tmp/snapshots
/tmp/snapshots
|-- metadata.db
`-- snapshots
    `-- 1
        |-- bin
        |-- dev
        |-- etc
        |-- home
        |-- lib
        |-- media
        |-- mnt
        |-- proc
        |-- root
        |-- run
        |-- sbin
        |-- srv
        |-- sys
        |-- tmp
        |-- usr
        `-- var

18 directories, 1 file
```

Here the metadata.db is a bolt database containing snapshot metadata.

# Design

For detailed containerd design, refer to:
- [design doc](https://github.com/containerd/containerd/blob/v1.3.2/design)
- [ops guide doc](https://github.com/containerd/containerd/blob/v1.3.2/docs/ops.md)

## Plugins

[containerd plugins](https://github.com/containerd/containerd/blob/v1.3.2/PLUGINS.md) include:
- smart client: the go-client of containerd provides many extension points for developers
- external plugins: containerd allows extensions through two method:
  - via a binary available in containerd's PATH
  - by configuring containerd to proxy to another gRPC service, e.g. [snapshotter service](https://godoc.org/github.com/containerd/containerd/api/services/snapshots/v1#SnapshotsServer)
- built-in plugins: containerd uses plugins internally to ensure that internal implementations are
  decoupled, stable, and treated equally with external plugins.

List of plugin type:

```go
const (
	// InternalPlugin implements an internal plugin to containerd
	InternalPlugin Type = "io.containerd.internal.v1"
	// RuntimePlugin implements a runtime
	RuntimePlugin Type = "io.containerd.runtime.v1"
	// RuntimePluginV2 implements a runtime v2
	RuntimePluginV2 Type = "io.containerd.runtime.v2"
	// ServicePlugin implements a internal service
	ServicePlugin Type = "io.containerd.service.v1"
	// GRPCPlugin implements a grpc service
	GRPCPlugin Type = "io.containerd.grpc.v1"
	// SnapshotPlugin implements a snapshotter
	SnapshotPlugin Type = "io.containerd.snapshotter.v1"
	// TaskMonitorPlugin implements a task monitor
	TaskMonitorPlugin Type = "io.containerd.monitor.v1"
	// DiffPlugin implements a differ
	DiffPlugin Type = "io.containerd.differ.v1"
	// MetadataPlugin implements a metadata store
	MetadataPlugin Type = "io.containerd.metadata.v1"
	// ContentPlugin implements a content store
	ContentPlugin Type = "io.containerd.content.v1"
	// GCPlugin implements garbage collection policy
	GCPlugin Type = "io.containerd.gc.v1"
)
```

**Outdated**

Containerd uses golang plugin features (v1.8) to dynamically load [plugins](https://github.com/containerd/containerd/blob/v1.0.2/design/plugins.md).

## Shims

From [lifecycle](https://github.com/containerd/containerd/blob/v1.3.2/design/lifecycle.md):

> While containerd is a daemon that provides API to manage multiple containers, the containers
> themselves are not tied to the lifecycle of containerd. Each container has a shim that acts as
> the direct parent for the container's processes as well as reporting the exit status and holding
> onto the STDIO of the container. This also allows containerd to crash and restore all functionality
> to containers. While containerd does fork off the needed processes to run containers, the shim and
> runc, these are re-parented to the system's init.
>
> Overall, a container's lifecycle is not tied to the containerd daemon. The daemon is a management
> API for multiple container whose lifecycle is tied to one shim per container.

Every container runs under a containerd shim. The shim allows for daemonless containers. It basically
sits as the parent of the container's process to facilitate a few things.
- First it allows the runtimes, i.e. runc, to exit after it starts the container. This way we don't
  have to have the long running runtime processes for containers. When you start mysql you should
  only see the mysql process and the shim.
- Second it keeps the STDIO and other fds open for the container in case containerd and/or docker
  both die. If the shim was not running then the parent side of the pipes or the TTY master would be
  closed and the container would exit.
- Finally it allows the container's exit status to be reported back to a higher level tool like
  docker without having the actual parent of the container's process and do a `wait4`.

**Shim v2**

There two versions of shim API, v1 and v2. The [v2 API](https://github.com/containerd/containerd/tree/release/1.2/runtime/v2)
is a more elegant API which makes running different kinds of runtime easier. The main goal for shim
v2 is that it makes no assumption on the PID of the container processes, thus making VM based
container runtime easier to integrate, since such runtime has no tight relationship with processes
running on containerd host.
- the original [proposal](https://github.com/containerd/containerd/issues/2426)
- example benefit can be found on [kata architecture](https://github.com/kata-containers/documentation/blob/4d47c3fa8d15fc8e26e83ec4dd4a7dac33b6cb54/design/architecture.md)

The [shim v2 API](https://github.com/containerd/containerd/blob/release/1.2/runtime/v2/shim/shim.go#L50)
is defined as a Golang interface with a gRPC service: `TaskService`. Runtime authors need to
implement the API as a bridge (or shim) between containerd and underline runtime. Since then
(containerd v1.2.0), many runtimes have implemented and migrated to v2 API, including
[runc](https://github.com/containerd/containerd/tree/release/1.2/runtime/v2/runc),
[runhcs](https://github.com/containerd/containerd/tree/release/1.2/runtime/v2/runhcs) (now [here](https://github.com/microsoft/hcsshim)),
[gvisor](https://github.com/google/gvisor-containerd-shim/tree/v0.0.2/pkg/v2),
[kata](https://github.com/kata-containers/runtime/tree/1.7.1/containerd-shim-v2), etc.

*References*

- https://groups.google.com/forum/#!topic/docker-dev/zaZFlvIx1_k
- https://github.com/crosbymichael/dockercon-2016

# Related Projects

## containerd vs docker

Docker is a complete platform and programming environment for containerized applications. containerd
is one of dozens of specialized components integrated into Docker. containerd 0.2.4 used in Docker
1.12 covers only container execution and process management. containerd's roadmap is to refactor the
Docker Engine codebase to extract more of its logic for distribution, networking and storage on a
single host into a reusable component that Docker will use, and that can be used by other container
orchestration projects or hosted container services.

## containerd vs oci,runc

Docker donated the OCI specification to the Linux Foundation in 2015, along with a reference
implementation called runc. containerd integrates OCI/runc into a feature-complete, production-ready
core container runtime. runc is a component of containerd, the executor for containers. containerd
has a wider scope than just executing containers: downloading container images, managing storage
and network interfaces, calling runc with the right parameters to run containers.

containerd fully leverages the Open Container Initiative's (OCI) runtime, image format specifications
and OCI reference implementation (runc) and will pursue OCI certification when it is available.
Because of its massive adoption, containerd is the industry standard for implementing OCI.

## containerd vs kubernetes,mesos,swarm

Kubernetes today uses Docker directly. Kubernetes implements container support in the Kubelet by
implementing its [Container Runtime Interface using containerd](https://github.com/containerd/cri).
Mesos and other orchestration engines can leverage containerd for core container runtime functionality
as well.

# Experiments (03/18/2018, v1.0.2)

## Installation

Make sure correct version of runc is installed (see runc.md), then install containerd binaries:

```console
$ wget https://github.com/containerd/containerd/releases/download/v1.0.2/containerd-1.0.2.linux-amd64.tar.gz
$ tar -xvzf containerd-1.0.2.linux-amd64.tar.gz
  bin/
  bin/containerd
  bin/ctr
  bin/containerd-shim
  bin/containerd-release
  bin/containerd-stress
$ sudo mv bin/* /usr/local/bin/
```

Now generate config and start containerd directly in foreground:

```console
$ sudo mkdir /etc/containerd
$ sudo bash -c "containerd config default > /etc/containerd/config.toml"
$ sudo containerd
INFO[0000] starting containerd                           module=containerd revision=cfd04396dc68220d1cecbe686a6cc3aa5ce3667c version=v1.0.2
INFO[0000] loading plugin "io.containerd.content.v1.content"...  module=containerd type=io.containerd.content.v1
INFO[0000] loading plugin "io.containerd.snapshotter.v1.btrfs"...  module=containerd type=io.containerd.snapshotter.v1
WARN[0000] failed to load plugin io.containerd.snapshotter.v1.btrfs  error="path /var/lib/containerd/io.containerd.snapshotter.v1.btrfs must be a btrfs filesystem to be used with the btrfs snapshotter" module=containerd
INFO[0000] loading plugin "io.containerd.snapshotter.v1.overlayfs"...  module=containerd type=io.containerd.snapshotter.v1
INFO[0000] loading plugin "io.containerd.metadata.v1.bolt"...  module=containerd type=io.containerd.metadata.v1
WARN[0000] could not use snapshotter btrfs in metadata plugin  error="path /var/lib/containerd/io.containerd.snapshotter.v1.btrfs must be a btrfs filesystem to be used with the btrfs snapshotter" module="containerd/io.containerd.metadata.v1.bolt"
INFO[0000] loading plugin "io.containerd.differ.v1.walking"...  module=containerd type=io.containerd.differ.v1
INFO[0000] loading plugin "io.containerd.gc.v1.scheduler"...  module=containerd type=io.containerd.gc.v1
INFO[0000] loading plugin "io.containerd.grpc.v1.containers"...  module=containerd type=io.containerd.grpc.v1
INFO[0000] loading plugin "io.containerd.grpc.v1.content"...  module=containerd type=io.containerd.grpc.v1
INFO[0000] loading plugin "io.containerd.grpc.v1.diff"...  module=containerd type=io.containerd.grpc.v1
INFO[0000] loading plugin "io.containerd.grpc.v1.events"...  module=containerd type=io.containerd.grpc.v1
INFO[0000] loading plugin "io.containerd.grpc.v1.healthcheck"...  module=containerd type=io.containerd.grpc.v1
INFO[0000] loading plugin "io.containerd.grpc.v1.images"...  module=containerd type=io.containerd.grpc.v1
INFO[0000] loading plugin "io.containerd.grpc.v1.leases"...  module=containerd type=io.containerd.grpc.v1
INFO[0000] loading plugin "io.containerd.grpc.v1.namespaces"...  module=containerd type=io.containerd.grpc.v1
INFO[0000] loading plugin "io.containerd.grpc.v1.snapshots"...  module=containerd type=io.containerd.grpc.v1
INFO[0000] loading plugin "io.containerd.monitor.v1.cgroups"...  module=containerd type=io.containerd.monitor.v1
INFO[0000] loading plugin "io.containerd.runtime.v1.linux"...  module=containerd type=io.containerd.runtime.v1
INFO[0000] loading plugin "io.containerd.grpc.v1.tasks"...  module=containerd type=io.containerd.grpc.v1
INFO[0000] loading plugin "io.containerd.grpc.v1.version"...  module=containerd type=io.containerd.grpc.v1
INFO[0000] loading plugin "io.containerd.grpc.v1.introspection"...  module=containerd type=io.containerd.grpc.v1
INFO[0000] serving...                                    address="/run/containerd/debug.sock" module="containerd/debug"
INFO[0000] serving...                                    address="/run/containerd/containerd.sock" module="containerd/grpc"
INFO[0000] containerd successfully booted in 0.006489s   module=containerd
```

## Use command line client

Use 'ctr' to interact with containerd, e.g.

```console
# Pull image from docker hub
$ sudo ctr images pull docker.io/library/redis:alpine

# Run container from the image, just like docker (redis is running in foreground)
$ sudo ctr run docker.io/library/redis:alpine redis
```

If we inspect running processes, we'll find the following ones:

```console
$ ps aux | grep redis
root      6493  0.0  0.0  51420  3936 pts/1    S+   04:08   0:00 sudo ctr run docker.io/library/redis:alpine redis
root      6494  0.5  0.5 376464 22140 pts/1    Sl+  04:08   0:00 ctr run docker.io/library/redis:alpine redis
root      6507  0.0  0.0   7536  3160 pts/0    Sl   04:08   0:00 containerd-shim -namespace default -workdir /var/lib/containerd/io.containerd.runtime.v1.linux/default/redis -address /run/containerd/containerd.sock -containerd-binary /usr/local/bin/containerd
systemd+  6523  0.2  0.1  21780  7308 ?        Ssl  04:08   0:00 redis-server
```

Note there is no runc since container is re-parented to containerd-shim.

## Use command line client (v1.3.2)

Follow the above same procedure to run a redis container, and inspect the result:
- the default runc shim has switched to shimv2 API
- containerd-shim is the child of systemd and parent of redis

```
$ ps aux | grep containerd-shim
root      520171  0.0  0.0 110788  7016 pts/1    Sl   13:43   0:00 /usr/bin/containerd-shim-runc-v2 -namespace default -id redis -addre

$ pstree -s 520171
systemd───containerd-shim─┬─redis-server───3*[{redis-server}]
                          └─13*[{containerd-shim}]
```

## Use golang client

To use golang client to interact with containerd, refer to [the getting started doc](https://github.com/containerd/containerd/blob/v1.0.2/docs/getting-started.md)

# References

- https://containerd.io/
- https://github.com/containerd/containerd
- http://blog.kubernetes.io/2017/11/containerd-container-runtime-options-kubernetes.html

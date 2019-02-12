<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
  - [Introduction (03/19/2017, v0.2)](#introduction-03192017-v02)
  - [Namespaces](#namespaces)
  - [Containerd-shim](#containerd-shim)
  - [Plugins](#plugins)
  - [Design](#design)
  - [Updates on 12/08/2017, v1.0](#updates-on-12082017-v10)
- [Related Projects](#related-projects)
  - [containerd vs docker](#containerd-vs-docker)
  - [containerd vs oci,runc](#containerd-vs-ocirunc)
  - [containerd vs kubernetes,mesos,swarm](#containerd-vs-kubernetesmesosswarm)
- [Experiments (03/18/2018, v1.0.2)](#experiments-03182018-v102)
  - [Installation](#installation)
  - [Use command line client](#use-command-line-client)
  - [Use golang client](#use-golang-client)
- [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

## Introduction (03/19/2017, v0.2)

containerd is an industry-standard core container runtime with an emphasis on simplicity, robustness
and portability. It is available as a daemon for Linux and Windows, which can manage the complete
container lifecycle of its host system: image transfer and storage, container execution and supervision,
low-level storage and network attachments, etc.

<p align="center"><img src="./assets/containerd.png" height="480px" width="auto"></p>

Note that based on containerd codebase, it is actually the shim that uses `runc` to start container.

## Namespaces

containerd offers a fully namespaced API so multiple consumers can all use a single containerd
instance without conflicting with one another. Namespaces allow multi-tenancy within a single daemon.

## Containerd-shim

Every container runs under a containerd shim. The shim allows for daemonless containers. It basically
sits as the parent of the container's process to facilitate a few things.
- First it allows the runtimes, i.e. runc, to exit after it starts the container. This way we don't
  have to have the long running runtime processes for containers. When you start mysql you should
  only see the mysql process and the shim.
- Second it keeps the STDIO and other fds open for the container incase containerd and/or docker
  both die. If the shim was not running then the parent side of the pipes or the TTY master would be
  closed and the container would exit.
- Finally it allows the container's exit status to be reported back to a higher level tool like
  docker without having the actual parent of the container's process and do a `wait4`.

*References*
- https://groups.google.com/forum/#!topic/docker-dev/zaZFlvIx1_k
- https://github.com/crosbymichael/dockercon-2016

## Plugins

Containerd uses golang plugin features (v1.8) to dynamically load [plugins](https://github.com/containerd/containerd/blob/v1.0.2/design/plugins.md)

## Design

For detailed containerd design, refer to [design doc here](https://github.com/containerd/containerd/blob/v1.0.2/design)

## Updates on 12/08/2017, v1.0

containerd reaches v1.0 on 12/2017.

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

Make sure correct version of runc in installed (see runc.md), then install containerd binaries:

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
$ containerd config default > /etc/containerd/config.toml
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

## Use golang client

To use golang client to interact with containerd, refer to [the getting started doc](https://github.com/containerd/containerd/blob/v1.0.2/docs/getting-started.md)

# References

- https://containerd.io/
- https://github.com/containerd/containerd
- http://blog.kubernetes.io/2017/11/containerd-container-runtime-options-kubernetes.html

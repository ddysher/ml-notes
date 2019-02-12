<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [skopeo](#skopeo)
- [buildah](#buildah)
- [podman](#podman)
- [img](#img)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# skopeo

Skopeo is a tool for interacting with container registry; precisely, anything that conforms to
container storage standards. It is mainly used to:
- inspect container image without pulling it;
- copy images between different types of container storages (usually two registries);
- delete images from remote registries directly;
- etc.

The types of container storage includes:
- Container Registries
- Docker Archive
- Local Filesystem
- etc

Note:
> Skopeo is split into a command line tool and a separate library github.com/containers/image.
> This library is now shared by many other container engines including Podman, Buildah, CRI-O.

*References*

- https://github.com/containers/skopeo
- https://www.redhat.com/en/blog/skopeo-10-released

# buildah

Buildah is a tool from RedHat to build oci-compatible container images. It can inter-operate with
docker images, e.g. build using dockerfile `buildah bud`, push buildah built image to docker daemon
via `buildah push <image> docker-daemon:<image>`, etc.

The default location (in rootless mode) to hold data and states is `.local/share/containers/storage`,
and in root mode, it's `/var/lib/containers/storage`.

```
$ buildah images
REPOSITORY                 TAG      IMAGE ID       CREATED      SIZE

$ buildah containers
CONTAINER ID  BUILDER  IMAGE ID     IMAGE NAME                       CONTAINER NAME


$ buildah from fedora
Getting image source signatures
Copying blob c7def56d621e done
Copying config a368cbcfa6 done
Writing manifest to image destination
Storing signatures
fedora-working-container

$ buildah images
REPOSITORY                 TAG      IMAGE ID       CREATED      SIZE
docker.io/library/fedora   latest   a368cbcfa678   3 days ago   189 MB

$ buildah containers
CONTAINER ID  BUILDER  IMAGE ID     IMAGE NAME                       CONTAINER NAME
b8a73e15e469     *     a368cbcfa678 docker.io/library/fedora:latest  fedora-working-container
```

Buildah has a `run` command to start a container, but:
> It should be noted that buildah run is primarily intended for helping debug during the build
> process. A runtime like runc or a container interface like CRI-O is more suited for starting
> containers in production.

```
$ buildah run fedora-working-container bash
[root@sugarcane /]#
```

A similar tool is Podman:
> In short, the `buildah run` command emulates the `RUN` command that is found in a Dockerfile
> while the `podman run` command emulates the `docker run` command. Podman is aimed at managing
> containers, images, and pods while Buildah focuses on the building of containers.

*References*

- https://github.com/containers/buildah
- https://www.projectatomic.io/blog/2017/11/getting-started-with-buildah/

# podman

Podman is a drop-in replacemnt of Docker from RedHat. The primary reason for launching the project
is due to Docker's not-so-open community, and RedHat's desire to control the whole container stack.
> Podman is a daemonless container engine for developing, managing, and running OCI Containers on
> your Linux System. Containers can either be run as root or in rootless mode. Simply put: `alias docker=podman`.

The whole stack includes:
- Podman manages containers (for production workload)
- Buildah builds containers
- Skopeo works with container registry

All projects share the same underline tools:
- https://github.com/containers/image
- https://github.com/containers/storage

*References*

- https://github.com/containers/podman

# img

img is a standalone, daemon-less, unprivileged Dockerfile and OCI compatible container image builder.
It is built on top of moby/buildkit. The commands/UX are the same as `docker {build,tag,push,pull,login,logout,save}`.

The default location (in rootless mode) to hold data and states is `.local/share/img/`.

*References*

- https://github.com/genuinetools/img/

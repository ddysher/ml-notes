<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Storage Drivers](#storage-drivers)
  - [Overview](#overview)
  - [Drivers](#drivers)
- [Docker Image IDs](#docker-image-ids)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Storage Drivers

## Overview

Functionality-wise, aufs is similar to overlayfs, both use union mount. btrfs is similar to zfs, both
are CoW filesystem - docker uses their snapshot feature. devicemapper is also similar to btrfs and zfs,
but works at block level - docker uses thin-provisioning and snapshotting capabilities in devicemapper.

Use the `info` subcommand to find out which storage driver is being used in Docker daemon, e.g. use
`overlay` storage driver with a Backing Filesystem value of `extfs`. The extfs value means that the
overlay storage driver is operating on top of an existing (ext) filesystem. The backing filesystem
refers to the filesystem that was used to create the Docker host's local storage area under `/var/lib/docker`.

There is a requirement for storage driver and backing filesystem:
- `overlay/overlay2` backing filesystem can be 'ext4,xfs'
- `aufs` backing filesystem can be 'ext4,xfs'
- `btrfs` backing filesystem is 'btrfs'
- `devicemapper` backing DEVICE is 'direct-lvm'
- `vfs` for debugging only
- `zfs` backing filesystem is 'zfs'

The choice of storage driver can affect the performance of containerized applications. So it's important
to understand the different storage driver options available and select the right one for applications.

## Drivers

**[aufs](https://docs.docker.com/storage/storagedriver/aufs-driver/)**

aufs is a unification filesystem. This means that it takes multiple directories on a single Linux
host, stacks them on top of each other, and provides a single unified view. To achieve this, aufs
uses a union mount.

aufs works at the file level. This means that all aufs CoW operations copy entire files - even if
only a small part of the file is being modified. However, a copy up operation only occurs once per
file on any given container. Subsequent reads and writes happen against the file's copy already
copied-up to the container's top layer.

The aufs storage driver deletes a file from a container by placing a whiteout file in the container's
top layer.

Calling rename(2) for a directory is not fully supported on aufs. It returns EXDEV `cross-device link not permitted`,
even when both of the source and the destination path are on a same aufs layer, unless the directory
has no children.

Image layers and their contents are stored under `/var/lib/docker/aufs/diff/`. The `/var/lib/docker/aufs/layers/`
directory contains metadata about how image layers are stacked.

Running containers are mounted below `/var/lib/docker/aufs/mnt/<container-id>`. Container metadata
and various config files that are placed into the running container are stored in `/var/lib/docker/containers/<container-id>`.
Files in this directory exist for all containers on the system, including ones that are stopped.
When a container is running the container's log files are also in this directory.

**[btrfs](https://docs.docker.com/storage/storagedriver/btrfs-driver/)**

btrfs is a next generation copy-on-write filesystem that supports many advanced storage technologies
that make it a good fit for Docker.

Docker leverages btrfs subvolumes and snapshots for managing the on-disk components of image and
container layers. btrfs subvolumes look and feel like a normal Unix filesystem. As such, they can
have their own internal directory structure that hooks into the wider Unix filesystem. Subvolumes
are natively copy-on-write and have space allocated to them on-demand from an underlying storage
pool. They can also be nested and snapped.

Snapshots are a point-in-time read-write copy of an entire subvolume. They exist directly below
the subvolume they were created from. Snapshots are first-class citizens in a btrfs filesystem. This
means that they look, feel, and operate just like regular subvolumes. The technology required to
create them is built directly into the btrfs filesystem thanks to its native copy-on-write design.

Docker's btrfs storage driver stores every image layer and container in its own btrfs subvolume or
snapshot. The base layer of an image is stored as a subvolume whereas child image layers and
containers are stored as snapshots.

btrfs does not support page cache sharing. This means that n containers accessing the same file
require n copies to be cached. (In aufs, file is shared by the  n containers in the read-only layer).

Commands to setup up btrfs driver:
```
sudo mkfs.btrfs -f /dev/xvdb
echo "/dev/xvdb /var/lib/docker btrfs defaults 0 0" >> /etc/fstab
```

**[devicemapper](https://docs.docker.com/storage/storagedriver/device-mapper-driver/)**

The devicemapper driver stores every image and container on its own virtual device. These devices are
thin-provisioned copy-on-write snapshot devices. devicemapper technology works at the block level
rather than the file level. This means that devicemapper storage driver's thin provisioning and
copy-on-write operations work with blocks rather than entire files.

Each image layer is a snapshot of the layer below it. The lowest layer of each image is a snapshot
of the base device that exists in the pool. This base device is a devicemapper artifact and not a
Docker image layer. A container is a snapshot of the image it is created from.

With the devicemapper driver, writing new data to a container is accomplished by an allocate-on-demand
operation. Updating existing data uses a copy-on-write operation. Because devicemapper is a block-based
technology these operations occur at the block level. For example, when making a small change to a
large file in a container, the devicemapper storage driver does not copy the entire file. It only
copies the blocks to be modified. Each block is 64KB.

Docker hosts running the devicemapper storage driver default to a configuration mode known as `loop-lvm`.
This mode uses sparse files to build the thin pool used by image and container snapshots. The mode is
designed to work out-of-the-box with no additional configuration. However, production deployments should
not run under loop-lvm mode. The preferred configuration for production deployments is `direct-lvm`.
This mode uses block devices to create the thin pool.

The `/var/lib/docker/devicemapper/mnt` directory contains the mount points for image and container
layers. The `/var/lib/docker/devicemapper/metadata` directory contains one file for every image
layer and container snapshot.

All blocks are 64KB. A write that uses less than 64KB still results in a single 64KB block being
allocated. Writing more than 64KB of data uses multiple 64KB  blocks. This can impact container
performance, especially in containers that perform lots of small writes. However, once a block is
allocated to a container subsequent reads and writes can operate directly on that block.

**[overlayfs](https://docs.docker.com/storage/storagedriver/overlayfs-driver/)**

overlayfs is a modern union filesystem that is similar to aufs. In comparison to aufs, overlayfs has
a simpler design, has been in the mainline Linux kernel since version 3.18, and is potentially faster.

overlayfs takes two directories on a single Linux host, layers one on top of the other, and provides
a single unified view. These directories are often referred to as layers and the technology used to
layer them is known as a union mount. The overlayfs terminology is "lowerdir" for the bottom layer
and "upperdir" for the top layer. The unified view is exposed through its own directory called "merged".

The overlay driver only works with two layers. This means that multi-layered images cannot be
implemented as multiple overlayfs layers. To create a container, the overlay driver combines the
directory representing the image's top layer plus a new directory for the container. The image's
top layer is the "lowerdir" in the overlay and read-only.

There are two versions of overlayfs driver:
- overlay: Each image layer is implemented as its own directory under `/var/lib/docker/overlay`
  Hard links are then used as a space-efficient way to reference data shared with lower layers.
- overlay2: While the overlay driver only works with a single lower overlayfs layer and hence
  requires hard links for implementation of multi-layered images, the overlay2 driver natively
  supports multiple lower overlayfs layers (up to 128). It's only compatible with Linux kernel
  4.0 and later. In overlay2, lowerdir is represented as multiple layers, e.g. lowerdir=dir1:dir2:dir3:dir4.

**[zfs](https://docs.docker.com/storage/storagedriver/zfs-driver/)**

zfs is a next generation filesystem that supports many advanced storage technologies such as volume
management, snapshots, checksumming, compression and deduplication, replication and more.

Commands to setup up zfs driver:
```
sudo zpool create -f zpool-docker /dev/xvdb
sudo zfs create -o mountpoint=/var/lib/docker zpool-docker/docker
```

*References*

- https://docs.docker.com/engine/userguide/storagedriver/imagesandcontainers/
- https://docs.docker.com/engine/userguide/storagedriver/

# Docker Image IDs

Docker 1.10 changed the way how docker images are stored and referenced, as well as the relationship
between image and layer, for more information, see [this blog](http://www.windsock.io/explaining-docker-image-ids/).

Summary:
- layer identification
  - Before docker 1.10, each layer is assigned a UUID
  - After docker 1.10, each layer is identified by its digest: `algorithm:hex`. The hex element is
    calculated by applying the algorithm (SHA256) to a layer's content.
- image & layer
  - Before docker 1.10, image and layer are synonymous: image is just a special layer (leaf layer with
    meaningful name). Each layer references its parent layer, and to construct an image, we start from
    the leaf layer, walk though layer lineage until we reach a layer without parent.
  - After docker 1.10, image and layer are no longer synonymous: image directly references one or more
    layers that eventually contribute to a derived container's filesystem. The image ID is also a
    digest, and is a computed SHA256 hash of the image configuration object.
- others
  - image manifest contains digests of the image's layers, which contain the SHA256 hashes of the
    compressed, archived diff contents.
  - docker creates intermediate images during a local image build, for the purposes of maintaining a
    build cache, which complicates locally built image format.

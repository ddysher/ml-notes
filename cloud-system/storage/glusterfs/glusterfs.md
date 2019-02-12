<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Architecture & Concepts](#architecture--concepts)
  - [Overview](#overview)
  - [Volume](#volume)
- [Components](#components)
  - [gluster](#gluster)
  - [glusterd](#glusterd)
  - [glusterfs](#glusterfs)
  - [glusterfsd](#glusterfsd)
  - [glusterd2 (v4.0+)](#glusterd2-v40)
  - [glustercli (v4.0+)](#glustercli-v40)
- [Experiments](#experiments)
  - [Running glusterfs](#running-glusterfs)
  - [glusterfs quota](#glusterfs-quota)
- [Projects](#projects)
  - [gluster swift](#gluster-swift)
  - [gluster csi driver](#gluster-csi-driver)
  - [gluster kubernetes](#gluster-kubernetes)
- [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Architecture & Concepts

## Overview

The most important concepts in GlusterFS are: brick, volume, translator, etc
- A Brick is the basic unit of storage in GlusterFS, represented by an export directory on a server in the trusted storage pool (A storage pool is a trusted network of storage servers).
- A volume is a logical collection of bricks. Most of the gluster management operations happen onthe volume.
- A translator converts requests from users into requests for storage. There are translators on both client side and server side.

## Volume

There are three building blocks for glusterfs volume types:
- distributed, where files spread across multiple bricks
- replicated, where each file is replicated to different bricks
- striped, where each file is striped and saved in different bricks

Based on these volume types, there are 'distributed replicated volume', 'distributed striped volume',
etc. These can be seen as different RAID levels.

*References*
- https://gluster.readthedocs.io/en/latest/Quick-Start-Guide/Architecture

# Components

## gluster

Client command line tool.

## glusterd

At startup, each node will runs a 'glusterd' management daemon. It manages all `glusterfsd` (see
below) and also connects to peers to establish membership.

## glusterfs

A client process for volume, running along side with glusterfsd (see below).

## glusterfsd

A glusterfsd daemon will be started for each brick. It is the main worker process in glusterfs. It
accepts tasks from glusterd; interacts with VFS layer, etc.

## glusterd2 (v4.0+)

glusterd2 (gd2) is a re-implementation of glusterd. It attempts to have better consistency, scalability
and performance when compared with the current glusterd, while also becoming more modular and easing
extensibility. For each volume brick, another server daemon (glusterfsd) is running to actually manage
the brick.

## glustercli (v4.0+)

The new cli working with glusterd2.

*References*

- http://www.aifei8.net/glusterfs-glusterfsd-zzact
- https://github.com/gluster/glusterd2/blob/v4.0.0/doc/quick-start-user-guide.md

# Experiments

## Running glusterfs

Bring up a fresh centos vm (using vagrant), then:

```
[vagrant@localhost ~]$ sudo yum -y install glusterfs
[vagrant@localhost ~]$ sudo yum -y install centos-release-gluster
[vagrant@localhost ~]$ sudo yum install glusterfs gluster-cli glusterfs-libs glusterfs-server
[vagrant@localhost ~]$ sudo systemctl start glusterd.service

[vagrant@localhost ~]$ sudo dd if=/dev/zero of=/tmp/store0 bs=512 count=1048576
[vagrant@localhost ~]$ sudo dd if=/dev/zero of=/tmp/store1 bs=512 count=1048576
[vagrant@localhost ~]$ sudo losetup /dev/loop0 /tmp/store0
[vagrant@localhost ~]$ sudo losetup /dev/loop1 /tmp/store1
[vagrant@localhost ~]$ sudo mkfs.xfs /dev/loop0
[vagrant@localhost ~]$ sudo mkfs.xfs /dev/loop1
[vagrant@localhost ~]$ sudo mkdir -p /export/loop0 && sudo mount -t xfs /dev/loop0 /export/loop0 && sudo mkdir -p /export/loop0/brick
[vagrant@localhost ~]$ sudo mkdir -p /export/loop1 && sudo mount -t xfs /dev/loop1 /export/loop1 && sudo mkdir -p /export/loop1/brick

# 192.168.44.44 is the address of this machine; glusterfs prevents us from using
# localhost; also, we 'force' at end of volume creation since two bricks are on
# the same server.
[vagrant@localhost ~]$ sudo gluster volume create testvol replica 2 transport tcp 192.168.44.44:/export/loop0/brick 192.168.44.44:/export/loop1/brick force
volume create: testvol: success: please start the volume to access data
[vagrant@localhost ~]$ sudo gluster volume start testvol
volume start: testvol: success
# Mount and test write to volume.
[vagrant@localhost ~]$ sudo mkdir /mnt/glusterfs
[vagrant@localhost ~]$ sudo mount -t glusterfs localhost:/testvol /mnt/glusterfs
[vagrant@localhost ~]$ sudo touch /mnt/glusterfs/abc

# Clean up.
[vagrant@localhost ~]$ sudo umount /mnt/glusterfs/
[vagrant@localhost ~]$ sudo rm -rf /mnt/glusterfs/
[vagrant@localhost ~]$ sudo gluster volume stop testvol
Stopping volume will make its data inaccessible. Do you want to continue? (y/n) y
volume stop: testvol: success
[vagrant@localhost ~]$ sudo gluster volume delete testvol
Deleting volume will erase all information about the volume. Do you want to continue? (y/n) y
volume delete: testvol: success
[vagrant@localhost ~]$ sudo umount /export/loop0
[vagrant@localhost ~]$ sudo umount /export/loop1
[vagrant@localhost ~]$ sudo losetup -d /dev/loop0
[vagrant@localhost ~]$ sudo losetup -d /dev/loop1
```

## glusterfs quota

Glusterfs can enforce quota on volume or volume directory level. Following is an example of quota
enforcement.

```
# Note it's not necessary to create devices, just use raw directory will suffice.
[vagrant@localhost ~]$ sudo mkdir -p /data/brick1 /data/brick2
[vagrant@localhost ~]$ sudo gluster volume create dirvol replica 2 transport tcp 192.168.44.44:/data/brick1 192.168.44.44:/data/brick2 force
[vagrant@localhost ~]$ sudo gluster volume start dirvol
volume start: testvol: success
[vagrant@localhost ~]$ sudo gluster volume quota dirvol enable
volume quota: success
[vagrant@localhost ~]$ sudo gluster volume quota dirvol limit-usage / 32MB
volume quota : success

# Check if it works by creating multiple files.
[vagrant@localhost ~]$ sudo mkdir /mnt/glusterfs-quota
[vagrant@localhost ~]$ sudo mount -t glusterfs localhost:/dirvol /mnt/glusterfs-quota
[vagrant@localhost ~]$ sudo bash -c 'base64 /dev/urandom | head -c 4000000 > /mnt/glusterfs-quota/4mb.txt'
[vagrant@localhost ~]$ sudo bash -c 'base64 /dev/urandom | head -c 30000000 > /mnt/glusterfs-quota/30mb.txt'
[vagrant@localhost ~]$ sudo bash -c 'base64 /dev/urandom | head -c 1000000 > /mnt/glusterfs-quota/1mb.txt'
bash: /mnt/glusterfs-quota/1mb.txt: Disk quota exceeded
[vagrant@localhost ~]$ sudo gluster volume quota dirvol list
                  Path                   Hard-limit  Soft-limit      Used  Available  Soft-limit exceeded? Hard-limit exceeded?
-------------------------------------------------------------------------------------------------------------------------------
/                                         32.0MB     80%(25.6MB)   32.4MB  0Bytes             Yes                  Yes
[vagrant@localhost ~]$ df -h
Filesystem                       Size  Used Avail Use% Mounted on
...
localhost:/dirvol                 32M   32M     0 100% /mnt/glusterfs-quota
```

# Projects

## gluster swift

Gluster-Swift provides object interface to GlusterFS volumes. It allows files and directories created
on GlusterFS volume to be accessed as objects via the OpenStack Swift and S3 API.

*References*

- [quick start](https://github.com/gluster/gluster-swift/blob/v2.3.0/doc/markdown/quick_start_guide.md)

## gluster csi driver

The [project](https://github.com/gluster/gluster-csi-driver) implements glusterfs csi driver, i.e.
CreateVolume, NodePublishVolume, etc. It uses kubernetes-csi common libraries, and the core logic
uses heketi to interact with glusterfs. When deployed to kubernetes, it uses kubernetes csi helper
tools, i.e. external attacher, external provisioner, etc

## gluster kubernetes

[gluster-kubernetes](https://github.com/gluster/gluster-kubernetes) is a project to provide Kubernetes
administrators a mechanism to easily deploy GlusterFS as a native storage service onto an existing
Kubernetes cluster. That is, running GlusterFS on top of Kubernetes. The project also uses heketi for
clients to use GlusterFS, i.e. all requests go to heketi, which in turn creates volumes. Heketi
topology file is used to discover local block storage.

# References

- https://gluster.readthedocs.io/en/latest/
- https://www.howtoforge.com/tutorial/high-availability-storage-with-glusterfs-on-centos-7/
- http://www.slashroot.in/gfs-gluster-file-system-complete-tutorial-guide-for-an-administrator
- http://events.linuxfoundation.org/sites/events/files/slides/Vault%202016-%20GlusterFS_and_its_distribution_model.pdf
- https://github.com/carmstrong/multinode-glusterfs-vagrant/blob/master/Vagrantfile

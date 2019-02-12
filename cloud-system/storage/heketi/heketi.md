<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Experiments](#experiments)
  - [Build heketi](#build-heketi)
  - [Run heketi server](#run-heketi-server)
  - [Load topology](#load-topology)
  - [Create volume](#create-volume)
- [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

Heketi provides a RESTful management interface which can be used to manage the lifecycle of GlusterFS
volumes. When a request is received to create a volume, Heketi will first allocate the appropriate
storage in a cluster, making sure to place brick replicas across failure domains. It will then format,
mounts the storage to create bricks for the volume requested.

Once all bricks have been automatically created, Heketi will finally satisfy the request by creating,
then starting the newly created GlusterFS volume.

To summarize, the core features provided via heketi is:
- easy to use REST management interface
- topology aware scheduling of glusterfs bricks

*References*

- https://github.com/heketi/heketi
- https://access.redhat.com/documentation/en-US/Red_Hat_Storage/3.1/html/Administration_Guide/ch06s02.html

# Experiments

## Build heketi

Download and build heketi server:

```shell
$ git clone https://github.com/heketi/heketi
$ make all
```

Note: follow `../glusterfs/glusterfs.md` to install glusterfs.

## Run heketi server

Before running heketi server, make sure it can ssh onto glusterfs server. There is also some
requirements, like db file. Here 192.168.44.44 is glusterfs server IP.

```shell
$ cat ~/.ssh/id_rsa.pub | ssh vagrant@192.168.44.44 'cat >> ~/.ssh/authorized_keys'
$ sudo mkdir -p /var/lib/heketi/
```

Now use the following config to start heketi server. Make sure keyfile location is correct:

```json
{
  "port": "8080",
  "use_auth": false,
  "glusterfs": {
    "executor": "ssh",
    "sshexec": {
      "keyfile": "/home/deyuan/.ssh/id_rsa",
      "user": "vagrant",
      "sudo": true
    },
    "db": "/var/lib/heketi/heketi.db",
    "loglevel" : "debug"
  }
}
```

Now start heketi server:

```shell
$ sudo ./heketi --config=/tmp/heketi.conf
$ curl localhost:8080/hello
```

## Load topology

Heketi needs topology in order to create volumes. For this experiment, we create two loop devices:

```shell
[vagrant@localhost ~]$ sudo dd if=/dev/zero of=/tmp/store0 bs=512 count=1048576
[vagrant@localhost ~]$ sudo dd if=/dev/zero of=/tmp/store1 bs=512 count=1048576
[vagrant@localhost ~]$ sudo losetup /dev/loop0 /tmp/store0
[vagrant@localhost ~]$ sudo losetup /dev/loop1 /tmp/store1
[vagrant@localhost ~]$ sudo ./client/cli/go/heketi-cli topology load --json=/tmp/topology.conf
```

Following is the topology:

```json
{
  "clusters": [
    {
      "nodes": [
        {
          "node": {
            "hostnames": {
              "manage": [
                "192.168.44.44"
              ],
              "storage": [
                "192.168.44.44"
              ]
            },
            "zone": 1
          },
          "devices": [
            "/dev/loop0",
            "/dev/loop1"
          ]
        }
      ]
    }
  ]
}
```

After loading the topology, `/dev/loop0` and `/dev/loop1` are added as PV using command `pvcreate`,
then each one is added as a volume group i.e. heketi adds only a single PV into a volume group. See
logs from heketi server:

```
[sshexec] DEBUG 2017/07/11 11:05:52 /src/github.com/heketi/heketi/pkg/utils/ssh/ssh.go:176: Host: 192.168.44.44:22 Command: sudo /bin/bash -c 'pvcreate --metadatasize=128M --dataalignment=256K /dev/loop0'
Result:   Physical volume "/dev/loop0" successfully created.
[sshexec] DEBUG 2017/07/11 11:05:52 /src/github.com/heketi/heketi/pkg/utils/ssh/ssh.go:176: Host: 192.168.44.44:22 Command: sudo /bin/bash -c 'vgcreate vg_5837734e0f3fee39da55df0686532031 /dev/loop0'
Result:   Volume group "vg_5837734e0f3fee39da55df0686532031" successfully created
[sshexec] DEBUG 2017/07/11 11:05:52 /src/github.com/heketi/heketi/pkg/utils/ssh/ssh.go:176: Host: 192.168.44.44:22 Command: sudo /bin/bash -c 'vgdisplay -c vg_5837734e0f3fee39da55df0686532031'
Result:   vg_5837734e0f3fee39da55df0686532031:r/w:772:-1:0:0:0:-1:0:1:1:389120:4096:95:0:95:4RqWFu-OddW-8Nzi-3eGx-dHWZ-xsWs-oW16iz
...
[sshexec] DEBUG 2017/07/11 11:05:53 /src/github.com/heketi/heketi/pkg/utils/ssh/ssh.go:176: Host: 192.168.44.44:22 Command: sudo /bin/bash -c 'pvcreate --metadatasize=128M --dataalignment=256K /dev/loop1'
Result:   Physical volume "/dev/loop1" successfully created.
[sshexec] DEBUG 2017/07/11 11:05:53 /src/github.com/heketi/heketi/pkg/utils/ssh/ssh.go:176: Host: 192.168.44.44:22 Command: sudo /bin/bash -c 'vgcreate vg_2d45ecf00b69177e639b52dbc6c2921a /dev/loop1'
Result:   Volume group "vg_2d45ecf00b69177e639b52dbc6c2921a" successfully created
[sshexec] DEBUG 2017/07/11 11:05:53 /src/github.com/heketi/heketi/pkg/utils/ssh/ssh.go:176: Host: 192.168.44.44:22 Command: sudo /bin/bash -c 'vgdisplay -c vg_2d45ecf00b69177e639b52dbc6c2921a'
Result:   vg_2d45ecf00b69177e639b52dbc6c2921a:r/w:772:-1:0:0:0:-1:0:1:1:389120:4096:95:0:95:Msoyu1-mstc-O6DR-JcUF-ekyf-4Rne-g8Cv4R
[sshexec] DEBUG 2017/07/11 11:05:53 /src/github.com/heketi/heketi/executors/sshexec/device.go:137: Size of /dev/loop1 in 192.168.44.44 is 389120
[heketi] INFO 2017/07/11 11:05:53 Added device /dev/loop1
```

## Create volume

Following command create a volume of 1GB (it won't succeeds since there's not enough space):

```shell
./client/cli/go/heketi-cli volume create --size=1
```

# References

- [glusterfs-dynamic-provisioning-using-heketi-as-external-storage-with-gke](https://medium.com/searce/glusterfs-dynamic-provisioning-using-heketi-as-external-storage-with-gke-bd9af17434e5)

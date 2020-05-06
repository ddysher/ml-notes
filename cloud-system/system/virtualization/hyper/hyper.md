<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Architecture](#architecture)
  - [Overview](#overview)
  - [Components](#components)
- [Experiments](#experiments)
  - [Build 'hyperkernel' and 'hyperstart'](#build-hyperkernel-and-hyperstart)
  - [Build 'hyper' and 'hyperd'](#build-hyper-and-hyperd)
  - [Run hyper](#run-hyper)
  - [Caveats](#caveats)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Architecture

## Overview

The document explains how hyper container works. The work flow is:
1. 'hyper' cli or third-party tools make REST call to hyperd to start/stop/xxx vm containers;
2. when 'hyperd' receives request, it calls underline hypervisor to spawn a new vm (Xen, kvm, etc).
   The VM runs a minimal kernel called 'hyperkernel', which also includes a tiny init service called
   'hyperstart'. runv is the acutal component that launches vm-based container.
3. 'hyperstart' lood images from host, and setup MNT namespace for the containers.

*References*

- http://docs.hypercontainer.io/

## Components

**runv**

runv is equivalent to runc; it is a command line tool and an implementation of oci runtime with vm
hypervisor as its runtime.

**runv-containerd**

runv-containerd is a high performance hypervisor based container daemon. It is similar to
docker-containerd. That is, it's a daemon listening on client request; when requested, it uses runv
to start/kill/etc container.

**hyperd**

hyperd is equivalent to docker daemon - the user-facing daemon.

# Experiments

- *Date: 1/3/2016, 5/1/2016*

## Build 'hyperkernel' and 'hyperstart'

Follow the repositry https://github.com/hyperhq/hyperstart to build hyperkernel and hyperstart. The
output in interest is 'hyper-initrd.img', which is the initrd rootfs for kernel. Another is the
pre-built kernel.

Building 'hyper-initrd.img' is done using 'build/make-initrd.sh' script. Before the script, hyper
already built a binary 'init' from 'src/' directory. Content of this initrd is simply the 'init'
binary plus its dependencies found via 'ldd' program. If virtualbox is used, initrd also contains
virtualbox driver. Also, it will produce a virtualbox iso image to boot directly (isolinux.bin, etc
are vendored in the repository).

'build/kernel' is prebuilt, kernel config file is under 'build/' directory as well. The kernel size
is 2.9M. For linux 4.0.x, alldefconfig produces a kernel with size 6.0M, and allnoconfig is 2.6M. So
the kernel built by hyper is probably based on allnoconfig (or similar 'bare' config) with a few
tweaks. Note 'build/kernel' is actually 'vmlinuz', just a rename.

## Build 'hyper' and 'hyperd'

Follow the repositry https://github.com/hyperhq/hyperd to build hyper and hyperd. If host doesn't
support Xen, then build config with './configure --without-xen'. Note 'runV' is also necessary to
clone since hyperd essentially use runV to start VM to run containers. It is the hypervisor runtime.
When build succeeeds, we get two binaries: 'hyper' and 'hyperd'.

'hyperd' reads its configuration from a file located at '/etc/hyper/config' (can be changed when
launching daemon). The file is in INI format and has several options, e.g.

```
Host   = tcp://localhost:1246
Bios   = /var/lib/hyper/bios.bin
Cbfs   = /var/lib/hyper/cbfs.rom
Kernel = /var/lib/hyper/kernerl-4.0.1
Initrd = /var/lib/hyper/initrd.img
Bridge = hyper0
BridgeIP = 192.168.123.1/24
```

## Run hyper

As mentioned above, we need a configuration file for daemon, start by creating one in '/tmp/hyper/config'
with the following content:

```
Bios   = /tmp/hyper/bios.bin
Cbfs   = /tmp/hyper/cbfs.rom
Kernel = /tmp/hyper/kernel
Initrd = /tmp/hyper/initrd.img
Bridge = hyper0
BridgeIP = 192.168.123.1/24
```

Copy 'kernel', 'hyper-initrd.img' from hyperstart repository to '/tmp/hyper' directory, and rename
to match the configuration file. Also, we need biso.bin and cbfs.rom, which can be fetched from
hyper tarball.

Then we can lauch daemon:

```
# Use --nondaemon to see its output easily
$ sudo ./hyperd --config=/tmp/hyper/config --nondaemon
```

Use './hyper list/create/etc' to create VM container.

## Caveats

- If building qemu from source, make sure use './configure --target-list=x86_64-softmmu --enable-virtfs'.
- Remember to check out to tagged version of hyper; otherwise, it may not work properly, e.g. pod
  keeps in pending state.
- To use a custom kernel, we need to disable cbfs section in the config file, or build a new cbfs
  using `make cbfs`. "cbfstool" can be built from https://github.com/wt/coreboot/tree/master/util/cbfstool.
  E.g. if we want to change the init process, we must create new cbfs; otherwise, we won't see
  changes we made even if we use new initrd.img. Also see https://github.com/hyperhq/hyperstart/issues/71

**TODOs**

- See how 'hyerstart' does the init job
- See how 'runV' implements OCI specification for hypervisor

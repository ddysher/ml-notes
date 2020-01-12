<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Build and run RancherOS](#build-and-run-rancheros)
  - [Install Qemu](#install-qemu)
  - [Get dapper](#get-dapper)
  - [Build RancherOS](#build-rancheros)
  - [Run RancherOS](#run-rancheros)
  - [SSH into RancherOS](#ssh-into-rancheros)
  - [Run RancherOS with VirtualBox](#run-rancheros-with-virtualbox)
- [Projects supporting RancherOS](#projects-supporting-rancheros)
  - [docker-from-scratch](#docker-from-scratch)
- [Others](#others)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Build and run RancherOS

*Date: 1/2/2016*

## Install Qemu

- Linux: $ apt-get install qemu
- MacOS: $ brew install qemu Or $ brew install xhyve

## Get dapper

```
$ go get github.com/rancher/dapper
```

Dapper is a warpper for docker build. It first builds an image based on Dockerfile.dapper, which
contains build environment. It then executes build command within the container. For example,
`dapper make` will build image using Dockerfile.dapper, then run `make` in that container.
Note, to make experiment eaiser, I need to change a few things:
1. For rancher/os's Dockerfile.dapper, add './build ./assets/docker' to the end of DAPPER_OUTPUT,
   which will help inspect build output;
2. Change mv to cp in Makefile to allow re-use downloaded files;
3. Commet out curl kernel and docker to speed up build. (After an initial run which already pulls
   the data).

## Build RancherOS

Steps included in the build script to build RancherOS with `./build.sh --dev`.
1. Use 'dapper' to setup environment and run `make all`, which involves all following steps.
2. Build binary 'rancheros' and save under 'bin/' directory. The binary is built using 'go build'.
3. Grab docker binary from docker website and save to 'assets/' directory.
4. Grab kernel release from rancher github 'os-kernel' repository. The repo contains custom build of
   kernel. Save it to 'build/kernel/'.
5. Build 'images.tar' using script './scripts/mk-images.tar.sh'. This image is simply a tar file
   containing all images for system-wide services, like rancher/os-udev, rancher/os-syslog, etc.
   The image is saved to 'build/' directory.
6. Build 'initrd'. After 'rancheros', 'docker', kernel' and 'images.tar' are ready, we start building
   'initrd', using './scripts/mk-initrd.sh'. It copies a bunch of files into './build/initrd' directory,
   which is the rootfs for kernel, the files including ones from kernel, from rancher/docker:1.9.1-2
   mage (or other version), rancheros binary, docker binary, images.tar etc. After './build/initrd' is
   ready, use cpio to create a archive file under './dist/artifacts/initrd'.
7. Save kernel binary 'vmlinuz' to './dist/artifacts/vmlinuz'.
8. Build docker image 'rancher/os:v0.4.3-dev' using Dockerfile. The container has 'vmlinuz', 'initrd',
   './scripts/installer', './build.conf', and its entrypoint is './scripts/installer/lay-down-os'.
9. Build iso image using './scripts/mk-rancheros-iso.sh'.

Summary: when the build is done, the ISO, vmlinuz and initrd should be in dist/artifacts:
- ISO: iso image of rancher OS;
- vmlinuz: custom build of linux kernel;
- initrd: most of rancher's artifacts are put into initrd (images.tar, bin/rancheros binary, etc).
  bin/rancheros is the 'init' program that kernel calls.

## Run RancherOS

Run rancheros with `./scripts/run`. The scripts basically prepares environment and start RancherOS
using qemu by default:


        exec qemu-system-x86_64 -serial stdio \
            -kernel ${KERNEL} \
            -initrd ${INITRD} \
            -m 1024 \
            -net nic,vlan=0,model=virtio \
            -net user,vlan=0,hostfwd=tcp::2222-:22,hostname=rancher-dev \
            -drive if=virtio,file=${HD} \
            ${KVM_ENABLE} \
            -smp 1 \
            -cdrom ${CLOUD_CONFIG_ISO} \
            -append "${KERNEL_ARGS}" \
            -nographic \
            -display none \
            ${QEMU_ARGS} \
            "${@}"
Where:
- KERNEL=dist/artifacts/vmlinuz;
- INITRD=dist/artifacts/initrd;
- HD=state/hd.img (craeted via `qemu-img create -f raw -o size=10G ${HD}`)
- KVM_ENABLE="-machine accel=kvm -cpu host" (used only if KVM is supported)
- CLOUD_CONFIG_ISO="${BUILD}/cloud-config.iso"
- KERNEL_ARGS={args passed to kernel}
- QEMU_ARGS={other args passed to qemu}

## SSH into RancherOS

After rancherOS started, we see something like below

     INFO[0209] Project [os]: Project started
     DEBU[0209] [4/4] Starting

To connect to rancherOS, we need to use ./scripts/ssh, which simply runs:

     $ ssh -p 2222 -F ./assets/scripts_ssh_config -i ${KEY:-./assets/rancher.key} rancher@localhost "$@"

Port 2222 is forwarded by qemu, see above qemu command '-net' option.

## Run RancherOS with VirtualBox

Just create a machine with Linux 2.6/3.x/4.x and use rancheros.iso for its optical drive; then
rancher OS will boot and give login console.

# Projects supporting RancherOS

## docker-from-scratch

https://github.com/rancher/docker-from-scratch

This repository builds an image that contains the minimal required environment to run docker daemon.
This is used to build "DFS_IMAGE=rancher/docker:1.9.1-2", which when building rancherOS, a container
is created, saved and exported to initrd to provide the environment to run rancherOS system docker.

##kernel repository

https://github.com/rancher/os-kernel and https://github.com/rancher/linux

- https://github.com/rancher/linux is just a fork of linux. Its main job is to host rancher's release (based on ubuntu release).
- https://github.com/rancher/os-kernel contains rancher's custom build of linux kernel. Compiled linux
  kernel is hosted on release page like: https://github.com/rancher/os-kernel/releases/download/Ubuntu-4.2.0-22.27/linux-4.2.6-rancher-x86.tar.gz

# Others

- Look into docker-from-scratch repository. How they run dind. Following command shows what's inside
  this minimal image that supports running docker:
  ```
  $ docker run --name daemon --privileged -d rancher/docker daemon -s aufs
  $ docker export daemon > dind.tar
  $ tar tvf dind.tar
  ```
- See how ./bin/rancheros does the init job: https://github.com/rancher/os

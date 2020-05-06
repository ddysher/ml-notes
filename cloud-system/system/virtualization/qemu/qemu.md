<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Introduction](#introduction)
- [Details](#details)
  - [qcow](#qcow)
  - [qemu & kvm](#qemu--kvm)
- [Experiment](#experiment)
  - [Install Qemu](#install-qemu)
  - [Run Qemu](#run-qemu)
  - [Run Qemu with KVM](#run-qemu-with-kvm)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Introduction

QEMU (short for Quick Emulator) is a free and open-source hosted hypervisor that performs hardware
virtualization. It emulates CPUs through dynamic binary translation and provides a set of
device models, enabling it to run a variety of unmodified guest operating systems.

QEMU is a generic and open source machine emulator and virtualizer. When used as a machine emulator,
QEMU can run OSes and programs made for one machine (e.g. an ARM board) on a different machine (e.g.
your own PC). By using dynamic translation, it achieves very good performance. When used as a
virtualizer, QEMU achieves near native performance by executing the guest code directly on the host
CPU. QEMU supports virtualization when executing under the Xen hypervisor or using the KVM kernel
module in Linux. When using KVM, QEMU can virtualize x86, server and embedded PowerPC, and S390 guests.

# Details

## qcow

qcow (qcow2) is a file format for disk image files used by QEMU, a hosted virtual machine monitor. It
stands for "QEMU Copy On Write" and uses a disk storage optimization strategy that delays allocation
of storage until it is actually needed.

## qemu & kvm

QEMU is a true hypervisor and KVM is just an accelerator. A hypervisor is a virtual machine manager
which creates virutal machines and manages it. A hypervisor where it is running is called a host
machine and the virtual machines created by hypervisor are called guest machine. Since, Kernel based
Virtual Machine (KVM) is just an accelerator. QEMU can exists without kvm, and qemu can manages all
the virtual machines resources such as virtual CPU, virtual hardwares. But, the processing of QEMU
for communication between guest CPU and host CPU is extremely slow. So, there arise a need to best
utilize the communication between virtual machine CPU and host machine CPU. And, this acceleration
part is done later separately through KVM, which only focuses on CPU part and don't other hardware
at all.

- https://www.quora.com/Virtualization/What-is-the-difference-between-KVM-and-QEMU

# Experiment

## Install Qemu

To install Qemu on Mac, just use homebrew:

```
$ brew install qemu
```

To install Qemu on Ubuntu/Debian, use apt-get:

```
$ apt-get install qemu
```

Or install from source following: http://wiki.qemu.org/Hosts/Linux

## Run Qemu

The easiest way to run qemu is to use an iso image:

```
$ qemu-system-x86_64 -m 1024 -cdrom ubuntu-14.04.3-desktop-amd64.iso
```

Note the '-m' option is necessary, otherwise we won't be able to boot. We can also create disk for
the vm:

```
$ qemu-img create -f qcow2 test.qcow2 16G
$ qemu-system-x86_64 -m 1024 -drive if=virtio,file=test.qcow2,cache=none \
      -cdrom ubuntu-14.04.3-desktop-amd64.iso
```

## Run Qemu with KVM

To install KVM, `apt-get install` will suffice on Ubuntu. If KVM is supported, just add option
`--enable-kvm` or `-machine accel=kvm -cpu host`, which is much faser than use full emulation
with Qemu.

- http://www.linuxtechi.com/install-kvm-kernel-based-virtual-machine-on-ubuntu-server-14-10/

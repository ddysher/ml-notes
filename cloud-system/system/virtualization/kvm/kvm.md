<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Introduction](#introduction)
- [Details](#details)
  - [Operation Mode](#operation-mode)
- [Experiment](#experiment)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Introduction

KVM (Kernel Virtual Machine) is a Linux kernel module that allows a user space program to utilize
the hardware virtualization features of various processors. It is a virtualization infrastructure
for the Linux kernel that turns it into a hypervisor.

KVM requires a processor with hardware virtualization extension. By itself, KVM does not perform
any emulation. Instead, it exposes the `/dev/kvm` interface, which a userspace host can then use to
set up the guest VM's address space; feed the guest simulated I/O; map the guest's video display
back onto the host. On Linux, QEMU versions 0.10.1 and later is one such userspace host. QEMU uses
KVM when available to virtualize guests at near-native speeds, but otherwise falls back to software-only
emulation.

# Details

## Operation Mode

Intel VT-x proposed a new mode methodology with two modes: VMX root mode and VMX non-root mode, for
running host VMM and guest respectively. Intel VT-x also contains a new structure: VMCS, which saves
all information both host and guest need. VMCS is one per guest. The `kvm_vcpu_ioctl()` method, under
linux source `virt/kvm/kvm_main.c`, issues commands based on different input. To  run vcpu, it calls
`kvm_arch_vcpu_ioctl_run()`, in which the cpu is first put into guest mode before executing guest code
(guest code can be either application code or guest kernel code).

- https://stackoverflow.com/questions/10922475/how-qemu-kvm-create-a-vm-thread-internally/18595619

# Experiment

- https://github.com/dpw/kvm-hello-world/

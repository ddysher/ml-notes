<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Workflow](#workflow)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

Nvidia docker is a tool to run docker container with GPU support. nvidia-docker v1 is essentially
a wrapper around docker, while nvidia-docker v2 is a more general container runtime.

*References*

- https://devblogs.nvidia.com/nvidia-docker-gpu-server-application-deployment-made-easy/
- https://devblogs.nvidia.com/gpu-containers-runtime/

# Workflow

*Date: 07/21/2019, v2.0.3*

There are three main repositories in nvidia-docker v2:
- https://github.com/NVIDIA/libnvidia-container
- https://github.com/NVIDIA/nvidia-container-runtime
- https://github.com/NVIDIA/nvidia-docker

**libnvidia-container**

libnvidia-container is a low-level library used to configure containers leveraging NVIDIA hardware.
The implementation relies on kernel primitives and is designed to be agnostic of the container
runtime, i.e. it's possible to configure a linux container manually (e.g. set up namespace, rootfs,
and isolate GPU) using libnvidia-container without using any container runtime.

The library includes a command-line utility called `nvidia-container-cli` and also provides an API
for integration into other runtimes (apart from Docker) in the future.

**nvidia-container-runtime**

nvidia-container-runtime contains two components:
- modified runc with a new hook call
- runtime hook implementation

The modification is done by cloning runc source code at a specific commit, apply pre-defined patches,
then build a customized runc binary renamed as nvidia-container-runtime. Here is an example build
process using [Dockerfile.ubuntu](https://github.com/NVIDIA/nvidia-container-runtime/blob/master/runtime/Dockerfile.ubuntu).

The hook binary is called from the [patched runc](https://github.com/NVIDIA/nvidia-container-runtime/blob/03af0a80dbcbcfa09a828cde46151749bee2480e/runtime/runc/96ec2177ae841256168fcf76954f7177af9446eb/0001-Add-prestart-hook-nvidia-container-runtime-hook-to-t.patch),
which parses configs and in turn, calls `nvidia-container-cli`. Most of the setup work is then done
in libnvidia-container. For example, the commonly used environment variable `NVIDIA_VISIBLE_DEVICES`
is defined in the hook binary, which parses the env and passes to `-device` parameter of `nvidia-container-cli`.

**nvidia-docker**

nvidia-docker itself is very simple based on the above two repositories. It is basically packages
for different linux distributions, with a docker config `daemon.json`.

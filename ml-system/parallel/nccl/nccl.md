<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

NCCL is a library of standard collective communication routines for GPUs, implementing MPI-like
interface, i.e. `all-reduce`, `all-gather`, `reduce`, `broadcast`, and `reduce-scatter`.
It has been optimized to achieve high bandwidth on any platform using PCIe, NVLink, NVswitch, as
well as networking using InfiniBand Verbs or TCP/IP sockets.

NCCL is usually integrated into machine learning frameworks like TensorFlow, PyTorch, etc.
- TensorFlow 1.13 moved NCCL to core, i.e. it compiles to TensorFlow and doesn't require additional installation
- Pytorch supports NCCL as the forth communication backend, others being TCP, Gloo and MPI

*References*

- https://github.com/NVIDIA/nccl
- https://medium.com/@auro_227/measuring-nvlink-traffic-when-using-tensorflows-nccl-library-fe4e5b22dcfa

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Horovod and MPI](#horovod-and-mpi)
- [Experiment](#experiment)
- [Blog summary](#blog-summary)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

Horovod is a distributed training framework for TensorFlow. The goal of Horovod is to make distributed
Deep Learning fast and easy to use. Instead of the native distributed TensorFlow workflow (PS-Worker),
horovod uses MPI model, which Uber found to be much more straightforward and require far less code
changes than the Distributed TensorFlow with parameter servers.

# Horovod and MPI

Horovod favors MPI for distributed TensorFlow. In particular, we wrap tensorflow optimizer with
`hvd.DistributedOptimizer`, which delegates computation to tensorflow optimizer, but averages gradients
using allreduce or allgather (MPI operation).

Another aspect is initialization, we use `hvd.BroadcastGlobalVariablesHook` to broadcast (MPI operation)
variable initialization, instead of using master worker. Using MPI is simpler and easy for newcomers
familiar to HPC.

# Experiment

*Date: 11/11/2017, v0.10.2*

To experiment on MacOS with only CPU, install mpi and horovod, and run official example under
`horovod/examples`:

```
brew install mpich2
pip install horovod
mpirun -np 4 -bind-to none python tensorflow_mnist.py
```

# Blog summary

Following is a summary from [blog](https://eng.uber.com/horovod/).

**Reason for choosing tensorflow**

- one of the most popular machine learning frameworks, so easy for newcomers to onboard
- provide both low-level details and higher abstraction (keras)
- support wide variety of machine learning use cases

**Reason for making adjustment to distributed tensorflow**

- many new concepts, hard to change existing code
- performance and GPU utilization is low in stock distributed tensorflow

**Challenges around PS-Worker architecture**

- identifying the right ratio of worker to parameter servers
- handling increased TensorFlow program complexity

**Referenced papers in Horovod**

- "Accurate, Large Minibatch SGD: Training ImageNet in 1 Hour" from Facebook convinced that improving
  training at large scale is possible and can greatly improve developer productivity
- "Bringing HPC Techniques to Deep Learning" from Baidu introduces an algorithm to improve distributed
  tensorflow (ring-allreduce algorithm). Implementation of the algorithm utilizes OpenMPI to setup
  communication infrastructure

**Benchmark**

Scaling using both Inception V3 and ResNet-101 models achieved an 88 percent efficiency mark. In other
words, the training was about twice as fast as standard distributed TensorFlow. Switching to RDMA did
not significantlyimprove performance for Inception V3 and ResNet-101 models, but did improve VGG-16
model, due to its large number of parameters.

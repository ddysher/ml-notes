<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Horovod and MPI](#horovod-and-mpi)
- [Blog summary](#blog-summary)
- [Experiment (usage)](#experiment-usage)
- [Experiment (implementation)](#experiment-implementation)
  - [Build Horovod](#build-horovod)
  - [Develop Horovod](#develop-horovod)
  - [Implementation Detail](#implementation-detail)
- [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

Horovod is a distributed training framework for TensorFlow. The goal of Horovod is to make distributed
Deep Learning fast and easy to use. Instead of the native distributed TensorFlow workflow (PS-Worker),
horovod uses MPI model, which Uber found to be much more straightforward and require far less code
changes than the Distributed TensorFlow with parameter servers.

Horovod is extended to also support other frameworks like Keras, PyTorch, MXNet, etc

# Horovod and MPI

Horovod favors MPI for distributed TensorFlow. It wraps tensorflow optimizer with `hvd.DistributedOptimizer`,
which delegates computation to tensorflow optimizer, but averages gradients using allreduce or
allgather (MPI operations).

Another aspect is initialization, it uses `hvd.BroadcastGlobalVariablesHook` to broadcast (MPI
operation) variable initialization, instead of using master worker. Using MPI is simpler and easy
for newcomers familiar to HPC.

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
not significantly improve performance for Inception V3 and ResNet-101 models, but did improve VGG-16
model, due to its large number of parameters.

# Experiment (usage)

*Date: 11/11/2017, v0.10.2*

To experiment on MacOS with only CPU, install mpi and horovod, and run official example under
`horovod/examples`:

```
brew install mpich2
pip install horovod
mpirun -np 4 -bind-to none python tensorflow_mnist.py
```

# Experiment (implementation)

*Date: 07/27/2019, v0.16.4*

## Build Horovod

Following [contributor guide](https://github.com/horovod/horovod/blob/master/docs/contributors.rst)
to install horovod. To experiment with only TensorFlow (and Keras), run:

```
$ git clone --recursive https://github.com/horovod/horovod.git
# commit id as of experimenting: 4376ac66aec7ef9ec3661ff8dfd1e0e7d61520f8

$ virtualenv env
$ . env/bin/activate

$ pip install tensorflow==1.12.0 # use older version as building with 1.14 failed
$ pip install keras==2.2.4
$ pip install pytest
$ pip install h5py future scipy mpi4py
```

Then build horovod (still in virtual environment):

```
$ cd $HOME
$ pip uninstall -y horovod
$ cd -

$ rm -rf build/ dist/
$ HOROVOD_WITH_TENSORFLOW=1 python setup.py install
```

If any changes are made to horovod, including python source, rebuild is needed:

```
$ HOROVOD_WITH_TENSORFLOW=1 python setup.py install
```

## Develop Horovod

To use newly built horovod, we must run all commands within virtual environment, but outside of
horovod source tree.

The `rank.py` file can be used to verify our build:

```
$ mpirun -np 2 python rank.py
local rank and size (for all processes running in a node)
0
2
global rank and size (for all processes)
0
2
local rank and size (for all processes running in a node)
1
2
global rank and size (for all processes)
1
2
```

The `train.py` file demonstrates the simplest distributed mechanism in horovod, run it via:

```
$ HOROVOD_LOG_LEVEL=debug mpirun -np 2 python train.py
```

The environment variable `HOROVOD_LOG_LEVEL` prints more information to diagnose, ref [PR](https://github.com/horovod/horovod/pull/671).

To leave virtual environment, run:

```
$ deactivate
```

## Implementation Detail

**hvd.init**

The `init()` method invokes `HorovodBasics` class defined in `horovod/common/basics.py`. To verify
this is correct, we can add python statements in `HorovodBasics.init()`, then rebuild horovod and
run the `train.py` script.

`HorovodBasics.init()` calls `MPI_LIB_CTYPES.horovod_init()`, which then invokes methods defined
in `horovod/common/operations.cc`. The C methods then initializes different environment, e.g. MPI,
NCCL, etc.

**hvd.DistributedOptimizer**

This is perhaps the most important part of Horovod; it defines an optimizer on top of framework
optimizer, to efficiently pass gradient tensors across different workers.

Most of the logics are implemented in `horovod/tensorflow/__init__.py`. To simply put, Horovod calls
TensorFlow optimizers to compute the gradients, then it calls ring allreduce (along with allgather,
broadcast) to "exchange" gradients in different workers, i.e.

```shell
# legacy tensorflow v1 optimizer interface
gradients = self._optimizer.compute_gradients(*args, **kwargs)
avg_grads = self._allreduce_grads(grads)
```

All of the data transfer operations are implemented in the `horovod/common/ops` directory, including
MPI, NCCL, Gloo, etc.

# References

- https://towardsdatascience.com/distributed-tensorflow-using-horovod-6d572f8790c4

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Concepts](#concepts)
  - [Fundamentals](#fundamentals)
- [Distributed](#distributed)
  - [Cluster](#cluster)
  - [Parallelism](#parallelism)
    - [Data parallelism](#data-parallelism)
    - [Model Parallelism](#model-parallelism)
  - [Strategy](#strategy)
    - [ParameterServer](#parameterserver)
  - [Summary](#summary)
- [Tensorflow APIs](#tensorflow-apis)
  - [Core API](#core-api)
  - [Layers](#layers)
  - [Estimator](#estimator)
  - [Eager Execution](#eager-execution)
- [Tensorflow Misc](#tensorflow-misc)
  - [XLA](#xla)
  - [Runtime](#runtime)
  - [Codelabs](#codelabs)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Concepts

## Fundamentals

**Tensor**

The central unit of data in TensorFlow is the tensor. A tensor consists of a set of primitive values
shaped into an array of any number of dimensions. A tensor's rank is its number of dimensions. Pay
attention that tensor is **the central unit of DATA**, and it flows through different operators.
Internally, TensorFlow represents tensors as n-dimensional arrays of base datatypes. Note that
`tf.Variable`, `tf.Constant`, `tf.Placeholder`, `tf.SparseTensor` are special tensors (will be
explained separately). For example, `tf.constant(42.0, name="answer")` creates a new tf.Operation
named "answer" and returns a tf.Tensor named "answer:0".
- shape: Number of elements in each dimension.
- rank:  Number of dimensions. Synonyms for rank include order or degree or n-dimension.

For more information:
- https://www.tensorflow.org/guide/tensors

**Graph**

A computational graph is a series of TensorFlow operations arranged into a graph of nodes. Each
node takes zero or more tensors as inputs and produces a tensor as an output. One type of node is
a constant (not a tensor!): it takes no input, and it outputs a value it stores internally.

For more information:
- https://www.tensorflow.org/guide/graphs

**Session**

A session encapsulates the control and state of the TensorFlow runtime. Nothing in a graph will be
evaluated unless running in a session.

Another take: TensorFlow uses the tf.Session class to represent a connection between the client
program -- typically a Python program, although a similar interface is available in other languages
-- and the C++ runtime. A tf.Session object provides access to devices in the local machine, and
remote devices using the distributed TensorFlow runtime. It also caches information about your
tf.Graph so that you can efficiently run the same computation multiple times.

**Operation**

Operation are also nodes. We can build more complicated computations by combining Tensor nodes with
operations. For example, "tf.add" is one type of operation: `node3 = tf.add(node1, node2)` produces
a node based on two nodes.

**Placeholder**

A graph can be parameterized to accept external inputs, known as placeholders. A placeholder is a
promise to provide a value later. Placeholders are used to hold training data, test data, etc. Data
is not set when defining the placeholders; rather, we feed value when running a graph in a session.
e.g.

```python
a = tf.placeholder(tf.float32)
b = tf.placeholder(tf.float32)
adder_node = a + b  # + provides a shortcut for tf.add(a, b)
print(sess.run(adder_node, {a: 3, b: 4.5}))
print(sess.run(adder_node, {a: [1, 3], b: [2, 4]}))
```

**Variable**

Variables allow us to add trainable parameters to a graph, i.e. model parameters. For example, in
linear model `y = W * x + b`, W and b are defined as variable since the goal of training is to
find suitable W and b (x and y are placeholder). Note that until we call sess.run, variables are
uninitialized. e.g.

```python
W = tf.Variable([.3], dtype=tf.float32)
b = tf.Variable([-.3], dtype=tf.float32)
x = tf.placeholder(tf.float32)
linear_model = W * x + b
```

**Optimizers**

TensorFlow provides optimizers that slowly change each variable in order to minimize the loss
function. The simplest optimizer is gradient descent. It modifies each variable according to the
magnitude of the derivative of loss with respect to that variable, e.g.

```python
optimizer = tf.train.GradientDescentOptimizer(0.01)
train = optimizer.minimize(loss)
```

**Device**

Ref:
- https://stackoverflow.com/questions/40061895/what-exactly-is-a-device-in-tensorflow

**Summary (Event)**

Summary is an operation we can add to a computational graph to collect training data. It will write
events to event file, which will then be read out by tensorboard for visualization.

# Distributed

## Cluster

First a little background of how tensorflow works in terms of a single local python process. From
C++ point of view, a local process can be divided into two parts: a master and a worker (note worker
here is different from worker in the "ps-worker" architecture). Master contains client and few other
components; it manages session, while worker manages graph. Master connects to worker, and issues
request to run operations on its graph.

**ClusterSpec**

A TensorFlow cluster comprises of one or more "jobs", each divided into lists of one or more "tasks".
A cluster is typically dedicated to a particular high-level objective, such as training a neural
network, using many machines in parallel. A cluster is defined by a `tf.train.ClusterSpec` object.

**Job/Task**

A job comprises a list of "tasks", which typically serve a common purpose. For example, a job named
ps (for "parameter server") typically hosts nodes that store and update variables; while a job named
worker typically hosts stateless nodes that perform compute-intensive tasks. The tasks in a job
typically run on different machines. The set of job roles is flexible: for example, a worker may
maintain some state.

A task corresponds to a specific TensorFlow server, and typically corresponds to a single process. A
task belongs to a particular "job" and is identified by its index within that job's list of tasks.

**Server**

Tensorflow server is a process running a `tf.train.Server` instance, which is a member of a cluster,
and exports a "master service" and "worker service", see below.

**Client**

Client is the python process which builds the graph, connects to local master via `Session()` or
remote master via `Session("grpc://...")`, and issues `session.run` calls.

Another take: a client is typically a program that builds a TensorFlow graph and constructs a
`tensorflow::Session` to interact with a cluster. Clients are typically written in Python or C++. A
single client process can directly interact with multiple TensorFlow servers, and a single server
can serve multiple clients.

**Master service**

An RPC service that provides remote access to a set of distributed devices, and acts as a session
target. The master service implements the `tensorflow::Session` interface, and is responsible for
coordinating work across one or more "worker services". All TensorFlow servers implement the [master
service.proto](https://github.com/tensorflow/tensorflow/blob/r1.4/tensorflow/core/protobuf/master_service.proto).

**Worker service**

An RPC service that executes parts of a TensorFlow graph using its local devices. All TensorFlow
servers implement the [worker_service.proto](https://github.com/tensorflow/tensorflow/blob/r1.4/tensorflow/core/protobuf/worker_service.proto).

## Parallelism

### Data parallelism

Data parallelism in a distributed training setting is when each replica trains on the same model but
over different data. After every few iterations, all replicas synchronize, either with one-another
(all-reduce) or via a central server (parameter server). 'PS-Worker' is a common architecture for
data parallelism.

**Between-Graph Replication vs In-Graph Replication**

- Both "between-graph" and "in-graph" computation belong to data parallelism
- The recommended approach for distributed training is "between-graph"; "in-graph replication" is
  the first approach in TensorFlow but it did not achieve the expected performance
  - https://stackoverflow.com/questions/41600321/distributed-tensorflow-the-difference-between-in-graph-replication-and-between

### Model Parallelism

Model parallelism is when each replica trains over same data but uses different part of the model.
This is trickier since (a) the model needs to be large enough (memory) to justify going over the
network; (b) the split needs to be careful enough such that the computation/communication is reasonable.

## Strategy

### ParameterServer

'PS-Worker' is a common architecture in data parallelism training, where one or more parameter
server(s) host the models parameters; a chief worker coordinates the training operations, etc; all
workers (including the chief worker) handle compute training steps and send updates to the
parameter servers. Note the term `worker` here is different from that in worker service; both PS
and Woker here are workers in tensorflow, see [tensorflow-ps-workers](./assets/tensorflow-ps-workers.svg).

**Synchronous training**

All the workers will read the parameters at the same time, compute a training operation and wait for
all the others to be done. Then the gradients will be averaged and a single update will be made to
parameters. So at any point in time, the workers will all be aware of the same values for the graph
parameters.

**Asynchronous training**

The workers will read from the parameter server(s) asynchronously, compute their training operation,
and send asynchronous updates. At any point in time, two different workers might be aware of different
values for the graph parameters. If one worker finished an iteration faster than the other workers,
it proceeds with the next iteration without waiting. The workers only interact with the shared
parameter server and don't interact with each other. When one worker updates the weights on the ps
the others will only see the change when they read the variables from the ps again. Asynchronous
training is faster but usually requires more steps to have the same accuracy as synchronous training.

*Reference*

- https://www.tensorflow.org/extend/architecture
- https://stackoverflow.com/questions/43147435/how-does-asynchronous-training-work-in-distributed-tensorflow
- https://stackoverflow.com/questions/34349316/synchronous-vs-asynchronous-computation-in-tensorflow

## Summary

**Job, Task, Server, Client, Master, Worker, etc**

Concepts:
- Job -> Tasks: Job contains identical tasks, each identified by its index in the job's task list.
- Task -> Server: Task runs TensorFlow server, usually a single process.
- Server -> Master/Worker: When running a server (tf.train.Server), both master and worker services will be created.
- Master/Worker: Two RPC services in a TensorFlow server. Client connect to master and master issue commands to workers.

Note that the Distributed Master and Worker Service only exist in distributed TensorFlow. The
single-process version of TensorFlow includes a special Session implementation that does everything
the distributed master does but only communicates with devices in the local process.

**Sync/Asyn Training + Data/Model Parallelism**

There are three basic strategies to train a model with multiple nodes:
- Data-parallel training with synchronous updates.
- Data-parallel training with asynchronous updates.
- Model-parallel training.

The above is quoted from: https://cloud.google.com/ml-engine/docs/distributed-tensorflow-mnist-cloud-datalab

# Tensorflow APIs

## Core API

Tensorflow core API, e.g. tf.train, tf.Variable, etc, is hard to use, it is recommended that machine
learning researchers or others who want fine-grained control over their model to use the core API.
In most cases, higher level APIs like tf.estimator are easier to learn and more consistent across
different users.

## Layers

The TensorFlow layers module provides a high-level API that makes it easy to construct a neural
network. It provides methods that facilitate the creation of dense (fully connected) layers and
convolutional layers, adding activation functions, and applying dropout regularization, e.g.
`tf.layers.conv2d()`.

## Estimator

TensorFlow's high-level machine learning API (tf.estimator) makes it easy to configure, train, and
evaluate a variety of machine learning models. Estimator offers classes you can instantiate to
quickly configure common model types such as regressors and classifiers. Example usage:

```
classifier = tf.estimator.DNNClassifier()
train_input_fn = tf.estimator.inputs.numpy_input_fn()
classifier.train(input_fn=train_input_fn, steps=2000)
```

If none of the predefined model meets your need, one can create custom model as well. The core of
custom model is to implement tf.estimator.EstimatorSpec.

One of the most commonly used method is `train_and_evaluate`, which trains and evaluates a model.
Evaluation happens along side with training, by passing a checkpoint hook to train(), i.e. evaluation
is triggered whenever there is a checkpoint save event.

```python
# python/estimator/training.py

listener_for_eval = _NewCheckpointListenerForEvaluate(
    evaluator, self._eval_spec.throttle_secs,
    self._continuous_eval_listener)
saving_listeners = [listener_for_eval]

self._estimator.train(
    input_fn=self._train_spec.input_fn,
    max_steps=self._train_spec.max_steps,
    hooks=train_hooks,
    saving_listeners=saving_listeners)
```

## Eager Execution

Eager execution is a feature that makes TensorFlow execute operations immediately: concrete values
are returned, instead of a computational graph to be executed later.  This provides more flexibility
for machine learning research and experimentation. As of r1.4, the feature is still in preview.
- https://research.googleblog.com/2017/10/eager-execution-imperative-define-by.html
- https://github.com/tensorflow/tensorflow/blob/f96ea92ea0399635c242e475a8a31c53b459bb2a/tensorflow/contrib/eager/python/g3doc/guide.md

# Tensorflow Misc

## XLA

XLA uses JIT compilation techniques to analyze the TensorFlow graph created by the user at runtime,
specialize it for the actual runtime dimensions and types, fuse multiple ops together and emit
efficient native machine code for them - for devices like CPUs, GPUs and custom accelerators (e.g.
Google’s TPU).
- https://developers.googleblog.com/2017/03/xla-tensorflow-compiled.html

## Runtime

To do efficient numerical computing in Python, we typically use libraries like NumPy that do expensive
operations such as matrix multiplication outside Python, using highly efficient code implemented in
another language. Unfortunately, there can still be a lot of overhead from switching back to Python
every operation. This overhead is especially bad if you want to run computations on GPUs or in a
distributed manner, where there can be a high cost to transferring data. TensorFlow also does its
heavy lifting outside Python, but it takes things a step further to avoid this overhead. Instead of
running a single expensive operation independently from Python, TensorFlow lets us describe a graph
of interacting operations that run entirely outside Python. (Approaches like this can be seen in a
few machine learning libraries.) The role of the Python code is therefore to build this external
computation graph, and to dictate which parts of the computation graph should be run.

## Codelabs

- https://codelabs.developers.google.com/codelabs/tensorflow-for-poets/index.html?index=..%2F..%2Findex#0

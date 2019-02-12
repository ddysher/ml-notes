<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Architecture](#architecture)
  - [Components](#components)
  - [Deployment](#deployment)
- [Flink vs Spark](#flink-vs-spark)
- [Experiment](#experiment)
- [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

https://cwiki.apache.org/confluence/pages/viewpage.action?pageId=65147077

# Overview

[Apache Flink](https://flink.apache.org/) is an open source streaming data flow engine that provides
communication, fault-tolerance, and data-distribution for distributed computations over data streams.
Flink is a top-level project of Apache. It is a scalable data analytics framework that is fully
compatible with Hadoop. Flink can execute both stream processing and batch processing easily.

The key vision for Apache Flink is to overcome and reduces the complexity that has been faced by other
distributed data-driven engines. This is achieved by integrating query optimization, concepts from
database systems and efficient parallel in-memory and out-of-core algorithms, with the MapReduce
framework. Apache Flink's pipelined architecture allows processing the streaming data faster with
lower latency than micro-batch architectures (Spark).

Flink is an alternative to MapReduce, it processes data more than 100 times faster than MapReduce.
It is independent of Hadoop but it can use HDFS to read, write, store, process the data. Flink does
not provide its own data storage system. It takes data from distributed storage. Flink is capable of:
- Batch Processing
- Interactive processing
- Real-time stream processing
- Graph Processing
- Iterative Processing
- In-memory processing

# Architecture

## Components

It is useful to view Flink as four layers:

<p align="center"><img src="./assets/Apache-Flink-ecosystem-components.png" height="360px" width="auto"></p>

- Storage: Flink doesn't have its own storage, but can be integrated into a couple of storage backend.
- Deploy: Flink has local mode and cluster mode (standalone, mesos, yarn, etc), similar to Spark.
- Kernel: Flink's core distributed streaming dataflow. This is the core layer of flink which provides
  distributed processing, fault tolerance, reliability, native iterative processing capability, etc.
- APIs: Flink has two types of APIs, and based on them, Flink has FlinkML, Gelley, Table libraries
  for different use cases.
  - DataSet API: Batch processing API. It is a special case of Stream processing where we have a finite data source.
  - DataStream API: Stream processing API. It handles a continuous stream of the data.

## Deployment

At deployment side, Flink has two components:
- JobManager: job manager runs as master, accepting request from client and dispatch work
- TaskManager: task manager runs on each slave, accepting work from job manager and returns result

An typical workflow in Flink:
- Deploy Flink cluster. Upon starting, TaskManager will register to JobManager, along with its slot.
  Each TaskManager can have multiple task slots to fully utilize node. A task slot is a thread in
  TaskManager JVM, thus it's common to set task slot to the number of physical cores of a node.
- Client submits Job to JobManager. Client can run anywhere as long as it has access to JobManager.
  Before submitting, Flink client will convert user code into dataflow graph. It then finds the
  location of JobManager via configuration and submit the Job.
- JobManager receives request from user, divides the job into multiple tasks and submit each task
  to different TaskManager (to be precise, task slot).
- TaskManager runs task in its JVM process, and reports back task status to JobManager.

<p align="center"><img src="./assets/deployment-architecture.jpg" height="360px" width="auto"></p>

Another execution model diagram below:
- Program: Developer wrote the application program.
- Parse and Optimize: The code parsing, Type Extractor, and Optimization are done during this step(Flink client code).
- DataFlow Graph: Each and every job converts into the data flow graph (Flink client code).
- Job Manager: Now job manager schedules the task on the task managers; keeps the data flow metadata.
  Job manager deploys the operators and monitors the intermediate task results
- Task Manager: The tasks are executed on the task manager, they are the worker nodes.

<p align="center"><img src="./assets/Apache-Flink-execution-model.png" height="360px" width="auto"></p>

# Flink vs Spark

Apache spark and Apache Flink both are open source platform for the batch processing as well as the
stream processing at the massive scale which provides fault-tolerance and data-distribution for
distributed computations. Both are alternative to Hadoop MapReduce.

> Flink is considered the 4G of big data, where 3G is Spark and 2G is MapReduce.

The most important difference is that Spark is batch first, while Flink is streaming first, which
also means for streaming at least, Flink is faster than Spark:
- Spark treats streaming as micro-batch, i.e. streaming data is divided into micro-batch and each
  micro-batch is processed with the same batch processing engine.
- Flink treats batch as a special streaming case, that is, batch is a finite set of streamed data.
  All computation uses the same streaming engine.

*References*

- https://data-flair.training/blogs/comparison-apache-flink-vs-apache-spark/
- https://zhuanlan.zhihu.com/p/36022692
- https://zhuanlan.zhihu.com/p/36024639

# Experiment

*Date: 12/09/2018, v1.7.0*

**Standlone Cluster**

Download Flink:

```
$ wget http://apache.01link.hk/flink/flink-1.7.0/flink-1.7.0-bin-scala_2.12.tgz
$ tar xvf flink-1.7.0-bin-scala_2.12.tgz
$ cd ./flink-1.7.0
```

Start local standalone cluster (run JobManager & TaskManager on local host):

```
$ ./bin/start-cluster.sh
Starting cluster.
Starting standalonesession daemon on host mangosteen.
Starting taskexecutor daemon on host mangosteen.
```

On one terminal, start netcat:

```
$ nc -l 9000
```

On the other terminal, start streaming application:

```
$ ./bin/flink run examples/streaming/SocketWindowWordCount.jar --port 9000
Starting execution of program
```

We can view logs from task executor about our application result:

```
$ tail -f log/flink-deyuan-taskexecutor-0-mangosteen.out
```

**Kubernetes**

As of v1.7.0, running on Kubernetes is quite naive:
- two deployment, one for job manager, the other for task manager
- one service, to expose job manager's rpc port, ui port, etc

Note that when two task manager pods are running on the same node, they will both report node
capacity to job manager, resulting in duplicate task slots.

```
$ cd experiments/kubernetes
$ kubectl create -f .
```

# References

- https://flink.apache.org/
- https://data-flair.training/blogs/apache-flink-tutorial/

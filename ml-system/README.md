<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Development](#development)
  - [Jupyter](#jupyter)
  - [Colaboratory](#colaboratory)
- [Frameworks](#frameworks)
  - [TensorFlow](#tensorflow)
  - [PyTorch](#pytorch)
  - [Keras](#keras)
  - [Theano](#theano)
  - [OpenCV](#opencv)
  - [Dlib](#dlib)
  - [XGBoost](#xgboost)
  - [NumPy](#numpy)
- [Data Management](#data-management)
  - [dvc](#dvc)
  - [Pachyderm](#pachyderm)
- [Model Management](#model-management)
  - [ModelDB](#modeldb)
  - [MLflow](#mlflow)
  - [ONNX](#onnx)
- [Serving](#serving)
  - [Seldon](#seldon)
  - [GraphPipe](#graphpipe)
- [Hadoop](#hadoop)
  - [Overview](#overview)
  - [Spark](#spark)
  - [Flink](#flink)
  - [Flume](#flume)
- [Platforms](#platforms)
  - [FfDL](#ffdl)
  - [Kubeflow](#kubeflow)
  - [PipelineAI](#pipelineai)
  - [RiseML](#riseml)
  - [FloydHub](#floydhub)
  - [Algorithmia](#algorithmia)
  - [OpenPAI (microsoft)](#openpai-microsoft)
  - [Comparison](#comparison)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Development

## Jupyter

ref: [jupyter](./jupyter)

## Colaboratory

A hosted Jupyter environment tool/service from Google. Users can work with Jupyter notebook just as
they would with Google doc. The notebooks are saved in Google Drive.

Code is running in virtual machines dedicated to a user. The environment is suitable for interactive
use cases: long running jobs may be stopped if used inappropriately.

Ref: https://research.google.com/colaboratory/faq.html

# Frameworks

## TensorFlow

ref: [tensorflow](./tensorflow)

## PyTorch

ref: [pytorch](./pytorch)

## Keras

ref: [keras](./keras)

## Theano

Theano is a Python library that allows you to define, optimize, and evaluate mathematical expressions.
It contains many building blocks for deep neural networks. Theano is a low-level library similar to
Tensorflow. Higher-level libraries include Keras and Caffe.

## OpenCV

[OpenCV](http://opencv.org) is an open-source BSD-licensed library that includes several hundreds of
computer vision algorithms. OpenCV has a modular structure, which means that the package includes
several shared or static libraries. As of v4.0.0 (11/2018), the main modules are:
- core. Core functionality (e.g. array operation, hardware acceleration, etc)
- imgproc. Image Processing
- imgcodecs. Image file reading and writing
- videoio. Video I/O
- highgui. High-level GUI
- video. Video Analysis
- calib3d. Camera Calibration and 3D Reconstruction
- features2d. 2D Features Framework
- objdetect. Object Detection
- dnn. Deep Neural Network module (e.g. load models from tensorflow/caffe2/etc)
- ml. Machine Learning (e.g. algorithms like knn/svm/etc)
- flann. Clustering and Search in Multi-Dimensional Spaces
- photo. Computational Photography
- stitching. Images stitching
- gapi. Graph API

There are also a lot of extra modules, see openc docs:: https://docs.opencv.org/4.0.0/

ref: [opencv](./opencv)

## Dlib

[Dlib](http://dlib.net) is a general purpose cross-platform open source software library written in
the C++ programming language. It aims to be a general software library, but now mostly becomes a
toolkit for making real world machine learning and data analysis applications in C++. As mentioned
in its introduction:

> In particular, it now contains software components for dealing with networking, threads, graphical
> interfaces, complex data structures, linear algebra, statistical machine learning, image processing,
> data mining, XML and text parsing, numerical optimization, Bayesian networks, and numerous other
> tasks. In recent years, much of the development has been focused on creating a broad set of statistical
> machine learning tools. However, dlib remains a general purpose library and welcomes contributions of
> high quality software components useful in any domain.

For more information, refer to official Github [repository](https://github.com/davisking/dlib/blob/master/python_examples/face_detector.py).
To experiment with python API, just `pip install dlib` and run `python_examples`.

## XGBoost

ref: [xgboost](./xgboost)

## NumPy

NumPy is the fundamental package for scientific computing with Python. It contains:
- a powerful N-dimensional array object
- sophisticated (broadcasting) functions
- tools for integrating C/C++ and Fortran code
- useful linear algebra, Fourier transform, and random number capabilities

Besides its obvious scientific uses, NumPy can also be used as an efficient multi-dimensional
container of generic data. Arbitrary data-types can be defined. This allows NumPy to seamlessly
and speedily integrate with a wide variety of databases.

# Data Management

## dvc

ref: [dvc](./dvc)

## Pachyderm

ref: [pachyderm](./pachyderm)

# Model Management

## ModelDB

ref: [modeldb](./modeldb)

## MLflow

ref: [mlflow](./mlflow)

## ONNX

ref: [onnx](./onnx)

# Serving

## Seldon

ref: [seldon](./seldon)

## GraphPipe

ref: [graphpipe](./graphpipe)

# Hadoop

## Overview

Currently, **four core modules** are included in Hadoop
- Hadoop Common: the libraries and utilities used by other Hadoop modules.
- Hadoop Distributed File System (HDFS): the Java-based scalable storage system.
- YARN: (Yet Another Resource Negotiator) provides resource management for processes running on Hadoop.
- MapReduce: a parallel processing software framework.

Other software components that can run on top of or alongside Hadoop:
- Ambari: A web interface for managing, configuring and testing Hadoop services and components.
- Cassandra: A distributed database system.
- Flume: Software that collects, aggregates and moves large amounts of streaming data into HDFS.
- HBase: A nonrelational, distributed database that runs on top of Hadoop.
- HCatalog: A table and storage management layer that helps users share and access data.
- Hive: A data warehousing and SQL-like query language that presents data in the form of tables.
- Oozie: A Hadoop job scheduler.
- Pig: A platform for manipulating data stored in HDFS.
- Solr: A scalable search tool that includes indexing, reliability, central configuration, failover and recovery.
- Spark: An open-source cluster computing framework with in-memory analytics.
- Sqoop: A connection and transfer mechanism that moves data between Hadoop and relational databases.
- Zookeeper: An application that coordinates distributed processing.

*References*

- https://www.sas.com/en_us/insights/big-data/hadoop.html

## Spark

ref: [spark](./spark)

## Flink

ref: [flink](./flink)

## Flume

ref: [flume](./flume)

# Platforms

## FfDL

ref: [ffdl](./ffdl)

## Kubeflow

ref: [kubeflow](./kubeflow)

## PipelineAI

ref: [pipelineai](./pipelineai)

## RiseML

ref: [riseml](./riseml)

## FloydHub

Takeaways:
- You can create a workspace within a project by clicking the "Create Workspace" button. You'll be
  able to create a blank workspace or import code from a public GitHub repository to bootstrap your
  workspace.

## Algorithmia

Takeaways:
- deploy autoscaling ml models using serverless microservices
  - upload model, write custom deserialization function then deploy
- catalog your ml portfolio
  - tag, version control AI models
  - easily search AI models
- AI marketplace
  - publish, search and run AI algorithms directly in browser
- data
  - hosted data, AWS, dropbox, etc; for non-hosted data, only connection is given
  - user collections, session collections, permanent collections, and temporary algorithm collections

## OpenPAI (microsoft)

[OpenPAI](https://github.com/Microsoft/pai) is an open source platform that provides complete AI
model training and resource management capabilities, it is easy to extend and supports on-premise,
cloud and hybrid environments in various scale. At its core, PAI runs Hadoop, ML/DL frameworks on
top of Kubernetes. The set of services running on PAI can be found [here](https://github.com/Microsoft/pai/wiki/Resource-Requirement).

## Comparison

*Date: 07/07/2018*

**Scope**

- ffdl: only training (can use seldon for serving)
- pipelineai: [continously] training, serving
- riseml: only training
- seldon: only serving

**Build Image**

- ffdl: training image contains framework library and custom scripts: `load.sh`, `train.sh`, `store.sh`
- pipelineai: pass arguments to cli, which then replaces placeholders in pre-built dockerfile
  template with the arguments.
- riseml: a custom python script, using string concatenation to build docker image; the script
  itself is built inside a docker image.
- seldon: recommend s2i from redhat, but also provide its own wrapper.

**Logging**

- ffdl: logging sidecar & elasticsearch. while the learning job is running, a process runs as a
  sidecar to extract the training data from the learner, and then pushes that data into the TDS,
  which pushes the data into ElasticSearch.
- pipelineai: todo
- riseml: logging sidecar & rabbitmq
- seldon: none

**Monitoring**

- ffdl: sidecar process for each learner (ps, worker) + per job monitoring process
- pipelineai: todo
- riseml: todo
- seldon: none

**Data**

- ffdl: remote storage (upload to s3)
- pipelineai: todo
- riseml: multi-access data volume (PV&PVC)
- seldon: none

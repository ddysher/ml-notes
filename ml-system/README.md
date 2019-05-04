<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Frameworks](#frameworks)
  - [tensorflow](#tensorflow)
  - [pytorch](#pytorch)
  - [keras](#keras)
  - [theano](#theano)
  - [opencv](#opencv)
  - [xgboost](#xgboost)
  - [lightgbm](#lightgbm)
  - [catboost](#catboost)
  - [dlib](#dlib)
  - [numpy](#numpy)
  - [sklearn](#sklearn)
- [Devel](#devel)
  - [jupyter](#jupyter)
  - [colaboratory](#colaboratory)
- [Data](#data)
  - [dali](#dali)
  - [dvc](#dvc)
  - [pachyderm](#pachyderm)
- [Model](#model)
  - [modeldb](#modeldb)
  - [onnx](#onnx)
- [Serving](#serving)
  - [graphpipe](#graphpipe)
  - [seldon](#seldon)
  - [tensorrt](#tensorrt)
- [AutoML](#automl)
  - [nni](#nni)
- [Hadoop](#hadoop)
  - [overview](#overview)
  - [spark](#spark)
  - [flink](#flink)
  - [flume](#flume)
- [Toolkits](#toolkits)
  - [mlflow](#mlflow)
  - [guildai](#guildai)
  - [ludwig](#ludwig)
- [Platforms](#platforms)
  - [ffdl](#ffdl)
  - [kubeflow](#kubeflow)
  - [pipelineai](#pipelineai)
  - [riseml](#riseml)
  - [openpai](#openpai)
  - [comparison](#comparison)
- [Commercial](#commercial)
  - [algorithmia](#algorithmia)
  - [dataiku](#dataiku)
  - [datarobot](#datarobot)
  - [datmo](#datmo)
  - [domino](#domino)
  - [h2o](#h2o)
  - [modelarts](#modelarts)
  - [rapidminer](#rapidminer)
  - [r2.ai](#r2ai)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Frameworks

## tensorflow

link: [tensorflow](../ml-core/tensorflow)

## pytorch

link: [pytorch](./pytorch)

## keras

link: [keras](./keras)

## theano

Theano is a Python library that allows you to define, optimize, and evaluate mathematical expressions.
It contains many building blocks for deep neural networks. Theano is a low-level library similar to
Tensorflow. Higher-level libraries include Keras and Caffe.

## opencv

link: [opencv](./opencv)

## xgboost

XGBoost is an optimized distributed gradient boosting library designed to be highly efficient,
flexible and portable. It implements machine learning algorithms under the Gradient Boosting
framework. XGBoost provides a parallel tree boosting (also known as GBDT, GBM) that solve many
data science problems in a fast and accurate way.

link: [xgboost](./xgboost)

## lightgbm

[LightGBM](https://github.com/Microsoft/LightGBM) is a fast, distributed, high performance gradient
boosting (GBDT, GBRT, GBM or MART) framework based on decision tree algorithms, used for ranking,
classification and many other machine learning tasks.

LightGBM improves on XGBoost. The LightGBM paper uses XGBoost as a baseline and outperforms it in
training speed and the dataset sizes it can handle. The accuracies are comparable.

*References*

- https://harrymoreno.com/2018/10/15/gradient-boosting-decisions-trees-xgboost-vs-lightgbm.html

## catboost

[CatBoost](https://catboost.ai/) is a fast, scalable, high performance open-source gradient boosting
on decision trees library. Catboost improves over LightGBM by handling categorical features better.

## dlib

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

## numpy

NumPy is the fundamental package for scientific computing with Python. It contains:
- a powerful N-dimensional array object
- sophisticated (broadcasting) functions
- tools for integrating C/C++ and Fortran code
- useful linear algebra, Fourier transform, and random number capabilities

Besides its obvious scientific uses, NumPy can also be used as an efficient multi-dimensional
container of generic data. Arbitrary data-types can be defined. This allows NumPy to seamlessly
and speedily integrate with a wide variety of databases.

## sklearn

link: [sklearn](./sklearn)

# Devel

## jupyter

link: [jupyter](./jupyter)

## colaboratory

A hosted Jupyter environment tool/service from Google. Users can work with Jupyter notebook just as
they would with Google doc. The notebooks are saved in Google Drive.

Code is running in virtual machines dedicated to a user. The environment is suitable for interactive
use cases: long running jobs may be stopped if used inappropriately.

Link: https://research.google.com/colaboratory/faq.html

# Data

## dali

DALI is a data pipeline library from NVIDIA to solve a couple issues:
- inconsistent data preprocessing in different frameworks
- CPU bottleneck for training with large amount of data

To simply put, DALI can be seen as a solution for data augmentation primarily for image tasks.
[Supported operations](https://docs.nvidia.com/deeplearning/sdk/dali-developer-guide/docs/supported_ops.html)
include:
- image transformation like resizing, sphere, etc
- data loading for TFRecords, LMDB (Caffe), RecordIO (MXNet), etc

*References*

- https://devblogs.nvidia.com/fast-ai-data-preprocessing-with-nvidia-dali/#
- https://docs.nvidia.com/deeplearning/sdk/dali-developer-guide/docs/index.html

## dvc

link: [dvc](./dvc)

## pachyderm

link: [pachyderm](./pachyderm)

# Model

## modeldb

link: [modeldb](./modeldb)

## onnx

link: [onnx](./onnx)

# Serving

## graphpipe

link: [graphpipe](./graphpipe)

## seldon

link: [seldon](./seldon)

## tensorrt

link: [tensorrt](./tensorrt)

# AutoML

## nni

[NNI (Neural Network Intelligence)](https://github.com/Microsoft/nni) is a toolkit to help users
design and tune machine learning models (e.g., hyperparameters), neural network architectures, or
complex system's parameters, in an efficient and automatic way.

Users submit `Experiment` to nni: each `Experiment` contains source code and configuration, which
include tunning algorithm, search space, etc. Tunner receives search space and generates specific
configurations for each trial. The trials are then submitted to training platform like local machine,
kubernetes, etc.

For souce code, users can either:
- use `nni` SDK to assign hyperparameters, report metrics, etc
- use annotations to implicitly assign hyperparameters, nni will convert the annotations to new code for each trial

*References*

- https://github.com/Microsoft/nni/blob/master/docs/en_US/Overview.md

# Hadoop

## overview

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

## spark

link: [spark](../ml-core/spark)

## flink

link: [flink](./flink)

## flume

link: [flume](./flume)

# Toolkits

## mlflow

link: [mlflow](./mlflow)

## guildai

[Guild](https://github.com/guildai/guildai) is a command line toolkit to run, track, and compare
machine learning experiments. It's similar to mlflow, pipelineai with regard to running task, but
apart from typical commands like `run`, `compare`, etc, it is also capable of performing
hyperparameter tuning, e.g.

```shell
guild run train.py x=uniform[-2.0:2.0] --optimizer bayesian --max-trials 20
```

Guild requires no code change from user - it uses python ast to replace parameter variables.

*References*

- https://github.com/gar1t/2019-sysml
- https://www.sysml.cc/doc/2019/demo_26.pdf

## ludwig

link: [ludwig](./ludwig)

# Platforms

## ffdl

link: [ffdl](./ffdl)

## kubeflow

link: [kubeflow](./kubeflow)

## pipelineai

link: [pipelineai](./pipelineai)

## riseml

link: [riseml](./riseml)

## openpai

[OpenPAI](https://github.com/Microsoft/pai) is an open source platform that provides complete AI
model training and resource management capabilities, it is easy to extend and supports on-premise,
cloud and hybrid environments in various scale. At its core, PAI runs Hadoop, ML/DL frameworks on
top of Kubernetes. The set of services running on PAI can be found [here](https://github.com/Microsoft/pai/wiki/Resource-Requirement).

## comparison

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
- riseml: logging sidecar & rabbitmq
- seldon: none

**Monitoring**

- ffdl: sidecar process for each learner (ps, worker) + per job monitoring process
- seldon: none

**Data**

- ffdl: remote storage (upload to s3)
- riseml: multi-access data volume (PV&PVC)
- seldon: none

# Commercial

## [algorithmia](https://algorithmia.com)

Algorithmia is a commercial platform for deploying and managing machine learning models:
- deploy autoscaling ml models with serverless, i.e. upload model, write custom deserialization function then deploy
- catalog your ml portfolio, that is, tag, version control AI models and easily search AI models
- AI marketplace to publish, search and run AI algorithms directly in browser
- data management
  - hosted data, AWS, dropbox, etc; for non-hosted data, only connection is given
  - user collections, session collections, permanent collections, and temporary algorithm collections

Relavance: 4

## [dataiku](https://www.dataiku.com/)

A platform for data analysts, engineers, and scientists together.
- Collaborative Data Science
- Code Or Click
- Prepare & Enrich
- Model & Predict
- Deploy & Run

Relavance: 3+

## [datarobot](https://www.datarobot.com)

Automated Machine Learning Platform.
- Ingest your data
- Select the target variable
- Build hundreds of models in one click
- Explore top models and get insights
- Deploy the best model

Relavance: 3+

## [datmo](https://www.datmo.com/)

Workflow tools to help experiment, deploy, and scale models:
- Experiment: `datmo environment setup`, etc
- Deploy: `datmo deploy`, etc
- Scale

Relavance: 3

## [domino](https://www.dominodatalab.com/)

Domino Data Science Platform: Domino provides an open, unified data science platform to build,
validate, deliver, and monitor models at scale. This accelerates research, sparks collaboration,
increases iteration speed, and removes deployment friction to deliver impactful models.

Relavance: 5

## [h2o](https://www.h2o.ai)

H2O driverless AI speeds up data science workflows by automating feature engineering, model tuning,
ensembling and model deployment.

Relavance: 2+

## [modelarts](https://www.huaweicloud.com/product/modelarts.html)

From Huawei, modelarts is a platform for model development, training, deployment, etc

Relavance: 5

## [rapidminer](https://rapidminer.com/)

Platform for Data Preparation, Machine Learning and Model Deployment.
- Studio for visual workflow
- Auto Model for building models (automatic machine learning, automatic feature engineering, etc)
- Turbo Prep for intuitive data prep

Relavance: 2

## [r2.ai](https://r2.ai/)

An AI development and deployment platform built with AutoML, including:
- data quality check
- feature processing
- model building

Relavance: 3+

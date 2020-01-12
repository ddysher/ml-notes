<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Frameworks](#frameworks)
  - [Deep Learning](#deep-learning)
  - [Machine Learning](#machine-learning)
- [Numerical](#numerical)
- [Devel](#devel)
- [Data](#data)
- [Model](#model)
- [Parallel](#parallel)
- [AutoML](#automl)
- [Toolkits](#toolkits)
- [Hadoop](#hadoop)
- [Platforms](#platforms)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

> A non-comprehensive list of machine learning libraries, systems, toolkits, etc (that I've investigated).

# Frameworks

## Deep Learning

List of high-level deep learning frameworks.

- [tensorflow](../ml-core/tensorflow)
- [pytorch](./frameworks/pytorch)
- [keras](./frameworks/keras)
- [theano](http://deeplearning.net/software/theano/)
- [chainer](https://chainer.org/)
- [mxnet](https://mxnet.apache.org/)
- [caffe](https://caffe.berkeleyvision.org/)
- [CNTK](https://docs.microsoft.com/en-us/cognitive-toolkit/)
- [paddlepaddle](https://www.paddlepaddle.org.cn/)
- [horovod](./frameworks/horovod)

List of low-level deep learning libraries that can be used independently or to power other deep
learning frameworks.

- [mkl-dnn](./frameworks/mkl-dnn)
- [cudnn](./frameworks/cudnn)
- [magmadnn](./numerical/magma)

## Machine Learning

List of machine learning frameworks, libraries, etc.

- [sklearn](./frameworks/sklearn)
- [opencv](./frameworks/opencv)
- [xgboost](./frameworks/xgboost)
- [lightgbm](./frameworks/lightgbm)
- [catboost](./frameworks/catboost)
- [dlib](./frameworks/dlib)
- [spaCy](https://spacy.io)

# Numerical

List of numerical interfaces, libraries, etc.

- [blas](./numerical/blas)
- [lapack](./numerical/lapack)
- [mkl](./numerical/mkl)
- [cublas](./parallel/cuda)
- [cusparse](./parallel/cuda)
- [magma](./numerical/magma)
- [eigen](./numerical/eigen)
- [numpy](./numerical/numpy)
- [pandas](https://github.com/pandas-dev/pandas)
- [kollas](https://github.com/databricks/koalas)

# Devel

List of projects for developing machine learning algorithms.

- [jupyter](./devel/jupyter)
- [colaboratory](./devel/colaboratory)

# Data

List of projects for processing data, data version control, etc.

- [dali](./data/dali)
- [dvc](./data/dvc)
- [pachyderm](./data/pachyderm)

# Model

List of projects for model management, model representation (e.g. IR), model compiler, model
serving, etc. Many model serving projects also contain a model optimizer for better inference
performance.

- [modeldb](./model/modeldb)
- [onnx](./model/onnx)
- [mmdnn](./model/mmdnn)
- [graphpipe](./model/graphpipe)
- [seldon](./model/seldon)
- [tensorrt](./model/tensorrt)
- [openvino](./model/openvino)

# Parallel

List of projects and algorithsm for parallel computing, high performance computing, networking, etc

- [mpi](./parallel/mpi)
- [nccl](./parallel/nccl)
- [gloo](https://github.com/facebookincubator/gloo)
- [cuda](./parallel/cuda)

Algorithms used in parallel computing or distributed training.

- [ring-allreduce]( http://andrew.gibiansky.com/blog/machine-learning/baidu-allreduce/)

# AutoML

List of projects for automl, including automated feature engineering, hp tuning, auto compression, etc.

- [nni](./automl/nni)

# Toolkits

List of toolkits in various aspects of machine learning.

- [mlflow](./toolkits/mlflow)
- [guildai](./toolkits/guildai)
- [ludwig](./toolkits/ludwig)

# Hadoop

List of projects in Hadoop stack.

- [spark](../ml-core/spark)
- [flink](./hadoop/flink)
- [flume](./hadoop/flume)

# Platforms

List of end-to-end machine learning platforms.

- [ffdl](./platforms/ffdl)
- [kubeflow](./platforms/kubeflow)
- [pipelineai](./platforms/pipelineai)
- [riseml](./platforms/riseml)
- [openpai](./platforms/openpai)

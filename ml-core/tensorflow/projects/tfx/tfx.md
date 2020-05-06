<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [TFX Pipeline](#tfx-pipeline)
  - [Components](#components)
  - [Orchestrator](#orchestrator)
- [TFX Libraries](#tfx-libraries)
  - [TensorFlow Data Validation (TFDV)](#tensorflow-data-validation-tfdv)
  - [TensorFlow Transform (TFT)](#tensorflow-transform-tft)
  - [TensorFlow (TF)](#tensorflow-tf)
  - [TensorFlow Model Analysis (TFMA)](#tensorflow-model-analysis-tfma)
  - [TensorFlow Metadata (TFMD)](#tensorflow-metadata-tfmd)
  - [TensorFlow Serving (TFS)](#tensorflow-serving-tfs)
  - [ML Metadata (MLMD)](#ml-metadata-mlmd)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

TFX is a Google-production-scale machine learning platform based on TensorFlow. It provides a
configuration framework and shared libraries to integrate common components needed to define,
launch, and monitor your machine learning system.

> When you’re ready to go beyond training a single model, or ready to put your amazing model to
> work and move it to production, TFX is there to help you build a complete ML pipeline.

There are two layers in TFX:
- The [tfx library](https://github.com/tensorflow/tfx): This is the library that calls into lower
  level libraries like tfdv, tft, etc, providing the actual user-facing APIs in TFX (called
  `Component`). It also uses orchestrator to connect different components, uses external SQL
  database to save metadata.
- Many low-level libraries like tfdv, tft, tfma, mlmd, etc, that provides the actual component
  implementations. These libraries are not meant to be used by users directly.

*References*

- https://www.tensorflow.org/tfx
- https://github.com/tensorflow/tfx

# TFX Pipeline

## Components

A TFX pipeline is a sequence of components that implement an ML pipeline. A TFX pipeline typically
includes the following components:
- ExampleGen is the initial input component of a pipeline that ingests and optionally splits the input dataset.
- StatisticsGen calculates statistics for the dataset.
- SchemaGen examines the statistics and creates a data schema.
- ExampleValidator looks for anomalies and missing values in the dataset.
- Transform performs feature engineering on the dataset.
- Trainer trains the model.
- Evaluator performs deep analysis of the training results.
- ModelValidator helps you validate your exported models, ensuring that they are "good enough" to be pushed to production.
- Pusher deploys the model on a serving infrastructure.

Components are bridges between libraries and users: components are implmented using libraries and
users use components to construct a pipeline. Because of this, users usually do not directly use
following libraries like `tfdv` or `ml-metadata`: all are encapsulated into components.

For example, in the chicago taxi example, the pipeline is created via a series calls from following
packages:

```python
from tfx.components import CsvExampleGen
from tfx.components import Evaluator
from tfx.components import ExampleValidator
from tfx.components import ModelValidator
from tfx.components import Pusher
from tfx.components import SchemaGen
from tfx.components import StatisticsGen
from tfx.components import Trainer
from tfx.components import Transform
```

while internally, the `tfx.components.SchemaGen` package leverages `tfdv` library to create schema.
For full example, refer to [the sample application](https://github.com/tensorflow/tfx/blob/0.13.0/tfx/examples/chicago_taxi_pipeline/taxi_pipeline_simple.py).

*References*

- https://www.tensorflow.org/tfx/guide/examplegen
- https://github.com/tensorflow/tfx/tree/master/tfx/components

## Orchestrator

Orchestrator is a system that enables composition and execution of above mentioned components.
Orchestrators use well-defined interface from components (refer to `BaseComponent` class), add
them into orchestrator specific DAG, then run the pipeline. Current orchestrator includes:
- apache beam (default)
- apache airflow
- kubelflow pipelines
- google cloud

Internally, tfx imports orchestrator SDK, e.g. `import kfp` for kubeflow pipelines, and use its
SDK to build executable pipelines defined from user code, e.g. argo Yaml. Therefore, similar to
tfx components, user only use tfx orchestration API, and doesn't directly use orchestrator libraries.

*References*

- https://www.tensorflow.org/tfx/guide/orchestra
- https://github.com/tensorflow/tfx/tree/master/tfx/orchestration

# TFX Libraries

## TensorFlow Data Validation (TFDV)

TensorFlow Data Validation (TFDV) is a **library** for exploring and validating machine learning
data. The core features of TFDV is:
- generate statistics of dataset
- dataset visualization (integrate with facets)
- generate schema based on dataset
- validate new dataset against schema
- anomaly detection, such as missing features, out-of-range values

The core API methods includes:

```python
# Generate stats from tfrecord
stats = tfdv.generate_statistics_from_tfrecord(data_location=path)

# Visualize stats
tfdv.visualize_statistics(stats)

# Infer schema from stats
schema = tfdv.infer_schema(stats)

# Assume that other_path points to another TFRecord file
other_stats = tfdv.generate_statistics_from_tfrecord(data_location=other_path)
anomalies = tfdv.validate_statistics(statistics=other_stats, schema=schema)
```

*References*

- https://www.tensorflow.org/tfx/data_validation/get_started
- https://github.com/tensorflow/data-validation

## TensorFlow Transform (TFT)

TensorFlow Transform (TFT) is a **library** for preproessing data with Tensorflow, e.g.

- normalize an input value by mean and standard deviation
- convert strings to integers by generating a vocabulary over all input values
- convert floats to integers by assigning them to buckets based on the observed data distribution

The output of Transform is a TensorFlow graph which can be used for both training and serving.

The `preprocessing function` is the most important concept of tf.Transform, which is a `logical
description` of a transformation to a dataset: TFT provides a canonical implementation with Beam.
There are two kinds of functions used to define preprocessing function:
- Any function that accepts and returns tensors.
- Any of the analyzers provided by `tf.Transform`.

The first kind of functions will add operations to the graph while analyzers won't. Analyzers
include functions like `tf.mean`, `tf.min`, that take input tensor values over the entire dataset
to generate a constant tensor that is returned as the output. Another difference is that first
kinds of functions are essentially batch based, meaning operations are operated on data batch,
while analyzers calculate output based on entire dataset, regardless of batch size.

Following is an example:

```python
import tensorflow as tf
import tensorflow_transform as tft

def preprocessing_fn(inputs):
  x = inputs['x']
  y = inputs['y']
  s = inputs['s']
  x_centered = x - tft.mean(x)
  y_normalized = tft.scale_to_0_1(y)
  s_integerized = tft.compute_and_apply_vocabulary(s)
  x_centered_times_y_normalized = x_centered * y_normalized
  return {
      'x_centered': x_centered,
      'y_normalized': y_normalized,
      'x_centered_times_y_normalized': x_centered_times_y_normalized,
      's_integerized': s_integerized
  }
```

*References*

- https://www.tensorflow.org/tfx/transform/get_started
- https://github.com/tensorflow/transform

## TensorFlow (TF)

The TensorFlow core, used for training models with TFX.

## TensorFlow Model Analysis (TFMA)

TensorFlow Model Analysis (TFMA) is a **library** for evaluating TensorFlow models. It allows users
to evaluate their models on large amounts of data in a distributed manner, using the same metrics
defined in their trainer. These metrics can be computed over different slices of data and visualized
in Jupyter notebooks.

TensorFlow Model Analysis (TFMA) can export a model's *evaluation graph* to a special SavedModel
called `EvalSavedModel`. (Note that the evaluation graph is used and not the graph for training or
inference.) The EvalSavedModel contains additional information that allows TFMA to compute the same
evaluation metrics defined in the model in a distributed manner over a large amount of data f
and user-defined slices.

*References*

- https://www.tensorflow.org/tfx/model_analysis/get_started
- https://github.com/tensorflow/model-analysis

## TensorFlow Metadata (TFMD)

TensorFlow Metadata provides standard representations for metadata that are useful when training
machine learning models with TensorFlow. Essentially, it contains all the serialization formats
used in various libraries, including:
- anomalies.proto
- metric.proto
- path.proto
- problem_statement.proto
- schema.proto
- statistics.proto

*References*

- https://github.com/tensorflow/metadata

## TensorFlow Serving (TFS)

TensorFlow Serving is a flexible, high-performance serving system for machine learning models,
designed for production environments.

*References*

- https://www.tensorflow.org/tfx/guide/serving
- https://github.com/tensorflow/serving

## ML Metadata (MLMD)

ML Metadata (MLMD) is a **library** for recording and retrieving metadata associated with ML
developer and data scientist workflows. MLMD is an integral part of TensorFlow Extended (TFX), but
is designed so that it can be used independently. As part of a broader platform like TFX, most users
only interact with MLMD when examining the results of pipeline components, for example in notebooks
or in TensorBoard.

MLMD keeps track of artifacts pipeline components depend upon (e.g. training data) and produce (e.g.
vocabularies and models). ML Metadata is available as a standalone library and has also been
integrated with TFX components for your convenience. MLMD allows you to discover the lineage of an
artifact (for example what data a model was trained on), find all artifacts created from an artifact
(for example all models trained on a specific dataset), and enables many other use cases.

*References*

- https://www.tensorflow.org/tfx/guide/mlmd
- https://github.com/google/ml-metadata

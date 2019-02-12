<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [TensorFlow Extended](#tensorflow-extended)
  - [TensorFlow Data Validation (TFDV)](#tensorflow-data-validation-tfdv)
  - [Tensorflow Transform](#tensorflow-transform)
  - [TensorFlow Model Analysis (TFMA)](#tensorflow-model-analysis-tfma)
  - [TensorFlow Serving](#tensorflow-serving)
- [TensorFlow Ecosystem](#tensorflow-ecosystem)
  - [TensorFlow Hub](#tensorflow-hub)
  - [TensorFlow Lite](#tensorflow-lite)
  - [TensorFlow Datasets](#tensorflow-datasets)
  - [Horovod](#horovod)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# TensorFlow Extended

## TensorFlow Data Validation (TFDV)

The core features of [tfdv](https://github.com/tensorflow/data-validation) is:
- generate statistics of dataset
- dataset visualization (integrate with facets)
- generate schema based on dataset
- validate new dataset against schema
- anomaly detection, such as missing features, out-of-range values

*References*

- https://github.com/tensorflow/data-validation
- https://www.tensorflow.org/tfx/data_validation/get_started

## Tensorflow Transform

TensorFlow Transform is a library for preproessing data with Tensorflow, e.g.

* Normalize an input value by mean and standard deviation
* Convert strings to integers by generating a vocabulary over all input values
* Convert floats to integers by assigning them to buckets based on the observed data distribution

The output of Transform is a TensorFlow graph which can be used for both training and serving.

*References*

- https://github.com/tensorflow/transform
- https://www.tensorflow.org/tfx/transform/get_started

## TensorFlow Model Analysis (TFMA)

TensorFlow Model Analysis (TFMA) can export a model's evaluation graph to a special SavedModel called
EvalSavedModel. (Note that the evaluation graph is used and not the graph for training or inference.)
The EvalSavedModel contains additional information that allows TFMA to compute the same evaluation
metrics defined in the model in a distributed manner over a large amount of data and user-defined
slices.

*References*

- https://github.com/tensorflow/model-analysis
- https://www.tensorflow.org/tfx/model_analysis/get_started

## TensorFlow Serving

TensorFlow Serving is a flexible, high-performance serving system for machine learning models,
designed for production environments.

*References*

- https://github.com/tensorflow/serving
- https://www.tensorflow.org/serving/

# TensorFlow Ecosystem

## TensorFlow Hub

TensorFlow Hub is a library for the publication, discovery, and consumption of reusable parts of
machine learning models. A module is a self-contained piece of a TensorFlow graph, along with its
weights and assets, that can be reused across different tasks in a process known as transfer
learning.

```python
import tensorflow as tf
import tensorflow_hub as hub

with tf.Graph().as_default():
  module_url = "https://tfhub.dev/google/nnlm-en-dim128-with-normalization/1"
  embed = hub.Module(module_url)
  embeddings = embed(["A long sentence.", "single-word",
                      "http://example.com"])

  with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())
    sess.run(tf.tables_initializer())

    print(sess.run(embeddings))
```

For visual models, it usually works by reusing the feature extraction capabilities from powerful
models trained on large dataset, and then simply train a new classification layer on top. To do
this, the first phase is to analyze all the images on disk and calculates and caches the bottleneck
values for each of them. 'Bottleneck' is an informal term we often use for the layer just before
the final output layer that actually does the classification. (TensorFlow Hub calls this an "image
feature vector".). That is, bottleneck layer outputs the features learned from pretrained model and
pass them to final classification layer. Since each image is iterated multiple times, bottleneck
outputs (for every image) are cached to speed up retrain.

*References*

- https://github.com/tensorflow/hub
- https://www.tensorflow.org/hub/

## TensorFlow Lite

TensorFlow Lite is the official solution for running machine learning models on mobile and embedded
devices with TensorFlow. It enables on-device machine learning inference with low latency and a
small binary size on Android, iOS, and other operating systems. TensorFlow Lite supercedes TensorFlow
Mobile.

TensorFlow Lite is comprised of a runtime on which you can run pre-existing models, and a suite of
tools that you can use to prepare your models for use on mobile and embedded devices. TensorFlow Lite
is not yet designed for training models. Instead, you train a model on a higher powered machine, and
then convert that model to the `.TFLITE` format, from which it is loaded into a mobile interpreter.
The graph converter is included with TensorFlow installation, and is called the `TensorFlow Lite
Optimizing Converter` or TOCO.

*References*

- https://github.com/tensorflow/tensorflow/tree/master/tensorflow/lite
- https://www.tensorflow.org/lite/
- [blog on tf lite conversion improvement (quantization)](https://medium.com/tensorflow/introducing-the-model-optimization-toolkit-for-tensorflow-254aca1ba0a3)

## TensorFlow Datasets

TensorFlow Datasets provides a collection of public datasets (vedio, image, text, etc) ready to use
with TensorFlow. It handles downloading and preparing the data and constructing `a tf.data.Dataset`,
e.g.

```python
import tensorflow_datasets as tfds

# See available datasets
print(tfds.list_builders())

# Construct a tf.data.Dataset
dataset = tfds.load(name="mnist", split=tfds.Split.TRAIN)

# Build your input pipeline
dataset = dataset.shuffle(1000).batch(128).prefetch(tf.data.experimental.AUTOTUNE)
features = dataset.make_oneshot_iterator().get_next()
image, label = features["image"], features["label"]
```

*References*

- https://github.com/tensorflow/datasets

## Horovod

ref: [horovod](./horovod)

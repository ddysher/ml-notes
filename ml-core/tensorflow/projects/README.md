<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [TensorFlow Ecosystem](#tensorflow-ecosystem)
  - [TensorFlow Hub](#tensorflow-hub)
  - [TensorFlow Lite](#tensorflow-lite)
  - [TensorFlow Model Optimization](#tensorflow-model-optimization)
  - [TensorFlow Datasets](#tensorflow-datasets)
  - [TensorFlow Extended](#tensorflow-extended)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

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
values for each of them. `Bottleneck` is an informal term we often use for the layer just before
the final output layer that actually does the classification. (TensorFlow Hub calls this an `image
feature vector`.). That is, bottleneck layer outputs the features learned from pretrained model and
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

## TensorFlow Model Optimization

The TensorFlow Model Optimization Toolkit is a suite of tools for optimizing ML models for deployment
and execution. Among many uses, the toolkit supports techniques used to:
- Reduce latency and inference cost for cloud and edge devices (e.g. mobile, IoT).
- Deploy models to edge devices with restrictions on processing, memory, power-consumption, network usage, and model storage space.
- Enable execution on and optimize for existing hardware or new special purpose accelerators.

TensorFlow Model Optimization provides:
- Sparsity and pruning: Sparse models are those where connections in between operators (i.e. neural
  network layers) have been pruned, introducing zeros to the parameter tensors.
- Quantization: Quantized models are those where we represent the models with lower precision, such
  as 8-bit integers as opposed to 32-bit float. Lower precision is a requirement to leverage certain
  hardware.

*References*

- https://github.com/tensorflow/model-optimization
- https://www.tensorflow.org/model_optimization/guide

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

## TensorFlow Extended

link: [tfx](./tfx)

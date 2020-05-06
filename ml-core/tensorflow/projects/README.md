<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Models & Datasets](#models--datasets)
  - [TensorFlow Models](#tensorflow-models)
  - [TensorFlow Hub](#tensorflow-hub)
  - [TensorFlow Datasets](#tensorflow-datasets)
- [Libraries & Extensions](#libraries--extensions)
  - [TensorFlow Model Optimization](#tensorflow-model-optimization)
  - [TensorFlow Tensor2Tensor](#tensorflow-tensor2tensor)
- [Deployment Targets](#deployment-targets)
  - [TensorFlow Lite (For Mobile & IoT)](#tensorflow-lite-for-mobile--iot)
  - [TensorFlow Extended (For Production)](#tensorflow-extended-for-production)
  - [TensorFlow JS (For JavaScript)](#tensorflow-js-for-javascript)
- [Misc.](#misc)
  - [Multi-Level Intermediate Representation (MLIR)](#multi-level-intermediate-representation-mlir)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

> A collection of projects related to TensorFlow, information about the projects can be found at:

- https://www.tensorflow.org/resources

# Models & Datasets

## TensorFlow Models

The TensorFlow official models are a collection of example models that use TensorFlow's high-level
APIs. They are intended to be well-maintained, tested, and kept up to date with the latest TensorFlow
API. They should also be reasonably optimized for fast performance while still being easy to read.

In short, there is no SDKs for using official models; instead, TensorFlow provide reference
implementations of popular models using TensorFlow high-level APIs like estimator and keras. In
addition, users can download checkpoints of these official model if necessary. To use pretrained
models *within Python code*, see TensorFlow Hub below.

*Reference*

- https://github.com/tensorflow/models/tree/master/official

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

- https://www.tensorflow.org/hub/
- https://github.com/tensorflow/hub

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

- https://www.tensorflow.org/datasets/
- https://github.com/tensorflow/datasets

# Libraries & Extensions

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

There are three different tools available:
- [Pre-optimized models](https://www.tensorflow.org/lite/models), i.e. off-the-shelf models that are ready to be used directly.
- Post-training toolings: post-training toolings are used to optimize an already-trained TensorFlow model, mostly using TensorFlow lite converter.
- Training-time toolings: training-time toolings are used to optimize model while it's being trained, e.g.
  ```python
  import tensorflow as tf
  import tensorflow_model_optimization as tfmot

  model = tf.keras.Sequential([...])

  pruning_schedule = tfmot.sparsity.keras.PolynomialDecay(
                        initial_sparsity=0.0, final_sparsity=0.5,
                        begin_step=2000, end_step=4000)

  model_for_pruning = tfmot.sparsity.keras.prune_low_magnitude(
      model, pruning_schedule=pruning_schedule)
  ...

  model_for_pruning.fit(...)
  ```

*References*

- https://github.com/tensorflow/model-optimization
- https://www.tensorflow.org/model_optimization/guide

## TensorFlow Tensor2Tensor

Tensor2Tensor, or T2T for short, is a library of deep learning models and datasets designed to make
deep learning more accessible and accelerate ML research. T2T was developed by researchers and
engineers in the Google Brain team and a community of users.

In short, T2T is a higher-level abstraction over TensorFlow, providing implementation of many
popular models, as well as dataset. The core concepts in T2T include:
- Problems: Problems consist of features such as inputs and targets, and metadata such as each
  feature's modality (e.g. symbol, image, audio) and vocabularies.
- Models: Models define the core tensor-to-tensor computation. They apply a default transformation
  to each input and output so that models may deal with modality-independent tensors (e.g. embeddings
  at the input; and a linear transform at the output to produce logits for a softmax over classes).
- Datasets: T2T provides datasets across modalities - text, audio, image - available for generation
  and use.

The suggested problems (i.e. models + datasets) are:
- Mathematical Language Understanding
- Story, Question and Answer
- Image Classification
- Image Generation
- Language Modeling
- Sentiment Analysis
- Speech Recognition
- Summarization
- Translation

Both [problems](https://github.com/tensorflow/tensor2tensor/tree/v1.15.0/tensor2tensor/data_generators),
[models](https://github.com/tensorflow/tensor2tensor/tree/v1.15.0/tensor2tensor/models) and
[datasets](https://github.com/tensorflow/tensor2tensor#adding-a-dataset) can be added easily
following T2T guidelines (e.g. by subclassing `t2t_model.T2TModel`). To use T2T, simply run:

```
t2t-trainer \
  --generate_data \
  --data_dir=./t2t_data \
  --output_dir=./t2t_train/mnist \
  --problem=image_mnist \
  --model=shake_shake \
  --hparams_set=shake_shake_quick \
  --train_steps=1000 \
  --eval_steps=100
```

T2T It is now in maintenance mode, superceded by library [Trax](https://github.com/google/trax).

*References*

- https://github.com/tensorflow/tensor2tensor

# Deployment Targets

## TensorFlow Lite (For Mobile & IoT)

TensorFlow Lite is the official solution for running machine learning models on mobile and embedded
devices with TensorFlow. It enables on-device machine learning inference with low latency and a
small binary size on Android, iOS, and other operating systems. TensorFlow Lite supercedes TensorFlow
Mobile.

TensorFlow Lite is comprised of a runtime on which you can run pre-existing models, and a suite of
tools that you can use to prepare your models for use on mobile and embedded devices. TensorFlow Lite
is not yet designed for training models; instead, you train a model on a higher powered machine, and
then convert that model to the `.TFLITE` format, from which it is loaded into a mobile interpreter.
The graph converter is included with TensorFlow installation, and is called the `TensorFlow Lite
Optimizing Converter` or TOCO. For example,

```python
converter = tf.lite.TFLiteConverter.from_saved_model(export_dir)
tflite_model = converter.convert()
```

In summary, TensorFlow Lite consists of two main components:
- The TensorFlow Lite interpreter, which runs specially optimized models on many different hardware
  types, including mobile phones, embedded Linux devices, and microcontrollers.
- The TensorFlow Lite converter, which converts TensorFlow models into an efficient form for use by
  the interpreter, and can introduce optimizations to improve binary size and performance.

*References*

- https://www.tensorflow.org/lite/
- https://github.com/tensorflow/tensorflow/tree/master/tensorflow/lite
- [introducing-the-model-optimization-toolkit-for-tensorflow](https://medium.com/tensorflow/introducing-the-model-optimization-toolkit-for-tensorflow-254aca1ba0a3)

## TensorFlow Extended (For Production)

link: [tfx](./tfx)

## TensorFlow JS (For JavaScript)

TensorFlow.js (TFJS) is a JavaScript Library for training and deploying machine learning models in
the browser and in Node.js. TFJS use cases include:
- Use [off-the-shelf JavaScript models](https://github.com/tensorflow/tfjs-models)
  or convert Python TensorFlow models, e.g. [Keras H5](https://www.tensorflow.org/js/tutorials/conversion/import_keras),
  [TensorFlow SavedModel](https://www.tensorflow.org/js/tutorials/conversion/import_saved_model),
  to run in the browser or under Node.js.
- Retrain pre-existing ML models using your own data.
- Build and train models directly in JavaScript using flexible and intuitive APIs.

The primary use case is to convert models trained from Python, convert to TFJS format and then run
inference in browser.

There is a high-level project built on top of TFJS called [ml5js](https://ml5js.org/).

# Misc.

## Multi-Level Intermediate Representation (MLIR)

[MLIR](https://github.com/tensorflow/mlir) is a common graph representation and legalization
framework, a common set of optimization and conversion passes and a full code generation pipeline.

MLIR is now part of LLVM project.

*References*

- https://www.tensorflow.org/js/
- https://github.com/tensorflow/tfjs

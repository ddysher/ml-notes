<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Concepts](#concepts)
  - [Model](#model)
  - [Layer](#layer)
  - [Backend](#backend)
  - [Preprocessing](#preprocessing)
  - [Callbacks](#callbacks)
  - [Application](#application)
  - [Others](#others)
- [Experiments](#experiments)
  - [Vision Models](#vision-models)
  - [Keras Specific](#keras-specific)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

[Keras](https://keras.io/) is a high-level neural networks API, written in Python and capable of
running on top of TensorFlow, CNTK, or Theano. It was developed with a focus on enabling fast
experimentation.

# Concepts

## Model

[Model](https://github.com/keras-team/keras/blob/2.2.2/docs/templates/models/about-keras-models.md) is the core concept in keras; there are two main types of model as of v2.2:
- [sequential model](https://github.com/keras-team/keras/blob/2.2.2/docs/templates/getting-started/sequential-model-guide.md): linear stack of models, simple yet powerful
- [model class used with functional API](https://github.com/keras-team/keras/blob/2.2.2/docs/templates/getting-started/functional-api-guide.md): for complex models, flexible but complicated

## Layer

Just the old-school [layer](https://github.com/keras-team/keras/blob/2.2.2/docs/templates/layers/about-keras-layers.md)
concept we use in deep learning. Keras has quite a few built-in layers, including:
- Core Layers
- Convolutional Layers
- Pooling Layers
- Locally-connected Layers
- Recurrent Layers
- Embedding Layers
- Merge Layers
- Advanced Activations Layers
- Normalization Layers
- Noise Layers
- Layer Wrappers

Refer to official site for detailed layers in each category.

## Backend

Keras is a model-level library, providing high-level building blocks for developing deep learning
models. It does not handle itself low-level operations such as tensor products, convolutions and
so on. Instead, it relies on a specialized, well-optimized tensor manipulation library to do so,
serving as the "backend engine" of Keras. For more information, see [this](https://github.com/keras-team/keras/blob/2.2.2/docs/templates/backend.md).

Keras doesn't provide a thorough guide on how to implement a backend; at its core, a backend
implements a bunch of methods for Keras to call, see [this article](https://hackernoon.com/the-meeshkan-keras-backend-covers-100-of-the-keras-public-api-why-this-matters-8207cb601f19)
for a case study.

## Preprocessing

Keras provides preprocessing tools for Sequence, Text and Image.

## Callbacks

A callback is a set of functions to be applied at given stages of the training procedure. You can
pass a list of callbacks (as the keyword argument callbacks) to the .fit() method of the Sequential
or Model classes. The relevant methods of the callbacks will then be called at each stage of the
training.

Callback must inherit abstract class `keras.callbacks.Callback`. There are couple of builtin
callbacks, e.g. LearningRateScheduler, ModelCheckpoint, ReduceLROnPlateau, etc.

## Application

Keras Applications are deep learning models that are made available alongside pre-trained weights,
e.g. Xception, VGG16, VGG19, ResNet50, InceptionV3, etc. These models can be used for prediction,
feature extraction, and fine-tuning.

Weights are downloaded automatically when instantiating a model. They are stored at ~/.keras/models/.

Ref: https://github.com/keras-team/keras-applications

## Others

Keras has built-in tools, algorithms for deep learning, including but not limited to:
- losses
- metrics
- activations
- optimizers
- initializers: set initial random weights of Keras layers.
- regularizers
- constraints: setting constraints (eg. non-negativity) on network parameters during optimization
- visualization
- sklean-wrapper
- etc

# Experiments

Experiments are based on official [examples @ version v2.2](https://github.com/keras-team/keras/blob/2.2.2/examples).
Sorted in increasing difficulty.

## Vision Models

Basic Models using keras Sequential model:

- mnist_mlp.py: Trains a simple deep multi-layer perceptron on the MNIST dataset.
- mnist_cnn.py: Trains a simple convnet on the MNIST dataset.
- cifar10_cnn.py: Trains a simple deep CNN on the CIFAR10 small images dataset.
- cifar10_resnet.py: Trains a ResNet on the CIFAR10 small images dataset.

## Text & sequences examples

- pretrained_word_embeddings.py: Loads pre-trained word embeddings (GloVe embeddings)
  into a frozen Keras Embedding layer, and uses it to train a text classification
  model on the 20 Newsgroup dataset.

## Keras Specific

- antirectifier: Demonstrates how to [write custom layers for Keras](https://github.com/keras-team/keras/blob/2.2.2/docs/templates/layers/writing-your-own-keras-layers.md).

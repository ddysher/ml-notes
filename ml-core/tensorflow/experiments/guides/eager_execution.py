#!/usr/bin/env python
#
# Programmers' Guide to Eager Execution.
#
# TensorFlow's eager execution is an imperative programming environment that
# evaluates operations immediately, without an extra graph-building step.
#
# https://www.tensorflow.org/guide/eager

from __future__ import print_function

import os
import tensorflow as tf
import tensorflow.contrib.eager as tfe

os.environ['TF_CPP_MIN_LOG_LEVEL']='2'

# Enable eager execution.
tf.enable_eager_execution()

#
# A toy dataset of points around 3 * x + 2
#
NUM_EXAMPLES = 1000
training_inputs = tf.random_normal([NUM_EXAMPLES])
noise = tf.random_normal([NUM_EXAMPLES])
training_outputs = training_inputs * 3 + 2 + noise

def prediction(input, weight, bias):
  return input * weight + bias

# A loss function using mean-squared error
def loss(weights, biases):
  error = prediction(training_inputs, weights, biases) - training_outputs
  return tf.reduce_mean(tf.square(error))

# Return the derivative of loss with respect to weight and bias
def grad(weights, biases):
  with tfe.GradientTape() as tape:
    loss_value = loss(weights, biases)
  return tape.gradient(loss_value, [weights, biases])

train_steps = 200
learning_rate = 0.01
# Start with arbitrary values for W and B on the same batch of data
W = tfe.Variable(5.)
B = tfe.Variable(10.)

print("Initial loss: {:.3f}".format(loss(W, B)))

for i in range(train_steps):
  dW, dB = grad(W, B)
  W.assign_sub(dW * learning_rate)
  B.assign_sub(dB * learning_rate)
  if i % 20 == 0:
    print("Loss at step {:03d}: {:.3f}".format(i, loss(W, B)))

print("Final loss: {:.3f}".format(loss(W, B)))
print("W = {}, B = {}".format(W.numpy(), B.numpy()))


#
# Use objects for state during eager execution
#
# With graph execution, program state (such as the variables) is stored in global
# collections and their lifetime is managed by the tf.Session object. In contrast,
# during eager execution the lifetime of state objects is determined by the
# lifetime of their corresponding Python object.

with tf.device("cpu:0"):
  v = tfe.Variable(tf.random_normal([1000, 1000]))
  v = None  # v no longer takes up CPU

#
# Work with graphs
#
# While eager execution makes development and debugging more interactive, TensorFlow
# graph execution has advantages for distributed training, performance optimizations,
# and production deployment. However, writing graph code can feel different than
# writing regular Python code and more difficult to debug.
#
# For building and training graph-constructed models, the Python program first
# builds a graph representing the computation, then invokes Session.run to send
# the graph for execution on the C++-based runtime. This provides:
#  - Automatic differentiation using static autodiff.
#  - Simple deployment to a platform independent server.
#  - Graph-based optimizations (common subexpression elimination, constant-folding, etc.).
#  - Compilation and kernel fusion.
#  - Automatic distribution and replication (placing nodes on the distributed system).
#
# Deploying code written for eager execution is more difficult: either generate
# a graph from the model, or run the Python runtime and code directly on the server.

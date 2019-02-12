#!/usr/bin/env python

from __future__ import print_function

import os
import tensorflow as tf
import horovod.tensorflow as hvd

# Horovod: initialize Horovod.
hvd.init()

# Model parameters
W = tf.Variable([.3], dtype=tf.float32)
b = tf.Variable([-.3], dtype=tf.float32)

# Model input and output
x = tf.placeholder(tf.float32)
y = tf.placeholder(tf.float32)
linear_model = W * x + b

# loss
loss = tf.reduce_sum(tf.square(linear_model - y)) # sum of the squares

# TensorFlow provides optimizers that slowly change each variable (here, W and
# b) in order to minimize the loss function. The simplest optimizer is gradient
# descent.
optimizer = tf.train.GradientDescentOptimizer(0.01)

# Horovod: add Horovod Distributed Optimizer.
optimizer = hvd.DistributedOptimizer(optimizer)

train = optimizer.minimize(loss)

# Horovod: broadcast initial variable states from rank 0 to all other processes.
hooks = [hvd.BroadcastGlobalVariablesHook(0)]

# training data
x_train = [1, 2, 3, 4]
y_train = [0, -1, -2, -3]

# training loop
init = tf.global_variables_initializer()

with tf.train.MonitoredTrainingSession(hooks=hooks) as sess:
  sess.run(init)                # reset values
  for i in range(100):
    sess.run(train, {x: x_train, y: y_train})

  # evaluate training accuracy
  curr_W, curr_b, curr_loss = sess.run([W, b, loss], {x: x_train, y: y_train})
  print("W: %s b: %s loss: %s"%(curr_W, curr_b, curr_loss))

  # only print the loss
  print(sess.run(loss, {x: x_train, y: y_train}))

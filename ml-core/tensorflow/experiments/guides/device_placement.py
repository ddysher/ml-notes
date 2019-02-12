#!/usr/bin/env python
#
# Programmers' Guide to using GPUs
#
# https://www.tensorflow.org/guide/using_gpu

from __future__ import print_function

import os
import tensorflow as tf

os.environ['TF_CPP_MIN_LOG_LEVEL']='2'

# If a TensorFlow operation has both CPU and GPU implementations, the GPU devices
# will be given priority when the operation is assigned to a device. For example,
# matmul has both CPU and GPU kernels. On a system with devices cpu:0 and gpu:0,
# gpu:0 will be selected to run matmul.

# Creates a graph.
a = tf.constant([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], shape=[2, 3], name='a')
b = tf.constant([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], shape=[3, 2], name='b')
c = tf.matmul(a, b)
# Creates a session with log_device_placement set to True.
sess = tf.Session(config=tf.ConfigProto(log_device_placement=True))
# Runs the op.
print(sess.run(c))

print("----------------")

# If you would like a particular operation to run on a device of your choice instead
# of what's automatically selected for you, you can use 'with tf.device' to create
# a device context such that all the operations within that context will have the
# same device assignment.

# If there is GPU, the output will be:
#
#  Device mapping:
#  /job:localhost/replica:0/task:0/gpu:0 -> device: 0, name: Tesla K40c, pci bus
#  id: 0000:05:00.0
#  b: /job:localhost/replica:0/task:0/cpu:0
#  a: /job:localhost/replica:0/task:0/cpu:0
#  MatMul: /job:localhost/replica:0/task:0/gpu:0
#  [[ 22.  28.]
#   [ 49.  64.]]
#
# Notice that `a` and `b` are assigned to cpu:0 as requested; while tf.matmul will
# run on gpu:0. Tensorflow will automatically copy tensor between devices; in this
# case, copy `a` and `b` from cpu:0 to gpu:0.

# Creates a graph.
with tf.device('/cpu:0'):
  a = tf.constant([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], shape=[2, 3], name='a')
  b = tf.constant([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], shape=[3, 2], name='b')
c = tf.matmul(a, b)

# Creates a session with log_device_placement set to True.
sess = tf.Session(config=tf.ConfigProto(log_device_placement=True))

# Runs the op.
run_metadata = tf.RunMetadata()
run_options = tf.RunOptions(
  trace_level=tf.RunOptions.FULL_TRACE,
  output_partition_graphs=True)
print(sess.run(c, options=run_options, run_metadata=run_metadata))
print(run_metadata)

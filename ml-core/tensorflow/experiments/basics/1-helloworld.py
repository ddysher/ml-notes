#!/usr/bin/env python
#
# Tensorflow "hello world" to verify installation.

from __future__ import print_function

import os
import tensorflow as tf

# To disable warnings like the following:
#  2017-10-29 14:23:11.397434: W tensorflow/core/platform/cpu_feature_guard.cc:45] The TensorFlow library wasn't compiled to use SSE4.2 instructions, but these are available on your machine and could speed up CPU computations.
#  2017-10-29 14:23:11.397466: W tensorflow/core/platform/cpu_feature_guard.cc:45] The TensorFlow library wasn't compiled to use AVX instructions, but these are available on your machine and could speed up CPU computations.
#  2017-10-29 14:23:11.397472: W tensorflow/core/platform/cpu_feature_guard.cc:45] The TensorFlow library wasn't compiled to use AVX2 instructions, but these are available on your machine and could speed up CPU computations.
#  2017-10-29 14:23:11.397477: W tensorflow/core/platform/cpu_feature_guard.cc:45] The TensorFlow library wasn't compiled to use FMA instructions, but these are available on your machine and could speed up CPU computations.
os.environ['TF_CPP_MIN_LOG_LEVEL']='2'

# Define a constant in tensorflow computation graph, signature:
#  def constant(value, dtype=None, shape=None, name="Const", verify_shape=False):
hello = tf.constant('Hello, TensorFlow!')

# Define a session. Session is an environment in which "Operation" objects are
# executed, and "Tensor" objects are evaluated.
sess = tf.Session()

# Runs operations and evaluates tensors in `fetches`.
print(sess.run(hello))
sess.close()

#!/usr/bin/env python
#
# Tensorflow "hello world" to verify installation.

from __future__ import print_function

import os
import tensorflow as tf

os.environ['TF_CPP_MIN_LOG_LEVEL']='2'

# x = tf.random_uniform([4, 10])
# sess = tf.Session()

# # Runs operations and evaluates tensors in `fetches`.
# print(sess.run(x))
# sess.close()

dataset1 = tf.data.Dataset.from_tensor_slices(tf.random_uniform([4, 10]))
print(dataset1)

a = tf.constant([[1],
                 [3]])
print(a)

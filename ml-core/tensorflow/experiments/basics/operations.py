#!/usr/bin/env python
#
# Operation APIs

from __future__ import print_function

import os
import tensorflow as tf

os.environ['TF_CPP_MIN_LOG_LEVEL']='2'

# Enable eager execution.
tf.enable_eager_execution()

# clip values to be within specified range.
v = tf.constant([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
print(tf.clip_by_value(v, 2.5, 4.5))

# using reduce_mean
print(tf.reduce_mean(v))    # reduce mean (all dimensions) - 3.5
print(tf.reduce_mean(v, 0)) # reduce mean (first dimension) - [2.5, 3.5, 4.5]

# using regularizer.
weights = tf.constant([[1.0, 2.0], [-3.0, 4.0]])
print(tf.contrib.layers.l1_regularizer(0.5)(weights))
print(tf.contrib.layers.l2_regularizer(0.5)(weights))

# using argmax; return index of max number.
A = [[1,3,4,5,6]]
B = [[1,3,4], [2,4,1]]
print(tf.argmax(A, 1))
print(tf.argmax(B, 1))

#!/usr/bin/env python

from __future__ import division, print_function, absolute_import

import tensorflow as tf
from tensorflow.contrib import autograph

def square_if_positive(x):
  if x > 0:
    x = x * x
  else:
    x = 0.0
  return x

# Print the converted tensorflow code.
print(autograph.to_code(square_if_positive))

# Usually, we use the function as graph operator.
tf_square_if_positive = autograph.to_graph(square_if_positive)
with tf.Graph().as_default():
  # The result works like a regular op: takes tensors in, returns tensors.
  # You can inspect the graph using tf.get_default_graph().as_graph_def()
  g_out1 = tf_square_if_positive(tf.constant( 9.0))
  g_out2 = tf_square_if_positive(tf.constant(-9.0))
  with tf.Session() as sess:
    print('Graph results: %2.2f, %2.2f\n' % (sess.run(g_out1), sess.run(g_out2)))

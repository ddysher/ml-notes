#!/usr/bin/env python

from __future__ import print_function

import os
import tensorflow as tf

os.environ['TF_CPP_MIN_LOG_LEVEL']='2'

# W and b are variables since they will be changed during training.
# x is placeholder to be injected with training data.
W = tf.Variable([.3], dtype=tf.float32)
b = tf.Variable([-.3], dtype=tf.float32)
x = tf.placeholder(tf.float32)
linear_model = W * x + b        # y = 0.3 * x - 0.3

# This initializes all variables, i.e, W, b
init = tf.global_variables_initializer()
sess = tf.Session()
sess.run(init)

# Now give input x = [1, 2, 3, 4], returns the prediction y. The second argument
# of run method is called 'feed_dict', which means caller should feed a dictionary
# of values to our previously defined placeholders.
#
# Session.run() method runs one "step" of TensorFlow computation, by running the
# necessary graph fragment to execute every `Operation` and evaluate every `Tensor`
# in the first argument, substituting the values in `feed_dict` for the corresponding
# input values. In the following call, tensorflow will perform a depth-first search
# to find all ops in order to run the graph. Note this doesn't have to be a whole
# graph, it can be a graph fragment.
#
# tf.Session.run requires you to specify a list of fetches, which determine the
# return values, and may be a tf.Operation, a tf.Tensor, or a tensor-like type such
# as tf.Variable. These fetches determine what subgraph of the overall tf.Graph
# must be executed to produce the result: this is the subgraph that contains all
# operations named in the fetch list, plus all operations whose outputs are used
# to compute the value of the fetches.
print(sess.run(linear_model, {x: [1, 2, 3, 4]}))

# This shows that our input data is x = [1, 2, 3, 4], y = [0, -1, -2, -3]; and the
# parameters we provided, i.e. W = [.3], b = [-.3], gives an error value of 23.66.
y = tf.placeholder(tf.float32)
squared_deltas = tf.square(linear_model - y)
loss = tf.reduce_sum(squared_deltas)
print(sess.run(loss, {x: [1, 2, 3, 4], y: [0, -1, -2, -3]})) # 23.66

# Re-assign W and b to perfect value.
fixW = tf.assign(W, [-1.])
fixb = tf.assign(b, [1.])
sess.run([fixW, fixb])
print(sess.run(loss, {x: [1, 2, 3, 4], y: [0, -1, -2, -3]})) # 0

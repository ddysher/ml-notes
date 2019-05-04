#!/usr/bin/env python
#
# Save model using "tf.saved_model.simple_save". Partially from:
#  https://medium.com/epigramai/tensorflow-serving-101-pt-1-a79726f7c103

import os
import tensorflow as tf

tf.app.flags.DEFINE_string('model_dir', '/tmp/tfmodel', 'Export directory.')
FLAGS = tf.app.flags.FLAGS

placeholder_name = 'a'
operation_name = 'add'

a = tf.placeholder(tf.int32, name=placeholder_name)
b = tf.constant(10)

# This is our model. Model input is 'a', output is 'add'.
add = tf.add(a, b, name=operation_name)

with tf.Session() as sess:
  # Run a few operations to make sure our model works.
  ten_plus_two = sess.run(add, feed_dict={a: 2})
  print('10 + 2 = {}'.format(ten_plus_two))

  ten_plus_ten = sess.run(add, feed_dict={a: 10})
  print('10 + 10 = {}'.format(ten_plus_ten))

  # Now save our model.

  # Pick out the model input and output tensor.
  a_tensor = sess.graph.get_tensor_by_name(placeholder_name + ':0')
  sum_tensor = sess.graph.get_tensor_by_name(operation_name + ':0')

  # Build a input/output dictionary.
  input_tensor, output_tensor = {}, {}
  input_tensor['inputs_1'] = a_tensor
  output_tensor['output1'] = sum_tensor

  # Use "tf.saved_model.simple_save" to save our model.
  tf.saved_model.simple_save(
    sess, FLAGS.model_dir,
    inputs=input_tensor, outputs=output_tensor)

  print("Model saved in path: %s" % FLAGS.model_dir)

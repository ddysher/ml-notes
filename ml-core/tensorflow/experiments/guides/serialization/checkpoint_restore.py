#!/usr/bin/env python
#
# Run `python checkpoint_save.py` first to generated saved graph and variables.
#
# https://blog.metaflow.fr/tensorflow-saving-restoring-and-mixing-multiple-models-c4c94d5d7125

from __future__ import print_function

import os
import tensorflow as tf

os.environ['TF_CPP_MIN_LOG_LEVEL']='2'

#
# Restoring operations and other metadata with "tf.train.import_meta_graph".
#

graph = tf.Graph() # Use a different graph here for simplicity and expliciticity.
with graph.as_default():
  # Let's load a previously saved meta graph in the graph.
  # This function returns a Saver.
  saver = tf.train.import_meta_graph('results/graph.ckpt.meta')

  # Finally we can retrieve tensors, operations, collections, etc. For example:
  W1 = graph.get_tensor_by_name('NN/W1:0')

  predictions = graph.get_operation_by_name('Accuracy/predictions')
  train_op = tf.get_collection('train_op')
  loss = tf.get_collection('Loss')

  inputs_placeholder = graph.get_tensor_by_name('Placeholder/inputs_placeholder:0')
  labels_placeholder = graph.get_tensor_by_name('Placeholder/labels_placeholder:0')

  with tf.Session() as sess:
    # Here we'll get an error if we try to use 'W1' directly, since importing
    # meta graph will not initialize variables/weights.
    #
    # print("W1 : %s" % W1.eval())

    # Instead, we should init the variables, run different operations just as
    # we'll do with a newly created graph.
    init_op = tf.global_variables_initializer()
    sess.run(init_op)
    print("W1:\n%s" % W1.eval())

#
# Restoring the weights with "saver.restore".
#

# Create some variables.
W1 = tf.get_variable("NN/W1", shape=[10, 1])
W2 = tf.get_variable("NN/W2", shape=[10, 1])

# Add ops to save and restore all the variables.
saver = tf.train.Saver()

# Later, launch the model, use the saver to restore variables from disk, and
# do some work with the model.
with tf.Session() as sess:
  # Restore variables from disk.
  saver.restore(sess, "results/graph.ckpt")
  print("Model restored.")
  # Check the values of the variables.
  print("W1:\n %s" % W1.eval())
  print("W2:\n %s" % W2.eval())

# import the inspect_checkpoint library
from tensorflow.python.tools import inspect_checkpoint as chkp

# print all tensors in checkpoint file
chkp.print_tensors_in_checkpoint_file(
  "results/graph.ckpt",
  tensor_name='', all_tensors=True, all_tensor_names=True)
print()

# print only a single tensor in checkpoint file
chkp.print_tensors_in_checkpoint_file(
  "results/graph.ckpt",
  tensor_name='NN/b1', all_tensors=False, all_tensor_names=False)
print()

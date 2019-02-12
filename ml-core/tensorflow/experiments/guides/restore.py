#!/usr/bin/env python
#
# Run `python save.py` first to generated saved graph and variables.
#
# https://www.tensorflow.org/guide/saved_model

from __future__ import print_function

import os
import tensorflow as tf

# import the inspect_checkpoint library
from tensorflow.python.tools import inspect_checkpoint as chkp

os.environ['TF_CPP_MIN_LOG_LEVEL']='2'

tf.reset_default_graph()

# Create some variables.
v1 = tf.get_variable("v1", shape=[3])
v2 = tf.get_variable("v2", shape=[5])

# Add ops to save and restore all the variables.
saver = tf.train.Saver()

# Later, launch the model, use the saver to restore variables from disk, and
# do some work with the model.
with tf.Session() as sess:
  # Restore variables from disk. Note: There is not a physical file called
  # /tmp/model.ckpt. It is the prefix of filenames created for the checkpoint.
  # Users only interact with the prefix instead of physical checkpoint files.
  saver.restore(sess, "/tmp/tf_save/model.ckpt")
  print("Model restored.")
  # Check the values of the variables
  print("v1 : %s" % v1.eval())
  print("v2 : %s" % v2.eval())

# print all tensors in checkpoint file
chkp.print_tensors_in_checkpoint_file("/tmp/model.ckpt", tensor_name='', all_tensors=True, all_tensor_names=True)

# tensor_name:  v1
# [ 1.  1.  1.]
# tensor_name:  v2
# [-1. -1. -1. -1. -1.]

# print only tensor v1 in checkpoint file
chkp.print_tensors_in_checkpoint_file("/tmp/model.ckpt", tensor_name='v1', all_tensors=False, all_tensor_names=False)

# tensor_name:  v1
# [ 1.  1.  1.]

# print only tensor v2 in checkpoint file
chkp.print_tensors_in_checkpoint_file("/tmp/model.ckpt", tensor_name='v2', all_tensors=False, all_tensor_names=False)

# tensor_name:  v2
# [-1. -1. -1. -1. -1.]

#!/usr/bin/env python
#
# https://www.tensorflow.org/guide/saved_model

from __future__ import print_function

import os
import tensorflow as tf

os.environ['TF_CPP_MIN_LOG_LEVEL']='2'

# Create some variables.
v1 = tf.get_variable("v1", shape=[3], initializer = tf.zeros_initializer)
v2 = tf.get_variable("v2", shape=[5], initializer = tf.zeros_initializer)

inc_v1 = v1.assign(v1+1)
dec_v2 = v2.assign(v2-1)

# Add an op to initialize the variables.
init_op = tf.global_variables_initializer()

# Add ops to save and restore all the variables.
saver = tf.train.Saver()

# Later, launch the model, initialize the variables, do some work, and save the
# variables to disk.
with tf.Session() as sess:
  sess.run(init_op)
  # Do some work with the model.
  inc_v1.op.run()
  dec_v2.op.run()
  # Save the variables to disk.
  save_path = saver.save(sess, "/tmp/tf_save/model.ckpt")
  print("Model saved in path: %s" % save_path)

# Export as human-readable text. The schema of the protocol buffer (MetaGraphDef)
# can be found at tensorflow/tensorflow/core/protobuf; some other definitions can
# be found at tensorflow/tensorflow/core/framework.
saver.export_meta_graph("/tmp/tf_save/model.ckpt.meta.json", as_text=True)

#!/usr/bin/env python

from __future__ import print_function

import tensorflow as tf
from tensorflow.python.saved_model import signature_constants
from tensorflow.python.saved_model import tag_constants


tf.app.flags.DEFINE_string('model_dir', '/tmp/mnist_model/1',
                           'Directory with model proto')
FLAGS = tf.app.flags.FLAGS


with tf.Session(graph=tf.Graph()) as sess:
  # Load the SavedModel.
  model = tf.saved_model.loader.load(sess, [tag_constants.SERVING], FLAGS.model_dir)
  # Print the input/output of the model, i.e. signature. The protocol buffer
  # locates at tensorflow/tensorflow/core/protobuf.
  print(model.meta_info_def)
  print(model.signature_def[signature_constants.DEFAULT_SERVING_SIGNATURE_DEF_KEY])

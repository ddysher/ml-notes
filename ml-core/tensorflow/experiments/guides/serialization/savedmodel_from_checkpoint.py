#!/usr/bin/env python
#
# Create SavedModel from checkpoint.

from __future__ import print_function

import os

import tensorflow as tf
from tensorflow.python.framework import graph_util,graph_io
from tensorflow.python.platform import gfile

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

restore_graph = tf.Graph()
with tf.Session(graph=restore_graph) as sess:
  restore_saver =  tf.train.import_meta_graph('results/graph.ckpt.meta')
  restore_saver.restore(
     sess, tf.train.latest_checkpoint('results'))

  input_tensor = {}
  input_tensor['inputs_1'] = sess.graph.get_tensor_by_name(
    'Placeholder/inputs_placeholder:0')
  output_tensor = {}
  output_tensor['output1'] = sess.graph.get_tensor_by_name(
    'Accuracy/predictions:0')

  tf.saved_model.simple_save(
    sess, export_dir='/tmp/tfckptmodel',
    inputs=input_tensor, outputs=output_tensor)

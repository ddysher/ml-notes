#!/usr/bin/env python
#
# https://medium.com/epigramai/tensorflow-serving-101-pt-1-a79726f7c103

import os
import tensorflow as tf
from tensorflow.python.saved_model import builder as saved_model_builder
from tensorflow.python.saved_model import signature_constants
from tensorflow.python.saved_model import signature_def_utils
from tensorflow.python.saved_model import tag_constants
from tensorflow.python.saved_model.utils import build_tensor_info

tf.app.flags.DEFINE_string('model_dir', '/tmp/simple_model',
                           'Model export directory.')
tf.app.flags.DEFINE_integer('model_version', 1, 'version number of the model.')
FLAGS = tf.app.flags.FLAGS

placeholder_name = 'a'
operation_name = 'add'

a = tf.placeholder(tf.int32, name=placeholder_name)
b = tf.constant(10)

# This is our model
add = tf.add(a, b, name=operation_name)

with tf.Session() as sess:
  # Run a few operations to make sure our model works
  ten_plus_two = sess.run(add, feed_dict={a: 2})
  print('10 + 2 = {}'.format(ten_plus_two))

  ten_plus_ten = sess.run(add, feed_dict={a: 10})
  print('10 + 10 = {}'.format(ten_plus_ten))

  # Pick out the model input and output
  a_tensor = sess.graph.get_tensor_by_name(placeholder_name + ':0')
  sum_tensor = sess.graph.get_tensor_by_name(operation_name + ':0')

  # Build TensorInfo proto, which has information about a Tensor necessary
  # for feeding or retrieval, see tensorflow/core/protobuf/meta_graph.proto
  model_input = build_tensor_info(a_tensor)
  model_output = build_tensor_info(sum_tensor)

  # Build SignatureDef proto, i.e. a signature definition for tfserving.
  # The key here (placeholder_name, operation_name) are user provided and
  # can be any string, but tensorflow provides a few default constants.
  signature_definition = signature_def_utils.build_signature_def(
      inputs={placeholder_name: model_input},
      outputs={operation_name: model_output},
      method_name=signature_constants.PREDICT_METHOD_NAME)

  builder = saved_model_builder.SavedModelBuilder(
      os.path.join(FLAGS.model_dir, str(FLAGS.model_version)))

  # Adds the current meta graph to the SavedModel and saves variables.
  builder.add_meta_graph_and_variables(
      sess, [tag_constants.SERVING],
      signature_def_map={
          signature_constants.DEFAULT_SERVING_SIGNATURE_DEF_KEY:
          signature_definition
      })

  # Save the model so we can serve it with a model server :)
  builder.save()

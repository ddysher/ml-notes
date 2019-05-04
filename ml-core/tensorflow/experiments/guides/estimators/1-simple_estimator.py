#!/usr/bin/env python
#
# Tensorflow estimator "hello world".

from __future__ import print_function

# numpy is often used to load, manipulate and preprocess data.
import numpy as np
import tensorflow as tf

# Declare list of features. We only have one numeric feature. There are many
# other types of columns that are more complicated and useful.
feature_columns = [tf.feature_column.numeric_column("x", shape=[1])]

# An estimator is the front end to invoke training (fitting) and evaluation
# (inference). There are many predefined types like linear regression,
# linear classification, and many neural network classifiers and regressors.
# The following code provides an estimator that does linear regression.
estimator = tf.estimator.LinearRegressor(feature_columns=feature_columns)

# TensorFlow provides many helper methods to read and set up data sets. Here
# we use two data sets: one for training and one for evaluation. We have to
# tell the function how many passes of data (num_epochs) we want and how big
# each batch should be. Then we use 'tf.estimator.inputs.numpy_input_fn()',
# which returns an input function to be called later in estimator.train() to
# fetch data. There are similar method like 'tf.estimator.inputs.pandas_input_fn()'.
x_train = np.array([1., 2., 3., 4.])
y_train = np.array([0., -1., -2., -3.])
x_eval = np.array([2., 5., 8., 1.])
y_eval = np.array([-1.01, -4.1, -7, 0.])
input_fn = tf.estimator.inputs.numpy_input_fn(
  {"x": x_train}, y_train, batch_size=4, num_epochs=None, shuffle=True)
train_input_fn = tf.estimator.inputs.numpy_input_fn(
  {"x": x_train}, y_train, batch_size=4, num_epochs=1000, shuffle=False)
eval_input_fn = tf.estimator.inputs.numpy_input_fn(
  {"x": x_eval}, y_eval, batch_size=4, num_epochs=1000, shuffle=False)

# We can invoke 1000 training steps by invoking the method and passing the
# training data set.
estimator.train(input_fn=input_fn, steps=1000)

# Here we evaluate how well our model did.
train_metrics = estimator.evaluate(input_fn=train_input_fn)
eval_metrics = estimator.evaluate(input_fn=eval_input_fn)
print("train metrics: %r"% train_metrics)
print("eval metrics: %r"% eval_metrics)

# Our model seems good, export it.
import tempfile
temp_export_dir = tempfile.mkdtemp()
print('Saving model to: %s' % temp_export_dir)

# When we are training our model we set up some infrastructure to feed input to
# the graph (typically batches from a training dataset), however, when we switch
# to 'serving' we will often read our input from somewhere else, and we need some
# separate infrastructure which replaces the input of the graph used for training.
# To simply put, in most cases, 'serving_input_receiver_fn' receives tf.Example,
# which is loaded using a placeholder. It is then parsed using parse_example,
# which takes expected features to be extracted.
# Ref: https://tensorflow.org/guide/saved_model#using_savedmodel_with_estimators
def serving_input_receiver_fn():
  """Builds the serving inputs."""
  example_string = tf.placeholder(shape=[None], dtype=tf.string)
  features = tf.parse_example(
    example_string,
    tf.feature_column.make_parse_example_spec(feature_columns))
  return tf.estimator.export.ServingInputReceiver(
    features, {'example_proto': example_string})

estimator.export_saved_model(
  temp_export_dir, serving_input_receiver_fn)

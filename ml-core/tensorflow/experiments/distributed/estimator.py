#  Copyright 2016 The TensorFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""Distributed Estimator

The example uses 'tf.estimator.train_and_evaluate', most of the code are the
same as tutorials/cnn_mnist.py. In fact, the goal of estimator design is to make
it transparent for model developers to run training/evaluation on local and
distributed environment. Therefore, the code here can run both locally and in
a distributed manner.

For more information, see:
 - https://towardsdatascience.com/how-to-configure-the-train-and-evaluate-loop-of-the-tensorflow-estimator-api-45c470f6f8d
 - https://www.tensorflow.org/api_docs/python/tf/estimator/train_and_evaluate
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import tensorflow as tf

tf.logging.set_verbosity(tf.logging.INFO)


def cnn_model_fn(features, labels, mode):
  """Model function for CNN."""
  # Input Layer
  input_layer = tf.reshape(features["x"], [-1, 28, 28, 1])

  # Convolutional Layer #1
  conv1 = tf.layers.conv2d(
    inputs=input_layer,
    filters=32,
    kernel_size=[5, 5],
    padding="same",
    activation=tf.nn.relu)

  # Pooling Layer #1
  pool1 = tf.layers.max_pooling2d(inputs=conv1, pool_size=[2, 2], strides=2)

  # Convolutional Layer #2
  conv2 = tf.layers.conv2d(
    inputs=pool1,
    filters=64,
    kernel_size=[5, 5],
    padding="same",
    activation=tf.nn.relu)

  # Pooling Layer #2
  pool2 = tf.layers.max_pooling2d(inputs=conv2, pool_size=[2, 2], strides=2)

  # Flatten tensor into a batch of vectors
  pool2_flat = tf.reshape(pool2, [-1, 7 * 7 * 64])

  # Dense Layer
  dense = tf.layers.dense(inputs=pool2_flat, units=1024, activation=tf.nn.relu)

  # Dropout
  dropout = tf.layers.dropout(
    inputs=dense, rate=0.4, training=mode == tf.estimator.ModeKeys.TRAIN)

  # Logits layer
  logits = tf.layers.dense(inputs=dropout, units=10)

  # Generate predictions (for PREDICT and EVAL mode)
  predictions = {
    "classes": tf.argmax(input=logits, axis=1),
    "probabilities": tf.nn.softmax(logits, name="softmax_tensor")
  }
  if mode == tf.estimator.ModeKeys.PREDICT:
    return tf.estimator.EstimatorSpec(mode=mode, predictions=predictions)

  # Calculate loss (for both TRAIN and EVAL modes)
  onehot_labels = tf.one_hot(indices=tf.cast(labels, tf.int32), depth=10)
  loss = tf.losses.softmax_cross_entropy(
    onehot_labels=onehot_labels, logits=logits)

  # Configure the Training Op (for TRAIN mode)
  if mode == tf.estimator.ModeKeys.TRAIN:
    optimizer = tf.train.GradientDescentOptimizer(learning_rate=0.001)
    train_op = optimizer.minimize(
      loss=loss,
      global_step=tf.train.get_global_step())
    return tf.estimator.EstimatorSpec(mode=mode, loss=loss, train_op=train_op)

  # Add evaluation metrics (for EVAL mode)
  # Note we pass 'predictions' to EstimatorSpec as well to support
  # custom metrics.
  eval_metric_ops = {
    "accuracy": tf.metrics.accuracy(
      labels=labels, predictions=predictions["classes"])}
  return tf.estimator.EstimatorSpec(
    mode=mode, loss=loss, predictions=predictions,
    eval_metric_ops=eval_metric_ops)


def compute_rmse(labels, predictions):
  pred_values = predictions['classes']
  # labels is 'int32' while pred_values is 'int64'. The conversion is
  # adapted from tf.metrics.accuracy.
  if labels.dtype != pred_values.dtype:
    from tensorflow.python.ops import math_ops
    pred_values = math_ops.cast(pred_values, labels.dtype)
  return {
    'rmse': tf.metrics.root_mean_squared_error(labels, pred_values)
  }


def main(unused_argv):
  # Load training and eval data (as np.array)
  mnist = tf.contrib.learn.datasets.load_dataset("mnist")
  train_data = mnist.train.images
  train_labels = np.asarray(mnist.train.labels, dtype=np.int32)
  eval_data = mnist.test.images
  eval_labels = np.asarray(mnist.test.labels, dtype=np.int32)

  # Create the Estimator; asking that checkpointing be done every 30 seconds
  # (to limit CPU overhead) and that only the last 3 checkpoints are saved
  # (to limit storage overhead):
  classifier = tf.estimator.Estimator(
    model_fn=cnn_model_fn, model_dir="/tmp/mnist_convnet_model",
    config = tf.estimator.RunConfig(
      save_checkpoints_secs=30, keep_checkpoint_max=3))

  # The estimator has only 'accuracy' as the evaluation metrics; here, we
  # create a new estimator with our custom 'rmse' metric. Note in this example,
  # we can of course add the metrics in the above model_fn, but we add it
  # here to demonstrate its usage, as we are not always able to modify estimator
  # implementation.
  classifier = tf.contrib.estimator.add_metrics(classifier, compute_rmse)

  # Train spec. Pay attention to the parameters here:
  # - batch_size: gradients are computed on training examples one batch at a time
  # - num_epochs: number of epochs to iterate over all data; 'None' means forever
  # - shuffle: shuffle data to have different workers working on different data,
  #   as well as avoiding overfitting
  # - max_steps: the TrainSpec requires the maximum number of steps for which to
  #   train the model. Note that this is max_steps, and not steps. If you have a
  #   checkpoint corresponding to step#1800 and you specify max_steps=2000, then
  #   training will resume at 1800 and go on for just 200 steps
  train_input_fn = tf.estimator.inputs.numpy_input_fn(
    x={"x": train_data}, y=train_labels,
    batch_size=100, num_epochs=None, shuffle=True)
  train_spec = tf.estimator.TrainSpec(
    input_fn=train_input_fn, max_steps=2000)

  # Eval spec. Pay attention to the parameters as well.
  # - batch_size: during evaluation, the only reason to read data in batches is
  #   to avoid over-allocating memory buffers
  # - num_epochs: number of epochs to iterate over all data; for evaluation, we
  #   only iterate data once
  # - shuffle: do not shuffle data
  # - steps: when evaluating, you can evaluate on the entire dataset by specifying
  #   steps=None in the EvalSpec
  # - start_delay_secs: start evaluating after N seconds
  # - throttle_secs: evaluate every N seconds
  eval_input_fn = tf.estimator.inputs.numpy_input_fn(
    x={"x": eval_data}, y=eval_labels,
    num_epochs=1, shuffle=False)
  eval_spec = tf.estimator.EvalSpec(
    input_fn=eval_input_fn, steps=None,
    start_delay_secs=15, throttle_secs=30)

  tf.estimator.train_and_evaluate(classifier, train_spec, eval_spec)


if __name__ == "__main__":
  tf.app.run()

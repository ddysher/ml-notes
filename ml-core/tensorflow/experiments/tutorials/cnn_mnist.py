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

"""Convolutional Neural Network Estimator for MNIST, built with tf.layers.

The MNIST dataset comprises 60,000 training examples and 10,000 test examples
of the handwritten digits 0-9, formatted as 28x28-pixel monochrome images.

From:
  https://github.com/tensorflow/tensorflow/blob/r1.4/tensorflow/examples/tutorials/layers/cnn_mnist.py
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import tensorflow as tf

tf.logging.set_verbosity(tf.logging.INFO)

# cnn_model_fn takes feature data (MNIST data), labels, and model mode (TRAIN,
# EVAL, PREDICT) as arguments; configures the CNN; and returns predictions,
# loss, and a training operation, as estimator spec.
def cnn_model_fn(features, labels, mode):
  """Model function for CNN."""
  # Input Layer
  #
  # The methods in the layers module for creating convolutional and pooling
  # layers for two-dimensional image data expect input tensors to have a shape
  # of [batch_size, image_height, image_width, channels] by default. This
  # behavior can be changed using the data_format parameter. Thus, here, we
  # reshape features["x"] to 4-D tensor: [batch_size, width, height, channels].
  #
  # Note that we've indicated -1 for batch size, which specifies that this
  # dimension should be dynamically computed based on the number of input values
  # in features["x"], holding the size of all other dimensions constant. This
  # allows us to treat batch_size as a hyperparameter that we can tune. For
  # example, if we feed examples into our model in batches of 5, features["x"]
  # will contain 3,920 values (one value for each pixel in each image), and
  # input_layer will have a shape of [5, 28, 28, 1]. Similarly, if we feed
  # examples in batches of 100, features["x"] will contain 78,400 values, and
  # input_layer will have a shape of [100, 28, 28, 1].
  input_layer = tf.reshape(features["x"], [-1, 28, 28, 1])

  # Convolutional Layer #1
  #
  # Computes 32 features using a 5x5 filter with ReLU activation, i.e. filter
  # size is 5x5 and depth is 32 (or the number of filters to apply is 32).
  # Padding is added to preserve width and height; that is, output shape is kept
  # as 28x28. If there is no padding, the output size would be 24x24 (28-5+1).
  # The activation argument specifies the activation function to apply to the
  # output of the convolution. Here, we specify ReLU activation with tf.nn.relu.
  #
  # Our output tensor produced by conv2d() has a shape of [batch_size, 28, 28, 32]:
  # the same height and width dimensions as the input, but now with 32 channels
  # holding the output from each of the filters.
  #
  # Input Tensor Shape: [batch_size, 28, 28, 1]
  # Output Tensor Shape: [batch_size, 28, 28, 32]
  conv1 = tf.layers.conv2d(
    inputs=input_layer,
    filters=32,
    kernel_size=[5, 5],
    padding="same",
    activation=tf.nn.relu)

  # Pooling Layer #1
  #
  # First max pooling layer with a 2x2 filter and stride of 2. Here we set a
  # stride of 2, which indicates that the subregions extracted by the filter
  # should be separated by 2 pixels in both the height and width dimensions
  # (for a 2x2 filter, this means that none of the regions extracted will overlap).
  # If you want to set different stride values for height and width, you can
  # instead specify a tuple or list (e.g., stride=[3, 6]).
  #
  # Input Tensor Shape: [batch_size, 28, 28, 32]
  # Output Tensor Shape: [batch_size, 14, 14, 32]
  pool1 = tf.layers.max_pooling2d(inputs=conv1, pool_size=[2, 2], strides=2)

  # Convolutional Layer #2
  #
  # Computes 64 features using a 5x5 filter with ReLU activation. Padding is
  # added to preserve width and height.
  #
  # Input Tensor Shape: [batch_size, 14, 14, 32]
  # Output Tensor Shape: [batch_size, 14, 14, 64]
  conv2 = tf.layers.conv2d(
    inputs=pool1,
    filters=64,
    kernel_size=[5, 5],
    padding="same",
    activation=tf.nn.relu)

  # Pooling Layer #2
  #
  # Second max pooling layer with a 2x2 filter and stride of 2
  #
  # Input Tensor Shape: [batch_size, 14, 14, 64]
  # Output Tensor Shape: [batch_size, 7, 7, 64]
  pool2 = tf.layers.max_pooling2d(inputs=conv2, pool_size=[2, 2], strides=2)

  # Flatten tensor into a batch of vectors
  #
  # Input Tensor Shape: [batch_size, 7, 7, 64]
  # Output Tensor Shape: [batch_size, 7 * 7 * 64], i.e. [batch_size, 3163]
  pool2_flat = tf.reshape(pool2, [-1, 7 * 7 * 64])

  # Dense Layer
  #
  # Densely connected layer with 1024 neurons The inputs argument specifies the
  # input tensor: our flattened feature map, pool2_flat. The units argument
  # specifies the number of neurons in the dense layer (1,024). The activation
  # argument takes the activation function; again, we'll use tf.nn.relu to add
  # ReLU activation.
  #
  # Input Tensor Shape: [batch_size, 7 * 7 * 64]
  # Output Tensor Shape: [batch_size, 1024]
  dense = tf.layers.dense(inputs=pool2_flat, units=1024, activation=tf.nn.relu)

  # Dropout
  #
  # Inputs specifies the input tensor, which is the output tensor from our
  # dense layer (dense). The rate argument specifies the dropout rate; here,
  # we use 0.4, which means 40% of the elements will be randomly dropped out
  # during training. The training argument takes a boolean specifying whether
  # or not the model is currently being run in training mode; dropout will only
  # be performed if training is True. Here, we check if the mode passed to our
  # model function cnn_model_fn is TRAIN mode.
  #
  # Input Tensor Shape: [batch_size, 1024]
  # Output Tensor Shape: [batch_size, 1024]
  dropout = tf.layers.dropout(
    inputs=dense, rate=0.4, training=mode == tf.estimator.ModeKeys.TRAIN)

  # Logits layer
  #
  # The final layer in our neural network is the logits layer, which will return
  # the raw values for our predictions. We create a dense layer with 10 neurons
  # (one for each target class 0-9), with linear activation (the default):
  #
  # Input Tensor Shape: [batch_size, 1024]
  # Output Tensor Shape: [batch_size, 10]
  logits = tf.layers.dense(inputs=dropout, units=10)

  # Generate predictions (for PREDICT and EVAL mode)
  #
  # The logits layer of our model returns our predictions as raw values in a
  # [batch_size, 10]-dimensional tensor. Let's convert these raw values into
  # two different formats that our model function can return:
  #  - The 'predicted class' for each example: a digit from 0-9.
  #  - The 'probabilities' for each possible target class for each example:
  #    the probability that the example is a 0, is a 1, is a 2, etc.
  predictions = {
    # For a given example, our predicted class is the element in the corresponding
    # row of the logits tensor with the highest raw value. We can find the index
    # of this element using the tf.argmax function: tf.argmax(input=logits, axis=1).
    #
    # The input argument specifies the tensor from which to extract maximum
    # values-here logits. The axis argument specifies the axis of the input
    # tensor along which to find the greatest value. Here, we want to find the
    # largest value along the dimension with index of 1, which corresponds to
    # our predictions (recall that our logits tensor has shape [batch_size, 10]).
    "classes": tf.argmax(input=logits, axis=1),
    # Add `softmax_tensor` to the graph. It is used for PREDICT and by the
    # `logging_hook`. tf.nn.softmax derives probabilities from our logits layer
    # by applying softmax activation using tf.nn.softmax:
    "probabilities": tf.nn.softmax(logits, name="softmax_tensor")
  }
  if mode == tf.estimator.ModeKeys.PREDICT:
    return tf.estimator.EstimatorSpec(mode=mode, predictions=predictions)

  # Calculate Loss (for both TRAIN and EVAL modes)
  #
  # Our labels tensor contains a list of predictions for our examples, e.g.
  # [1, 9, ...]. In order to calculate cross-entropy, first we need to convert
  # labels to the corresponding one-hot encoding:
  #   [[0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
  #    [0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
  #    ...]
  onehot_labels = tf.one_hot(indices=tf.cast(labels, tf.int32), depth=10)
  # Next, we compute cross-entropy of onehot_labels and the softmax of the
  # predictions from our logits layer. Both onehot_labels and logits have
  # dimension: [batch_size, 10]
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
  eval_metric_ops = {
    "accuracy": tf.metrics.accuracy(
      labels=labels, predictions=predictions["classes"])}
  return tf.estimator.EstimatorSpec(
    mode=mode, loss=loss, eval_metric_ops=eval_metric_ops)


def main(unused_argv):
  # Load training and eval data
  mnist = tf.contrib.learn.datasets.load_dataset("mnist")
  train_data = mnist.train.images # Returns np.array
  train_labels = np.asarray(mnist.train.labels, dtype=np.int32)
  eval_data = mnist.test.images # Returns np.array
  eval_labels = np.asarray(mnist.test.labels, dtype=np.int32)

  # Create the Estimator
  #
  # The 'model_dir' argument specifies the directory where model data
  # (checkpoints) will be saved.
  mnist_classifier = tf.estimator.Estimator(
    model_fn=cnn_model_fn, model_dir="/tmp/mnist_convnet_model")

  # Set up logging for predictions
  #
  # Since CNNs can take a while to train, let's set up some logging so we can
  # track progress during training. We can use TensorFlow's tf.train.SessionRunHook
  # to create a tf.train.LoggingTensorHook that will log the probability values
  # from the softmax layer of our CNN.
  #
  # We store a dict of the tensors we want to log in tensors_to_log. Each key
  # is a label of our choice that will be printed in the log output, and the
  # corresponding label is the name of a Tensor in the TensorFlow graph. Here,
  # our probabilities can be found in 'softmax_tensor', the name we gave our
  # softmax operation earlier when we generated the probabilities in cnn_model_fn.
  tensors_to_log = {"probabilities": "softmax_tensor"}
  logging_hook = tf.train.LoggingTensorHook(
    tensors=tensors_to_log, every_n_iter=50)

  # Train the model
  train_input_fn = tf.estimator.inputs.numpy_input_fn(
    x={"x": train_data},
    y=train_labels,
    batch_size=100,
    num_epochs=None,
    shuffle=True)

  mnist_classifier.train(
    input_fn=train_input_fn,
    steps=20000,
    hooks=[logging_hook])

  # Evaluate the model and print results
  eval_input_fn = tf.estimator.inputs.numpy_input_fn(
    x={"x": eval_data},
    y=eval_labels,
    num_epochs=1,
    shuffle=False)

  eval_results = mnist_classifier.evaluate(input_fn=eval_input_fn)
  print(eval_results)


if __name__ == "__main__":
  tf.app.run()

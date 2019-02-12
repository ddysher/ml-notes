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
"""An Example of a DNNClassifier for the Iris dataset.

From:
  https://github.com/tensorflow/models/tree/v1.7.0/samples/core/get_started
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import tensorflow as tf

# Avoid generating iris_data.pyc; must appear before 'import iris_data'.
import sys
sys.dont_write_bytecode = True

import iris_data

parser = argparse.ArgumentParser()
parser.add_argument('--batch_size', default=100, type=int, help='batch size')
parser.add_argument('--train_steps', default=1000, type=int,
                    help='number of training steps')

def main(argv):
  args = parser.parse_args(argv[1:])

  # Fetch the data; train_x looks like (using print):
  #      SepalLength  SepalWidth  PetalLength  PetalWidth
  # 0        6.4         2.8          5.6         2.2
  # 1        5.0         2.3          3.3         1.0
  # ..       ...         ...          ...         ...
  # 118      4.8         3.0          1.4         0.1
  # 119      5.5         2.4          3.7         1.0
  #
  # [120 rows x 4 columns]
  (train_x, train_y), (test_x, test_y) = iris_data.load_data()

  # Feature columns describe how to use the input. The features we are looping
  # at here are:
  #   - SepalLength
  #   - SepalWidth
  #   - PetalLength
  #   - PetalWidth
  #
  # The 'key' is a unique string identifying the input feature. Note we are not
  # feeding data here; we are creating a feature colume, which is an iterable
  # containing all the feature set used by a model. A feature column is a data
  # structure that tells your model how to interpret the data in each feature.
  # Data are fed into the model later using data input function, e.g. iris_data.train_input_fn.
  # See: https://www.tensorflow.org/get_started/feature_columns#categorical_identity_column
  #
  # An input function is a function that returns a tf.data.Dataset object which
  # outputs the following two-element tuple:
  #  features - A Python dictionary in which:
  #    - Each key is the name of a feature.
  #    - Each value is an array containing all of that feature's values.
  #  label - An array containing the values of the label for every example.
  #
  # A clearer way:
  #   my_feature_columns = [
  #     tf.feature_column.numeric_column(key='SepalLength'),
  #     tf.feature_column.numeric_column(key='SepalWidth'),
  #     tf.feature_column.numeric_column(key='PetalLength'),
  #     tf.feature_column.numeric_column(key='PetalWidth')
  #   ]
  my_feature_columns = [] # length of 'my_feature_columns' is 4, as shown above
  for key in train_x.keys():
    my_feature_columns.append(tf.feature_column.numeric_column(key=key))

  # Build 2 hidden layer DNN with 10, 10 units respectively. One important
  # parameterwe didn't specify is 'optimizer', the default one in DNNClassifier
  # is 'AdagradOptimizer'; other supported optimizers are AdadeltaOptimizer
  # GradientDescentOptimizer, MomentumOptimizer, etc
  classifier = tf.estimator.DNNClassifier(
    feature_columns=my_feature_columns,
    # Two hidden layers of 10 nodes each. To use a different DNN architecture,
    # just change the number and length of the list.
    hidden_units=[10, 10],
    # The model must choose between 3 classes.
    n_classes=3)

  # Train the Model.
  classifier.train(
    input_fn=lambda:iris_data.train_input_fn(train_x, train_y, args.batch_size),
    steps=args.train_steps)

  # Evaluate the model.
  eval_result = classifier.evaluate(
    input_fn=lambda:iris_data.eval_input_fn(test_x, test_y, args.batch_size))

  print('\nTest set accuracy: {accuracy:0.3f}\n'.format(**eval_result))

  # Generate predictions from the model
  expected = ['Setosa', 'Versicolor', 'Virginica']
  predict_x = {                 # Features
    'SepalLength': [5.1, 5.9, 6.9],
    'SepalWidth':  [3.3, 3.0, 3.1],
    'PetalLength': [1.7, 4.2, 5.4],
    'PetalWidth':  [0.5, 1.5, 2.1],
  }

  predictions = classifier.predict(
    input_fn=lambda:iris_data.eval_input_fn(
      predict_x, labels=None, batch_size=args.batch_size))

  template = ('\nPrediction is "{}" ({:.1f}%), expected "{}"')

  for pred_dict, expec in zip(predictions, expected):
    # pred_dict contains keys:
    #  - probabilities: a list, one probability item for each class
    #  - class_ids: a one-element array that identifies the most probable species
    #  - logits
    class_id = pred_dict['class_ids'][0]
    probability = pred_dict['probabilities'][class_id]

    print(template.format(iris_data.SPECIES[class_id], 100 * probability, expec))


if __name__ == '__main__':
  tf.logging.set_verbosity(tf.logging.INFO)
  tf.app.run(main)

import pandas as pd
import tensorflow as tf

TRAIN_URL = "http://download.tensorflow.org/data/iris_training.csv"
TEST_URL = "http://download.tensorflow.org/data/iris_test.csv"

CSV_COLUMN_NAMES = ['SepalLength', 'SepalWidth',
                    'PetalLength', 'PetalWidth', 'Species']
SPECIES = ['Setosa', 'Versicolor', 'Virginica']

def maybe_download():
  train_path = tf.keras.utils.get_file(TRAIN_URL.split('/')[-1], TRAIN_URL)
  test_path = tf.keras.utils.get_file(TEST_URL.split('/')[-1], TEST_URL)

  return train_path, test_path


def load_data(y_name='Species'):
  """Returns the iris dataset as (train_x, train_y), (test_x, test_y)."""
  # Create a local copy of the training set.
  # 'train_path' now holds the pathname: ~/.keras/datasets/iris_training.csv
  train_path, test_path = maybe_download()

  # Parse the local CSV file. 'train' holds a pandas DataFrame, which is data
  # structure analogous to a table.
  train = pd.read_csv(
    train_path,
    names=CSV_COLUMN_NAMES,    # list of column names
    header=0)                  # ignore the first row of the CSV file.
  # 1. Assign the DataFrame's labels (the right-most column) to train_label.
  # 2. Delete (pop) the labels from the DataFrame.
  # 3. Assign the remainder of the DataFrame to train_features
  train_features, train_label = train, train.pop(y_name)

  # Note variable here, e.g. 'train_features', is instance of custom class - it's
  # not simply a dictionary or list. Looping through train_features.keys() gives
  # ['SepalLength', 'SepalWidth', 'PetalLength', 'PetalWidth'], which is number
  # of features, but len(train_features) gives 120, which is number of samples.

  # Apply the preceding logic to the test set.
  test = pd.read_csv(test_path, names=CSV_COLUMN_NAMES, header=0)
  test_features, test_label = test, test.pop(y_name)

  return (train_features, train_label), (test_features, test_label)


def train_input_fn(features, labels, batch_size):
  """An input function for training"""
  # Convert the inputs to a Dataset. Using the tf.data.Dataset.from_tensor_slices
  # function to create a tf.data.Dataset representing slices of the array. The
  # array is sliced across the first dimension. For example, an array containing
  # the mnist training data has a shape of (60000, 28, 28). Passing this to
  # from_tensor_slices returns a Dataset object containing 60000 slices, each
  # one a 28x28 image.
  dataset = tf.data.Dataset.from_tensor_slices((dict(features), labels))
  print(dataset)

  # Shuffle, repeat, and batch the examples. Calling the tf.data.Dataset.repeat
  # method without any arguments ensures that the train method has an infinite
  # supply of (now shuffled) training set examples.
  dataset = dataset.shuffle(1000).repeat().batch(batch_size)

  # Return the dataset.
  return dataset


def eval_input_fn(features, labels, batch_size):
  """An input function for evaluation or prediction"""
  features = dict(features)
  if labels is None:
    # No labels, use only features.
    inputs = features
  else:
    inputs = (features, labels)

  # Convert the inputs to a Dataset.
  dataset = tf.data.Dataset.from_tensor_slices(inputs)

  # Batch the examples
  assert batch_size is not None, "batch_size must not be None"
  dataset = dataset.batch(batch_size)

  # Return the dataset.
  return dataset


# The remainder of this file contains a simple example of a csv parser,
#   implemented using a the `Dataset` class.

# `tf.parse_csv` sets the types of the outputs to match the examples given in
#   the `record_defaults` argument.
CSV_TYPES = [[0.0], [0.0], [0.0], [0.0], [0]]

def _parse_line(line):
  # Decode the line into its fields
  fields = tf.decode_csv(line, record_defaults=CSV_TYPES)

  # Pack the result into a dictionary
  features = dict(zip(CSV_COLUMN_NAMES, fields))

  # Separate the label from the features
  label = features.pop('Species')

  return features, label


def csv_input_fn(csv_path, batch_size):
  # Create a dataset containing the text lines.
  dataset = tf.data.TextLineDataset(csv_path).skip(1)

  # Parse each line.
  dataset = dataset.map(_parse_line)

  # Shuffle, repeat, and batch the examples.
  dataset = dataset.shuffle(1000).repeat().batch(batch_size)

  # Return the dataset.
  return dataset

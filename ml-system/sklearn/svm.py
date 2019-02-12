#!/usr/bin/env python3

from sklearn import svm
from sklearn.metrics import accuracy_score

from utils import make_dictionary, extract_features

# full_training trains on full dataset.
def full_training():
  TRAIN_DIR = "./train-mails"
  TEST_DIR = "./test-mails"

  dictionary = make_dictionary(TRAIN_DIR)

  print("reading and processing emails from file.")
  features_matrix, labels = extract_features(TRAIN_DIR, dictionary)
  test_feature_matrix, test_labels = extract_features(TEST_DIR, dictionary)

  print("training model.")
  clf = svm.SVC()
  clf.fit(features_matrix, labels)

  predicted_labels = clf.predict(test_feature_matrix)

  print("FINISHED classifying. accuracy score: ")
  print(accuracy_score(test_labels, predicted_labels))


# mini_training trains on 1/10 dataset, to test parameter tuning.
def mini_training():
  TRAIN_DIR = "./train-mails"
  TEST_DIR = "./test-mails"

  dictionary = make_dictionary(TRAIN_DIR)

  print("reading and processing emails from file.")
  features_matrix, labels = extract_features(TRAIN_DIR, dictionary)
  test_feature_matrix, test_labels = extract_features(TEST_DIR, dictionary)

  features_matrix = features_matrix[:int(len(features_matrix)/10)]
  labels = labels[:int(len(labels)/10)]

  print("training model.")
  # Tunning 'kernel', 'C' and 'gamma'.
  clf = svm.SVC(kernel="rbf", C=100)
  clf.fit(features_matrix, labels)

  predicted_labels = clf.predict(test_feature_matrix)

  print("FINISHED classifying. accuracy score: ")
  print(accuracy_score(test_labels, predicted_labels))


if __name__ == "__main__":
  full_training()

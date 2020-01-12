#!/usr/bin/env python3

from sklearn import tree
from sklearn.metrics import accuracy_score

from utils import make_dictionary, extract_features

if __name__ == "__main__":
  TRAIN_DIR = "./train-mails"
  TEST_DIR = "./test-mails"

  dictionary = make_dictionary(TRAIN_DIR)

  print("reading and processing emails from file.")
  features_matrix, labels = extract_features(TRAIN_DIR, dictionary)
  test_feature_matrix, test_labels = extract_features(TEST_DIR, dictionary)

  print("training model.")
  model = tree.DecisionTreeClassifier(criterion="entropy")
  model.fit(features_matrix, labels)

  predicted_labels = model.predict(test_feature_matrix)

  print("FINISHED classifying. accuracy score: ")
  print(accuracy_score(test_labels, predicted_labels))

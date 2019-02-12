#!/usr/bin/env python3

import os
import numpy as np
from collections import Counter

# make_dictionary reads each file (email) in a directory, and turns it into a
# list of tuples, where each tuple is (word, frequency). It also deletes words
# of length 1 and that are not purely alphabetical, and only return the most
# frequent 3000 number of words, i.e. to clean the data. The final result is
# as follows:
#   [('order', 1414), ('address', 1299), ('report', 1217), ('mail', 1133), ...]
def make_dictionary(root_dir):
  all_words = []
  emails = [os.path.join(root_dir,f) for f in os.listdir(root_dir)]
  for mail in emails:
    with open(mail) as m:
      for line in m:
        words = line.split()
        all_words += words
  dictionary = Counter(all_words)
  list_to_remove = list(dictionary)
  # if you have python version 2.x, use:
  # list_to_remove = dictionary.keys()

  for item in list_to_remove:
    if item.isalpha() == False:
      del dictionary[item]
    elif len(item) == 1:
      del dictionary[item]
  dictionary = dictionary.most_common(3000)

  return dictionary


# extract_features extracts features of the given dataset. Naive Bayes Classifier
# assumes the features (in this case we had words as input) are independent, i.e.
# each word is a feature (we have 3000 features) and each one is independent with
# others.
#
# There are 260 emails in test set. Result of feature matrix (260 x 3000)
# [[0. 0. 0. ... 0. 0. 0.]
#  [1. 0. 0. ... 0. 0. 0.]
#  [0. 0. 0. ... 0. 0. 0.]
#  ...
#  [0. 2. 0. ... 0. 0. 0.]
#  [0. 0. 0. ... 0. 0. 0.]
#  [1. 2. 0. ... 0. 0. 0.]]
#
# Result of label (260)
# [1. 1. 1. 1. 1. 0. 0. 1. 0. 1. 0. 1. 0. 0. 1. 0. 1. 1. 1. 1. 0. 0. 0. 1.
#  0. 0. 0. 0. 0. 1. 0. 1. 1. 0. 1. 1. 0. 1. 0. 0. 1. 1. 1. 0. 0. 0. 1. 1.
#  0. 1. 0. 0. 1. 0. 1. 0. 1. 0. 0. 1. 0. 1. 0. 1. 1. 0. 0. 0. 1. 1. 1. 1.
#  0. 0. 0. 1. 0. 1. 1. 0. 1. 0. 1. 0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 1. 1. 1.
#  1. 1. 1. 1. 1. 1. 0. 1. 0. 1. 1. 0. 1. 1. 1. 1. 0. 0. 0. 1. 1. 0. 0. 0.
#  1. 0. 0. 0. 0. 0. 1. 0. 1. 0. 0. 1. 1. 0. 0. 1. 1. 0. 0. 0. 1. 1. 0. 1.
#  1. 1. 0. 0. 0. 0. 1. 0. 1. 0. 0. 0. 1. 0. 0. 0. 0. 1. 0. 1. 0. 0. 1. 1.
#  1. 0. 0. 0. 1. 1. 1. 0. 1. 0. 1. 1. 0. 1. 1. 1. 1. 0. 0. 1. 0. 1. 0. 0.
#  0. 0. 1. 1. 0. 0. 0. 0. 1. 1. 0. 1. 0. 0. 0. 1. 1. 1. 0. 0. 0. 0. 1. 0.
#  0. 0. 1. 1. 1. 1. 1. 0. 1. 0. 1. 1. 1. 1. 1. 1. 1. 1. 1. 0. 1. 1. 0. 1.
#  1. 0. 0. 1. 1. 0. 1. 1. 1. 0. 0. 0. 0. 1. 1. 0. 0. 0. 1. 1.]
#
# Taking a look at the last email (spmsgc91.txt based on reading loop), its feature
# matrix is:
#   [1. 2. 0. ... 0. 0. 0.]
# which means 1 occurance of word 'order' and 2 occurances of word 'address'. The
# label value is '1', which means it is a spam email.
def extract_features(mail_dir, dictionary):
  files = [os.path.join(mail_dir,fi) for fi in os.listdir(mail_dir)]
  features_matrix = np.zeros((len(files),3000))
  train_labels = np.zeros(len(files))
  count = 0;
  docID = 0;
  for fil in files:
    with open(fil) as fi:
      for i, line in enumerate(fi):
        if i == 2:
          words = line.split()
          for word in words:
            wordID = 0
            for i, d in enumerate(dictionary):
              if d[0] == word:
                wordID = i
                features_matrix[docID, wordID] = words.count(word)
      train_labels[docID] = 0;
      filepathTokens = fil.split('/')
      lastToken = filepathTokens[len(filepathTokens) - 1]
      if lastToken.startswith("spmsg"):
        train_labels[docID] = 1;
        count = count + 1
      docID = docID + 1
  return features_matrix, train_labels

from nltk.corpus import stopwords
from nltk.cluster.util import cosine_distance
import networkx as nx
import nltk
import numpy as np


class SummarizeText(object):
    result = {}

    def __init__(self):
        nltk.download('stopwords', download_dir="/root/nltk_data")

    def sentence_similarity(self, sent1, sent2, stopwords=None):
        if stopwords is None:
            stopwords = []

        sent1 = [w.lower() for w in sent1]
        sent2 = [w.lower() for w in sent2]

        all_words = list(set(sent1 + sent2))

        vector1 = [0] * len(all_words)
        vector2 = [0] * len(all_words)

        # build the vector for the first sentence
        for w in sent1:
            if w in stopwords:
                continue
            vector1[all_words.index(w)] += 1

        # build the vector for the second sentence
        for w in sent2:
            if w in stopwords:
                continue
            vector2[all_words.index(w)] += 1

        return 1 - cosine_distance(vector1, vector2)

    def build_similarity_matrix(self, sentences, stop_words):
        # Create an empty similarity matrix
        similarity_matrix = np.zeros((len(sentences), len(sentences)))

        for idx1 in range(len(sentences)):
            for idx2 in range(len(sentences)):
                if idx1 == idx2:  #ignore if both are same sentences
                    continue
                similarity_matrix[idx1][idx2] = self.sentence_similarity(
                    sentences[idx1], sentences[idx2], stop_words)

        return similarity_matrix

    def predict(self, X, features_names, meta):
        if meta and 'tags' in meta and 'text_tagging_passed' in meta[
                'tags'] and meta['tags']['text_tagging_passed']:
            self.result = meta['tags']

            summarize_text = []
            stop_words = stopwords.words('english')

            sentences = str(X[0]).split(".")
            sentence_similarity_martix = self.build_similarity_matrix(
                sentences, stop_words)

            if sentence_similarity_martix.any():

                sentence_similarity_graph = nx.from_numpy_array(
                    sentence_similarity_martix)
                if sentence_similarity_graph:

                    scores = nx.pagerank(sentence_similarity_graph)
                    if scores:

                        ranked_sentence = sorted(
                            ((scores[i], s) for i, s in enumerate(sentences)),
                            reverse=True)
                        if ranked_sentence:
                            for i in range(2):
                                summarize_text.append("".join(
                                    ranked_sentence[i][1]))

                            if len(summarize_text) >= 2:
                                self.result["summarize_text_passed"] = True
                                self.result["summarize_text_result"] = str(
                                    summarize_text)
                            else:
                                self.result["summarize_text_passed"] = False
                                self.result[
                                    "failure_reason"] = "Could not summarize text"

        return X

    def tags(self):
        return self.result

from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.stem.porter import PorterStemmer
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import stopwords
import nltk
import re
import os
import pandas


class TextTagging(object):
    result = {}
    stop_words = None

    def __init__(self):
        nltk.download('stopwords', download_dir="/root/nltk_data")
        nltk.download('wordnet', download_dir="/root/nltk_data")
        self.stop_words = set(stopwords.words("english"))

    def predict(self, X, features_names, meta):
        if meta and 'tags' in meta and 'sentiment_analysis_passed' in meta[
                'tags'] and meta['tags']['sentiment_analysis_passed']:
            self.result = meta['tags']

            corpus = []

            text = re.sub('[^a-zA-Z]', ' ', X[0]).lower()
            text = re.sub("&lt;/?.*?&gt;", " &lt;&gt; ", text)
            text = re.sub("(\\d|\\W)+", " ", text)
            text = text.split()

            ps = PorterStemmer()
            lem = WordNetLemmatizer()
            text = [
                lem.lemmatize(word) for word in text
                if not word in self.stop_words
            ]
            text = " ".join(text)
            corpus.append(text)

            # Uncommon words
            freq1 = pandas.Series(
                ' '.join(corpus).split()).value_counts()[-20:]

            tags = []
            for index, freq in enumerate(freq1.iteritems()):
                if index >= 5:
                    break
                else:
                    tags.append("#" + freq[0])

            if tags and len(tags) > 0:
                self.result["text_tagging_passed"] = True
                self.result["tags"] = str(tags)
            else:
                self.result["text_tagging_passed"] = False
                self.result["failure_reason"] = "Could not tag text"

        return X

    def tags(self):
        return self.result

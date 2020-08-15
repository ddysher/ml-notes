from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class SentimentAnalysis(object):
    result = {}
    analyser = None

    def __init__(self):
        self.analyser = SentimentIntensityAnalyzer()

    def predict(self, X, features_names, meta):
        if len(X) > 0:
            sentence = X[0]
            score = self.analyser.polarity_scores(sentence)

            self.result["sentiment_analysis_passed"] = True
            self.result["input_text"] = sentence
            self.result["sentiment_analysis_result"] = score
        else:
            self.result["sentiment_analysis_passed"] = False
            self.result[
                "failure_reason"] = "Sentiment Analysis does not have a valid input array"
        return X

    def tags(self):
        return self.result

"""Baseline predictors."""
from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, make_pipeline


class Majority:
    def fit(self, texts, labels):
        self.label = Counter(labels).most_common(1)[0][0]

    def predict(self, texts):
        return [self.label] * len(texts)


class TfidfLogReg:
    def fit(self, texts, labels):  # LogisticRegression refuses a one-class fold
        self.pipe = Majority() if len(set(labels)) == 1 else make_pipeline(
            FeatureUnion([("word", TfidfVectorizer(ngram_range=(1, 2))),
                          ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5)))]),
            LogisticRegression(max_iter=2000, class_weight="balanced", random_state=20261028))  # = PARAMS.random_state
        self.pipe.fit(texts, labels)

    def predict(self, texts):
        return list(self.pipe.predict(texts))

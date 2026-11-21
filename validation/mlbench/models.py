"""Baseline predictors; every later model plugs in through Predictor."""
from collections import Counter
from typing import Protocol

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, make_pipeline


class Predictor(Protocol):
    name: str

    def fit(self, texts: list[str], labels: list[str]) -> None: ...

    def predict(self, texts: list[str]) -> list[str]: ...


class Majority:
    name = "majority"

    def fit(self, texts, labels):
        self.label = Counter(labels).most_common(1)[0][0]

    def predict(self, texts):
        return [self.label] * len(texts)


class TfidfLogReg:
    name = "tfidf_logreg"

    def __init__(self, random_state: int = 20261028):
        self.random_state = random_state

    def fit(self, texts, labels):
        self.single = labels[0] if len(set(labels)) == 1 else None
        if self.single is not None:
            return
        self.pipe = make_pipeline(
            FeatureUnion([("word", TfidfVectorizer(ngram_range=(1, 2))),
                          ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5)))]),
            LogisticRegression(max_iter=2000, class_weight="balanced", random_state=self.random_state))
        self.pipe.fit(texts, labels)

    def predict(self, texts):
        return [self.single] * len(texts) if self.single is not None else list(self.pipe.predict(texts))

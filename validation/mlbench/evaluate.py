"""Grouped cross-validation and fixed-prediction scoring."""
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GroupKFold


def _metrics(gold: list[str], pred: list[str]) -> dict:
    classes = sorted(set(gold))
    f1s = f1_score(gold, pred, labels=classes, average=None, zero_division=0)
    return {"n": len(gold), "accuracy": accuracy_score(gold, pred),
            "macro_f1": float(f1s.mean()) if classes else None,
            "per_class": {c: {"f1": float(f), "support": gold.count(c)} for c, f in zip(classes, f1s)}}


def cross_validate(make, rows, label: str, folds: int = 5) -> dict:
    gold, pred = [], []
    for tr, te in GroupKFold(n_splits=folds).split(rows, groups=[r.group for r in rows]):
        m = make()
        m.fit([rows[i].text for i in tr], [getattr(rows[i], label) for i in tr])
        pred += m.predict([rows[i].text for i in te])
        gold += [getattr(rows[i], label) for i in te]
    return _metrics(gold, pred)


def score_fixed(pred: dict[tuple[str, str], str], rows, label: str) -> dict:
    """Scores only rows that have a prediction, keyed (group, outlet)."""
    hit = [r for r in rows if (r.group, r.outlet) in pred]
    return _metrics([getattr(r, label) for r in hit], [pred[(r.group, r.outlet)] for r in hit])

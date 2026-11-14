"""Stub reviewer for offline tests: answers for one target card, rejects every other card."""
from biasguard.providers import ProviderCallError


def assessment(card, verdict, quote, source="text", kind="behavioral", satisfied=None, missing=()):
    if verdict == "not_supported" and satisfied is None:
        return {"card_id": card["id"], "verdict": "not_supported", "evidence": [], "necessary_conditions": [],
                "mechanism": "", "alternative_explanation": "", "missing_context": []}
    n = len(card["necessary_conditions"])
    k = n if satisfied is None else satisfied
    return {"card_id": card["id"], "verdict": verdict,
            "evidence": [{"source": source, "quote": quote, "kind": kind}],
            "necessary_conditions": [{"condition_index": i, "status": "satisfied" if i < k else "unknown",
                                      "evidence_indices": [0] if i < k else []} for i in range(n)],
            "mechanism": "m", "alternative_explanation": "a", "missing_context": list(missing)}


class StubReviewer:
    def __init__(self, target, quote, advocate="supported", skeptic="supported", source="text",
                 fail=False, skeptic_satisfied=None, advocate_satisfied=None):
        self.target, self.quote, self.source, self.fail = target, quote, source, fail
        self.verdicts = {"advocate": advocate, "skeptic": skeptic}
        self.satisfied = {"advocate": advocate_satisfied, "skeptic": skeptic_satisfied}
        self.last_call = None

    def select(self, text, context, cards, max_candidates):
        return {"candidate_ids": [self.target], "selection_uncertainty": [], "selection_note": ""}

    def review(self, text, context, cards, role):
        if self.fail:
            raise ProviderCallError("stub failure")
        out = []
        for c in cards:
            if c["id"] == self.target:
                out.append(assessment(c, self.verdicts[role], self.quote, self.source, satisfied=self.satisfied[role]))
            else:
                out.append(assessment(c, "not_supported", ""))
        return {"role": role, "assessments": out}

    def provider_info(self):
        return {"provider": "stub"}

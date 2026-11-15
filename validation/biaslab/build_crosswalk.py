"""One-off generator for crosswalk.json. Re-running it discards review statuses set by hand."""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

from biasguard.catalog import load_cards

MESA = Path(__file__).resolve().parents[1] / "mesa_bias_expanded"
FULL_ARTICLE = {"source_selection", "one_sided_sourcing", "commission_and_omission_of_information",
                "contextual_omission", "size_allocation", "story_placement", "picture_selection",
                "picture_explanation", "event_selection"}
# Media techniques assessable from headlines and ledes. Their cards are lab candidates
# (validation/biaslab/proposed_cards/); the crosswalk names the card each would map to.
MEDIA_HEADLINE = ("ad_hominem causal_overclaim cherry_picking consequence_framing emphasis_framing episodic_framing "
                  "false_dilemma fear_appeal labeling loaded_language metaphorical_framing responsibility_framing "
                  "selective_statistics spin strawman thematic_framing word_choice").split()
HAND = {
    "illusory_truth_effect": {"review_status": "pilot"},
    "selective_statistics": {"required_evidence": [
        "the presented numerator and denominator",
        "documented relevant comparison population",
        "evidence that the populations are comparable"]},
}


def build() -> list[dict]:
    sys.path.insert(0, str(MESA))
    cards = {c["id"]: c for c in load_cards()}
    out = []
    for item in json.loads((MESA / "missing_concepts.json").read_text(encoding="utf-8")):
        sid = item["id"]
        kind = importlib.import_module(f"mechanisms.{sid}").METADATA["kind"]
        card = cards.get(sid.replace("_", "-"))
        if card:
            policy = card.get("review_policy", "bias_error_review")
            tier = ("internal_state" if kind == "psychological_state"
                    else "decision_history" if policy == "requires_behavioral_evidence" else "headline_lede")
            rec = {"simulation_id": sid, "detector_id": card["id"], "relationship": "candidate_same_id",
                   "evidence_tier": tier, "policy": policy, "review_status": "needs_domain_review",
                   "required_evidence": []}
        else:
            rec = {"simulation_id": sid, "detector_id": None, "relationship": "unsupported_in_current_taxonomy",
                   "evidence_tier": "full_article" if sid in FULL_ARTICLE else "headline_lede",
                   "policy": "media_pattern_review", "review_status": "needs_domain_review", "required_evidence": []}
        if sid in MEDIA_HEADLINE:
            rec.update({"detector_id": sid.replace("_", "-"), "relationship": "equivalent_within_task",
                        "review_status": "pilot",
                        "policy": "effect_context_only" if sid in ("spin", "thematic_framing") else "media_pattern_review"})
        rec.update(HAND.get(sid, {}))
        out.append(rec)
    return sorted(out, key=lambda r: r["simulation_id"])


if __name__ == "__main__":
    Path(__file__).with_name("crosswalk.json").write_text(
        json.dumps(build(), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

"""Check reviewer-agent outputs for one task batch: python3 runs/check_out.py <run> <stage> <batch-file> [role]
stage: select | review. Prints one line per event: OK or the problem."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from biasguard.engine import BiasGuard
from biasguard.news import catalog_cards, MAX_CANDIDATES
run, stage, batch = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
role = sys.argv[4] if len(sys.argv) > 4 else None
if run.parent.parent.name == "lab":  # validation lab run: runs/lab/<run>/<config>
    from validation.biaslab import configs
    bg = BiasGuard(cards=configs.catalog(run.name))
else:
    bg = BiasGuard(cards=catalog_cards("media" if "bgm" in run.name else "behavioural"))
task = json.loads(batch.read_text())
by = {c["id"]: c for c in bg.cards}
for ev in task["events"]:
    p = run / ("selections" if stage == "select" else f"reviews/{role}") / f"{ev['event']}.json"
    try:
        raw = json.loads(p.read_text())
        if stage == "select":
            bg._validate_selection(raw, MAX_CANDIDATES)
        else:
            bg._normalize_review(raw, role, ev["text"], ev["context"], [by[c] for c in ev["card_ids"]])
            bad = [e["quote"][:50] for a in raw["assessments"] for e in a["evidence"]
                   if e["source"] == "text" and e["quote"] not in ev["text"]]
            if bad: raise ValueError(f"quotes not found verbatim in text: {bad}")
        print(ev["event"], "OK")
    except Exception as exc:
        print(ev["event"], "PROBLEM:", type(exc).__name__, str(exc)[:300])

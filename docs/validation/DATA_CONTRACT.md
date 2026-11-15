# Data contract for the learning loop

What the detector's outputs and the human reviews are, so that every number built on them means one thing.

| Item | Contract |
|---|---|
| **Entity** | One row per event × card × detector version × data pack (`validation/learning/snapshot.py`). |
| **Primary key** | `(event, card_id, pack_version, detector_version, catalog)`. |
| **Prediction** | The detector's status for the card on that event, and its tier (`ai_confident` / `needs_human`). |
| **Inputs at prediction time** | Each outlet's first headline and lede for the event, outlet placements, event timing. Nothing from human review. |
| **Label** | An editor review of one finding: `verified`, `corrected` or `rejected` (`validation/reference/labels.jsonl`). |
| **Label timing** | After publication, with no deadline. Most findings never get a label. |
| **Label bias** | *Anchored*: the reviewer sees the AI's finding first. *Partial*: only shown findings can be reviewed, so missed findings are invisible. *Selected*: findings waiting for a person are reviewed first; a 5% random audit covers the "AI onaylı" tier. |
| **What labels can estimate** | Verify-pass precision per card and per slice. They cannot estimate recall. |
| **Binding** | A label counts only for the pack version and event-text hash it was made on. |
| **Splits** | By event. Time-ordered: a candidate detector version is judged on reviews made before it was written (the replay set). |
| **Slices** | Card, catalogue (behavioural / media), bloc of the quoted outlets (sol / orta / sağ / karışık), month, event size, tier. |
| **Sensitive fields** | None stored. No reviewer identity. Quotes are text already public on the site. |
| **Snapshot id** | `<pack version>_<catalog>_<detector version>`; a snapshot is written once and never changed. |
| **Detector version** | First 12 hex digits of SHA-256 over card hash, prompts version and the candidate limit. |

A rate is always shown with its counts. A rate with no cases is "not estimable", never zero.

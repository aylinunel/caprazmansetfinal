# Self-serving bias: implementation note

This module is a compact, hypothetical process model—not a statement, media, or person detector. For each explicitly supplied outcome, it reports an internal-responsibility share between 0 and 1. Let `b` be the evidence-based internal share, `q` the supplied causal-evidence quality, `s` the intervention strength, and `t=1` for success or `t=0` for failure. The illustrative process is

`share = b + s * (1 - q) * (t - b)`.

Thus, when causal evidence is ambiguous, success pulls attribution toward internal credit and failure pulls it toward external attribution. High-quality evidence attenuates the pull; at `q=1` the attribution is unchanged even if it favors the speaker. `strength` in `[0,1]` is an uncalibrated intervention setting, not a probability or estimated effect size. The strength-zero reference returns `b` for the same task inputs; it is a supplied-evidence reference, not a claim of perfect rationality.

## Task, state, and units

Each chronological context requires exactly the phase-invariant task keys `outcome` (`success` or `failure`), `evidence_internal_share` (`b`, in `[0,1]`), and `evidence_quality` (`q`, in `[0,1]`). The metric is the current event's fraction of causal responsibility attributed internally. State preserves the count, cumulative current and evidence-based shares, and the ordered outcomes across events; it does not feed history back into the per-event attribution equation. The runner-provided state/agent/round/uniform fields are not scenario inputs and randomness is not used.

## Scenarios and necessary condition

The positive sequence supplies ambiguous causal evidence and includes both success and failure. With `b=.35`, `q=.20`, and `s=.8`, the success share is `.766` and the failure share is `.126`; the final failure therefore decreases relative to the `.35` reference. The boundary scenario retains a favorable success attribution (`b=.80`) but sets evidence quality to `1.0`, removing ambiguity—the necessary condition for this model's self-favoring distortion. Intervention and reference are then equal at `.80`, rather than the boundary merely assigning a zero metric.

## Assumptions and limitations

Outcome, causal share, and evidence quality are hypothetical structured inputs, never inferred from wording or hidden motives. Whether those inputs reflect valid causal evidence is outside the model. The linear directional pull, endpoints, and evidence-quality attenuation are illustrative design choices, not empirically estimated psychology. Other benign explanations—including objectively greater personal contribution to success or external causes of failure—may produce self-favorable but supported attributions. No test or simulation establishes empirical validity, diagnostic status, prevalence, or detection accuracy.

# Sexual Overperception Bias — illustrative implementation

## Process and task metric

Each task context supplies three hypothetical ratings in `[0, 1]`: explicit direct reciprocal evidence `D`, ambiguous warmth `W`, and personally directed attention `A`. The strength-zero reference estimate is `D`, not a claim of perfect judgment. The illustrative intervention produces

`estimate = D + strength × 0.5 × W × A × (1 − D)`.

The effect is an interaction: warmth alone or personalized attention alone adds nothing; both ambiguous cues are required, and already-direct evidence leaves less room for excess attribution. The primary metric is a bounded (0–1) illustrative inferred-interest estimate, **not** a calibrated probability, diagnosis, consent assessment, or observation of another person’s internal state. State records the latest estimate and number of evaluated steps while preserving other supplied state fields.

## Scenarios and boundary

The positive scenario combines low explicit evidence (`D=0.1`) with ambiguous warmth (`W=0.8`) and personalized attention (`A=0.75`), yielding `0.316` at strength `0.8` versus `0.1` at strength zero. The boundary retains warmth but removes personalized attention (`A=0`); because a necessary interacting cue is absent, the intervention and reference estimates are equal. Generic friendliness and gender are not treated as evidence and are not inputs.

## Assumptions and limitations

The coefficient is an explicit, hypothetical process choice, not a published effect size; strength is an uncalibrated intervention parameter. Structured ratings are supplied by the simulation designer and are not inferred from language, identity, or observed behavior. The model excludes situational nuance, alternative interpretations, consent, and individual variation; even a high estimate cannot establish another person’s interest. This implementation is synthetic and has no empirical validation claim.

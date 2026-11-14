# `ad_hominem` implementation note

This module is an explicitly hypothetical attention-allocation process, not an NLP detector, a psychological diagnosis, or an empirically validated model. The supplied spec defines ad hominem as attacking a person's character, identity, or past instead of assessing the claim, but leaves the annotation boundary blank. This implementation operationalizes that boundary with structured scenario facts: an attack must be person-directed (`personal_attack_present`), have positive intensity, and be irrelevant to the claim to divert review attention. No attack is inferred from words or hidden motives.

## Process and metric

Each review turn has a normalized attention budget of 1. For evidence amount `E > 0`, explicit attack intensity `I ∈ [0,1]`, explicit claim relevance `R ∈ [0,1]`, and intervention strength `s ∈ [0,1]`:

- attack demand is `D = I × (1 − R)` for a person-directed attack; otherwise `D = 0`;
- diverted attention is `V = s × D`;
- primary metric is `E × (1 − V)`, or units of claim evidence reviewed that turn.

At strength zero, the justified reference policy reviews all supplied evidence (`E` units) regardless of attack. State accumulates evidence units reviewed, normalized attention diverted, and turns processed. Calls use only supplied values and are deterministic.

## Scenarios and necessary condition

The positive scenario supplies 3 evidence units, a person-directed attack of intensity 0.6, and relevance 0. At strength 0.8, the model diverts 0.48 of the normalized budget and reviews 1.56 evidence units, below the 3-unit reference. The boundary scenario keeps the personal attack and intensity but sets relevance to 1: the personal critique is claim-relevant rather than a substitute for assessing the claim, so the necessary irrelevance condition is absent; the metric equals the 3-unit reference. A non-personal remark also does not activate the process.

## Assumptions and limitations

The linear salience-to-attention allocation, normalized budget, input scores, and strength setting are illustrative assumptions only, not measured coefficients or prevalence estimates. Evidence units represent available reviewable material and do not encode evidence quality. The implementation cannot assess whether a real critique is relevant, whether an attack occurred, or how humans respond; those facts must be supplied by the scenario author. Alternative explanations for attention allocation are not modeled. Software tests verify only the specified synthetic equations and interface, not empirical validity.

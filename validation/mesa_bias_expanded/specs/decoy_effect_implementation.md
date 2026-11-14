# Decoy Effect — illustrative mechanism

## Process and task

This module models a single three-option choice task. Each option supplies a utility in `[0, 1]` and two explicitly directional, higher-is-better attribute scores in `[0, 1]`; the caller also identifies the target and decoy. The reference policy assigns each option a softmax share from its supplied utility, at unit temperature. At strength `s`, if the target strictly dominates the decoy on both attributes (at least one strictly) and the remaining competitor does **not** dominate it, the target logit receives an illustrative attraction increment:

`bonus = s × 1.2 × (1 − mean_absolute_attribute_distance(target, decoy))`.

The returned primary metric is the target's resulting softmax probability, in probability units `[0, 1]`. At strength zero this exactly reduces to the stated utility-softmax reference. The coefficient `1.2` is a transparent modeling assumption, not an estimated effect size. The module reports whether this process changes the task baseline and records the last task result in state.

## Necessary conditions and scenarios

The explicit target/decoy identities, three valid alternatives, and target's strict attribute dominance over the decoy are required evidence; malformed or absent evidence raises `ValueError`, rather than generating a zero metric. The effect additionally requires asymmetric dominance: the sole competitor must not also dominate the decoy.

The positive scenario has target `[0.8, 0.7]`, competitor `[0.5, 0.8]`, and decoy `[0.6, 0.5]`; at strength `.8`, the target receives a bonus and its choice probability increases over the same task's reference. The boundary scenario changes the competitor to `[0.9, 0.8]`, so it too dominates the decoy; the asymmetry condition is absent and the metric equals the strength-zero reference.

## Assumptions and limitations

The model assumes supplied utilities are comparable, both attributes are consistently oriented, and mean absolute distance is a reasonable illustrative proxy for decoy-target similarity. It does not infer products, preferences, attribute meanings, or dominance from prose, and it is not an NLP detector, population claim, or empirical psychology model. A third option may convey useful information or have no effect in real settings. `strength` is a generic intervention setting, not prevalence or calibrated confidence. All outputs are synthetic and the mechanism has not been empirically validated.

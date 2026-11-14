# Omission Bias: illustrative implementation

## Process and task metric

This hypothetical task presents one paired action/inaction case with normalized action harm and omission harm. The strength-zero reference assigns both pathways the same harm-proportional blame after applying the same explicit accountability gate (the actor knew the risk, had a duty to act, and made an intentional choice):

`B_action = action_harm × accountability` and `B_omission = omission_harm × accountability`, where `accountability` is 1 only when all three supplied facts are true, otherwise 0.

For an eligible, comparable pair only, the intervention adds an action-specific premium: `premium = strength × 0.25 × min(action_harm, omission_harm)`. The resulting action blame is capped at 1. The primary metric is `B_action_adjusted - B_omission`, in normalized illustrative blame points. Using the lesser harm ties the extra action judgment to severity common to both pathways; it is not a free-standing offset. Strength is an uncalibrated intervention control, and 0.25 is a hypothetical task coefficient, not an estimated effect size.

## Conditions and scenarios

The positive scenario holds harms, knowledge, duty, and intentionality equal and supplies comparable consequences. The boundary scenario keeps those facts and harms fixed but sets `consequences_comparable` to false. Since comparability is necessary for the action premium, the boundary output equals the strength-zero reference. All required flat fields are present in both scenarios; phase-specific type and range checks happen in `evaluate`.

## Assumptions and limitations

This is a small constructed blame-judgment process, not a classifier, NLP detector, diagnosis, or population model. It does not infer knowledge, duty, intention, or consequence similarity: they are explicit hypothetical inputs. Real judgments may reasonably depend on causal control, alternatives, uncertainty, costs, foreseeability, law, and many other facts. The model holds selected accountability facts shared across both pathways and cannot establish that any observed difference in real life is bias. Software tests check the specified implementation only; they do not constitute empirical validation. No empirical-validity claim is made.

# Response Bias: illustrative implementation

## Process and task metric

This plugin models one narrow questioning-situation pathway: on an explicitly sensitive item, when an evaluative audience is present and the answer is not in private mode, the respondent selects the option maximizing

`task_utility + strength × social_approval`.

Each option's task utility and social-approval score are explicit supplied values in `[0, 1]`. The strength-zero reference selects the option with the highest task utility, using stable input-order tie breaking. This is a transparent comparison policy, not a claim that it is a perfect or universally rational answer.

Contexts are processed chronologically. State retains selected response IDs, the count of eligible items, and cumulative task-utility regret relative to the best-utility option. The primary metric is cumulative regret divided by eligible-item count, in illustrative utility points per eligible item; with no eligible items it is zero. The active flag is true only when an eligible response actually differs from the task-utility reference.

## Necessary conditions and scenarios

The positive scenario has multiple sensitive items, an explicitly evaluative audience, and non-private response mode. Options trade off task utility and supplied social approval, so at strength `0.8` the approval-favored, lower-utility response is selected and mean regret rises relative to strength zero.

The boundary scenario retains sensitive items and the same options but removes the evaluative-audience condition. No audience-driven shift is eligible, so intervention and reference metrics are equal. This is a process boundary, not a hardcoded zero outcome.

A private response mode also disables this modeled pathway. A single unusual answer or deliberate privacy choice alone is not interpreted as evidence of a general response tendency. Sampling bias and other response-style mechanisms are not modeled.

## Assumptions and limitations

This is a compact hypothetical process model, not an NLP detector, diagnosis, population estimate, or empirical claim. Utilities, sensitivity, audience condition, privacy mode, and approval scores must be supplied; none are inferred from text or behavior. It represents only one possible social-approval response distortion and does not capture all survey wording effects, acquiescence, recall, selection, or sampling processes. Strength is an uncalibrated intervention coefficient; its numeric value is not an estimated effect size or prevalence. Passing software checks establishes executable-contract consistency only, not empirical validity.

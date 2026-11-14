# The Illusion of Explanatory Depth — implementation note

## Process and metric

For a prompted mechanism explanation, the task supplies a positive count of causal parts (`mechanism_parts`), how many the participant can explain (`explained_parts`), and a pre-prompt self-assessment (`self_assessed_parts`). Let demonstrated depth be `D = explained_parts / mechanism_parts` and claimed depth be `C = self_assessed_parts / mechanism_parts`. The positive explanation-depth gap is `G = max(0, C - D)`. The illustrative report is `R = D + strength × G`; the primary metric is `R - D`, reported in fractions of the mechanism's causal parts (0–1). This models overestimated understanding specifically when claimed depth exceeds demonstrated depth after an explanation prompt. The state tracks rounds, cumulative excess, and the latest reported and demonstrated depths.

## Reference, activation, and necessary condition

Strength zero is an explicit task reference: the reported depth equals the depth demonstrated in the explanation (`R = D`), rather than asserting perfect understanding or optimal behavior. At positive strength, only a strictly positive self-assessment-minus-explanation gap activates the process. The positive scenario supplies 8 parts, 2 explained, and 7 claimed; at strength 0.8, `D=.25`, `C=.875`, and excess is `.8 × (.875-.25)=.5`. The boundary scenario supplies 8 parts, 6 explained, and 3 claimed, so the necessary positive gap is absent and the metric equals the reference at zero.

## Assumptions and limitations

This is a compact, hypothetical process model, not a classifier, diagnosis, or estimate of population behavior. It assumes a pre-prompt self-assessment and treats mechanism parts as equally weighted; it cannot represent explanation coherence, dependencies, or whether a part is genuinely causal. Poor explanation performance may instead reflect memory, language, time, motivation, or prompt design. Strength is an uncalibrated intervention parameter, not a published effect size. Executable checks establish only software-contract behavior, not empirical validity.

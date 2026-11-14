# Priming implementation note

## Process and task metric

This plugin models a narrow, hypothetical category-choice task. Each chronological task context contains two top-level fields: `exposures` and `options`. An exposure is an explicit structured `{cue, category}` record; the category association is supplied as task data and is never inferred from cue wording. An option is `{id, category, score}`, where `score` is its baseline task utility. The task stipulates that exposure and the later choice have no deliberate inferential link.

For each category \(c\), prior activation decays by 25% per context and every explicit exposure adds one unit:

\[
A_t(c)=0.75A_{t-1}(c)+N_t(c).
\]

At intervention strength \(s\), option \(j\) is selected by maximizing

\[
U_t(j)=\text{score}_t(j)+s\cdot0.8\cdot A_t(\text{category}(j)).
\]

The finite primary metric is an exposed-category choice indicator: 1 when the selected option’s category has positive activation at that time, otherwise 0. It is a task response, not a measure of error, truth, bias severity, or real-world prevalence. The trace reports the category activation and baseline/selected choices. State carries the category-specific activation and the latest choices/metric forward without mutating inputs.

## Reference and necessary condition

Strength zero is the explicit reference policy: choose the option with the highest supplied baseline score, breaking ties by the input order. At positive strength, only a prior explicit exposure whose category is represented by a choice option can influence that choice. The boundary scenario still has a chronological exposure and later alternatives but none has the exposed category; it removes the exposure-to-option category match, so the activation cannot alter the choice or metric. An absent or malformed input is rejected rather than treated as evidence of no effect.

## Scenarios

The positive scenario exposes the category `nature`, then presents an option in that category with baseline score 0 against an unexposed `routine` option scored 0.30. After one intervening context, nature activation is 0.75 and at strength 0.8 its utility increment is 0.48, enough to change the choice. The boundary scenario exposes `nature` but offers only `routine` and `work` options, so both strength settings choose `routine` and have equal metrics. Contexts are genuine chronological events and activation is carried between them.

## Scope, assumptions, and limitations

The decay factor and gain are transparent scenario-design assumptions, not calibrated coefficients or published effect sizes. Strength is an uncalibrated intervention setting, not confidence or population prevalence. The explicit labels and scores make this a compact process illustration only. Priming has multiple forms: this model does not establish that exposure causes any real response, does not infer a priming effect from word co-occurrence, and does not detect or diagnose cognition from text. A category choice can be benign or useful; the process is not inherently an error. Passing code tests and the runner's executable contract is not empirical or human validation.

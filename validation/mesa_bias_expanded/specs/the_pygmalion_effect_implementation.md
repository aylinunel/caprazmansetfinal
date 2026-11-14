# The Pygmalion effect — illustrative implementation

## Process and task metric

This plugin models a narrow expectation-to-treatment-to-performance pathway, not a prediction or language detector. An explicitly supplied evaluator expectation is compared with a supplied neutral reference. For intervention strength `s`, the support allocation is

`T = min(1, baseline_support + s × support_opportunity × max(evaluator_expectation − neutral_expectation, 0))`.

The task score is `min(score_ceiling, baseline_score + T × support_effect)`, measured in illustrative task-score points on a 0–100 scale. The fixed-support reference policy at strength zero uses `T = baseline_support`, regardless of evaluator expectation. Thus the comparison isolates expectation-linked treatment, rather than assuming that the baseline is perfect or has no support. State records the current explicit expectation, treatment allocation, performance score, and fixed-support reference score.

## Necessary conditions and scenarios

The mechanism requires an expectation above the neutral reference, an available support opportunity, and positive efficacy with score headroom for support to change the task outcome. The positive scenario supplies all these conditions. The boundary scenario removes the treatment opportunity (`support_opportunity = 0`), so the expectation cannot change treatment and both strengths yield the same score. This reflects the annotation boundary: expectation or prediction alone is not the modeled effect.

All task facts are structured, hypothetical inputs. The plugin does not infer another person's expectations, motives, treatment, or performance from text or behavior. It reports the task score as its primary metric and exposes treatment and score comparison in state and trace.

## Assumptions and limitations

Coefficients and inputs are illustrative user-settable assumptions, not empirical estimates. Strength is an uncalibrated intervention setting, not a probability, prevalence, or confidence score. The model omits reciprocal feedback, institutional context, alternative causes of performance, and heterogeneity; a bounded score cannot establish real-world causation. Enhanced support can be beneficial and the concept is not classified as a cognitive error. Software contract and scenario tests are not empirical or human validation.

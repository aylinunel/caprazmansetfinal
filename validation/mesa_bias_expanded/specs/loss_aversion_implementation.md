# Loss aversion — illustrative implementation

## Process and task

This plugin chooses among explicitly supplied lotteries. Each option lists outcomes `value` and `probability`, and the task supplies a `reference_point` `r`. For outcome `x`, let `d = x - r`. At intervention strength `s` in `[0, 1]`, the assumed option score is

`V_s = Σ p · (d if d ≥ 0 else (1 + 2s) · d)`.

The selected option is the one with the greatest `V_s`; ties go to the first option. The returned primary metric is the selected option's **unweighted expected reference-relative payoff**, `Σ p(x-r)`, in payoff points. Thus the metric reports a task outcome rather than the internal weighted score. The trace records the reference and weighted choice.

## Strength-zero reference and necessary condition

At `s=0`, every gain and loss is weighted by one, so the comparator chooses the option with the greatest expected reference-relative payoff. This is a transparent reference policy, not a claim of perfect rationality. A mechanism effect requires at least one possible outcome below the supplied reference point and a choice-ranking consequence. If no listed outcome is below the reference, all scores equal their unweighted expected values at every strength, so the same choice and metric result. The positive scenario compares a mixed gain/loss lottery (expected payoff +1) with a sure zero; at `s=.8`, its assumed loss-weighted score is lower and the sure option is chosen. The boundary scenario includes only outcomes at or above the reference, removing the necessary loss condition; the strength-zero and strength-.8 choices therefore coincide.

## Assumptions and limitations

The process takes probabilities, outcomes and the reference point as explicit hypothetical task facts; it does not infer them, classify language, diagnose a person, or model media. The multiplier `1 + 2s` is an illustrative user-settable assumption, not a calibrated coefficient or empirical effect estimate. Strength is an intervention setting, not a confidence or prevalence measure. Lotteries are treated as linear in payoff at strength zero, and no learning, memory, peer influence, affordability, or separate risk-preference model is included. Risk aversion or inability to bear a loss alone does not establish loss aversion. Results and executable tests are synthetic and provide no evidence of empirical validity or detection accuracy.

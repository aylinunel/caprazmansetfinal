# Automation Bias — illustrative implementation

**Process.** The module models a structured choice among options with supplied synthetic task scores from 0 to 100. The reference policy selects the highest-scoring option when an independent verification is available and otherwise follows the automated recommendation. If verification is available and the recommendation is strictly inferior, the mechanism changes only the recommendation's choice score:

`adjusted_recommendation = recommendation_score + strength × (best_score − recommendation_score + 0.5)`

The 0.5-point margin is an explicit illustrative authority assumption, not an estimated effect. The selected option's task score (unadjusted) is the primary metric. `active` is true only when the mechanism changes the reference choice; state carries the decision count, cumulative deference overrides, last choice, and any other prior fields.

**Task and units.** Each decision chooses one option. `task_scores` are synthetic task-outcome points (0–100); the reported `selected_task_score` is the chosen option's raw score. At strength zero, the mechanism reproduces the stated reference policy.

**Necessary condition and boundary.** Automation use alone is not treated as bias. An independent check must be available and must favor a strictly higher-scoring alternative than the recommendation. With no available check, the policy follows the automated recommendation at both zero and positive strength; this is the boundary scenario and yields the same metric as the reference.

**Scenarios.** In the positive case, verification favors an option scored 8.0 over the recommended option scored 7.5. At strength 0.8, the modeled adjusted recommendation score is 8.3, so the recommendation is chosen and the task metric falls from 8.0 to 7.5. In the boundary case, the same scores are evaluator-side task outcomes, but verification is unavailable to the decision process; both policies follow the recommendation and report 7.5.

**Assumptions and limitations.** Inputs are stipulated structured facts; this is not an NLP detector, diagnosis, population model, or fitted account of human trust. Verification status distinguishes a decision-available check from evaluator-only scoring information. The bonus, one-step decision setup, score scale, and tie-breaking by option order are modeling choices. Real automation use may be appropriate or beneficial, and no behavioral or empirical validity is claimed. Tests establish software behavior only; the mechanism is explicitly hypothetical and not empirically validated.

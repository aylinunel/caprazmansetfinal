# Status Quo Bias — illustrative implementation

## Process and task

This plugin simulates one hypothetical choice among named options with supplied task utilities, an explicit incumbent (or `None`), and one nonnegative switching cost. When an incumbent exists, the zero-strength reference scores it at its utility and scores each challenger at utility minus the switching cost. The reference selects the highest net score, breaking ties lexicographically. If the best challenger still exceeds the incumbent, the illustrative status-quo premium is `1.5 × strength × (best challenger net utility − incumbent utility)`. It is added only to the incumbent's selection score. The selected option's reported metric remains its utility after any real switching cost, not its premium-inflated score. `active` is true only when the premium changes the reference choice.

The primary metric is **selected net task utility**, in illustrative task-utility units after explicit switching cost. The zero-strength comparator is the same choice rule with all premiums zero; it is not claimed to be perfectly rational. `state` records the selected option, last metric, decision count, and last premium, while retaining any other supplied state fields.

## Necessary conditions and annotation boundary

A premium requires a named, available incumbent and a challenger whose net utility remains higher after the supplied switching cost. With no incumbent, or when switching costs make the incumbent at least as good as every challenger, the premium is zero. Thus ordinary continuity explained by actual switching costs is not modeled as an error. This stylized task does not represent uncertainty, learning, identity, risk, or hidden motives.

## Scenarios

- **Positive:** incumbent utility 1.0, challenger utility 1.4, switching cost 0.05. At strength 0 the challenger is selected with net utility 1.35; at strength 0.8 the gap-scaled premium can make the incumbent win, lowering selected task utility.
- **Boundary:** same utilities, switching cost 0.5. The challenger net utility is only 0.9, below incumbent utility 1.0, so the incumbent is a justified choice at both strengths and the metric is equal.

## Assumptions and limitations

Utilities, switching costs, the 1.5 coefficient, and strength are explicit illustrative assumptions; strength is an uncalibrated intervention setting, not prevalence, confidence, or an empirically estimated effect. This compact hypothetical model treats options and task utilities as already known, has deterministic tie-breaking, and omits search, uncertainty, preference construction, stakes, and history beyond a decision counter. It is neither an NLP detector nor a diagnosis, population claim, or empirical validity result. Test and integration success checks software behavior only.

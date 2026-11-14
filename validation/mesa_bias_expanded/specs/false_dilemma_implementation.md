# False Dilemma implementation note

This illustrative mechanism takes a supplied menu of feasible options with utilities on a 0–1 scale, a named two-option framed pair, and an explicit boolean saying the frame claims to be exhaustive. The strength parameter is modeled as the probability of accepting that frame (not as calibrated confidence). If the frame is asserted exhaustive and at least one third feasible option exists, the accepted-frame policy selects the highest-utility option in the pair; otherwise the reference policy selects the highest-utility option in the complete feasible menu. Listed order breaks utility ties.

The primary metric is expected utility regret per decision, in utility points:

`strength × (best feasible-menu utility − best framed-pair utility)`

when both necessary conditions (an exhaustive binary claim and more than two feasible alternatives) are present; it is zero otherwise. Choice probabilities are the corresponding mixture of the frame-constrained choice and the full-menu reference choice. The strength-zero reference is therefore the explicit full-menu utility-maximizing policy, not a claim of perfect rationality. State carries the step count, cumulative expected regret, and most recent choice probabilities/expected utility.

The positive scenario supplies three feasible options (utilities .55, .60, and .90), with the .55/.60 pair framed as exhaustive; at strength .8 expected regret is .24 utility points. The boundary scenario has only the two framed options feasible, so there is no omitted third option and the primary metric equals the strength-zero reference at zero. A non-exhaustive frame is also treated as outside the mechanism condition.

All utilities and feasibility facts are explicit synthetic inputs; missing or malformed evidence raises `ValueError`. The model does not infer framing from natural language, assess whether a binary framing is normatively misleading, model frame authorship or reader interpretation, or establish human behavior, accuracy, effect sizes, or prevalence. A two-option choice may be entirely appropriate. The implementation is not empirically validated.

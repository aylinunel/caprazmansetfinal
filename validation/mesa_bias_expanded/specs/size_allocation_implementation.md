# Size allocation: implementation note

This illustrative `media_practice` module allocates a supplied finite package budget among at least two named stories. For story *i* with explicit nonnegative editorial-priority score *pᵢ*, *n* stories, total budget *B*, and strength *s*, it assigns:

`allocationᵢ = (1 − s) × (B / n) + s × B × pᵢ / Σp`

The primary metric is the focal story's allocation in presentation units (for example words, seconds, or layout units); all story allocations sum to the supplied budget, subject to floating-point rounding. At strength zero, the stated reference policy gives every story an equal share. Strength one uses fully score-proportional allocation; intermediate values interpolate between the two. The strength parameter is an illustrative setting, not an empirical effect size.

The necessary condition for a difference from the equal-share reference is a nonuniform distribution of supplied priority scores. The positive scenario gives the focal story a score of 8 against two scores of 2, so at strength 0.8 its 120-unit package share is 80 units, versus 40 under the reference. The boundary scenario gives all three stories equal scores; removing score differentiation yields the same 40-unit focal share at strength 0.8 as at strength zero.

Inputs are structured authored facts, not story-text analysis. The supplied concept spec leaves its annotation boundary blank, so this module operationalizes only a transparent score-conditioned allocation example; it does not claim that the score is fair, accurate, or used by actual editors. Unequal size can have benign editorial explanations. The process is synthetic and explicitly not empirically validated; it omits newsroom constraints, deliberation, alternative allocation policies, and audience effects, and is not a classifier or a measure of bias.
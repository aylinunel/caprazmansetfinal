# Benjamin Franklin effect: illustrative implementation

This module models only the specified direction: the helper gives a favor, then the helper's liking rating for that recipient may rise. It does not model liking by a person who received kindness.

## Process and task measure

Each target has a carried helper-liking rating from 0 to 100. For a previously unseen target, `liking_before` seeds that rating. The reference policy retains the current rating. With strength \(s\), effort \(e\), and current rating \(L\), a unique event explicitly marked `direction="given"` updates it as:

\[
L_{next} = L + 0.25\,s\,e\,(100-L)
\]

The primary metric is the next helper-liking rating in hypothetical rating points (0–100). The factor 0.25 is an illustrative, uncalibrated fraction of remaining scale headroom—not a published effect size. Favor effort is an explicit input in [0, 1]. A processed event ID cannot be applied twice. At strength zero the reference rule applies unchanged.

## Necessary condition and examples

The mechanism requires an explicitly supplied own-giving event with positive effort. `direction="received"` and `direction="none"` retain the rating, providing the boundary comparison. The positive chronological scenario seeds a rating of 50, then applies an own-given favor of effort 0.5; at strength 0.8, the final rating is 55, versus 50 under the reference. The boundary scenario seeds the same rating but has the target give the helper a favor; both strength 0.8 and the reference finish at 50.

## Assumptions and limitations

Ratings, direction, effort, and event identity are structured hypothetical facts, not inferred from language. The linear effort relationship, headroom rule, and coefficient are modeling choices only. The model does not establish that favors cause liking in real people, quantify any real-world effect, or distinguish self-justification from alternative explanations. It omits favor type/cost, relationship history, cultural and individual variation, and measurement uncertainty. It is not empirically validated and is not a classifier or psychological diagnosis.

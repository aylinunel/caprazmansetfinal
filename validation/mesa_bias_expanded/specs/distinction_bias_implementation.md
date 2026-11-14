# Distinction Bias — illustrative implementation

This module models a two-option evaluation task. Each option supplies a use-value and a comparison-feature value on compatible 0–100 scales; the context supplies the feature's explicit use-relevance `r` in `[0,1]` and an evaluation mode. The primary metric is the perceived option-evaluation gap, in evaluation-gap points:

`metric = abs(use_value_1 - use_value_2) + (strength * (1 - r) * abs(comparison_value_1 - comparison_value_2))`

The added term is applied only in **joint** evaluation; it is exactly zero in separate evaluation. The reference policy at strength zero is `abs(use_value_1 - use_value_2)`, regardless of mode. This is a stated comparator, not a claim that it is a perfect or universally rational judgment. `active` is true only if joint evaluation, positive strength, a nonzero feature gap, and some declared feature irrelevance all coincide. Returned state carries round count, cumulative metric, last metric, and last active flag.

The positive scenario uses joint evaluation with low declared relevance and a feature gap that widens the use-value gap. The boundary scenario keeps the same evidence but changes to separate evaluation, removing the necessary comparison condition; its metric must therefore equal the strength-zero reference. A wholly use-relevant comparison feature likewise adds no distortion.

All utilities, feature values, relevance, mode, and prior state are explicit inputs and validated; missing evidence is rejected rather than converted to a zero. The relevance declaration is assumed, not inferred. This small synthetic process illustrates one interpretation of the supplied definition; it is not an NLP detector, diagnosis, population claim, empirically validated model, or estimated effect size. Real feature differences can be useful or important, and one declared feature cannot represent the complexity of actual separate use or human evaluation.

# Suggestibility — illustrative implementation

## Process and task

This plugin models one hypothetical recall-quantity estimate. Let `U` be unaided recall, `S` the suggested quantity, `a` the supplied independent-appraisal level, and `s` the intervention strength. If (and only if) the suggestion is explicitly external and unsupported, the reported estimate is

`R = U + s(1 - a)(S - U)`.

Otherwise `R = U`. The primary metric is `|R - T|`, absolute error from the supplied target quantity `T`, in quantity-estimate units. The output state is `{}` because this single retrieval event retains no across-round process state.

## Reference and activation

Strength zero is the explicit unaided-recall reference (`R = U`) on the same inputs; it is not claimed to be a perfectly rational or accurate person. `active` is true only when an eligible suggestion with nonzero displacement actually changes the estimate. The equation represents a hypothetical pull toward suggestion content, with independent appraisal attenuating it. It does not model the quality of evidence-based correction.

## Necessary conditions and scenarios

An externally supplied, unsupported suggestion is necessary for this model's influence; appraisal further controls its magnitude. The positive scenario uses target and unaided recall of 10, an unsupported external suggestion of 18, and appraisal of 0.25, so strength 0.8 gives `R = 14.8` and error 4.8 versus reference error 0. The boundary scenario changes the same suggestion to supported content, removing the unsupported-content condition; both strengths therefore retain unaided recall and have equal error.

## Assumptions and limitations

The numeric quantities and appraisal value are explicit synthetic inputs, not inferred internal states. The linear interpolation and coefficients are user-settable illustrative assumptions; strength is uncalibrated and is neither prevalence nor confidence. This compact model omits memory encoding, source monitoring, wording, social context, repeated exposure, and individual variation. It cannot distinguish truthful correction processes beyond excluding supported content from this particular mechanism, and it is not an NLP detector, diagnosis, empirical finding, or claim about real-world accuracy. Passing software checks establishes interface behavior only, not empirical validity.

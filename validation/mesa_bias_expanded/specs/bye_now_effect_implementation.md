# Bye-Now Effect: illustrative implementation

This plugin is a deliberately hypothetical process model of the proposed association in which exposure to **bye** activates **buy** through shared sound and may affect spending. It is not an NLP detector: scenarios supply an explicit `bye_exposure` boolean and each choice option supplies a `sound_association` value in `[0, 1]`. Those fields represent structured simulated evidence, not inferred motive or evidence that a real person experienced priming.

## Process and observable

For each chronological choice step, sound activation is `a_t = min(1, 0.5*a_(t-1) + e_t)`, where `e_t` is 1 only for explicit exposure in that step. The reference policy at strength zero chooses the option with the highest supplied base utility (ties retain list order). At strength `s`, option `j` is chosen by maximizing `utility_j + s * 0.75 * a_t * sound_association_j`. The coefficients (one-half retention and at-most 0.75 utility shift) are transparent illustrative assumptions, not estimates. The primary metric is the selected purchase option's supplied price, or zero for a non-purchase option, in currency units spent in the current step. State also carries activation, cumulative spend, last choice, and exposure count.

## Necessary conditions and scenarios

A nonzero proposed effect requires both explicit prior/current `bye_exposure` and a purchase option with positive explicitly supplied sound association; that option must be marked as a purchase. A lone isolated word without a choice opportunity, or a purchase without exposure, cannot establish this mechanism. The positive scenario has an exposure step followed by a choice between waiting (utility 0) and a sound-linked purchase (utility -0.2); at strength 0.8, residual activation is 0.5 and the adjusted target utility is 0.1, so modeled spend changes from 0 to 20. The boundary scenario removes exposure while preserving the option facts, making activation zero and the primary metric equal to the reference.

## Scope and limitations

This is a compact synthetic choice model, not a fitted theory, population claim, classifier, or empirical validation. The proposed effect is explicitly unvalidated. It assumes utilities and prices are meaningful and comparable, sound association is accurately supplied, activation decays geometrically, and the specified sound-linked choice relation is appropriate. Context, individual variation, attention, alternative explanations for buying, and any real-world effect size are omitted. Spending changes in these scenarios are consequences of stipulated synthetic inputs only; media practices and purchases are not automatically errors.
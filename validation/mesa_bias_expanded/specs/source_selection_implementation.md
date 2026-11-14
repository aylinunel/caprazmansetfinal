# Source selection: illustrative implementation

**Process.** For the supplied eligible roster, partition sources into the designated target-view group and all alternative-view sources. Given a selection budget of `B` slots and group sizes `n_t` and `n_a`, allocate a rounded target quota

`q_t = round_half_up(B * n_t * (1 + 4s) / (n_t * (1 + 4s) + n_a))`,

where `s` is the intervention strength in `[0,1]`; cap quotas at group capacity and fill any remaining slots from available sources. Within each group, preserve supplied roster order. At strength zero, this is the explicit reference policy: allocate slots proportionally to the numbers of eligible target and alternative sources. The factor `4` is an illustrative assumption, not a measured effect.

**Task and metric.** Select up to `selection_budget` eligible sources for a hypothetical editorial item. The primary metric is `target_view_share`: the fraction of selected sources whose supplied `view` equals `target_view`, on `[0,1]`. Returned state carries the completed round count, source IDs chosen by round, and the last metric. It does not infer source stance, quality, or intent.

**Necessary condition and boundary.** A source-selection effect requires at least one eligible target-view source and at least one eligible alternative-view source. If either group is absent, the weighted allocation resolves to the same selections as the strength-zero reference; no competing-view selection effect is represented. Missing eligible evidence raises `ValueError`, rather than being treated as a zero score.

**Scenarios.** The positive example supplies two eligible sources for each of two views with a two-source budget; the reference selects one from each view, while strength `0.8` selects two target-view sources. The boundary example has eligible sources only for the target view, so strength `0.8` and zero produce the same metric and source choices.

**Assumptions and limitations.** This is a synthetic, process-level media-practice illustration and is not empirically validated. Labels, eligibility, roster completeness, and the budget are structured inputs supplied by the caller; this is not an NLP detector. All non-target views are collapsed together, source quality and independence are not modeled, and a real one-sided roster may reflect legitimate assignment constraints rather than an error. The model cannot distinguish those explanations from these inputs alone. Passing software tests validates only the implementation against its stated rules, not real-world behavior or detection accuracy.

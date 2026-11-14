# Hindsight Bias — illustrative mechanism

## Process and metric

This module models one binary-event timeline: first a pre-outcome forecast probability `p` is recorded; later the event outcome `y` may become explicitly known. The reference policy preserves the recorded forecast verbatim. With known `y`, the illustrative reconstructed recollection is `p_recalled = p + strength × (y − p)`, where `strength ∈ [0,1]` is a user-settable intervention parameter, not an effect estimate. The primary metric is the absolute outcome-aligned shift `|p_recalled − p|`, in probability points on a 0–1 scale. Before an outcome is known, or when it remains explicitly unknown, there is no reconstruction and the metric is zero.

This is deliberately about retrospective beliefs regarding prior predictability. It neither scores the original decision nor infers decision quality from the result. A recorded forecast and a later, explicitly known outcome are necessary for a positive metric; explicitly unknown outcome is the boundary case. The positive scenario records `p=0.2`, then reveals `y=1`, yielding `p_recalled=0.84` and shift `0.64` at strength `0.8`. The boundary scenario follows the same forecast with `outcome_known=False` and matches the reference metric of zero.

## Assumptions and limitations

The model assumes the supplied forecast is a trustworthy record and uses a simple linear blend to represent outcome-consistent retrospective reconstruction. It covers only a single binary event, not memory noise, elicited confidence, richer forecasting, or decision quality. The coefficient and resulting values are illustrative, not empirically validated; the module is not a detector, diagnosis, population claim, or NLP classifier. Other explanations or reporting practices may account for retrospective forecast changes in real settings. Media practices and beneficial heuristics are not treated as errors by this mechanism.

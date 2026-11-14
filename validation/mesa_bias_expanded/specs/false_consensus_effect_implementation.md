# False Consensus Effect — illustrative implementation

This module models a forecast of peer agreement with an explicitly supplied own position; it does not infer beliefs from language or treat a communication practice as an error. For `n` supplied peer choices, let `q` be the observed fraction matching the agent's own position. The strength-zero reference forecast is `q`. At strength `s`, the mechanism uses an assumed own-position pseudo-count mass of `4s`:

`forecast = (n*q + 4s) / (n + 4s)`

The primary metric is this forecast as a fraction from 0 to 1. The coefficient 4 is a transparent illustrative assumption, not a measured effect size. With no explicitly owned position (`own_position=None`), agreement-with-self is undefined; the boundary task instead forecasts the observed A share and is unchanged by strength. Thus, the necessary condition is both explicit ownership and supplied non-empty peer-position evidence.

The positive scenario supplies one A and four B responses while the agent owns A, so the forecast at strength 0.8 exceeds the observed 0.2 share. The boundary scenario removes the owned-position condition and returns the strength-zero A-share reference. The state retains complete per-step forecast and reference histories.

**Assumptions and limitations:** This is a compact synthetic process illustration, not a classifier, diagnosis, population claim, or fitted model; it is explicitly not empirically validated. A supplied sample may be unrepresentative, and a forecast is not actual peer agreement or forecast accuracy. It does not model pluralistic ignorance, private/public belief gaps, deliberation, or whether projection is beneficial in any setting. Strength is an intervention parameter, not prevalence or confidence. Missing or invalid observations raise `ValueError` rather than being interpreted as zero agreement.

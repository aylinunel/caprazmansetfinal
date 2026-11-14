# Messenger Effect — implementation note

## Process and task

For one otherwise fixed message, the supplied `message_support` (strictly between 0 and 1) is the strength-zero reference probability of reception. The explicit signed `messenger_affinity` cue and `cue_salience` alter reception odds by

`odds(reception) = odds(message_support) × exp(strength × 1.5 × messenger_affinity × cue_salience)`.

The reported `reception_probability` is the corresponding logistic probability on a 0–1 scale. It is an expected task response, not a realized choice or a judgment of message truth. The coefficient 1.5 is a transparent illustrative assumption; strength is an uncalibrated intervention setting, not a measured effect size or confidence estimate. State records the last task reception and number of task evaluations.

## Reference, condition, and scenarios

The explicit reference policy sets the cue contribution to zero (`strength=0`) while retaining the same message inputs. A messenger effect requires an available cue (`cue_salience > 0`) and nonzero signed affinity. The positive fixture uses message support 0.60, affinity 0.80, and salience 0.90, so strength 0.8 raises reception relative to the reference. The boundary fixture retains the same message and affinity but sets salience to zero: the messenger cue is unavailable, so the odds multiplier is exactly one and reception equals the reference.

Only `message_support`, `messenger_affinity`, and `cue_salience` are declared required scenario inputs; all are validated inside `evaluate`. Runner-owned state and scheduling fields are not scenario inputs.

## Scope and limitations

This is a compact hypothetical process illustration, not an NLP detector, diagnosis, population claim, or empirically validated model. The cue is explicitly relational/familiarity affinity, not status or authority; status-driven deference is outside this module. Messenger cues may be informative or benign, and the implementation cannot assess whether a cue is warranted. A negative affinity lowers reception symmetrically in the equation. The form and coefficient are simple user-settable assumptions; neither simulated changes nor passing implementation tests establish real-world accuracy, prevalence, or causation.

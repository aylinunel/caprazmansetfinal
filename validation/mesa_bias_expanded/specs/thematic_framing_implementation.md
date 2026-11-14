# Thematic framing implementation note

This is a **hypothetical, synthetic-only media-practice model**, not an empirical account of newsroom behavior, a quality judgment, or an NLP detector. It covers only trend-based contextualization of an incident; it does not model institutional or process framing.

## Process and metric

For a chronological sequence of supplied rates, define the trend signal as `abs(last - first) × abs(last - first) / sum(abs(adjacent change))`, with the signal set to zero for a flat sequence. This is the magnitude of the endpoint change discounted by reversals. The available context capacity is `article_word_budget - incident_word_reserve`. When the source is verified, the topic matches, relevance is positive, and the series is non-flat, the current allocation is:

`floor(context capacity × strength × context relevance × trend signal)`

The returned primary metric is whole **article words allocated to the trend-context passage in this step**. The model carries a cumulative word total, round count, and per-step allocation history in state. The coefficient `strength` is an illustrative control from 0 to 1, not an estimated effect size.

## Reference, conditions, and scenarios

At strength zero the explicit reference policy is incident-only copy: allocate zero words to trend context while retaining the incident word reserve. A positive scenario uses a verified, topic-matched, steadily rising four-period sequence; at strength 0.8 with the included budgets and relevance, the process allocates 43 context words. The boundary scenario keeps the data but removes topic match, a necessary condition, and therefore equals the zero-strength reference (zero allocated words) even at 0.8. Missing or malformed trend evidence raises `ValueError`; it is not silently treated as a zero metric.

## Assumptions and limitations

A publisher may choose to use supported contextual facts, and doing so is not inherently misleading or erroneous; this model represents only one possible space-allocation choice. It does not establish that a trend is causally relevant, that a given context is balanced or useful, or that an audience's interpretation changes. Verification, topical match, comparability, and rates are supplied structured facts rather than inferred. The specification's annotation-boundary field is blank, so the implementation adopts the narrow boundary above and makes no stronger claim. There is no empirical validation or detection-accuracy evidence.

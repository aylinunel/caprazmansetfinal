# Representativeness heuristic: illustrative implementation

## Process and task

The plugin simulates a structured categorization choice among supplied options. Every option provides a prior frequency, a likelihood for the supplied evidence, and a numeric prototype-similarity score. It first computes and normalizes `prior × likelihood` across options, then normalizes prototype similarities. For option *i*, the choice score is

`score_i = (1 − strength) × posterior_i + strength × normalized_similarity_i`.

The highest score is selected, with input order breaking ties. At strength zero, the reference policy selects the maximum posterior based on the supplied priors and likelihoods. Strength is an uncalibrated intervention setting; it is not an empirical effect size or confidence estimate.

The primary metric is a 0/1 selected-option error against the explicitly supplied `true_option`. That answer is part of this hypothetical task, not an inferred hidden state or real-world diagnosis. State records the latest choice and task error while preserving other prior state fields.

## Conditions and scenarios

At least two distinct options, valid finite [0, 1] priors/likelihoods/similarities, positive total prior-times-likelihood evidence, positive total similarity, and a `true_option` among the options are required. The heuristic needs a meaningful prototype-similarity contrast to change the score vector. In the positive scenario, the evidence-favored true option A has posterior 6/7 while less likely B has posterior 1/7; B has the stronger supplied prototype match. The blend therefore selects B at strength .8, whereas strength zero selects A. In the boundary scenario, both options have exactly equal prototype similarity. This removes the differential prototype cue; the score ranking then matches the posterior reference and the metric is equal.

## Scope and limitations

This is a compact process illustration, not an NLP detector, classifier of people, diagnosis, or population claim. It assumes the supplied structured values are meaningful and does not assess their quality. Prototype similarity can be useful; this example only constructs a conflict with supplied probabilistic evidence. Similarity substitution can overlap with base-rate neglect, but neither label follows automatically from the other or from a choice observation. No empirical validity or detection accuracy is claimed.
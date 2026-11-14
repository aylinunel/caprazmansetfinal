# Mere Exposure Effect — illustrative implementation

## Process and task

This plugin models preference among a small, explicitly supplied set of items. Each round supplies `options` (item IDs and finite baseline utility values) and `exposures` (neutral encounters with those items). Per-item exposure counts are carried chronologically in `state.exposure_counts`. No claim, truth judgment, or substantive new information is represented; the annotation boundary is liking through familiarity, not belief that a repeated claim is true.

After adding this round's encounters, the intervention computes an item-specific familiarity lift

\[
L_i = s\, 0.30\left(1-e^{-\max(n_i-1,0)/2}\right),
\]

where `n_i` is the accumulated count and `s` is the supplied strength in [0, 1]. Thus an item must be encountered at least twice for the illustrative lift to become positive, and the lift saturates. Choice maximizes `baseline utility + L_i`, with a stable lexical tie-break. The primary metric is `L_i` for the selected option, in illustrative utility points above its baseline utility. The numerical coefficients are design assumptions, not measured effect sizes.

## Reference and scenarios

At strength zero, all supplied exposures and counts remain in state, but every `L_i` is zero and choice maximizes baseline utility alone. This is the explicit comparator, not a claim of perfect or universally rational behavior.

The positive scenario exposes option A in each of three chronological rounds. Its utility begins below B, but repeated familiarity can make A the selected option and yield a positive metric. The boundary scenario presents A once and B once, then no item again. It removes repetition, a necessary condition in this model; the nonlinear repeated-exposure lift stays zero and treatment matches the strength-zero choice.

## Assumptions and limitations

Exposure lists are stipulated neutral encounters; this is not an NLP, image, or media detector. The process omits affect, attention, context, individual differences, semantic content, and whether repeated contact actually feels familiar. It simulates only a bounded preference effect, not truth belief, persuasion, or an individual diagnosis. Strength is an uncalibrated intervention setting. Tests and runner validation establish executable behavior only, not empirical validity.

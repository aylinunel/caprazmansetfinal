# Rosy Retrospection — illustrative implementation

## Process and task metric

This synthetic chronological task records an episode's explicit experience rating (0–100) and nonnegative salience weights for positive and negative details. At a later simulated round, it reconstructs cue valence after differential accessibility loss. For elapsed rounds `t`, positive and negative accessible saliences are `P_t = P exp(-0.10t)` and `N_t = N exp(-0.45t)`. Encoded valence is `(P-N)/(P+N)`; recalled valence is `(P_t-N_t)/(P_t+N_t)`. The reported recalled episode rating is `clip(actual_rating + strength × 20 × (recalled_valence - encoded_valence), 0, 100)`. Thus a shift requires recorded experience, elapsed time, and both positive and negative cue salience. It is a specific assumed memory-reconstruction process, not a generic belief update or detector.

The primary metric is an illustrative **recalled episode rating**, in task rating points on a 0–100 scale. During the experience phase the metric is the supplied rating. The strength-zero reference returns the recorded episode rating on recall: it is an explicit no-reconstruction policy, not a claim of perfect memory. Strength scales the hypothetical differential-accessibility process and is neither calibrated confidence nor an empirical effect size.

## Conditions and scenarios

The positive scenario records a mixed-valence episode rated 50, then recalls that same episode one round later. Faster loss of negative-cue accessibility makes its reconstructed rating exceed the recorded-rating reference. The boundary scenario records positive cues but no negative cues. With no negative evidence available to fade asymmetrically, the encoded and reconstructed valences are identical and intervention/reference ratings match. This removes a necessary condition rather than assigning a zero by scenario label. Inputs are explicit structured hypothetical episode facts; the mechanism does not treat nostalgia-related spending or broad societal declinism as evidence of this cognitive process.

## Assumptions and limitations

The relative decay rates, maximum 20-point mapping, equal availability of details in the positive example, and linear strength interpolation are illustrative user-settable assumptions, not published effect sizes or fitted parameters. The model excludes rehearsal, retrieval goals, mood, context, individual differences, detail creation, and many other memory processes. Its narrow cue-weighted process cannot infer real people's memories, causes, or diagnoses. Software tests and runner integration assess executable contracts only, not empirical validity.
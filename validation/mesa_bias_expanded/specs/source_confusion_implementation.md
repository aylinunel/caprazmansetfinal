# Source Confusion — implementation note

## Process and task measure

For each remembered item, candidate source `j` has supplied source-cue match `C_j` and content familiarity `F_j`, each constrained to `[0, 1]`. At intervention strength `s`, the illustrative source-attribution score is

`S_j(s) = (1 - s) C_j + s F_j`.

The selected source is the candidate with the highest score; exact ties are resolved by source ID so the process is deterministic. `strength = 0` is the explicit reference policy: select the candidate with the strongest source-specific cue match. At positive strength, content familiarity competes with retained source cues. Thus a remembered item's familiar content can be selected as coming from a different candidate even when the target source has the strongest source cue. This is a proposed process illustration, not a fitted or validated account.

The per-item primary metric is `source_misattribution`: `1` when the selected source differs from supplied `origin_source`, otherwise `0` (binary error per remembered item). The state carries the number of processed items and misattributions, last selected source, and last score margin. `active` is true only when the blended-evidence choice differs from the source-cue reference choice. Trace lines expose the inputs and choice. The score margin is an uncalibrated process quantity, not human confidence.

## Conditions and scenarios

Inputs in every phase are the top-level fields `origin_source` and `candidate_sources`. Evaluation validates each candidate's unique `source_id`, `source_cue_match`, and `content_familiarity`; the origin must be one of the candidates. The positive example includes a source with stronger source-cue evidence and a competing source with stronger familiarity. The boundary example has only the true source as a candidate, removing the alternative-source condition required for misattribution; changing familiarity weight cannot create a wrong-source choice there.

A wrong origin judgment does not imply that remembered content is false. Conversely, this model does not represent source forgetting as a separate outcome: a weak or ambiguous source cue may produce a small simulated score margin, but the task still requires a choice among supplied candidates. It does not infer truth, detect source confusion in natural language, or estimate a person's state.

## Assumptions and limitations

The linear blend and supplied scores are hypothetical, user-settable task abstractions. Strength is an uncalibrated intervention parameter, not a prevalence or confidence estimate. The model omits encoding, later cue changes, source-knowledge availability outside the supplied candidates, individual differences, and graded uncertainty. Scenarios and executable checks establish only that this implementation follows its stated contract; they provide no empirical validation or population claim.

# Dunning–Kruger Effect: illustrative mechanism

This plugin models a narrow **task-level review-allocation process**, not a person, diagnosis, detector, or population. Every structured item supplies an ID, objectively scored correctness, reported confidence in `[0, 1]`, and positive `review_value` (the task value assigned to checking that item); each batch also supplies a finite review budget. The primary metric is the **count of incorrect current-batch answers left unreviewed**.

The model carries counts and confidence sums chronologically. Let `a` be cumulative accuracy and `c̄` mean cumulative reported confidence. At least four scored attempts and two errors are required. The joint evidence gate is

`g = max(0, (0.5 − a) / 0.5) × max(0, c̄ − a)`.

The `0.5` marker is an illustrative user-set task threshold, not a published or calibrated cutoff. For item `i`, review priority is

`pᵢ = review_valueᵢ × ((1 − confidenceᵢ) − 6 × strength × g × confidenceᵢ)`.

A bounded queue selects the highest-priority items (ID breaks ties). The base policy values consequential uncertainty. When repeated evidence jointly shows low task accuracy and confidence above accuracy, the assumed suppression term further lowers priority for confident items, potentially leaving a confident error unreviewed in favor of another item. The coefficient `6` is an illustrative assumption, not an empirical effect size. The returned metric counts objectively incorrect items not selected in that batch; the correctness field is used to score outcomes, not to infer hidden psychology.

**Strength-zero reference.** At strength zero, the queue ranks `review_value × (1 − confidence)`, an explicit consequential-uncertainty review policy. It is a task-specific comparator, not a claim of ideal or universally rational behavior. `strength` in `[0, 1]` scales only the assumed evidence-gated suppression.

**Scenarios.** Both scenarios have two chronological contexts, and each evaluation carries cumulative score and confidence history into the next batch. The positive scenario begins with four scored items at 25% accuracy and mean confidence 0.75. In its second two-item batch, one high-value confident answer is incorrect and one low-value uncertain answer is correct. With prior history included, the strength-zero queue reviews the error, while strength 0.8 selects the uncertain correct answer, leaving one additional current-batch error unreviewed. The boundary begins with five items (three correct, two errors) and then supplies one correct answer and one error; cumulative accuracy is 4/7, above the illustrative 0.5 low-accuracy threshold. The required low-competence condition is therefore absent, the gate is zero, and the final-batch metric and selection match strength zero.

**Assumptions and limitations.** All observations are synthetic structured inputs, not detected from language. The process assumes comparable attempts, reliable answer keys and confidence reports, externally meaningful review values, and a particular review-allocation policy. Difficulty, noisy scoring, unfamiliarity, anxiety, fatigue, poor instructions, or strategic reporting can produce similar patterns. It does not model feedback, learning, incentives, or alternative metacognitive processes and cannot support a diagnosis or population-level inference from an individual or anecdote. Strength is uncalibrated; the coefficient and threshold are hypothetical. Software tests verify implementation behavior, not psychological validity or detection accuracy.

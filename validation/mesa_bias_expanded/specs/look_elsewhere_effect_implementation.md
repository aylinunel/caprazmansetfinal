# Look-elsewhere effect: illustrative implementation

## Process and task metric

Each task step supplies `candidate_z_scores`, the complete set of comparable standardized test statistics explored. The simulated analyst chooses index \(i^*=\arg\max_i |z_i|\), computes its two-sided single-test probability \(p_s=\operatorname{erfc}(|z_{i^*}|/\sqrt{2})\), and computes the independent-tests family-wise reference \(p_f=1-(1-p_s)^m\), where \(m\) is the number of supplied tests. The reported evidence metric is

\[
E(s)=(1-s)(-\log_{10}p_f)+s(-\log_{10}p_s), \qquad s\in[0,1].
\]

The finite, task-specific metric is **reported \(-\log_{10}(p)\)**; larger values mean stronger stated evidence. At strength zero the explicit reference policy reports family-wise-adjusted evidence. Increasing strength moves the report toward the selected test's unadjusted evidence, modeling how selection from multiple opportunities can make a result look more impressive when multiplicity is ignored. The selection and multiplicity relation—not a generic belief offset—drives the difference. State records the candidate count, selected index/statistic, both probabilities, and reported evidence; the trace explains the computation.

## Inputs, scenarios, and boundary

`candidate_z_scores` is the only metadata-required scenario input because it is the only task field required on every call. Evaluation validates it as a nonempty sequence of finite, non-boolean numeric z-scores in [-8, 8]; phase-specific or malformed evidence is rejected rather than treated as no effect. Runner-owned context fields are not scenario data.

The positive scenario supplies five candidate tests, so the selected unadjusted evidence exceeds the family-wise reference and strength .8 increases the final mean metric relative to strength zero. The boundary supplies one candidate only: there is no multiplicity to ignore, so its family-wise and single-test probabilities coincide and both strengths produce the same metric. Both scenarios use the same task construction and the boundary removes the necessary condition (search across multiple candidates), rather than forcing a zero outcome.

## Assumptions and limitations

The independent-tests adjustment is an intentionally transparent approximation; real test statistics may be dependent and need not be standard normal. Inputs are supplied structured facts, not inferred from text, and the model cannot establish whether a search was exploratory or confirmatory, whether hypotheses were preregistered, or whether independent replication exists. Exploratory searches can be useful and honest; the concept is the overstatement of selected evidence when multiplicity is ignored, not dishonesty or a diagnosis. Strength is an uncalibrated intervention setting, coefficients/process choices are illustrative, and this implementation makes no empirical validity or detection-accuracy claim.

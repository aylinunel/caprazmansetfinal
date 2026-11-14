# Accountability diffusion in AI — illustrative mechanism

## Process and metric

For each required remediation action, the reference policy assigns the lead to the stakeholder with the highest supplied `role_fit` (ties by stakeholder ID), without treating an explicit disclaimer as proof that the task is ownerless. This is a simple comparison policy, not a claim of ideal responsibility allocation. The mechanism uses the supplied task-level uniform draw: a cascade is enabled only when there are multiple listed stakeholders, the role-fit lead explicitly disclaims, and `uniform < strength`. If enabled, ownership follows the lead's explicit `refers_to` links until an actor explicitly accepts, a terminal disclaimer is reached, or a referral cycle is encountered. Terminal disclaimers and cycles leave the action unowned. There is no inference from text or from distributed work alone.

The primary metric is `unowned_required_action`, a binary task-level indicator: **1** if no stakeholder owns the required action, otherwise **0**. State records the task count, cumulative unresolved count, owner history, and last owner. `active` indicates that the resulting owner differs from the role-based reference owner. The uniform draw gates the complete referral cascade once per task; the model does not model independent actor-level probabilities.

## Necessary conditions and scenarios

A required action, explicit stakeholder role-fit evidence, and explicit ownership decisions are required; missing/impossible evidence raises `ValueError`, rather than being scored as zero. Diffusion additionally requires more than one stakeholder, an explicit disclaimer by the reference lead, and a successful strength-controlled gate. The positive example has two stakeholders who explicitly disclaim in a referral chain terminating without an owner; at strength 0.8 and uniform 0.5, the unowned metric changes from 0 to 1 relative to the role-based reference. The boundary example retains distributed work but has both stakeholders explicitly accept; it therefore produces the same metric and owner as the strength-zero reference.

## Assumptions and limitations

This is a compact synthetic process illustration, not empirical psychology, prevalence estimation, a classifier, a diagnosis, or an NLP detector. Role-fit scores, decisions, referrals, and strength are hypothetical user-supplied inputs; strength is not a calibrated effect size. Real accountability may be shared constructively, formally assigned outside the observed group, or affected by legal, institutional, and organizational arrangements omitted here. A binary metric and single referral chain cannot represent all those cases. Software tests validate implementation behavior only and do not constitute empirical validation.

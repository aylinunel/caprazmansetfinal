# Loaded language — implementation note

This module implements a **hypothetical media-practice / reader-appraisal process**, not a detector or an empirically validated psychology model. For an event with supplied factual appraisal `v`, linked evaluative wording with supplied appraisal `e` and intensity `i`, intervention strength `s` gives `w = s × i` and reader appraisal `a = (1 − w) × v + w × e`. The primary metric is `a`, normalized appraisal points on `[-1, 1]` (negative to positive evaluation). The returned state records the appraisal sequence and latest framing shift.

**Task and reference.** Estimate an illustrative reader's appraisal of the same reported event. At strength zero, the explicit reference policy uses the reported factual appraisal alone: `a = v`. Strength is a user-settable illustrative control, not a probability or estimated effect size.

**Necessary conditions and boundary.** The shift applies only when evaluative wording is explicitly present and explicitly targets the event. Missing required fields, malformed values, or out-of-range appraisals are errors. A negative event report alone is not loaded language: if no evaluative wording is supplied, the result remains `v`. Supplied evaluation about something other than the event also leaves the event appraisal at `v`.

**Scenarios.** The positive example pairs factual appraisal `0.2` with event-linked evaluation `−0.8` at intensity `0.75`; strength `0.8` yields `−0.4` versus the strength-zero `0.2`. The boundary example reports an event at `−0.7` without evaluative wording; both strengths return `−0.7`.

**Assumptions and limitations.** Inputs are structured hypothetical annotations; the module does not inspect words, establish whether a phrase is warranted, or measure a real audience response. A linear blend is a compact process assumption without fitted coefficients, human validation, or detection-accuracy evidence. Evaluative phrasing may be justified, ordinary, or benign; it is not inherently an error or harm. The module is explicitly **not empirically validated**.

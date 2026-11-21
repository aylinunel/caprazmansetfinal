# Single-source lens and expert-trained AI: decisions so far (brainstorm, 2026-11-20)

Status: brainstorm in progress, not an approved design.

## Why (owner's words)
Discover how different media framings, through media manipulation and the use of behavioural biases,
affect our world view if we consume news from a single source. Seeing an overview of how a country's
media presented a specific news story gives more insight into hidden agendas.

## Decided
1. Two views: "one story, whole country" (the existing Olay page, told better) and "one outlet, whole
   season" (new: the world as a single-source reader sees it, against the full spectrum).
2. Wording: describe patterns with their strength (option b). Name the pattern outright ("X systematically
   plays down Y", option a) only when it is unmistakable. Proposed rule for "unmistakable": at least 20
   eligible stories, a gap of at least 2 to 1 against outlets on the same stories, q < 0.01 after
   multiple-comparison correction, and the pattern holds in every month. Behaviour, never motive.
3. Score: short term, an outlet's "distance from the full picture" uses only proven measures (coverage,
   loaded wording, headline vs lede, timing, party tone), compared within the same stories (regression with
   event fixed effects). AI findings appear beside it as "additional insights", labelled AI imzalı.
4. New: a structured "behavioural scientist AI checker" dashboard under Yönetim, where experts review,
   reject and explain AI findings; every review, rejection and explanation becomes training data, so the
   AI gets stronger with each one. A concept joins the score once the expert answer key shows it is reliable.

## Related
- Stakeholder report: https://claude.ai/artifact/9szRkwkQAYjcGzeGMw1Xv1
- Plan: docs/superpowers/plans/2026-11-17-ml-narrative-and-behavioural.md (answer key, measurement, learning)

## AI denetim masası (built 2026-11-20)
- Reviewer: only the owner (a behavioural-science expert); the existing owner-only `reviews` collection is enough.
- Critique of the old "Bilişsel inceleme (YZ)" page: a 101,501 px report with 1,425 buttons, free-text-only judgement,
  no progress, hidden evidence, no filters, three words for one status, mixed queues.
- Strategy: job = "judge each finding fast and in a way the AI can learn from"; outcome = concepts made measurable
  (20 expert reviews each, keep-rate with a one-sided 95% Wilson lower bound, same as validation/feedback/stats.py).
- Design: queues (Davranışsal / Medya teknikleri / Bekleyen medya kartları / Anlatı kodlamaları), one finding in focus,
  all outlets' headlines with quoted words highlighted, the card's necessary conditions (Var / Yok / Belirsiz), verdict
  Doğru / Kısmen doğru / Yanlış (= verified / corrected / rejected, so public pages keep their meaning), reason chips,
  correct-concept picker, explanation, seconds spent; keys 1/2/3, J/K, Enter; undo toast; learning panel per concept.
- Data: core key BGC (necessary conditions of concepts with findings); reviews export and validation/feedback labels
  carry verdict, reason, card_correct, conditions, seconds. The old report stays at ?v=ozet.

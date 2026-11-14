# Çapraz Manşet Final: integration design

**Date:** 14 November 2026
**Status:** revision 2, after the owner's decisions of 14 November (see "Owner decisions" below). Where an
earlier section conflicts with that section, the decisions win.

## Inputs

| Input | What it is | State when read |
|---|---|---|
| `aylinunel/caprazmansetnov26`, branch `claude/sleepy-goodall-sd1d9r` @ `49b60bc4fd0407f8f979c08cd7e5ab0641ad040d` (ahead of `main` by site changes only) | The existing project (8.1): Python batch pipeline, static site, BiasGuard | Read in full; not modified |
| "Claude Code developments…" report | Ten proposed Claude Code controls (A01–A10) and seven required corrections | Written against `caprazmanset-oct26` (React/tRPC/MySQL/pnpm), a different codebase. **Skipped for now at the owner's request; an updated version for the November repo will replace it** |
| "Integrating the Mesa Cognitive-Bias Simulation Framework…" guide | How to use the Mesa package as an offline validation lab | Read in full |
| `mesa_bias_expanded_complete.zip` | 138 Mesa mechanisms, 590 checksummed files, 40 MB (35 MB is sweep output) | Unpacked and inspected; its tests were not re-run |

| `reference_adapter.py` | The guide's Appendix A demo: `selective_statistics` rendered for a mock detector | Read; kept as a reference fixture, not as lab code |
| "Benchmark patterns, not a replacement detector" and `repositories.json` | Review of eight open-source projects for test design and harnesses | Read in full |
| "Mesa sample" write-up | The earlier four-rule Mesa demo (`legacy_mesa_model.py`) | Read; no action, it stays the partial proxy it says it is |
| `expanded_mesa.py`, `expanded_mesa_biases.py`, `test_pluralistic_ignorance.py`, `test_standalone.py` | Sent separately | Byte-identical to the copies inside the archive |

Not supplied: the Phase 1 starter kit (`guard.py`, `safe_pr_check.py`, reviewer definition). Not needed
while the controls are on hold.

## Intent

`caprazmansetfinal` is the next version of Çapraz Manşet: the owner's headline-comparison pipeline plus
BiasGuard, with stronger analysis and bias labels whose accuracy has been measured. Before the site goes
live, every AI label is verified and corrected by educated human reviewers. The aim is the most accurate
detector reachable before that date, with the evidence to say how accurate.

## Goals

1. The new repo starts as an exact, attributed copy of the 8.1 project, with all existing tests passing.
2. *(On hold.)* Claude Code controls for this codebase: a guard, an explicit check runner and a
   read-only reviewer. Waiting for the owner's updated report.
3. BiasGuard can be run against controlled Mesa-derived cases without ever seeing the answer, and every
   attempt is recorded, including failures.
4. Human verification of AI labels produces a reference set, and BiasGuard versions are compared on it
   with honest denominators.
5. A written gate decides which labels may appear on the public site.

## Non-goals

- Changing the pipeline's analysis stages, the site design or the scalable-architecture migration in
  `.10x/decisions/architect/scalable-architecture.md`. Those are separate projects.
- Calling a model provider. Every plan runs offline; live reviewer runs stay a deliberate owner action.
- The report's A05 (TypeScript LSP), A08 (GitHub MCP), A09 (Context7) and A10 (PR Review Toolkit).
  The repo has four small `.ts` files and no TypeScript build; the other three duplicate tools already in use.

## Anti-goals

These would make the work a failure even if it runs:

- A simulation result, a software-test count or an AI-authored benchmark presented as detector accuracy.
- A failed, missing or unassessed review counted as "no bias".
- Simulation internals (strength, expected label, scenario name, seed, split) reaching the detector.
- A Mesa metric averaged into a BiasGuard verdict or shown as a confidence percentage.
- Any public label that infers intent, mental state or political affiliation.
- An AI label published as human-verified when it was not.
- "AI onaylı" presented as a measured accuracy or a probability.

## What the existing project already does

- **Pipeline** (`pipeline/capraz_pipeline/`): ingest → score → classify → cluster → events → topics →
  analyse → narratives → export to `core.bin` and monthly packs. Tests: `unittest`, offline.
- **BiasGuard** (`biasguard/`): 116 concept cards; a selector, an advocate and a skeptic; exact-quote
  checks; necessary-condition gates. `BiasGuard.analyze(text, context, stakes, mode, max_candidates,
  exhaustive)` returns one of `input_rejected`, `offline_candidates_only`, `analysis_incomplete`,
  `review_complete`. Reviewers are injectable (`BiasGuard(cards=..., reviewer=...)`).
- **News input** (`biasguard/news.py`): one case per event, each outlet's first headline and lede, plus a
  context block. BiasGuard does not see full articles.
- **Recorded weakness** (`docs/biasguard-simulation/summary.json`): 23 of 52 cases completed; 24 of 62
  required labels delivered end to end. Completion, not labelling, was the main loss.
- **CI**: one job, pipeline unit tests only. BiasGuard and site logic tests are not in CI.

## Findings that shaped the design

1. **The report's stack assumptions do not apply.** No pnpm, no database, no migrations, no draft/publish
   workflow. The guard and runner keep their architecture and get a new policy map. The "editorial
   invariants" reviewer is replaced by an "analysis invariants" reviewer with this repo's contracts.
2. **The crosswalk has a concrete starting point.** 112 of 138 Mesa ids equal a BiasGuard card id after
   `_`→`-`. The other 26 are media practices with no card. Same id is a proposal, not a semantic match.
3. **Evidence access is the binding limit.** With headlines and ledes only, concepts that need a full
   source inventory, omitted context, images or page layout are not assessable.
4. **A lab-only catalogue extension gives a real comparison.** `BiasGuard(cards=...)` accepts an injected
   catalogue, so a proposed card can be evaluated as "candidate" against the stock "baseline" without
   touching `biasguard/data/cards.json`.
5. **Human verification makes real measurement possible.** The owner confirmed reviewers will verify and
   correct AI labels. That verification is the reference set; it must be captured in a form the metrics
   can read, and reviewers must first label blind to the AI output for the measured sample.

## Approaches considered

**A. Three layers in one repo, built in order (chosen).** Seed from 8.1; add controls; add an offline
lab package next to BiasGuard; add human-reference tooling and gates. The production path is unchanged
until a measured comparison justifies a change.
*Trade-off:* slower to visible detector changes. In return every later claim has a denominator.

**B. Extend the catalogue first.** Add the 26 media cards and new prompts now, validate afterwards.
*Rejected:* it raises the number of labels per event before anything measures whether they are right,
which is the guide's main warning, and most of the 26 are not assessable from headlines.

**D. Adopt promptfoo and Pydantic AI as the harness, as the benchmark review suggests.**
*Not adopted for now:* BiasGuard already has strict schemas, exact-quote checks and a file-based reviewer
workflow, and the lab's value is in denominators those tools do not define (ineligible, unassessed,
family-level resampling). A stdlib harness keeps the repo free of a Node test runner and a second
schema layer. Revisit if the test matrix outgrows `unittest`. The review's test-design ideas are
adopted: matched control/treatment pairs, and paired perturbations (outlet-order reversal, outlet
relabelling, irrelevant detail) scored for consistency. No code or data is copied from those projects;
CoBBLEr has no verified licence and the benchmark is CC BY-SA.

**C. Keep the lab in a separate repo.** Cleaner separation, no vendored 5 MB.
*Rejected:* the lab must run a frozen copy of the same BiasGuard code and card hash; two repos make that
drift silently.

## Design

### Layer 1: foundation

In scope now: the repo is seeded with the full tree at the commit above, in one commit, with
`docs/provenance/seed.json` recording source repo, commit and date; CI runs the BiasGuard and site-logic
tests alongside the pipeline tests.

#### Controls (on hold)

Everything from here to "Layer 2" is a draft kept for the rewrite. It is not part of the current plans.

- The repo is seeded with the full tree at the commit above, in one commit, with
  `docs/provenance/seed.json` recording source repo, commit and date.
- `.claude/hooks/guard.py`: a pure classifier plus a JSON adapter, registered as a blocking `PreToolUse`
  hook. Three outcomes: deny, ask, normal. It never executes the command it is judging.
- `scripts/safe_check.py`: plans the checks for a change and runs them only with `--run
  --confirm-isolated`. Fixed argument vectors, timeouts, no installs, no repairs.
- `.claude/skills/check/SKILL.md`: human-invoked wrapper for the runner.
- `.claude/agents/analysis-invariants.md`: `tools: Read, Grep, Glob`, advisory, no memory.
- CI gains BiasGuard, site-logic, guard, runner and lab jobs.

The report's seven corrections are requirements, not follow-ups:

| Correction | How it is met |
|---|---|
| Guard and runner disagree on commands | One module, `scripts/check_contract.py`, holds the command list; both import it; a test asserts equality |
| Credentials hashed before refusal | Credential-path refusal runs before any file is opened; tested with a planted fake `.env` and an `open` spy |
| Plain `git diff` treated as safe | Only the hardened form is normal; plain `git diff` asks |
| Fingerprint limits overstated | The report file states the limits verbatim; plan-only reports carry `observed: null` |
| Environment filtering described as isolation | `--confirm-isolated` is labelled human attestation in output |
| Policy-bearing files unprotected | The policy map lists them (below) |
| Deleted workflows linted | Deleted paths stay in scope but are never passed to a check |

Guard policy map for this repo:

- **Deny:** reading credential files (`.env*`, `*.pem`, `*.key`, `id_*`, `.netrc`, `.npmrc`, `~/.ssh`,
  `~/.aws`, `~/.config/gh`, `.claude/settings.local.json`); editing `public/index.html` (generated by
  `site.py`); PowerShell.
- **Ask:** edits to `public/data/**`, `data/reference/**`, `runs/**`, `biasguard/data/**`,
  `validation/mesa_bias_expanded/**`, `validation/biaslab/crosswalk.json`,
  `validation/reference/**`, `.github/workflows/**`, `.claude/**`, `scripts/**`,
  `pipeline/requirements.txt`, `validation/requirements.txt`, `pipeline/capraz_pipeline/config.py`;
  Bash that ingests, builds, applies reviews, pushes, installs, deletes recursively, uses the network,
  or is not recognised; any path outside the project root.
- **Normal:** the commands in the check contract, hardened Git inspection, and plain listing commands.

### Layer 2: the validation lab

A package `validation/biaslab/`, plus the vendored simulator at `validation/mesa_bias_expanded/` (sweep
output directories excluded; checksums verified by a test).

```
Mesa plugin ──▶ sim.py ──▶ private record (strength, draw, trace, expected relation)
                   │
                   ▼
              renderer.py ──▶ DetectorInput(text, context)   ← the only thing the detector sees
                                   │
                                   ▼
                        BiasGuard.analyze(...)  (frozen version, injected reviewer)
                                   │
                                   ▼
                          adapter.py ──▶ Assessment ──▶ ledger.py (every attempt, append-only)
                                                             │
                                                             ▼
                                                        metrics.py
```

- **Crosswalk** (`crosswalk.json`): one record per Mesa id with detector id or `null`, relationship,
  evidence tier, policy and review status. Only records whose status is `pilot` or `approved` resolve to
  a detector id. Everything else is reported as ineligible, in its own denominator.
- **Evidence tiers:** `headline_lede`, `full_article`, `decision_history`, `internal_state`. A concept
  above the available tier is ineligible, never negative.
- **Renderer:** a whitelist. Output is exactly `text` and `context`. A leak check rejects any rendered
  case containing a forbidden token (label, concept id, scenario name, strength, seed, split, case id).
  Turkish templates; several surface variants per family so wording cannot give the label away.
- **Expected relation** comes from the realised simulation step (`active`), never from strength alone.
- **Families:** every case built from the same facts shares a family id and a split. This fixes the
  reference adapter's admitted flaw of putting near-duplicates on both sides.
- **Adapter statuses:** `supported`, `contextual_effect`, `not_supported`, `uncertain`, `unassessed`,
  `ineligible`, `error`. They are never collapsed. `offline_candidates_only` and an absent card map to
  `unassessed`; `analysis_incomplete` maps to `error` for cards not fully assessed.
- **Invariance perturbations:** each case can be re-rendered with outlet order reversed, outlets
  relabelled, or one irrelevant sentence added. The expected status is unchanged; a change is counted
  as an inconsistency, separately from correctness.
- **Pilot concepts:** `selective_statistics` (no card: exercises the ineligible path on baseline and a
  lab-only proposed card on candidate) and `illusory_truth_effect` (existing card).
- **Metrics:** completion, decision coverage, strict supported-positive precision, end-to-end recall,
  conditional recall, unsupported-assertion rate on missing-context controls. A zero denominator yields
  `None`, displayed as "not estimable". Intervals use a clustered paired bootstrap over families.

### Layer 3: human reference and measured improvement

- **Blind first, then verify.** For the measured sample, reviewers label events without seeing AI output;
  two reviewers per item; disagreements are adjudicated and kept. Verification-and-correction of AI
  labels for publication is a separate pass and is recorded as such.
- **Reference states:** `supported`, `reviewed_negative`, `unresolved`, `ineligible`. Evidence adequacy
  is scored separately from label correctness.
- **Splits** group by event and by syndicated text family, with a later time window held out.
- **Comparison:** baseline and candidate BiasGuard versions run on identical inputs under frozen
  manifests; one detector change at a time, chosen from a measured failure cause.
- **Publication gate** per label, pre-registered in `validation/reference/gates.json`. A label is
  `public`, `review_only` or `hidden`. Undefined metrics never pass. Labels without enough reference
  support stay `review_only`.
- **Site rule:** an AI label is shown as **YZ**; it is shown as human-verified only when a verification
  record exists for that event, card and data-pack version.

## Decisions made on the owner's behalf

Each is a default the owner can overturn before execution.

1. The seed is a snapshot commit, not an import of the old history. The old repo keeps the history.
2. `runs/` (14 MB of recorded reviewer output) and `public/` (56 MB) are copied, because the build and the
   BiasGuard page depend on them.
3. Lab and control tests use `unittest`, as the repo does. The vendored Mesa suite keeps `pytest` and runs
   as its own CI job.
4. Mesa's 35 MB of sweep output is not vendored; `results/FINAL_STATUS.json` and `coverage.json` are.
5. The two pilot concepts are as listed. A different pair changes only the renderer task.

## Open items only the owner can settle

1. **Reviewers:** how many, and roughly how many events each can label blind before launch. This sets
   which labels can ever leave `review_only`.
2. **Gate thresholds.** The guide's figures (99% completion, 80% coverage, 90% lower bound on strict
   precision) are illustrative. Plan 3 uses them as placeholders marked "not yet agreed".
3. **Crosswalk approval.** The 112 same-id matches stay `needs_domain_review` until someone with domain
   knowledge approves each. The plans approve only the two pilot entries, as `pilot`.

## Left to the builder

Internal function bodies, test helper layout, Turkish wording of additional template variants beyond the
ones pinned in the plans, and report formatting.

## Owner decisions (14 November 2026)

1. **Every event starts AI-only.** No human has reviewed anything yet. The public feed shows each
   finding with a status: **AI onaylı** (approved by the AI reviewer) or **İnsan kontrolü bekliyor** (needs the
   verify-and-correct pass). After review it becomes **İnsan doğruladı** or **İnsan düzeltti**; a
   rejected finding is removed.
2. **The 26 media concepts are shown as "Medyanın oyunları"**, a group separate from behavioural biases
   ("Davranışsal yanlılıklar"). They attach to the headlines and ledes that show them.
3. **Recall can be partial.** No recall floor gates publication. Recall is not measured by the
   verify pass and the site never claims completeness.
4. **Gate thresholds:** the owner asked for a recommendation; see "Recommended thresholds".
5. **Pilot concepts stay:** selective statistics and illusory truth.
6. **Everything is committed to `aylinunel/caprazmansetfinal`.** `caprazmansetnov26` is read, never written.
7. **The detector improves as data arrives**, following the `mle-workflow` skill.

### What the published data shows today

The 8.1 BiasGuard run in `core.bin` reviewed 150 of 150 events with no failures and 2,236 verified
quotes. It produced **0 supported findings and 439 uncertain ones, every one `needs_context`**. The
detector, given headlines and ledes, never commits to a behavioural bias. Two consequences:

- Neither reviewer ever returned `supported`. The advocate said `uncertain` on all 439; the skeptic said
  `uncertain` on 220 and `not_supported` on 219. No finding has every condition satisfied.
- Under the owner's rule below, 257 of the 439 (58.5%) are **AI onaylı** and 182 are
  **İnsan kontrolü bekliyor**.
- The first improvement target is not completion (that was the synthetic run's problem) but the fact
  that behavioural-bias cards ask for evidence a headline cannot contain. Media-technique cards
  describe what the text itself does, so they are the likelier source of confident findings.

The site already has an owner-only editor review (`rev7` in `site/js/app.js`): findings can be rejected
or corrected with a note, stored in the artifact's `reviews` collection. Plan 3 extends this rather
than adding a second mechanism.

### Naming: AI, not YZ

The reviewer is called **AI** in all new wording: the abbreviation for artificial intelligence and the
initials of Abdi İpekçi. The AI is written about as a person ("AI onayladı", "AI'ın incelemesi"), not as
a tool. The personification itself (name, portrait, voice, the commemoration text) is a later piece of
work and is not planned here. The existing site still says YZ in many places; renaming those is part of
that later work, so until then new badges say AI next to older YZ marks.

### What "AI onaylı" means

It is a rule, not a probability, chosen by the owner on 14 November 2026. A finding is **AI onaylı** when
the card has not been demoted by human feedback and at least one of these holds:

- **not dismissed:** neither the advocate nor the skeptic returned `not_supported`; or
- **partly confirmed by the skeptic:** the skeptic marked at least one necessary condition `satisfied`,
  whatever its overall verdict.

Everything else that is shown is **İnsan kontrolü bekliyor**. Exact-quote checking still applies to
every finding before it is shown at all.

On the 8.1 run this gives 257 **AI onaylı** findings: 220 that neither reviewer dismissed, plus 37 that
the skeptic rejected overall while confirming one condition. Known weaknesses, accepted with the rule:

- No **AI onaylı** finding today was called `supported` by either reviewer; both said the pattern is
  possible and needs more context. The badge means "left standing", not "confirmed".
- 37 carry the badge although the skeptic's verdict was `not_supported`.
- About a third are context effects the catalogue marks as not necessarily an error.
- Two reviews by the same model can share the same mistake.

The badge's one-line explanation on the site: "AI bu örüntüyü olası buldu: sorgulayan inceleme reddetmedi ya da koşullardan en az birini doğruladı. Kesin değil; henüz insan kontrolünden geçmedi." The audit sample and the card thresholds below are
what turn the badge into evidence over time.

### Recommended thresholds

| Setting | Recommended | Why |
|---|---|---|
| Run completion to publish a build | ≥ 95% of events reviewed | Unreviewed events are shown as "incelenemedi", not as clean. The 8.1 run reached 100%; the synthetic run reached 44% |
| Reviews before a card is judged | 15 human-reviewed findings | The leanest count at which one rejection can still be told apart from two |
| Keep a card eligible for **AI onaylı** | one-sided 95% lower bound of precision ≥ 0.70 | With 15 reviews this means at most 1 rejection (14 of 15 gives 0.75; 13 of 15 gives 0.67). The price of the leaner rule: a card can stay eligible while its true precision is nearer 70% than 90%. A wrong public bias label on a named outlet is the costly mistake, so precision is favoured |
| Hide a card | precision below 0.50 after ≥ 10 reviews | More often wrong than right |
| Audit sample | 5% of **AI onaylı** findings, at random, go to reviewers anyway | Otherwise the confident tier is never checked and its precision is unknown |
| Recall floor | none | Owner decision 3 |

Before a card has 15 reviews, the rule above decides alone, and that card's findings are first in the
review queue. Precision measured from the verify pass is optimistic, because a reviewer who sees the
AI's answer tends to agree with it; the numbers are labelled "verify-pass precision" wherever shown.

### Medyanın oyunları

- A second catalogue file, `biasguard/data/media_cards.json`, with `entry_type: "media_practice"` and
  `review_policy: "media_pattern_review"`. The 116 behavioural cards are untouched.
- 17 of the 26 are assessable from headlines and ledes and get cards. The other 9 need full articles,
  images or page layout (`source_selection`, `one_sided_sourcing`,
  `commission_and_omission_of_information`, `contextual_omission`, `size_allocation`, `story_placement`,
  `picture_selection`, `picture_explanation`, `event_selection`) and are listed on the method page as
  "bu veriyle ölçülemiyor".
- A media finding describes what the text does. It never says why, and never names intent.
- Ten of these concepts are already scored by the deterministic headline scorer
  (`shared/analysis/rules.cjs`). The two are shown side by side under the same group, each labelled with
  its method; they are not merged into one score.
- Every media card goes through the lab as a candidate before it enters the production file.

### How the detector learns (mle-workflow)

No model is trained here. "Learning" means four things that change as reviewed data grows:

1. **Routing statistics.** Per-card verify-pass precision moves cards in and out of **AI onaylı**.
2. **Regression memory.** Every human correction becomes a permanent replay case; a detector change
   that breaks a previously corrected case is visible before release.
3. **Detector versions.** Card wording, prompts and retrieval settings change one at a time, each
   chosen from a measured error cluster and promoted only if it does not regress the replay set.
4. **New insight.** Reviewers can note a pattern no card covers; recurring notes, and clusters of
   rejected findings, become proposals for new or split cards, tested in the lab first.

Iteration compact for the first iteration:

```text
Goal: publish bias and media-technique findings whose status is honest and whose precision rises with review
Who cares: readers (trust), outlets named in findings (fair treatment), the owner (credibility)
Decision owner: Aylin Unel
Action changed by the model: which findings appear on an event page, and under which status badge
Success metric: verify-pass precision per card, with one-sided 95% lower bound
Guardrail metrics: run completion; share of findings awaiting review; reviewer workload per build;
  audit-sample precision of the AI onaylı tier; lab forbidden-rate on controls
Mistake budget: AI onaylı tier — at most 1 rejection in 15 reviewed findings per card
Unacceptable mistakes: a finding that states intent, mental state or affiliation; a failed review shown
  as "no bias"; an unreviewed finding shown as human-verified; a quote that is not in the source
Acceptable mistakes: missed findings (partial recall); findings parked as "İnsan kontrolü bekliyor"
Assumptions: reviewers are available for the verify pass; headlines and ledes only
Constraints: no provider calls from CI; reviewer agents run as in biasguard/AGENT_REVIEW.md
Labels and data snapshot: verify-pass labels keyed by event, card, data-pack version and text hash
Baseline: 8.1 BiasGuard, 116 cards, prompts as seeded
Candidate signals: reviewer disagreement, unsatisfied conditions, missing context, per-card history,
  outlet and topic slices
Threshold or config plan: the table above, stored in validation/reference/gates.json
Eval slices: card, card group (behavioural / media), outlet bloc (sol / orta / sağ), month, event size
Known risks: verify-pass anchoring; same-model reviewer correlation; small counts per card;
  feedback loop if only non-confident findings are reviewed (hence the audit sample)
Next experiment: find out why no behavioural finding reaches `supported` (which necessary conditions
  stay `unknown`), and test media-technique cards as candidates in the lab
Rollback or fallback: keep the previous biasguard.json and card hash; a build can be reassembled from them
```

## Plans

| Plan | File | Depends on |
|---|---|---|
| 1. Foundation | `docs/superpowers/plans/2026-11-14-foundation.md` | nothing |
| 2. Mesa validation lab | `docs/superpowers/plans/2026-11-14-mesa-validation-lab.md` | Plan 1 |
| 3. Review status and feedback | `docs/superpowers/plans/2026-11-14-review-status-and-feedback.md` | Plan 1 |
| 4. Medyanın oyunları | `docs/superpowers/plans/2026-11-14-medyanin-oyunlari.md` | Plans 2 and 3 |
| 5. Learning loop | `docs/superpowers/plans/2026-11-14-learning-loop.md` | Plan 3 |
| Not scheduled: blind reference study | `docs/superpowers/plans/parked/2026-11-14-blind-reference-study.md` | owner decision |
| On hold: Claude Code controls | `docs/superpowers/plans/parked/2026-11-14-claude-code-controls.md` | the owner's updated report |

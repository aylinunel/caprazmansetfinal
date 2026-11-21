# Graph Report - caprazmansetfinal  (2026-11-21)

## Corpus Check
- 177 files · ~258,684 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 4, .css 1)

## Summary
- 2692 nodes · 6511 edges · 124 communities (115 shown, 9 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 478 edges (avg confidence: 0.87)
- Token cost: 674,905 input · 0 output

## Graph Freshness
- Built from commit: `98a3c991`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- logic.js (site/js/v7)
- app.js (site/js)
- oruntu.js (site/js/v7)
- turkish-layer.js (site/js)
- test_news.py
- labels.py
- Store (pipeline/capraz_pipeline)
- aix.py
- t3() (site/js)
- summarize
- engine.py (biasguard)
- analyze.py (pipeline/capraz_pipeline)
- Çapraz Manşet README (root)
- with (.github/workflows)
- gzip
- catalog.py (biasguard)
- run.py (validation/biaslab)
- Capraz Manset 7.0 Structure  (docs/superpowers/plans)
- insights.py
- renderer.py (validation/biaslab)
- lean() (site/js)
- srcName() (site/js)
- test_lens.py
- mh_rr
- validation/ README (offline  (validation)
- ADR-0002: Reproducible day-p (pipeline)
- build() (pipeline/capraz_pipeline)
- anlati.js (site/js/v7)
- explain_rules.py (biasguard)
- BiasGuard (biasguard)
- run() (validation/tests)
- aiimza.js (site/js/v7)
- render() (validation/tests)
- Capraz Manset UX Rethink Imp (docs/superpowers/plans)
- pgMine() (site/js)
- RunTest
- AI denetim masası (behaviour (docs/superpowers/specs)
- Headline scorer (rules.cjs,  (docs)
- ADDED Requirements
- events.py (pipeline/capraz_pipeline)
- Broadsheet in motion: dynami (docs/superpowers/specs)
- crosswalk.py (validation/tests)
- normalize() (validation/tests)
- lens.py
- 28 framing and cognitive-bia (docs)
- numpy (pipeline/capraz_pipeline)
- cluster.py (pipeline/capraz_pipeline)
- snapshot.py
- test_routing.py
- reference_adapter.py (validation/reference_adapter)
- Medyanin oyunlari: cards for (docs/validation)
- Reviewer agents (Çapraz Manş (biasguard)
- Single-source lens ("Tek kaynak okuru") — design
- classify.py (pipeline/capraz_pipeline)
- Machine Learning for the Nar (docs/superpowers/plans)
- parti.js (site/js/v7)
- Mercek (aylinunel/mediabias; (docs)
- Claude Code Controls Impleme (docs/superpowers/plans/parked)
- Capraz Manset Final: integra (docs/superpowers/specs)
- renderFeed
- pgSources() (site/js)
- desk.js (site/js/v7)
- smoke.cjs (site/tests)
- route() (site/js)
- renderFeed() (site/js)
- confirmed_skips
- Review Status and Feedback I (docs/superpowers/plans)
- dots.js (site/js/v7)
- viz.js (site/js/v7)
- yontem.js (site/js/v7)
- argparse (biasguard)
- editorial.ts (shared)
- MeasureTest
- json
- Capraz Manset 7.0 Kindred-st (docs/superpowers/plans)
- Learning Loop Implementation (docs/superpowers/plans)
- Layer 2: validation lab (val (docs/superpowers/specs)
- graph.js (site/js/v7)
- olay.js
- Data contract for the learni (docs/validation)
- Front-end architecture (hash (root)
- test_aix.py
- errors.py
- Detector iterations (docs/validation)
- checklist.cjs (pipeline/capraz_pipeline)
- errors.ts (shared/_core)
- const.ts (shared)
- motion.js (site/js/v7)
- iframe-scroll.cjs (site/tests)
- yontem-wheel.cjs (site/tests)
- perf.cjs (site/tests)
- MediaCardsTest
- tasks.md
- score_bridge.cjs (pipeline/capraz_pipeline)
- realize
- loader.js (site/js)
- NOTICE.md: Attribution and p (root)
- card_stats
- kurum.js (site/js/v7)
- promotion.py
- Mobile and accessibility pas (docs/superpowers/plans)
- ymScrollTo() (site/js/v7)
- fog.js (site/js/v7)
- home.js (site/js/v7)
- ilan.js (site/js/v7)
- turkish-layer.js Turkish ref (docs)
- config.py
- cloud-env-setup.sh (root)
- 17 candidate media-technique cards
- reference.Label (append-only human label)
- SeedTest
- run
- GitHub Actions checks.yml
- whatsnew.py
- findingGroups
- proposal.md
- rules.cjs
- cli_more.py

## God Nodes (most connected - your core abstractions)
1. `BiasGuard` - 65 edges
2. `srcName()` - 45 edges
3. `build()` - 43 edges
4. `route()` - 37 edges
5. `t3()` - 34 edges
6. `Çapraz Manşet README` - 33 edges
7. `render()` - 31 edges
8. `Store` - 30 edges
9. `apply()` - 28 edges
10. `DetectorInput` - 27 edges

## Surprising Connections (you probably didn't know these)
- `assert_no_leak()` --semantically_similar_to--> `packets.blind_packet()`  [INFERRED] [semantically similar]
  validation/biaslab/renderer.py → docs/superpowers/plans/parked/2026-11-14-blind-reference-study.md
- `promotable()` --semantically_similar_to--> `gate.decide()`  [INFERRED] [semantically similar]
  validation/biaslab/promote.py → docs/superpowers/plans/parked/2026-11-14-blind-reference-study.md
- `Measures (proven, rule-based; the outlet's first headline per story)` --references--> `headline_lede_gap()`  [INFERRED]
  docs/superpowers/specs/2026-11-21-single-source-lens-design.md → pipeline/capraz_pipeline/analyze.py
- `Impact` --references--> `merge()`  [INFERRED]
  openspec/changes/add-single-source-lens/proposal.md → pipeline/capraz_pipeline/narratives.py
- `Task 3: Confirmed skips` --references--> `confirmed_skips()`  [INFERRED]
  docs/superpowers/plans/2026-11-21-single-source-lens.md → pipeline/capraz_pipeline/lens.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **BiasGuard selector/advocate/skeptic review and apply flow** — biasguard_agent_review_news_inputs, biasguard_agent_review_news_tasks, biasguard_agent_review_selector_agents, biasguard_agent_review_advocate_agents, biasguard_agent_review_skeptic_agents, biasguard_agent_review_news_apply, biasguard_agent_review_biasguard_json [EXTRACTED 1.00]
- **Çapraz Manşet pipeline stage flow (ingest → export)** — pipeline_readme_ingest, pipeline_readme_score, pipeline_readme_classify, pipeline_readme_cluster, pipeline_readme_events, pipeline_readme_topics, pipeline_readme_analyse, pipeline_readme_export [EXTRACTED 1.00]
- **Claude Code guard, check contract and plan-first runner control system** — docs_superpowers_plans_parked_2026_11_14_claude_code_controls_check_contract, docs_superpowers_plans_parked_2026_11_14_claude_code_controls_guard_classify, docs_superpowers_plans_parked_2026_11_14_claude_code_controls_pretooluse_hook, docs_superpowers_plans_parked_2026_11_14_claude_code_controls_safe_check_change_set, docs_superpowers_plans_parked_2026_11_14_claude_code_controls_safe_check_plan, docs_superpowers_plans_parked_2026_11_14_claude_code_controls_safe_check_run, docs_superpowers_plans_parked_2026_11_14_claude_code_controls_ci_checks_workflow [EXTRACTED 1.00]
- **Outlet distance score: proven measures + within-story regression + AI insights** — docs_superpowers_specs_2026_11_20_single_source_lens_decisions_distance_from_full_picture, docs_superpowers_specs_2026_11_20_single_source_lens_decisions_proven_measures, docs_superpowers_specs_2026_11_20_single_source_lens_decisions_event_fixed_effects_regression, docs_superpowers_specs_2026_11_20_single_source_lens_decisions_additional_insights_ai_imzali [EXTRACTED 1.00]
- **Pattern naming safeguards** — docs_superpowers_specs_2026_11_20_single_source_lens_decisions_pattern_strength_wording, docs_superpowers_specs_2026_11_20_single_source_lens_decisions_unmistakable_pattern_rule, docs_superpowers_specs_2026_11_20_single_source_lens_decisions_behaviour_not_motive [EXTRACTED 1.00]
- **Headline scorer steps (quote stripping, lexicon, weights, bands, evidence)** — docs_biases_and_detection_unquoted, docs_biases_and_detection_lexicon_rules, docs_biases_and_detection_anchoring_structural_rule, docs_biases_and_detection_weights_score, docs_biases_and_detection_score_bands, docs_biases_and_detection_evidence_strength [EXTRACTED 1.00]
- **Human answer key measurement chain (packets, record, alpha, evals, mlbench)** — docs_superpowers_plans_2026_11_17_ml_narrative_and_behavioural_blind_coding_packets, docs_superpowers_plans_2026_11_17_ml_narrative_and_behavioural_coding_record, docs_superpowers_plans_2026_11_17_ml_narrative_and_behavioural_krippendorff_alpha, docs_superpowers_plans_2026_11_17_ml_narrative_and_behavioural_narrative_agent_eval, docs_superpowers_plans_2026_11_17_ml_narrative_and_behavioural_behaviour_blind_eval, docs_superpowers_plans_2026_11_17_ml_narrative_and_behavioural_mlbench [EXTRACTED 1.00]
- **Learning loop iteration cycle (snapshot, errors, replay, promotion, insights)** — docs_superpowers_plans_2026_11_14_learning_loop_build_snapshots, docs_superpowers_plans_2026_11_14_learning_loop_error_analysis, docs_superpowers_plans_2026_11_14_learning_loop_replay_set, docs_superpowers_plans_2026_11_14_learning_loop_promotion_gate_module, docs_superpowers_plans_2026_11_14_learning_loop_drift_and_insights, docs_validation_iterations_the_loop [EXTRACTED 1.00]
- **Lab build→tasks→score pipeline** — validation_biaslab_renderer, validation_biaslab_renderer_assert_no_leak, validation_biaslab_adapter, validation_biaslab_ledger, validation_biaslab_metrics, validation_biaslab_metrics_paired_bootstrap, validation_biaslab_run [EXTRACTED 1.00]
- **Publication gating chain (gate → label_status → BGG → bgLabelState)** — validation_biaslab_gate_decide, validation_reference_gates, validation_reference_label_status, pipeline_capraz_pipeline_build_bgg_bgv, site_js_v7_logic_bglabelstate [EXTRACTED 1.00]
- **Review status and feedback flow (routing, audit, editor review, labels, card gate, badges)** — docs_superpowers_plans_2026_11_14_review_status_and_feedback_routing_rule_tier, docs_superpowers_plans_2026_11_14_review_status_and_feedback_audit_sample, docs_superpowers_plans_2026_11_14_review_status_and_feedback_editor_review_export, docs_superpowers_plans_2026_11_14_review_status_and_feedback_label_import, docs_superpowers_plans_2026_11_14_review_status_and_feedback_card_stats_and_gate, docs_superpowers_plans_2026_11_14_review_status_and_feedback_status_badges [EXTRACTED 1.00]
- **Expert review learning loop** — docs_superpowers_specs_2026_11_20_single_source_lens_decisions_ai_denetim_masasi, docs_superpowers_specs_2026_11_20_single_source_lens_decisions_expert_feedback_training_loop, docs_superpowers_specs_2026_11_20_single_source_lens_decisions_reviews_export_labels, docs_superpowers_specs_2026_11_20_single_source_lens_decisions_concept_measurability_criterion, docs_superpowers_specs_2026_11_20_single_source_lens_decisions_expert_answer_key [INFERRED 0.85]
- **Finding block evolution across 7.0 structure, UX rethink and broadsheet motion** — docs_superpowers_specs_2026_11_05_capraz_7_structure_design_finding_block, docs_superpowers_plans_2026_11_05_capraz_7_structure_findingblock, docs_superpowers_specs_2026_11_05_ux_rethink_design_finding_block_layered, docs_superpowers_plans_2026_11_05_ux_rethink_findingblock_v8, docs_superpowers_specs_2026_11_06_broadsheet_motion_design_body_components [INFERRED 0.85]
- **Homepage hero evolution: dot-matrix LED hero -> fog split card -> both headlines with tint** — docs_superpowers_plans_2026_11_05_kindred_style_dot_matrix_hero, docs_superpowers_plans_2026_11_05_ux_rethink_foghero, docs_superpowers_specs_2026_11_05_ux_rethink_design_fog_split_card_hero, docs_superpowers_plans_2026_11_06_broadsheet_motion_hero_click_to_tint, docs_superpowers_specs_2026_11_06_broadsheet_motion_design_hero_both_headlines_tint [INFERRED 0.85]
- **Media card lifecycle: candidate → lab → promotion → site** — docs_superpowers_plans_2026_11_14_medyanin_oyunlari_seventeen_media_cards, validation_biaslab_renderer, validation_biaslab_promote_promotable, validation_biaslab_promote_promote, biasguard_data_media_cards, biasguard_news_apply, site_js_v7_logic_findinggroups [INFERRED 0.85]

## Communities (124 total, 9 thin omitted)

### Community 0 - "logic.js (site/js/v7)"
Cohesion: 0.05
Nodes (68): Stretched card link (.xstretch), 9 not-measurable concepts ('Bu veriyle ölçülemiyor'), Task 5: Wording helpers, BREG bias registry / bg7k alias, biasChip(), aliasEscape(), anEmpty(), anPage() (+60 more)

### Community 1 - "app.js (site/js)"
Cohesion: 0.05
Nodes (60): ADR-0001, ADR-0002, actorMatrix(), actorsOf(), artRow(), bg7AdminFindings(), bg7AiTag(), bg7CardLine() (+52 more)

### Community 2 - "oruntu.js (site/js/v7)"
Cohesion: 0.10
Nodes (63): findingBlock(), glClose(), glOpen(), yzBadge(), yzBlock(), orAnBars(), orAnKeys(), orAnlati() (+55 more)

### Community 3 - "turkish-layer.js (site/js)"
Cohesion: 0.07
Nodes (52): admittedSet(), appealPayload(), appealSubmit(), appealValidate(), applyOwnerSources(), basisEligible(), blocOf(), blocOfLean() (+44 more)

### Community 4 - "test_news.py"
Cohesion: 0.10
Nodes (10): apply(), FileReviewer, _outlet_counts(), _card(), GateTests, MediaPassTests, ReplayTests, _review() (+2 more)

### Community 5 - "labels.py"
Cohesion: 0.19
Nodes (6): append(), import_export(), read(), export(), LabelsTest, rev()

### Community 6 - "Store (pipeline/capraz_pipeline)"
Cohesion: 0.08
Nodes (16): collector_files(), ingest(), _lines(), main(), build_reference(), assemble(), article_id(), canonical_url() (+8 more)

### Community 7 - "aix.py"
Cohesion: 0.10
Nodes (21): Where it lives, auc(), _bloc(), _bloc_rate(), boot_mean_ci(), cite_index(), cited(), _cited() (+13 more)

### Community 8 - "t3() (site/js)"
Cohesion: 0.07
Nodes (59): artUrl(), renderSources(), t3(), v3After(), v3ansButtons(), v3answers(), v3bindStore(), v3chip() (+51 more)

### Community 9 - "summarize"
Cohesion: 0.14
Nodes (13): CHANGE_PROTOCOL.md, compare() / NotComparable, paired_bootstrap(), diff(), _r(), ratio(), Row, summarize() (+5 more)

### Community 10 - "engine.py (biasguard)"
Cohesion: 0.13
Nodes (13): prompts(), _mapping(), OpenAIReviewer, _parse_provider_json(), ProviderCallError, ProviderConfigurationError, _redacted_exception(), _selector_schema() (+5 more)

### Community 11 - "analyze.py (pipeline/capraz_pipeline)"
Cohesion: 0.09
Nodes (18): advanced_outlets(), agenda(), feed_table(), framing_pca(), headline_lede_gap(), jsd(), lead_lag(), mantel() (+10 more)

### Community 12 - "Çapraz Manşet README (root)"
Cohesion: 0.07
Nodes (41): Scorer parity test vs 4.0 (22,213/22,213), Mercek human review and export (append-only, different approver, 80/10/10 split), Çapraz Manşet README, Accessibility and performance (44px targets, 4.5:1 contrast, no reduced-motion by owner decision), Agenda similarity (φ correlation, Mantel test 9,999 permutations), AI finding review status (AI onaylı / İnsan kontrolü bekliyor / İnsan doğruladı / düzeltti), capraz_pipeline.aix AI analyses (key AIX; AUC 0.48 vs loaded-language, κ 0.08 vs Anlatı), Analysis pipeline (pipeline/) (+33 more)

### Community 13 - "with (.github/workflows)"
Cohesion: 0.07
Nodes (42): runs-on, steps, timeout-minutes, jobs, biasguard, lab, mesa, pipeline (+34 more)

### Community 14 - "gzip"
Cohesion: 0.16
Nodes (11): convert(), _dump(), main(), split(), compare(), _done(), _findings(), main() (+3 more)

### Community 15 - "catalog.py (biasguard)"
Cohesion: 0.11
Nodes (15): _card_document(), card_hash(), CatalogError, coverage(), ENTRY_TYPES media_practice / REVIEW_POLICIES media_pattern_review, load_cards(), load_media_cards(), load_source_index() (+7 more)

### Community 16 - "run.py (validation/biaslab)"
Cohesion: 0.13
Nodes (15): cases.private.jsonl (private case records), Lab statuses (supported, contextual_effect, not_supported, uncertain, unassessed, ineligible, error), Assessment, Span, verify_spans(), Attempt, Ledger, main() (+7 more)

### Community 17 - "Capraz Manset 7.0 Structure  (docs/superpowers/plans)"
Cohesion: 0.10
Nodes (32): blameByBloc, Capraz Manset 7.0 Structure Redesign Implementation Plan, biasguard explain stage (explain-tasks / explain-apply / validate_explain), findingBlock (claim / viz / means / Nasil olctuk), ilanSearch / trFold Turkish-folded search, kurumLines7 outlet profile links to patterns, logic.js pure logic module (CommonJS-exported), narrGroups (+24 more)

### Community 18 - "insights.py"
Cohesion: 0.13
Nodes (10): co_occurrence(), drift(), new_pattern_notes(), proposals(), _rate_by_card(), report(), tier_shift(), InsightsTest (+2 more)

### Community 19 - "renderer.py (validation/biaslab)"
Cohesion: 0.10
Nodes (18): Case kinds (positive, inactive/boundary/quoted controls, missing_context), Perturbations (reverse_outlets, relabel_outlets, irrelevant_detail), selective_statistics (pilot concept), cases.Case, case_id(), DetectorInput, cases.expected(), expected() (+10 more)

### Community 20 - "lean() (site/js)"
Cohesion: 0.15
Nodes (36): advHeat(), advScatter(), atlasColor(), atlasEntities(), atlasNeighbours(), atlasParallel(), atlasRadius(), atlasScatter() (+28 more)

### Community 21 - "srcName() (site/js)"
Cohesion: 0.11
Nodes (37): artOf(), artRows(), blameStats(), bloc(), cmpBrief(), compareHeads(), compareMark(), covOf() (+29 more)

### Community 22 - "test_lens.py"
Cohesion: 0.12
Nodes (13): Task 3: Confirmed skips, big_stories(), compute(), days_active(), distance(), feed_complete(), group(), is_notice_article() (+5 more)

### Community 23 - "mh_rr"
Cohesion: 0.16
Nodes (9): Review Focus, Task 1: Shared rate statistics, Task 4: Measures, verdicts and the lens file, Task 7: Rebuild, verify, publish, _rate(), bh_q(), cmh_p(), mh_rr() (+1 more)

### Community 24 - "validation/ README (offline  (validation)"
Cohesion: 0.09
Nodes (32): CheckList behavioural evaluation (eval/checklist_tr.jsonl: MFT, INV, DIR), Mercek 116 cognitive concepts (The Decision Lab directory), numpy==2.5.3, scikit-learn==1.9.1, scipy==1.18.1, validation.feedback import/status (reviews to labels, per-card statistics), validation/reference/gates.json (demote/hide concepts), Learning loop (docs/validation/ITERATIONS.md: replay set, promotion gate) (+24 more)

### Community 25 - "ADR-0002: Reproducible day-p (pipeline)"
Cohesion: 0.09
Nodes (23): ADR-0002: Reproducible day-partitioned analysis pipeline (Çapraz Manşet 5.0), backfill-data branch of turkish-news-scraper (139,702 articles, 28 outlets), tr_lower / tr_words Turkish-aware lowercasing, Analysis pipeline README (Çapraz Manşet 5.0), capraz_pipeline.reference.build_reference (data/reference/), python -m capraz_pipeline run (ingest + build + site), classify stage (section/political; TF-IDF + logistic regression, 5-fold CV), cluster stage (cluster.py; cosine ≥0.33, 48h, 40% linkage, ≤120, ≥5 outlets) (+15 more)

### Community 26 - "build() (pipeline/capraz_pipeline)"
Cohesion: 0.19
Nodes (11): build(), _gz(), ingest_totals(), _json(), load_articles(), pack_month(), review_keys(), params_dict() (+3 more)

### Community 27 - "anlati.js (site/js/v7)"
Cohesion: 0.13
Nodes (30): anPageNasil(), narrMap(), pgAnlati(), pgAnlatiOlay(), v7BlocTxt(), v7Body(), v7Cell(), v7Colors() (+22 more)

### Community 28 - "explain_rules.py (biasguard)"
Cohesion: 0.08
Nodes (24): compose(), concept_means(), _first_sentence(), _fit(), _join(), main(), _outlets(), _quote_line() (+16 more)

### Community 29 - "BiasGuard (biasguard)"
Cohesion: 0.10
Nodes (10): _all_offsets(), BiasGuard, _copy_call_metadata(), InputRejectedError, _safe_message(), _sha(), selected_cards(), write_tasks() (+2 more)

### Community 30 - "run() (validation/tests)"
Cohesion: 0.29
Nodes (4): build(), score(), label(), ReplayTest

### Community 31 - "aiimza.js (site/js/v7)"
Cohesion: 0.09
Nodes (37): Task 6: The lens on the outlet page and the Kurumlar ranking, aiBox(), aiCard(), aiConceptName(), aiConceptText(), aiItems(), aiLegend(), aiMount() (+29 more)

### Community 32 - "render() (validation/tests)"
Cohesion: 0.11
Nodes (6): assert_no_leak(), kinds(), Leak, render(), variants(), RendererTest

### Community 33 - "Capraz Manset UX Rethink Imp (docs/superpowers/plans)"
Cohesion: 0.11
Nodes (27): Capraz Manset UX Rethink Implementation Plan, Event page story-first order (pgOlay7, v7-kisaca), findingBlock v8 (read / Neden onemli / Nasil olctuk / table), fogHero / fogMount WebGL2 fog split-card hero, GLOSSARY and glossTerms popovers, NAV_SUB plain-language section subtitles, outletKisaca, recentSplits (+19 more)

### Community 34 - "pgMine() (site/js)"
Cohesion: 0.11
Nodes (33): bbar(), blindspotPage(), cards(), dietBar(), fold5(), followBtn(), follows(), forYou() (+25 more)

### Community 35 - "RunTest"
Cohesion: 0.09
Nodes (4): assessment(), StubReviewer, jsonl(), RunTest

### Community 36 - "AI denetim masası (behaviour (docs/superpowers/specs)"
Cohesion: 0.10
Nodes (22): Plan: ML narrative and behavioural (2026-11-17), Single-source lens and expert-trained AI: decisions (2026-11-20), Additional insights (AI imzalı), AI denetim masası (behavioural scientist AI checker), Core key BGC, Bilişsel inceleme (YZ) page (old report), Distance from the full picture score, Regression with event fixed effects (+14 more)

### Community 37 - "Headline scorer (rules.cjs,  (docs)"
Cohesion: 0.14
Nodes (26): Biases and bias detection (Çapraz Manşet 6.0 and Mercek), Active outlet (≥ half of days + placement), Agenda similarity (φ, average linkage, Mantel r=0.03), Blind spots (Ground News rule adapted; binomial p<0.10; 42 in 6.0), Çapraz Manşet 6.0 (deterministic detection; 194,383 articles), Event clustering (pair F1 0.857; 140 locked events), Event selection (Olay seçimi), Evidence strength (evidenceOf: güçlü / orta / zayıf) (+18 more)

### Community 38 - "ADDED Requirements"
Cohesion: 0.10
Nodes (20): ADDED Requirements, Purpose, Requirement: AI findings stay outside the score, Requirement: Comparison group and lens holders, Requirement: Distance from the full picture, Requirement: Same-story comparison, Requirement: Skips only for complete feeds, Requirement: Stories that count (+12 more)

### Community 39 - "events.py (pipeline/capraz_pipeline)"
Cohesion: 0.15
Nodes (10): active_outlets(), binom_cdf(), blind_spot(), bloc(), build_events(), event_record(), keywords(), near_duplicates() (+2 more)

### Community 40 - "Broadsheet in motion: dynami (docs/superpowers/specs)"
Cohesion: 0.16
Nodes (20): CSS intro zoom + incoming page turn, Broadsheet in Motion Implementation Plan, GSAP 3.12.5 + ScrollTrigger + Lenis 1.1.13 (vendor first, CDN fallback), motion.js (motionLoad, motionMount, motionUnmount, MOTION), MOTION_K component timeline registry, Newsreader display font and --serif token, Performance trace (no task > 50 ms at 4x throttle) and screenshots, pNums Turkish count-phrase extractor (+12 more)

### Community 41 - "crosswalk.py (validation/tests)"
Cohesion: 0.08
Nodes (15): Lab-gated promotion, Crosswalk review status (needs_domain_review/pilot/approved/rejected), Evidence tiers (headline_lede → internal_state), illusory_truth_effect (pilot concept), coverage(), Entry, load(), parse() (+7 more)

### Community 42 - "normalize() (validation/tests)"
Cohesion: 0.28
Nodes (3): normalize(), AdapterTest, run()

### Community 43 - "lens.py"
Cohesion: 0.16
Nodes (12): Task 2: Who is compared, which stories count, _load(), load_articles(), main(), _eligible(), is_all_caps(), _load_checked(), main() (+4 more)

### Community 44 - "28 framing and cognitive-bia (docs)"
Cohesion: 0.13
Nodes (23): Ad Hominem (scored key), Anchoring Bias (scored key), Anchoring structural rule (number + unit before first colon/dash), Authority Bias (scored key), Bandwagon Effect (scored key), Base Rate Fallacy, Cherry Picking, Consequence Framing (+15 more)

### Community 45 - "numpy (pipeline/capraz_pipeline)"
Cohesion: 0.13
Nodes (7): wording_similarity(), decide(), event_topic_model(), gsdmm(), headline_topics(), npmi(), TopicsTest

### Community 46 - "cluster.py (pipeline/capraz_pipeline)"
Cohesion: 0.14
Nodes (6): cluster(), links(), merge(), pair_scores(), art(), ClusterTest

### Community 47 - "snapshot.py"
Cohesion: 0.20
Nodes (11): main(), _bloc_mix(), detector_version(), load_core(), read(), rows(), _size(), snapshot_id() (+3 more)

### Community 48 - "test_routing.py"
Cohesion: 0.08
Nodes (11): stamped(), in_audit_sample(), review_queue(), tier(), a(), ApplyOnRecordedRunTest, AuditTest, ev() (+3 more)

### Community 49 - "reference_adapter.py (validation/reference_adapter)"
Cohesion: 0.19
Nodes (13): Assessment, build_records(), Detector, DetectorInput, Evidence, load(), main(), MockContractDetector (+5 more)

### Community 50 - "Medyanin oyunlari: cards for (docs/validation)"
Cohesion: 0.20
Nodes (21): Ad hominem (Kisiye saldiri), Causal overclaim (Kanitsiz nedensellik), Cherry picking (Secmeci kanit kullanimi), Consequence framing (Sonuc cercevelemesi), effect_context_only policy, Emphasis framing (Vurgu cercevelemesi), Episodic framing (Olay odakli cerceveleme), False dilemma (Yanlis ikilem) (+13 more)

### Community 51 - "Reviewer agents (Çapraz Manş (biasguard)"
Cohesion: 0.22
Nodes (16): Reviewer agents (Çapraz Manşet 7.0) – AGENT_REVIEW.md, Advocate agents, biasguard.json → core.bin key BG, Circuit breaker (BREAKER_TRIPPED after five failed batches; not_attempted), FileReviewer (select/review interface), 'incelenemedi' display for empty media catalogue, biasguard/data/media_cards.json (empty until approved and lab-passed), Media-technique pass (Medyanın oyunları, --catalog media) (+8 more)

### Community 52 - "Single-source lens ("Tek kaynak okuru") — design"
Cohesion: 0.13
Nodes (14): AI layer (AI imzalı, outside the score), Anti-goals (a failure even if it works), Approaches (owner chose A), Constraints, Goals, Intent, Left to the builder, Measures (proven, rule-based; the outlet's first headline per story) (+6 more)

### Community 53 - "classify.py (pipeline/capraz_pipeline)"
Cohesion: 0.12
Nodes (10): apply(), cross_validate(), doc(), load_labels(), path_words(), TextModel, train(), DayCache (+2 more)

### Community 54 - "Machine Learning for the Nar (docs/superpowers/plans)"
Cohesion: 0.24
Nodes (15): validation/answerkey package (human answer key), Blind precision and estimated recall for the behavioural review, Blind coding packets and import, Answer-key coding record and gold (codings.jsonl), Deferred stages 6-7 (Turkish language model, in-house detector), Human examples in BiasGuard review tasks (learning without retraining), Krippendorff's alpha agreement statistic, Machine Learning for the Narrative Map and the Behavioural Review (plan) (+7 more)

### Community 55 - "parti.js (site/js/v7)"
Cohesion: 0.30
Nodes (16): pgParti(), ptAxes(), ptClose(), ptData(), ptHeat(), ptHow(), ptLate(), ptLeanSort() (+8 more)

### Community 56 - "Mercek (aylinunel/mediabias; (docs)"
Cohesion: 0.14
Nodes (16): Causal Overclaim, Commission and omission of information, Conservative gate (omission/sourcing/statistics → candidate unless full text and ≥2 outlets), contextual_omission (media technique), Loaded Language (Yüklü dil), Mercek (aylinunel/mediabias; LLM-based evidence-backed framing findings), Mercek causal_overclaim (media technique), Mercek input prep (Jaccard 48h grouping, frozen snapshots, publisher masking) (+8 more)

### Community 57 - "Claude Code Controls Impleme (docs/superpowers/plans/parked)"
Cohesion: 0.24
Nodes (14): analysis-invariants read-only reviewer agent (11 invariants), check_contract (Check, CHECKS, routine_argvs, select), check skill (.claude/skills/check/SKILL.md), CI checks.yml jobs per check id, Credential patterns (.env, *.pem, id_rsa, ~/.ssh ...), Claude Code Controls Implementation Plan (ON HOLD), guard.py classify (Decision deny / ask / normal), PreToolUse hook adapter and .claude/settings.json registration (+6 more)

### Community 58 - "Capraz Manset Final: integra (docs/superpowers/specs)"
Cohesion: 0.22
Nodes (11): gates.json thresholds (agreed: false), Claude Code controls (guard, safe_check, reviewer) - on hold, Layer 3: human reference and measured improvement, Capraz Manset Final: integration design, Layer 1: foundation (seeded copy of 8.1), Medyanin oyunlari media catalogue (media_cards.json), Owner decisions (14 November 2026), Publication gate per label (public / review_only / hidden) (+3 more)

### Community 59 - "renderFeed"
Cohesion: 0.20
Nodes (15): bg7(), bg7ev(), bg7k(), bg7Live(), bg7Rates(), bg7Stats(), evx(), feedChips() (+7 more)

### Community 60 - "pgSources() (site/js)"
Cohesion: 0.31
Nodes (9): fig(), kuFindKeys(), kuFindMean(), kuMean(), pgMap(), pgSources(), polOf(), registerCheck() (+1 more)

### Community 61 - "desk.js (site/js/v7)"
Cohesion: 0.29
Nodes (15): deskCardOptions(), deskHeadlines(), deskItems(), deskLearning(), deskName(), deskOpen(), deskOutlets(), deskRerender() (+7 more)

### Community 62 - "smoke.cjs (site/tests)"
Cohesion: 0.13
Nodes (12): Anlatı topic, bias explainers, Nasıl çalışır scroll fix Plan, Anlatı haritası top-level topic, NAV / SUB navigation tables, argv, { chromium }, clicks, evals, fs (+4 more)

### Community 63 - "route() (site/js)"
Cohesion: 0.15
Nodes (14): adminFoot(), adminShell(), footer2(), layoutPills(), menuLock(), navGroup(), navHTML(), rev7Init() (+6 more)

### Community 64 - "renderFeed() (site/js)"
Cohesion: 0.14
Nodes (20): covBar(), dArrow(), dBox(), diaBlind(), diaPipeline(), diaScheme(), evCoverage(), evTable() (+12 more)

### Community 65 - "confirmed_skips"
Cohesion: 0.15
Nodes (9): Global Constraints, Single-Source Lens Implementation Plan, Context, Decisions, Risks / Trade-offs, minutes(), vectors(), confirmed_skips() (+1 more)

### Community 66 - "Review Status and Feedback I (docs/superpowers/plans)"
Cohesion: 0.23
Nodes (12): New-pattern reviewer notes (Kartlarda olmayan bir oruntu), Deterministic 5% audit sample (in_audit_sample), Card statistics and gate (wilson_lower, card_stats, card_status), Editor review approve action and export (reviewsExport, reviewState), Label import (validation/feedback/labels.py, Label, labels.jsonl), Review queue (least-reviewed cards first), Review Status and Feedback Implementation Plan, Routing rule tier() in biasguard/routing.py (ai_confident / needs_human) (+4 more)

### Community 67 - "dots.js (site/js/v7)"
Cohesion: 0.26
Nodes (11): dmCardFx(), dmColor(), dmFeedWatch(), dmHash(), dmHeads(), dmMake(), S, dmMount() (+3 more)

### Community 68 - "viz.js (site/js/v7)"
Cohesion: 0.20
Nodes (6): vzDist(), vzLine(), vzQ(), vzRows(), vzTicks(), vzTipAttr()

### Community 69 - "yontem.js (site/js/v7)"
Cohesion: 0.27
Nodes (12): conceptLibrary(), glossaryHTML(), kaynakHtml(), pgYontem7(), trBlock(), trN(), trQ(), turkiyeBlocks() (+4 more)

### Community 70 - "argparse (biasguard)"
Cohesion: 0.29
Nodes (5): _build_parser(), _emit(), _load_capabilities(), main(), _read_utf8()

### Community 71 - "editorial.ts (shared)"
Cohesion: 0.18
Nodes (11): collectorArticleSchema, CollectorBatch, collectorBatchSchema, httpsUrl, kindValues, publicationErrors(), PublicationRecord, safeExternalUrl() (+3 more)

### Community 72 - "MeasureTest"
Cohesion: 0.23
Nodes (3): strata(), verdict(), MeasureTest

### Community 73 - "json"
Cohesion: 0.08
Nodes (14): biasguard/data/cards.json (116 behavioural cards), biasguard/data/media_cards.json, dataset_from_html(), _card_ids(), catalog(), manifest(), _proposed(), target() (+6 more)

### Community 74 - "Capraz Manset 7.0 Kindred-st (docs/superpowers/plans)"
Cohesion: 0.24
Nodes (12): dm-band drifting dot-matrix page-header band, Capraz Manset 7.0 Kindred-style restyle plan, Dot-matrix LED charts (vzDist / vzLine canvas), Dot-matrix LED hero (dmHero) rendering the split card, dots.js engine (dmMake, dmMount, dmHeads, DM_DATA), Kindred style (Inter, #f7f7f5 off-white, #111 ink, black pills), Kindred site-wide colour and font tokens, Rainbow underglow CTA pill (+4 more)

### Community 75 - "Learning Loop Implementation (docs/superpowers/plans)"
Cohesion: 0.21
Nodes (11): Drift, co-occurrence and new-pattern proposals (insights.py), Learning Loop Implementation Plan, Permanent replay set (ReplayCase, replay.jsonl), Grouped cross-validation by event (GroupKFold), How the detector learns (mle-workflow: routing stats, regression memory, versions, new insight), Iteration compact for the first iteration, Plans table (foundation, Mesa lab, review status, Medyanin oyunlari, learning loop), Time-ordered event split (replay set) (+3 more)

### Community 76 - "Layer 2: validation lab (val (docs/superpowers/specs)"
Cohesion: 0.20
Nodes (11): Adapter statuses (never collapsed), BiasGuard (116 concept cards, advocate and skeptic reviewers), Capraz Manset pipeline (ingest to core.bin), Crosswalk (Mesa id to detector card id), Evidence tiers (headline_lede, full_article, decision_history, internal_state), Invariance perturbations (outlet order, relabelling, irrelevant detail), Mesa cognitive-bias simulation framework (138 mechanisms), Pilot concepts: selective_statistics and illusory_truth_effect (+3 more)

### Community 77 - "graph.js (site/js/v7)"
Cohesion: 0.21
Nodes (7): tipOff(), g6AgendaData(), g6Bloc(), g6Build(), g6Load(), g6Mount(), g6Tok()

### Community 78 - "olay.js"
Cohesion: 0.27
Nodes (11): anPageOlay(), olayCommon(), olayDeep(), olayGroups(), olayHead(), olayHeadlines(), olayKisaca(), olayOutlets() (+3 more)

### Community 79 - "Data contract for the learni (docs/validation)"
Cohesion: 0.31
Nodes (11): Data contract and idempotent build snapshots (validation/learning/snapshot.py), Error analysis: confusion, clusters, stuck conditions (errors.py), next_move rule (better card wording / evidence / threshold / fallback), Data contract for the learning loop, Detector version (12 hex of SHA-256 over card hash, prompts version, candidate limit), Evaluation slices (card, catalogue, bloc, month, event size, tier), Snapshot id <pack>_<catalog>_<detector version>, Snapshot row entity (event x card x detector version x pack) (+3 more)

### Community 80 - "Front-end architecture (hash (root)"
Cohesion: 0.20
Nodes (10): app.js router and data access, Design system (newsprint tokens, Newsreader, IBM Plex, Bricolage Grotesque, fixed placement colours), Finding block (claim → chart → Nasıl ölçtük? → table), fog.js hero state machine (WebGL2 fog, click-to-tint), Front-end architecture (hash-routed SPA, site/js/v7 in V7_ORDER), Motion system (motion.js, data-m kinds, MOTION_K registry), Page lifecycle (motionUnmount, redirectRoute, render, motionMount), Vendored libraries (GSAP, ScrollTrigger, Lenis, AntV G6, D3 7.9.0) (+2 more)

### Community 81 - "test_aix.py"
Cohesion: 0.20
Nodes (4): ComputeTest, core_fixture(), HelperTest, StatsTest

### Community 82 - "errors.py"
Cohesion: 0.17
Nodes (12): Label, latest(), clusters(), confusion(), joined(), next_move(), report(), stuck_conditions() (+4 more)

### Community 83 - "Detector iterations (docs/validation)"
Cohesion: 0.36
Nodes (10): Fail-closed promotion gate (promotion.py, PROMOTION_GATES), Slice regressions (per card and bloc_mix, min_n 10), Detector iterations, Iteration 1 compact, Iteration Compact (template), Next experiment: media-technique cards as lab candidates, Observation Ledger (iteration 0 baseline), Promotion gate (fail-closed metric limits) (+2 more)

### Community 84 - "checklist.cjs (pipeline/capraz_pipeline)"
Cohesion: 0.20
Nodes (7): cases, fs, got, MAP, out, path, R

### Community 85 - "errors.ts (shared/_core)"
Cohesion: 0.29
Nodes (5): BadRequestError(), ForbiddenError(), HttpError, NotFoundError(), UnauthorizedError()

### Community 86 - "const.ts (shared)"
Cohesion: 0.20
Nodes (7): AXIOS_TIMEOUT_MS, COOKIE_NAME, NOT_ADMIN_ERR_MSG, OAUTH_STATE_COOKIE, OAuthState, ONE_YEAR_MS, UNAUTHED_ERR_MSG

### Community 87 - "motion.js (site/js/v7)"
Cohesion: 0.31
Nodes (5): motionAdd(), motionEach(), motionLoad(), motionMount(), motionRun()

### Community 88 - "iframe-scroll.cjs (site/tests)"
Cohesion: 0.22
Nodes (6): { chromium }, fs, http, path, root, TYPES

### Community 89 - "yontem-wheel.cjs (site/tests)"
Cohesion: 0.22
Nodes (6): { chromium }, fs, http, path, root, TYPES

### Community 90 - "perf.cjs (site/tests)"
Cohesion: 0.22
Nodes (6): { chromium }, fs, http, path, [siteDir, route = "#/olay?e=s4374"], TYPES

### Community 92 - "tasks.md"
Cohesion: 0.50
Nodes (3): 1. Statistics and data, 2. Site, 3. Release

### Community 93 - "score_bridge.cjs (pipeline/capraz_pipeline)"
Cohesion: 0.25
Nodes (4): path, R, readline, rl

### Community 94 - "realize"
Cohesion: 0.18
Nodes (6): _sources(), realize(), Realized, scenario(), MediaRendererTest, SimTest

### Community 95 - "loader.js (site/js)"
Cohesion: 0.32
Nodes (4): gunzip(), ADR-0002, load(), unbase64()

### Community 96 - "NOTICE.md: Attribution and p (root)"
Cohesion: 0.33
Nodes (5): NOTICE.md: Attribution and permission status, Çapraz Manşet 3.0 uploaded HTML (design, branding, dataset source), data/import-manifest.json (asset/data hashes), Ponytail skill (.claude/skills/ponytail/SKILL.md, MIT, DietrichGebert), scraper/upstream/UPSTREAM_PROVENANCE.json

### Community 97 - "card_stats"
Cohesion: 0.21
Nodes (7): main(), card_stats(), card_status(), wilson_lower(), labels(), one(), StatsTest

### Community 98 - "kurum.js (site/js/v7)"
Cohesion: 0.52
Nodes (6): kuDil(), kuFirst(), kuFp(), kuLink(), kuName(), kurumFindings7()

### Community 100 - "promotion.py"
Cohesion: 0.17
Nodes (8): assert_promotion_ready(), decide(), _kept_rate(), metrics_from(), record(), slice_regressions(), PromotionTest, replay()

### Community 101 - "Mobile and accessibility pas (docs/superpowers/plans)"
Cohesion: 0.50
Nodes (4): smoke.cjs Playwright route smoke test, Mobile and accessibility pass (44px targets, 4.5:1 contrast, tap tooltips), Remove reduced motion (dmCalm, g6Calm, vzCalm, reduce), Mobile, accessibility, motion budget and performance

### Community 102 - "ymScrollTo() (site/js/v7)"
Cohesion: 0.60
Nodes (5): MOTION.lenis smooth scroll path, wireYontem(), ymGo(), ymOpen(), ymScrollTo()

### Community 103 - "fog.js (site/js/v7)"
Cohesion: 0.60
Nodes (3): fogDark(), fogMount(), fogSmooth()

### Community 104 - "home.js (site/js/v7)"
Cohesion: 0.70
Nodes (4): feedCard(), feedHTML(), feedMore(), pgHome7()

### Community 105 - "ilan.js (site/js/v7)"
Cohesion: 0.80
Nodes (4): ilanItems(), ilanResults(), pgIlan(), wireIlan()

### Community 106 - "turkish-layer.js Turkish ref (docs)"
Cohesion: 0.50
Nodes (4): T3 notice split (resmî ilan detection; ≥50% notices listed separately), T6 near-duplicates (char n-gram cosine ≥0.90; duplicate_cosine), T7 suffix-aware word marking (≤2 suffix layers, stem ≥4 letters), turkish-layer.js Turkish refinements (T1–T7)

### Community 107 - "config.py"
Cohesion: 0.13
Nodes (11): Params, candidates(), diverge(), first(), _card_conditions(), finalize(), _focus(), _load() (+3 more)

### Community 113 - "17 candidate media-technique cards"
Cohesion: 0.15
Nodes (14): data/reference/editorial.json, Foundation Implementation Plan, Medyanın Oyunları Implementation Plan, effect_context_only policy (thematic_framing, spin), 17 candidate media-technique cards, Mesa Validation Lab Implementation Plan, Validation lab (validation/biaslab), Review status and feedback plan (+6 more)

### Community 114 - "reference.Label (append-only human label)"
Cohesion: 0.15
Nodes (7): Reference states (supported, reviewed_negative, unresolved, ineligible), packets.py (blind/verify packets, CSV import), packets.blind_packet(), packets.import_csv(), agreement() (Cohen's kappa), build_reference(), reference.Label (append-only human label)

### Community 115 - "SeedTest"
Cohesion: 0.18
Nodes (7): docs/provenance/seed.json, docs/provenance/seed-manifest.json, public/data packs (7, byte-identical), Source snapshot caprazmansetnov26 @ 49b60bc (Çapraz Manşet 8.1), SeedTest, Vendored Mesa bias simulator (mesa_bias_expanded), ExpandedDecisionModel

### Community 116 - "run"
Cohesion: 0.33
Nodes (6): run(), _id(), read(), ReplayCase, write(), write_inputs()

### Community 117 - "GitHub Actions checks.yml"
Cohesion: 0.22
Nodes (6): GitHub Actions checks.yml, CI job biasguard, CI job pipeline, CI job repo, CI job site-logic, CiTest

### Community 118 - "whatsnew.py"
Cohesion: 0.33
Nodes (5): build(), _d(), _load(), _n(), _sig()

### Community 119 - "findingGroups"
Cohesion: 0.33
Nodes (7): 'incelenemedi' state, 'Medyanın oyunları' group (vs 'Davranışsal yanlılıklar'), core.bin keys BGG / BGV, core.bin key BGM (biasguard-media.json), bgLabelState(), findingGroups(), label_status.json

### Community 120 - "proposal.md"
Cohesion: 0.29
Nodes (6): Capabilities, Impact, Modified Capabilities, New Capabilities, What Changes, Why

### Community 121 - "rules.cjs"
Cohesion: 0.57
Nodes (6): bandOf(), evidenceOf(), runRules(), runScore(), scoreText(), unquoted()

## Ambiguous Edges - Review These
- `Mobile and accessibility pass (44px targets, 4.5:1 contrast, tap tooltips)` → `Remove reduced motion (dmCalm, g6Calm, vzCalm, reduce)`  [AMBIGUOUS]
  docs/superpowers/plans/2026-11-06-broadsheet-motion.md · relation: conceptually_related_to

## Knowledge Gaps
- **78 isolated node(s):** `ADR-0001`, `ADR-0002`, `ADR-0001`, `ADR-0002`, `Stretched card link (.xstretch)` (+73 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 552 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `apply()` connect `test_news.py` to `catalog.py (biasguard)`, `test_routing.py`, `Reviewer agents (Çapraz Manş (biasguard)`, `findingGroups`, `explain_rules.py (biasguard)`, `BiasGuard (biasguard)`?**
  _High betweenness centrality (0.170) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `BiasGuard` (e.g. with `OpenAIReviewer` and `ProviderCallError`) actually correct?**
  _`BiasGuard` has 13 INFERRED edges - model-reasoned connections that need verification._
- **What connects `ADR-0001`, `ADR-0002`, `ADR-0001` to the rest of the system?**
  _78 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `logic.js (site/js/v7)` be split into smaller, more focused modules?**
  _Cohesion score 0.05331510594668489 - nodes in this community are weakly interconnected._
- **Why does `core.bin key BGM (biasguard-media.json)` connect `findingGroups` to `build() (pipeline/capraz_pipeline)`, `test_news.py`?**
  _High betweenness centrality (0.132) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `srcName()` (e.g. with `pgSource()` and `renderFeed()`) actually correct?**
  _`srcName()` has 9 INFERRED edges - model-reasoned connections that need verification._

### Low-confidence Hints
_AMBIGUOUS edges — the extractor was unsure. Verify before acting on these._

- **What is the exact relationship between `Mobile and accessibility pass (44px targets, 4.5:1 contrast, tap tooltips)` and `Remove reduced motion (dmCalm, g6Calm, vzCalm, reduce)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
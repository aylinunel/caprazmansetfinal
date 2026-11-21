# Graph Report - caprazmansetfinal  (2026-11-21)

## Corpus Check
- 192 files · ~263,021 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: (none) 5, .css 1)

## Summary
- 2710 nodes · 6593 edges · 119 communities (108 shown, 11 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 442 edges (avg confidence: 0.87)
- Token cost: 0 input · 132,873 output

## Community Hubs (Navigation)
- Site Tests and Deep Links
- App Router and Data Access
- Core Finding Blocks
- BiasGuard CLI
- URL Packing
- Turkish Layer and Appeals
- Rule Explanations
- Sources and Answers UI
- Agreement Statistic
- Review Export Import
- AI-vs-Rules Analysis
- BiasGuard News Runner
- Project Principles
- CI Workflow
- Outlet Analysis
- 7.0 Structure and Findings
- Article Ingest
- BiasGuard Engine
- Validation Lab Cases
- Whats New Builder
- Card Catalog
- Concept Catalogue and Deps
- Atlas and Advanced Charts
- Single-Source Lens Build
- Data Architecture ADRs
- Answer Key Plan Tasks
- Replay Runs
- Article Rows and Compare
- ML and Lens Plans
- Narrative Map Pages
- Leak Guard
- Change Protocol Metrics
- Lab Concept Targets
- Admin Shell and Footer
- AI Imza Box
- Reference Adapter Results
- UX Rethink
- Bias Concepts Overview
- Media Techniques Group
- Broadsheet Motion
- Crosswalk and Evidence Tiers
- Mesa Simulation
- Section Classifier
- Span Verification
- BiasGuard Gate Tests
- Event Clustering
- Promotion Gate
- Review Queue Tiers
- Events and Blind Spots
- Scored Bias Keys
- Detector Protocol
- Headline Scoring
- Topic Models
- Media Technique Cards
- Lens Measures and Verdicts
- Narratives Pipeline
- Reviewer Agents
- Card Data and Configs
- Rate Statistics
- Headline Compare
- Lab-Gated Promotion
- Party Page
- Omission and Loaded Language
- Repo Checks and Contracts
- Feedback and Gates
- Wording Similarity Build
- Comparison Charts
- AI Denetim Masası
- Navigation and Smoke Tests
- Apply-on-Run Tests
- Blind Reference Packets
- AI Onaylı Meaning
- Blind Spot Pages
- Dot-Matrix Engine
- Viz Helpers
- Method Page
- Editorial Schema
- Agenda Graph
- Finding Routing
- Provenance Seed
- Kindred Style
- Validation Lab Overview
- Pipeline Config
- Learning Data Contract
- Learning Loop
- Front-End Architecture
- CI Jobs
- Editorial Policy
- Detector Iterations
- Checklist Detector
- HTTP Errors
- Auth Constants
- Motion System
- Iframe Scroll Test
- Method Wheel Test
- Perf Test
- Method Diagrams
- Lens Page Rendering
- Implementation Plans
- Score Bridge
- Data Loader
- Attribution Notice
- Article Row Controls
- Outlet Page
- Lens Distance
- Mobile and Accessibility
- Method Scroll
- Fog Hero
- Official Notices Page
- Turkish Layer Tasks
- Lens Compute Tests
- Vendored Mesa Tests
- Cloud Setup Script

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
10. `load_cards()` - 27 edges

## Surprising Connections (you probably didn't know these)
- `assert_no_leak()` --semantically_similar_to--> `packets.blind_packet()`  [INFERRED] [semantically similar]
  validation/biaslab/renderer.py → docs/superpowers/plans/parked/2026-11-14-blind-reference-study.md
- `promotable()` --semantically_similar_to--> `gate.decide()`  [INFERRED] [semantically similar]
  validation/biaslab/promote.py → docs/superpowers/plans/parked/2026-11-14-blind-reference-study.md
- `ENTRY_TYPES media_practice / REVIEW_POLICIES media_pattern_review` --conceptually_related_to--> `load_media_cards()`  [INFERRED]
  docs/superpowers/plans/2026-11-14-medyanin-oyunlari.md → biasguard/catalog.py
- `core.bin key BGM (biasguard-media.json)` --shares_data_with--> `apply()`  [INFERRED]
  docs/superpowers/plans/2026-11-14-medyanin-oyunlari.md → biasguard/news.py
- `Anlatı topic, bias explainers, Nasıl çalışır scroll fix Plan` --references--> `assemble()`  [EXTRACTED]
  docs/superpowers/plans/2026-11-14-anlati-nav-bias-toc.md → pipeline/capraz_pipeline/site.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **BiasGuard selector/advocate/skeptic review and apply flow** — biasguard_agent_review_news_inputs, biasguard_agent_review_news_tasks, biasguard_agent_review_selector_agents, biasguard_agent_review_advocate_agents, biasguard_agent_review_skeptic_agents, biasguard_agent_review_news_apply, biasguard_agent_review_biasguard_json [EXTRACTED 1.00]
- **Headline scorer steps (quote stripping, lexicon, weights, bands, evidence)** — docs_biases_and_detection_unquoted, docs_biases_and_detection_lexicon_rules, docs_biases_and_detection_anchoring_structural_rule, docs_biases_and_detection_weights_score, docs_biases_and_detection_score_bands, docs_biases_and_detection_evidence_strength [EXTRACTED 1.00]
- **Learning loop iteration cycle (snapshot, errors, replay, promotion, insights)** — docs_superpowers_plans_2026_11_14_learning_loop_build_snapshots, docs_superpowers_plans_2026_11_14_learning_loop_error_analysis, docs_superpowers_plans_2026_11_14_learning_loop_replay_set, docs_superpowers_plans_2026_11_14_learning_loop_promotion_gate_module, docs_superpowers_plans_2026_11_14_learning_loop_drift_and_insights, docs_validation_iterations_the_loop [EXTRACTED 1.00]
- **Media card lifecycle: candidate → lab → promotion → site** — docs_superpowers_plans_2026_11_14_medyanin_oyunlari_seventeen_media_cards, validation_biaslab_renderer, validation_biaslab_promote_promotable, validation_biaslab_promote_promote, biasguard_data_media_cards, biasguard_news_apply, site_js_v7_logic_findinggroups [INFERRED 0.85]
- **Lab build→tasks→score pipeline** — validation_biaslab_renderer, validation_biaslab_renderer_assert_no_leak, validation_biaslab_adapter, validation_biaslab_ledger, validation_biaslab_metrics, validation_biaslab_metrics_paired_bootstrap, validation_biaslab_run [EXTRACTED 1.00]
- **Review status and feedback flow (routing, audit, editor review, labels, card gate, badges)** — docs_superpowers_plans_2026_11_14_review_status_and_feedback_routing_rule_tier, docs_superpowers_plans_2026_11_14_review_status_and_feedback_audit_sample, docs_superpowers_plans_2026_11_14_review_status_and_feedback_editor_review_export, docs_superpowers_plans_2026_11_14_review_status_and_feedback_label_import, docs_superpowers_plans_2026_11_14_review_status_and_feedback_card_stats_and_gate, docs_superpowers_plans_2026_11_14_review_status_and_feedback_status_badges [EXTRACTED 1.00]
- **Publication gating chain (gate → label_status → BGG → bgLabelState)** — validation_biaslab_gate_decide, validation_reference_gates, validation_reference_label_status, pipeline_capraz_pipeline_build_bgg_bgv, site_js_v7_logic_bglabelstate [EXTRACTED 1.00]
- **Claude Code guard, check contract and plan-first runner control system** — docs_superpowers_plans_parked_2026_11_14_claude_code_controls_check_contract, docs_superpowers_plans_parked_2026_11_14_claude_code_controls_guard_classify, docs_superpowers_plans_parked_2026_11_14_claude_code_controls_pretooluse_hook, docs_superpowers_plans_parked_2026_11_14_claude_code_controls_safe_check_change_set, docs_superpowers_plans_parked_2026_11_14_claude_code_controls_safe_check_plan, docs_superpowers_plans_parked_2026_11_14_claude_code_controls_safe_check_run, docs_superpowers_plans_parked_2026_11_14_claude_code_controls_ci_checks_workflow [EXTRACTED 1.00]
- **Finding block evolution across 7.0 structure, UX rethink and broadsheet motion** — docs_superpowers_specs_2026_11_05_capraz_7_structure_design_finding_block, docs_superpowers_plans_2026_11_05_capraz_7_structure_findingblock, docs_superpowers_specs_2026_11_05_ux_rethink_design_finding_block_layered, docs_superpowers_plans_2026_11_05_ux_rethink_findingblock_v8, docs_superpowers_specs_2026_11_06_broadsheet_motion_design_body_components [INFERRED 0.85]
- **Homepage hero evolution: dot-matrix LED hero -> fog split card -> both headlines with tint** — docs_superpowers_plans_2026_11_05_kindred_style_dot_matrix_hero, docs_superpowers_plans_2026_11_05_ux_rethink_foghero, docs_superpowers_specs_2026_11_05_ux_rethink_design_fog_split_card_hero, docs_superpowers_plans_2026_11_06_broadsheet_motion_hero_click_to_tint, docs_superpowers_specs_2026_11_06_broadsheet_motion_design_hero_both_headlines_tint [INFERRED 0.85]
- **Outlet distance score: proven measures + within-story regression + AI insights** — docs_superpowers_specs_2026_11_20_single_source_lens_decisions_distance_from_full_picture, docs_superpowers_specs_2026_11_20_single_source_lens_decisions_proven_measures, docs_superpowers_specs_2026_11_20_single_source_lens_decisions_event_fixed_effects_regression, docs_superpowers_specs_2026_11_20_single_source_lens_decisions_additional_insights_ai_imzali [EXTRACTED 1.00]
- **Expert review learning loop** — docs_superpowers_specs_2026_11_20_single_source_lens_decisions_ai_denetim_masasi, docs_superpowers_specs_2026_11_20_single_source_lens_decisions_expert_feedback_training_loop, docs_superpowers_specs_2026_11_20_single_source_lens_decisions_reviews_export_labels, docs_superpowers_specs_2026_11_20_single_source_lens_decisions_concept_measurability_criterion, docs_superpowers_specs_2026_11_20_single_source_lens_decisions_expert_answer_key [INFERRED 0.85]
- **Pattern naming safeguards** — docs_superpowers_specs_2026_11_20_single_source_lens_decisions_pattern_strength_wording, docs_superpowers_specs_2026_11_20_single_source_lens_decisions_unmistakable_pattern_rule, docs_superpowers_specs_2026_11_20_single_source_lens_decisions_behaviour_not_motive [EXTRACTED 1.00]
- **Çapraz Manşet pipeline stage flow (ingest → export)** — pipeline_readme_ingest, pipeline_readme_score, pipeline_readme_classify, pipeline_readme_cluster, pipeline_readme_events, pipeline_readme_topics, pipeline_readme_analyse, pipeline_readme_export [EXTRACTED 1.00]
- **Answer-key measurement pipeline (record, packets, desk, evals)** — docs_superpowers_plans_2026_11_17_ml_narrative_and_behavioural_coding_record, docs_superpowers_plans_2026_11_17_ml_narrative_and_behavioural_blind_packets, docs_superpowers_plans_2026_11_17_ml_narrative_and_behavioural_blind_desk_mode, docs_superpowers_plans_2026_11_17_ml_narrative_and_behavioural_behaviour_eval [EXTRACTED 0.90]
- **Single-source lens build pipeline** — docs_superpowers_plans_2026_11_21_single_source_lens_stats_module, docs_superpowers_plans_2026_11_21_single_source_lens_lens_module, docs_superpowers_plans_2026_11_21_single_source_lens_core_key_lens, docs_superpowers_plans_2026_11_21_single_source_lens_lens_js [EXTRACTED 0.90]

## Communities (119 total, 11 thin omitted)

### Community 0 - "Site Tests and Deep Links"
Cohesion: 0.05
Nodes (67): Stretched card link (.xstretch), 9 not-measurable concepts ('Bu veriyle ölçülemiyor'), BREG bias registry / bg7k alias, biasChip(), aliasEscape(), anEmpty(), anPage(), anVal() (+59 more)

### Community 1 - "App Router and Data Access"
Cohesion: 0.06
Nodes (64): actorMatrix(), actorsOf(), bg7(), bg7AdminFindings(), bg7AiTag(), bg7CardLine(), bg7caveat(), bg7Concept() (+56 more)

### Community 2 - "Core Finding Blocks"
Cohesion: 0.10
Nodes (63): findingBlock(), glClose(), glOpen(), yzBadge(), yzBlock(), orAnBars(), orAnKeys(), orAnlati() (+55 more)

### Community 3 - "BiasGuard CLI"
Cohesion: 0.07
Nodes (13): _build_parser(), _emit(), _load_capabilities(), main(), _read_utf8(), review_keys(), OptionalReviewKeysTest, build() (+5 more)

### Community 4 - "URL Packing"
Cohesion: 0.07
Nodes (27): convert(), _dump(), main(), split(), UrlPackTest, clusters(), confusion(), joined() (+19 more)

### Community 5 - "Turkish Layer and Appeals"
Cohesion: 0.07
Nodes (52): admittedSet(), appealPayload(), appealSubmit(), appealValidate(), applyOwnerSources(), basisEligible(), blocOf(), blocOfLean() (+44 more)

### Community 6 - "Rule Explanations"
Cohesion: 0.07
Nodes (26): compose(), concept_means(), _first_sentence(), _fit(), _join(), main(), _outlets(), _quote_line() (+18 more)

### Community 7 - "Sources and Answers UI"
Cohesion: 0.07
Nodes (56): renderSources(), t3(), v3After(), v3ansButtons(), v3answers(), v3bars(), v3bindStore(), v3chip() (+48 more)

### Community 8 - "Agreement Statistic"
Cohesion: 0.08
Nodes (23): _coded(), krippendorff_alpha(), percent_agreement(), blame_level(), frame_category(), human_rows(), load_codebook(), agreement_report() (+15 more)

### Community 9 - "Review Export Import"
Cohesion: 0.11
Nodes (13): append(), import_export(), Label, latest(), read(), card_stats(), card_status(), wilson_lower() (+5 more)

### Community 10 - "AI-vs-Rules Analysis"
Cohesion: 0.09
Nodes (25): auc(), _bloc(), _bloc_rate(), boot_mean_ci(), cite_index(), cited(), _cited(), compute() (+17 more)

### Community 11 - "BiasGuard News Runner"
Cohesion: 0.11
Nodes (16): _outlet_counts(), prompts(), selected_cards(), write_tasks(), _mapping(), OpenAIReviewer, _parse_provider_json(), ProviderCallError (+8 more)

### Community 12 - "Project Principles"
Cohesion: 0.07
Nodes (41): Scorer parity test vs 4.0 (22,213/22,213), Mercek human review and export (append-only, different approver, 80/10/10 split), Çapraz Manşet README, Accessibility and performance (44px targets, 4.5:1 contrast, no reduced-motion by owner decision), Agenda similarity (φ correlation, Mantel test 9,999 permutations), AI finding review status (AI onaylı / İnsan kontrolü bekliyor / İnsan doğruladı / düzeltti), capraz_pipeline.aix AI analyses (key AIX; AUC 0.48 vs loaded-language, κ 0.08 vs Anlatı), Analysis pipeline (pipeline/) (+33 more)

### Community 13 - "CI Workflow"
Cohesion: 0.07
Nodes (42): runs-on, steps, timeout-minutes, jobs, biasguard, lab, mesa, pipeline (+34 more)

### Community 14 - "Outlet Analysis"
Cohesion: 0.09
Nodes (19): active_outlets(), advanced_outlets(), agenda(), feed_table(), framing_pca(), headline_lede_gap(), jsd(), mantel() (+11 more)

### Community 15 - "7.0 Structure and Findings"
Cohesion: 0.10
Nodes (32): blameByBloc, Capraz Manset 7.0 Structure Redesign Implementation Plan, biasguard explain stage (explain-tasks / explain-apply / validate_explain), findingBlock (claim / viz / means / Nasil olctuk), ilanSearch / trFold Turkish-folded search, kurumLines7 outlet profile links to patterns, logic.js pure logic module (CommonJS-exported), narrGroups (+24 more)

### Community 16 - "Article Ingest"
Cohesion: 0.10
Nodes (16): collector_files(), ingest(), _lines(), main(), build_reference(), dataset_from_html(), assemble(), article_id() (+8 more)

### Community 17 - "BiasGuard Engine"
Cohesion: 0.11
Nodes (8): _all_offsets(), BiasGuard, _copy_call_metadata(), InputRejectedError, _safe_message(), _sha(), ReviewerSchemaError, TaskCatalogTests

### Community 18 - "Validation Lab Cases"
Cohesion: 0.10
Nodes (19): Case kinds (positive, inactive/boundary/quoted controls, missing_context), illusory_truth_effect (pilot concept), Perturbations (reverse_outlets, relabel_outlets, irrelevant_detail), selective_statistics (pilot concept), cases.Case, case_id(), DetectorInput, cases.expected() (+11 more)

### Community 19 - "Whats New Builder"
Cohesion: 0.09
Nodes (15): build(), _d(), _load(), _n(), _sig(), co_occurrence(), drift(), new_pattern_notes() (+7 more)

### Community 20 - "Card Catalog"
Cohesion: 0.12
Nodes (14): _card_document(), card_hash(), CatalogError, coverage(), ENTRY_TYPES media_practice / REVIEW_POLICIES media_pattern_review, load_cards(), load_media_cards(), load_source_index() (+6 more)

### Community 21 - "Concept Catalogue and Deps"
Cohesion: 0.09
Nodes (32): CheckList behavioural evaluation (eval/checklist_tr.jsonl: MFT, INV, DIR), Mercek 116 cognitive concepts (The Decision Lab directory), numpy==2.5.3, scikit-learn==1.9.1, scipy==1.18.1, validation.feedback import/status (reviews to labels, per-card statistics), validation/reference/gates.json (demote/hide concepts), Learning loop (docs/validation/ITERATIONS.md: replay set, promotion gate) (+24 more)

### Community 22 - "Atlas and Advanced Charts"
Cohesion: 0.15
Nodes (36): advHeat(), advScatter(), atlasColor(), atlasEntities(), atlasNeighbours(), atlasParallel(), atlasRadius(), atlasScatter() (+28 more)

### Community 23 - "Single-Source Lens Build"
Cohesion: 0.12
Nodes (18): big_stories(), compute(), confirmed_skips(), days_active(), _eligible(), feed_complete(), group(), is_all_caps() (+10 more)

### Community 24 - "Data Architecture ADRs"
Cohesion: 0.09
Nodes (23): ADR-0002: Reproducible day-partitioned analysis pipeline (Çapraz Manşet 5.0), backfill-data branch of turkish-news-scraper (139,702 articles, 28 outlets), tr_lower / tr_words Turkish-aware lowercasing, Analysis pipeline README (Çapraz Manşet 5.0), capraz_pipeline.reference.build_reference (data/reference/), python -m capraz_pipeline run (ingest + build + site), classify stage (section/political; TF-IDF + logistic regression, 5-fold CV), cluster stage (cluster.py; cosine ≥0.33, 48h, 40% linkage, ≤120, ≥5 outlets) (+15 more)

### Community 25 - "Answer Key Plan Tasks"
Cohesion: 0.07
Nodes (29): Blind precision and estimated recall for BiasGuard review, Blind mode in the AI denetim masasi (desk.js), Blind packets and desk-export import (core key BLIND), Coding record, gold and agreement report, Human few-shot examples for BiasGuard reviewers, Krippendorff's alpha (agreement statistic), validation/mlbench baselines (majority, TF-IDF LogReg), Narrative codebook (blame level, frame category) (+21 more)

### Community 26 - "Replay Runs"
Cohesion: 0.16
Nodes (11): run(), build(), _id(), read(), ReplayCase, score(), write(), write_inputs() (+3 more)

### Community 27 - "Article Rows and Compare"
Cohesion: 0.11
Nodes (35): artRows(), artUrl(), bbar(), cards(), cmpBrief(), compareMark(), dietBar(), dietCounts() (+27 more)

### Community 28 - "ML and Lens Plans"
Cohesion: 0.08
Nodes (28): Plan: ML narrative and behavioural (2026-11-17), validation/answerkey package (append-only human coding record), Single-source lens and expert-trained AI: decisions (2026-11-20), Additional insights (AI imzalı), AI denetim masası (behavioural scientist AI checker), Core key BGC, Bilişsel inceleme (YZ) page (old report), Distance from the full picture score (+20 more)

### Community 29 - "Narrative Map Pages"
Cohesion: 0.13
Nodes (30): anPageNasil(), narrMap(), pgAnlati(), pgAnlatiOlay(), v7BlocTxt(), v7Body(), v7Cell(), v7Colors() (+22 more)

### Community 30 - "Leak Guard"
Cohesion: 0.11
Nodes (6): assert_no_leak(), kinds(), Leak, render(), variants(), RendererTest

### Community 31 - "Change Protocol Metrics"
Cohesion: 0.14
Nodes (13): CHANGE_PROTOCOL.md, compare() / NotComparable, paired_bootstrap(), diff(), _r(), ratio(), Row, summarize() (+5 more)

### Community 32 - "Lab Concept Targets"
Cohesion: 0.08
Nodes (7): target(), build(), _jsonl(), lab_concepts(), score(), MediaCardsTest, RunTest

### Community 33 - "Admin Shell and Footer"
Cohesion: 0.09
Nodes (33): adminFoot(), adminShell(), fixLink(), follows(), footer2(), forYou(), isFollowing(), layoutPills() (+25 more)

### Community 34 - "AI Imza Box"
Cohesion: 0.12
Nodes (29): aiBox(), aiCard(), aiConceptName(), aiConceptText(), aiItems(), aiLegend(), aiMount(), aiQuote() (+21 more)

### Community 35 - "Reference Adapter Results"
Cohesion: 0.16
Nodes (10): cases.private.jsonl (private case records), Lab statuses (supported, contextual_effect, not_supported, uncertain, unassessed, ineligible, error), Assessment, Span, Attempt, Ledger, _assess(), text_summary() (+2 more)

### Community 36 - "UX Rethink"
Cohesion: 0.11
Nodes (27): Capraz Manset UX Rethink Implementation Plan, Event page story-first order (pgOlay7, v7-kisaca), findingBlock v8 (read / Neden onemli / Nasil olctuk / table), fogHero / fogMount WebGL2 fog split-card hero, GLOSSARY and glossTerms popovers, NAV_SUB plain-language section subtitles, outletKisaca, recentSplits (+19 more)

### Community 37 - "Bias Concepts Overview"
Cohesion: 0.14
Nodes (26): Biases and bias detection (Çapraz Manşet 6.0 and Mercek), Active outlet (≥ half of days + placement), Agenda similarity (φ, average linkage, Mantel r=0.03), Blind spots (Ground News rule adapted; binomial p<0.10; 42 in 6.0), Çapraz Manşet 6.0 (deterministic detection; 194,383 articles), Event clustering (pair F1 0.857; 140 locked events), Event selection (Olay seçimi), Evidence strength (evidenceOf: güçlü / orta / zayıf) (+18 more)

### Community 38 - "Media Techniques Group"
Cohesion: 0.13
Nodes (23): 'incelenemedi' state, 'Medyanın oyunları' group (vs 'Davranışsal yanlılıklar'), core.bin keys BGG / BGV, core.bin key BGM (biasguard-media.json), bandOf(), evidenceOf(), runRules(), runScore() (+15 more)

### Community 39 - "Broadsheet Motion"
Cohesion: 0.16
Nodes (20): CSS intro zoom + incoming page turn, Broadsheet in Motion Implementation Plan, GSAP 3.12.5 + ScrollTrigger + Lenis 1.1.13 (vendor first, CDN fallback), motion.js (motionLoad, motionMount, motionUnmount, MOTION), MOTION_K component timeline registry, Newsreader display font and --serif token, Performance trace (no task > 50 ms at 4x throttle) and screenshots, pNums Turkish count-phrase extractor (+12 more)

### Community 40 - "Crosswalk and Evidence Tiers"
Cohesion: 0.17
Nodes (10): Crosswalk review status (needs_domain_review/pilot/approved/rejected), Evidence tiers (headline_lede → internal_state), coverage(), Entry, load(), parse(), resolve(), _resolves() (+2 more)

### Community 41 - "Mesa Simulation"
Cohesion: 0.19
Nodes (6): _sources(), realize(), Realized, scenario(), MediaRendererTest, SimTest

### Community 42 - "Section Classifier"
Cohesion: 0.14
Nodes (8): apply(), cross_validate(), doc(), load_labels(), path_words(), TextModel, train(), DayCache

### Community 43 - "Span Verification"
Cohesion: 0.19
Nodes (5): normalize(), verify_spans(), StubReviewer, AdapterTest, run()

### Community 44 - "BiasGuard Gate Tests"
Cohesion: 0.12
Nodes (7): write_results(), _card(), GateTests, MediaPassTests, _review(), Reviewer, RollbackTests

### Community 45 - "Event Clustering"
Cohesion: 0.15
Nodes (9): lead_lag(), cluster(), links(), merge(), minutes(), pair_scores(), vectors(), art() (+1 more)

### Community 46 - "Promotion Gate"
Cohesion: 0.17
Nodes (8): assert_promotion_ready(), decide(), _kept_rate(), metrics_from(), record(), slice_regressions(), PromotionTest, replay()

### Community 47 - "Review Queue Tiers"
Cohesion: 0.17
Nodes (7): review_queue(), tier(), a(), ev(), QueueTest, TierTest, one()

### Community 48 - "Events and Blind Spots"
Cohesion: 0.16
Nodes (8): binom_cdf(), blind_spot(), build_events(), event_record(), keywords(), near_duplicates(), stable_ids(), EventsTest

### Community 49 - "Scored Bias Keys"
Cohesion: 0.13
Nodes (23): Ad Hominem (scored key), Anchoring Bias (scored key), Anchoring structural rule (number + unit before first colon/dash), Authority Bias (scored key), Bandwagon Effect (scored key), Base Rate Fallacy, Cherry Picking, Consequence Framing (+15 more)

### Community 50 - "Detector Protocol"
Cohesion: 0.19
Nodes (13): Assessment, build_records(), Detector, DetectorInput, Evidence, load(), main(), MockContractDetector (+5 more)

### Community 51 - "Headline Scoring"
Cohesion: 0.17
Nodes (4): rules_key(), score(), Store, CrossDayTest

### Community 52 - "Topic Models"
Cohesion: 0.13
Nodes (6): decide(), event_topic_model(), gsdmm(), headline_topics(), npmi(), TopicsTest

### Community 53 - "Media Technique Cards"
Cohesion: 0.20
Nodes (21): Ad hominem (Kisiye saldiri), Causal overclaim (Kanitsiz nedensellik), Cherry picking (Secmeci kanit kullanimi), Consequence framing (Sonuc cercevelemesi), effect_context_only policy, Emphasis framing (Vurgu cercevelemesi), Episodic framing (Olay odakli cerceveleme), False dilemma (Yanlis ikilem) (+13 more)

### Community 54 - "Lens Measures and Verdicts"
Cohesion: 0.14
Nodes (5): strata(), verdict(), complete_fixture(), MeasureTest, small_fixture()

### Community 55 - "Narratives Pipeline"
Cohesion: 0.16
Nodes (10): candidates(), diverge(), first(), _card_conditions(), finalize(), _focus(), _load(), merge() (+2 more)

### Community 56 - "Reviewer Agents"
Cohesion: 0.22
Nodes (16): Reviewer agents (Çapraz Manşet 7.0) – AGENT_REVIEW.md, Advocate agents, biasguard.json → core.bin key BG, Circuit breaker (BREAKER_TRIPPED after five failed batches; not_attempted), FileReviewer (select/review interface), 'incelenemedi' display for empty media catalogue, biasguard/data/media_cards.json (empty until approved and lab-passed), Media-technique pass (Medyanın oyunları, --catalog media) (+8 more)

### Community 57 - "Card Data and Configs"
Cohesion: 0.18
Nodes (8): biasguard/data/cards.json (116 behavioural cards), biasguard/data/media_cards.json, _card_ids(), catalog(), manifest(), _proposed(), Lab-only proposed card selective-statistics, ConfigsTest

### Community 58 - "Rate Statistics"
Cohesion: 0.18
Nodes (5): _rate(), bh_q(), cmh_p(), mh_rr(), StatsTest

### Community 59 - "Headline Compare"
Cohesion: 0.22
Nodes (17): artOf(), compareHeads(), covOf(), defaultPair(), exampleEvent(), htoks(), leadEvent(), markText() (+9 more)

### Community 60 - "Lab-Gated Promotion"
Cohesion: 0.19
Nodes (4): Lab-gated promotion, promotable(), promote(), PromoteTest

### Community 61 - "Party Page"
Cohesion: 0.30
Nodes (16): pgParti(), ptAxes(), ptClose(), ptData(), ptHeat(), ptHow(), ptLate(), ptLeanSort() (+8 more)

### Community 62 - "Omission and Loaded Language"
Cohesion: 0.14
Nodes (16): Causal Overclaim, Commission and omission of information, Conservative gate (omission/sourcing/statistics → candidate unless full text and ≥2 outlets), contextual_omission (media technique), Loaded Language (Yüklü dil), Mercek (aylinunel/mediabias; LLM-based evidence-backed framing findings), Mercek causal_overclaim (media technique), Mercek input prep (Jaccard 48h grouping, frozen snapshots, publisher masking) (+8 more)

### Community 63 - "Repo Checks and Contracts"
Cohesion: 0.24
Nodes (14): analysis-invariants read-only reviewer agent (11 invariants), check_contract (Check, CHECKS, routine_argvs, select), check skill (.claude/skills/check/SKILL.md), CI checks.yml jobs per check id, Credential patterns (.env, *.pem, id_rsa, ~/.ssh ...), Claude Code Controls Implementation Plan (ON HOLD), guard.py classify (Decision deny / ask / normal), PreToolUse hook adapter and .claude/settings.json registration (+6 more)

### Community 64 - "Feedback and Gates"
Cohesion: 0.20
Nodes (14): New-pattern reviewer notes (Kartlarda olmayan bir oruntu), Deterministic 5% audit sample (in_audit_sample), Card statistics and gate (wilson_lower, card_stats, card_status), Editor review approve action and export (reviewsExport, reviewState), gates.json thresholds (agreed: false), Label import (validation/feedback/labels.py, Label, labels.jsonl), Review queue (least-reviewed cards first), Review Status and Feedback Implementation Plan (+6 more)

### Community 65 - "Wording Similarity Build"
Cohesion: 0.22
Nodes (9): wording_similarity(), build(), _gz(), ingest_totals(), _json(), load_articles(), pack_month(), params_dict() (+1 more)

### Community 66 - "Comparison Charts"
Cohesion: 0.16
Nodes (16): bloc(), cmpBest(), cmpState(), deviceStats(), fig(), firstBy(), kuFindKeys(), kuFindMean() (+8 more)

### Community 67 - "AI Denetim Masası"
Cohesion: 0.29
Nodes (15): deskCardOptions(), deskHeadlines(), deskItems(), deskLearning(), deskName(), deskOpen(), deskOutlets(), deskRerender() (+7 more)

### Community 68 - "Navigation and Smoke Tests"
Cohesion: 0.13
Nodes (12): Anlatı topic, bias explainers, Nasıl çalışır scroll fix Plan, Anlatı haritası top-level topic, NAV / SUB navigation tables, argv, { chromium }, clicks, evals, fs (+4 more)

### Community 70 - "Blind Reference Packets"
Cohesion: 0.15
Nodes (7): Reference states (supported, reviewed_negative, unresolved, ineligible), packets.py (blind/verify packets, CSV import), packets.blind_packet(), packets.import_csv(), agreement() (Cohen's kappa), build_reference(), reference.Label (append-only human label)

### Community 71 - "AI Onaylı Meaning"
Cohesion: 0.25
Nodes (9): Claude Code controls (guard, safe_check, reviewer) - on hold, Layer 3: human reference and measured improvement, Capraz Manset Final: integration design, Layer 1: foundation (seeded copy of 8.1), Medyanin oyunlari media catalogue (media_cards.json), Owner decisions (14 November 2026), 8.1 run: 0 supported, 439 uncertain findings, Owner-only editor review (rev7) (+1 more)

### Community 72 - "Blind Spot Pages"
Cohesion: 0.21
Nodes (14): bg7k(), bg7Stats(), blindspotPage(), briefDays(), evx(), feedChips(), feedFilters(), fSel() (+6 more)

### Community 73 - "Dot-Matrix Engine"
Cohesion: 0.26
Nodes (11): dmCardFx(), dmColor(), dmFeedWatch(), dmHash(), dmHeads(), dmMake(), S, dmMount() (+3 more)

### Community 74 - "Viz Helpers"
Cohesion: 0.20
Nodes (6): vzDist(), vzLine(), vzQ(), vzRows(), vzTicks(), vzTipAttr()

### Community 75 - "Method Page"
Cohesion: 0.27
Nodes (12): conceptLibrary(), glossaryHTML(), kaynakHtml(), pgYontem7(), trBlock(), trN(), trQ(), turkiyeBlocks() (+4 more)

### Community 76 - "Editorial Schema"
Cohesion: 0.18
Nodes (11): collectorArticleSchema, CollectorBatch, collectorBatchSchema, httpsUrl, kindValues, publicationErrors(), PublicationRecord, safeExternalUrl() (+3 more)

### Community 77 - "Agenda Graph"
Cohesion: 0.21
Nodes (7): tipOff(), g6AgendaData(), g6Bloc(), g6Build(), g6Load(), g6Mount(), g6Tok()

### Community 78 - "Finding Routing"
Cohesion: 0.24
Nodes (3): stamped(), in_audit_sample(), AuditTest

### Community 79 - "Provenance Seed"
Cohesion: 0.18
Nodes (7): docs/provenance/seed.json, docs/provenance/seed-manifest.json, public/data packs (7, byte-identical), Source snapshot caprazmansetnov26 @ 49b60bc (Çapraz Manşet 8.1), SeedTest, Vendored Mesa bias simulator (mesa_bias_expanded), ExpandedDecisionModel

### Community 80 - "Kindred Style"
Cohesion: 0.24
Nodes (12): dm-band drifting dot-matrix page-header band, Capraz Manset 7.0 Kindred-style restyle plan, Dot-matrix LED charts (vzDist / vzLine canvas), Dot-matrix LED hero (dmHero) rendering the split card, dots.js engine (dmMake, dmMount, dmHeads, DM_DATA), Kindred style (Inter, #f7f7f5 off-white, #111 ink, black pills), Kindred site-wide colour and font tokens, Rainbow underglow CTA pill (+4 more)

### Community 81 - "Validation Lab Overview"
Cohesion: 0.20
Nodes (11): Adapter statuses (never collapsed), BiasGuard (116 concept cards, advocate and skeptic reviewers), Capraz Manset pipeline (ingest to core.bin), Crosswalk (Mesa id to detector card id), Evidence tiers (headline_lede, full_article, decision_history, internal_state), Invariance perturbations (outlet order, relabelling, irrelevant detail), Mesa cognitive-bias simulation framework (138 mechanisms), Pilot concepts: selective_statistics and illusory_truth_effect (+3 more)

### Community 82 - "Pipeline Config"
Cohesion: 0.24
Nodes (7): Params, compare(), _done(), _findings(), main(), _top(), _tr()

### Community 83 - "Learning Data Contract"
Cohesion: 0.31
Nodes (11): Data contract and idempotent build snapshots (validation/learning/snapshot.py), Error analysis: confusion, clusters, stuck conditions (errors.py), next_move rule (better card wording / evidence / threshold / fallback), Data contract for the learning loop, Detector version (12 hex of SHA-256 over card hash, prompts version, candidate limit), Evaluation slices (card, catalogue, bloc, month, event size, tier), Snapshot id <pack>_<catalog>_<detector version>, Snapshot row entity (event x card x detector version x pack) (+3 more)

### Community 84 - "Learning Loop"
Cohesion: 0.24
Nodes (10): Drift, co-occurrence and new-pattern proposals (insights.py), Learning Loop Implementation Plan, Permanent replay set (ReplayCase, replay.jsonl), How the detector learns (mle-workflow: routing stats, regression memory, versions, new insight), Iteration compact for the first iteration, Plans table (foundation, Mesa lab, review status, Medyanin oyunlari, learning loop), Time-ordered event split (replay set), Cards raised together (co-occurrence lift) (+2 more)

### Community 85 - "Front-End Architecture"
Cohesion: 0.20
Nodes (10): app.js router and data access, Design system (newsprint tokens, Newsreader, IBM Plex, Bricolage Grotesque, fixed placement colours), Finding block (claim → chart → Nasıl ölçtük? → table), fog.js hero state machine (WebGL2 fog, click-to-tint), Front-end architecture (hash-routed SPA, site/js/v7 in V7_ORDER), Motion system (motion.js, data-m kinds, MOTION_K registry), Page lifecycle (motionUnmount, redirectRoute, render, motionMount), Vendored libraries (GSAP, ScrollTrigger, Lenis, AntV G6, D3 7.9.0) (+2 more)

### Community 86 - "CI Jobs"
Cohesion: 0.22
Nodes (6): GitHub Actions checks.yml, CI job biasguard, CI job pipeline, CI job repo, CI job site-logic, CiTest

### Community 87 - "Editorial Policy"
Cohesion: 0.20
Nodes (8): data/reference/editorial.json, effect_context_only policy (thematic_framing, spin), 17 candidate media-technique cards, Review status and feedback plan, gate.decide(), wilson_lower(), validation/reference/gates.json, label_status.json

### Community 88 - "Detector Iterations"
Cohesion: 0.36
Nodes (10): Fail-closed promotion gate (promotion.py, PROMOTION_GATES), Slice regressions (per card and bloc_mix, min_n 10), Detector iterations, Iteration 1 compact, Iteration Compact (template), Next experiment: media-technique cards as lab candidates, Observation Ledger (iteration 0 baseline), Promotion gate (fail-closed metric limits) (+2 more)

### Community 89 - "Checklist Detector"
Cohesion: 0.20
Nodes (7): cases, fs, got, MAP, out, path, R

### Community 90 - "HTTP Errors"
Cohesion: 0.29
Nodes (5): BadRequestError(), ForbiddenError(), HttpError, NotFoundError(), UnauthorizedError()

### Community 91 - "Auth Constants"
Cohesion: 0.20
Nodes (7): AXIOS_TIMEOUT_MS, COOKIE_NAME, NOT_ADMIN_ERR_MSG, OAUTH_STATE_COOKIE, OAuthState, ONE_YEAR_MS, UNAUTHED_ERR_MSG

### Community 92 - "Motion System"
Cohesion: 0.31
Nodes (5): motionAdd(), motionEach(), motionLoad(), motionMount(), motionRun()

### Community 93 - "Iframe Scroll Test"
Cohesion: 0.22
Nodes (6): { chromium }, fs, http, path, root, TYPES

### Community 94 - "Method Wheel Test"
Cohesion: 0.22
Nodes (6): { chromium }, fs, http, path, root, TYPES

### Community 95 - "Perf Test"
Cohesion: 0.22
Nodes (6): { chromium }, fs, http, path, [siteDir, route = "#/olay?e=s4374"], TYPES

### Community 96 - "Method Diagrams"
Cohesion: 0.31
Nodes (9): dArrow(), dBox(), diaBlind(), diaPipeline(), diaScheme(), limits5(), methodSecs(), nfmt() (+1 more)

### Community 97 - "Lens Page Rendering"
Cohesion: 0.36
Nodes (6): lensAiBox(), lensBody(), lensRowSvg(), lensSection(), lensStripSvg(), lensX()

### Community 98 - "Implementation Plans"
Cohesion: 0.36
Nodes (7): Foundation Implementation Plan, Medyanın Oyunları Implementation Plan, Mesa Validation Lab Implementation Plan, Validation lab (validation/biaslab), Blind Reference Study Implementation Plan (NOT SCHEDULED), Parked plan: Claude Code controls, Çapraz Final Integration Design Spec

### Community 99 - "Score Bridge"
Cohesion: 0.25
Nodes (4): path, R, readline, rl

### Community 100 - "Data Loader"
Cohesion: 0.32
Nodes (4): gunzip(), ADR-0002, load(), unbase64()

### Community 101 - "Attribution Notice"
Cohesion: 0.33
Nodes (5): NOTICE.md: Attribution and permission status, Çapraz Manşet 3.0 uploaded HTML (design, branding, dataset source), data/import-manifest.json (asset/data hashes), Ponytail skill (.claude/skills/ponytail/SKILL.md, MIT, DietrichGebert), scraper/upstream/UPSTREAM_PROVENANCE.json

### Community 102 - "Article Row Controls"
Cohesion: 0.33
Nodes (7): artRow(), devChips(), hlTitle(), qLoad(), qRecord(), qSave(), renderQueue()

### Community 103 - "Outlet Page"
Cohesion: 0.52
Nodes (6): kuDil(), kuFirst(), kuFp(), kuLink(), kuName(), kurumFindings7()

### Community 106 - "Mobile and Accessibility"
Cohesion: 0.50
Nodes (4): smoke.cjs Playwright route smoke test, Mobile and accessibility pass (44px targets, 4.5:1 contrast, tap tooltips), Remove reduced motion (dmCalm, g6Calm, vzCalm, reduce), Mobile, accessibility, motion budget and performance

### Community 107 - "Method Scroll"
Cohesion: 0.60
Nodes (5): MOTION.lenis smooth scroll path, wireYontem(), ymGo(), ymOpen(), ymScrollTo()

### Community 108 - "Fog Hero"
Cohesion: 0.60
Nodes (3): fogDark(), fogMount(), fogSmooth()

### Community 109 - "Official Notices Page"
Cohesion: 0.80
Nodes (4): ilanItems(), ilanResults(), pgIlan(), wireIlan()

### Community 110 - "Turkish Layer Tasks"
Cohesion: 0.50
Nodes (4): T3 notice split (resmî ilan detection; ≥50% notices listed separately), T6 near-duplicates (char n-gram cosine ≥0.90; duplicate_cosine), T7 suffix-aware word marking (≤2 suffix layers, stem ≥4 letters), turkish-layer.js Turkish refinements (T1–T7)

## Ambiguous Edges - Review These
- `Mobile and accessibility pass (44px targets, 4.5:1 contrast, tap tooltips)` → `Remove reduced motion (dmCalm, g6Calm, vzCalm, reduce)`  [AMBIGUOUS]
  docs/superpowers/plans/2026-11-06-broadsheet-motion.md · relation: conceptually_related_to

## Knowledge Gaps
- **91 isolated node(s):** `ADR-0001`, `ADR-0002`, `ADR-0002`, `ADR-0001`, `scraper/upstream/UPSTREAM_PROVENANCE.json` (+86 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 543 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `core.bin key BGM (biasguard-media.json)` connect `Media Techniques Group` to `Wording Similarity Build`, `Rule Explanations`?**
  _High betweenness centrality (0.198) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `BiasGuard` (e.g. with `OpenAIReviewer` and `ProviderCallError`) actually correct?**
  _`BiasGuard` has 13 INFERRED edges - model-reasoned connections that need verification._
- **What connects `ADR-0001`, `ADR-0002`, `ADR-0002` to the rest of the system?**
  _91 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Site Tests and Deep Links` be split into smaller, more focused modules?**
  _Cohesion score 0.05403508771929825 - nodes in this community are weakly interconnected._
- **Why does `findingGroups()` connect `Media Techniques Group` to `Site Tests and Deep Links`?**
  _High betweenness centrality (0.194) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `srcName()` (e.g. with `pgSource()` and `renderFeed()`) actually correct?**
  _`srcName()` has 9 INFERRED edges - model-reasoned connections that need verification._

### Low-confidence Hints
_AMBIGUOUS edges — the extractor was unsure. Verify before acting on these._

- **What is the exact relationship between `Mobile and accessibility pass (44px targets, 4.5:1 contrast, tap tooltips)` and `Remove reduced motion (dmCalm, g6Calm, vzCalm, reduce)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
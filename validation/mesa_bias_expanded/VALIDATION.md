# Executed validation of the 138-module Mesa expansion

**Executable scope complete: True.** The run reports 138/138 passing process contracts, 1531 passed pytest cases, 0 failed/error cases, and 0 skips. The paired sweep completed 138 concepts and 277 named task scenarios with 0 execution failures.

All 277/277 larger-sweep scenario means met their declared directional or boundary-equality expectations. This includes 9972 paired-agent observations and 28584 agent-step trace records. The pytest suite includes a complete standalone-script contract check in a temporary folder without the modular source directory.

The exact missing scope comprises 138 canonical entries: 112 from the attachment's cognitive-concept layer and 26 from its other source layers. Source-layer labels are not psychological classifications; the implemented registry distinguishes biases, heuristics, learning/motivational effects, psychological states and media practices. Each entry has distinct source metadata, executable process code, task inputs/state, an explicit reference policy, positive and boundary scenarios, a module-specific test file, and an implementation note. Source labels, source variants and annotation boundaries are retained in `missing_concepts.json`.

The paired sweep used 12 agents per condition, 3 seeds, and strength 0.8 versus strength zero. Agent conditions received matched input scenarios and uniform random draws. Scenarios run their own number of chronological contexts; a one-step choice is not presented as longitudinal evidence. Metrics have concept-specific units and are never reduced to one global bias score.

`coverage.json` contains every contract's actual directional comparison. `pytest_results.xml` and `pytest_results.txt` retain executed software cases. `sweep/paired_agents.csv` and `sweep/traces.jsonl` preserve numeric observables, paired differences and per-agent process traces. `sweep/summary.json` reports seed-level comparisons and between-seed variation. No dropped or failed output is replaced with a fabricated negative result.

The unchanged original anchoring/confirmation demonstration is retained in `legacy_mesa_model.py`, with its regression cases. The original bandwagon/social-norms peer averaging remains explicitly partial and is not silently declared a full implementation by this expansion.

## First larger sweep and repair

The first 12-agent sweep had 1 recorded execution failure(s). Its raw outputs are retained in `results/sweep_first_attempt`, not discarded. The pluralistic-ignorance teaching fixture described three people and therefore rejected larger agent indexes. An opt-in built-in population factory now creates complete hypothetical group vectors for the chosen agent count under the same teaching assumptions. Custom group data are never resized or inferred. New 12- and 50-agent tests preserve private-expression reference behavior, the no-misperception boundary, and strict rejection of mismatched custom groups. The final sweep above was executed again after this integration repair.

## What passing these checks does not establish

These are implementation-authored, synthetic task models. Passing a positive example, a boundary control, and an equation oracle establishes code behavior under those assumptions. It does not independently establish expert validity, human-population behavior, effect size, construct identification, causal inference, model calibration or detection accuracy. The model has no natural-language/image detector and cannot diagnose bias in an actual person or newsroom.

Heuristics and learning/motivational effects are preserved as potentially useful processes rather than blanket errors. Media practices are structured presentation-process models, not evidence that a publisher acted deceptively. Narrow or uncertain effects are only hypothesized rules, not universal empirical facts.

Models use explicit task state and freeze peer snapshots before proposals. Default agent populations share the teaching scenario; deterministic effects can be identical across agents/seeds. More copies of a synthetic rule are not independent human observations. Combining incompatible units or automatically layering all 138 mechanisms into one decision is unsupported; joint modeling requires a separately designed, compatible task and update policy.

## Reproduce

```bash
python -m pip install -r requirements.txt
python -m pytest -q --junitxml=results/pytest_results.xml
python expanded_mesa.py validate --output results/coverage.json
python expanded_mesa.py sweep --agents 12 --replicates 3 --output results/sweep
python build_validation_report.py
python export_single_file.py
```

The standalone `expanded_mesa_biases.py` embeds the exact same source code, definitions and scenarios. It requires Mesa 3.5.2 and NumPy at runtime, not the module directory or pytest. The source package includes tests and implementation notes for inspectability.

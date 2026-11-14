# Expanded Mesa model: 138 additional task-specific mechanisms

`expanded_mesa.py` extends the previous scalar-belief demonstration with a plugin-based Mesa model. Each missing concept gets its own executable process, required task inputs, state, metric, positive scenario, boundary control, and tests. `expanded_mesa_biases.py`, generated only after full executable-contract success, is a single-file version with the same code and scenarios embedded.

The exact requested missing scope is **138 canonical entries**: 112 from the attachment's cognitive-concept layer and 26 from its other source layers (10 media-form, 10 cross-concept, and 6 media-technique entries). Source-layer membership is not a psychological classification. The implemented registry separately distinguishes cognitive biases, heuristics, learning effects, motivational mechanisms, psychological states and media practices. These are not 138 additional empirically established cognitive errors. Definitions and source boundaries are preserved from the user's attachment in `source_biases.md` and `missing_concepts.json`.

The original anchoring and confirmation rules are retained unchanged in `legacy_mesa_model.py`. Bandwagon/social-norms peer averaging remains a partial proxy in that original demonstration; the requested 138-module expansion does not silently upgrade those two proxy claims.

## Install and run

Use Python 3.11+. The runtime is pinned to Mesa 3.5.2:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python expanded_mesa.py list
python expanded_mesa.py describe base_rate_fallacy
python expanded_mesa.py run base_rate_fallacy --agents 12 --replicates 3 --seed 42 --output demo
python expanded_mesa.py validate --output results/coverage.json
python expanded_mesa.py sweep --agents 12 --replicates 3 --output sweep_output
python -m pytest -q
```

Windows activation alternative: `.venv\Scripts\Activate.ps1`.

For the standalone deliverable, only Mesa and NumPy are needed:

```bash
python -m pip install mesa==3.5.2 numpy
python expanded_mesa_biases.py describe base_rate_fallacy
python expanded_mesa_biases.py run base_rate_fallacy --agents 20 --replicates 5 --output demo
python expanded_mesa_biases.py validate
```

No LLM/API calls, credentials, external data services, or persistent servers are used by the scripts. Empirical fitting and real data are outside the sample.

## How the expanded model works

`ExpandedDecisionModel` creates registered Mesa `TaskAgent`s. Instead of forcing every construct into the same belief number, agents carry concept-specific state dictionaries: relevant money, memory, option, expectation, responsibility or structured presentation state according to the task.

Each step freezes all previous states, runs every proposal, then commits every proposal. Peers are adjacent agents on a ring. Every plugin receives a copy of its agent's prior state and neighboring agents' prior states, plus explicit task observations and a pre-generated uniform draw. This supports genuine peer-state processes where the plugin uses them, without accidental sequential updates.

A matched comparison runs strength zero and the chosen intervention strength on identical scenarios, seeds, initial states, networks and random draws. Strength is an illustrative intervention coefficient—not a measured bias prevalence, an effect-size estimate or confidence score. Agents have homogeneous initial task state by default; differences arise only where task inputs or supplied stochastic draws create them. Identical agents are not evidence of real-world consensus.

Default scenarios may be one-step choices or multi-round histories. Simulation length is the explicit number of chronological contexts; the runner does not fabricate extra repetitions for temporal concepts. A task that requires history must expose that history or carry it in state. All internal psychological states are explicitly assumed synthetic inputs, never inferred from a real person's behavior.

The pluralistic-ignorance teaching task has an opt-in population factory that generates explicit group vectors for the requested number of agents using the same homogeneous toy assumptions. A custom scenario's group facts are never resized, repeated, or inferred: its private-position and perception vectors must cover the simulated population.

## Inspect and customize a task

`describe <id>` shows its primary observable, units, input requirements, state, assumptions, limitations and teaching scenarios. A module's implementation note explains its equation or process and reference policy. These policies are justified toy comparators, not universal optimal decision makers.

To modify an example, copy a scenario shown by `describe` to a JSON file with `name`, `initial_state`, a chronological `contexts` list, and `expectation`. Then run:

```bash
python expanded_mesa.py run base_rate_fallacy --scenario-file custom_scenario.json \
  --agents 12 --replicates 3 --strength 0.6 --output custom_output
```

Reserved fields `state`, `peer_states`, `round_index`, `agent_index`, and `uniform` are supplied by the runner and cannot be overridden in contexts. Required inputs must be present and valid; missing evidence is an error, not a negative finding. JSON is treated only as data and never executed.

## Read the outputs correctly

`paired_agents.csv` contains task-specific intervention and reference observables, their differences, and units. `summary.json` averages paired differences within each seed and reports between-seed sample standard deviation. A deterministic process can have zero variation across seeds; running more identical synthetic agents does not create independent behavioral evidence.

`traces.jsonl` records agent states and explanations for both reference and intervention conditions. `failures.json` records any execution errors; the command exits with code 2 when a requested concept fails. `run_metadata.json` records parameters and runtime versions. `validate` reports missing, broken or failing modules and exits nonzero rather than substituting a generic penalty.

Metrics from different tasks have different units. Do **not** average memory retention, money valuation, attention allocation, confidence gaps and media exposure into one global “bias score.” Beneficial heuristics and learning/motivational mechanisms are not harmful by default. The runner isolates task models; combining several mechanisms on one decision requires an explicit compatible task design and documented update order. It does not assert that all 138 mechanisms co-occur.

Media modules simulate structured presentation choices or consequences from supplied facts. They do not parse Turkish semantics, inspect actual photographs, prove editorial intention, or validate quotations from real articles. Cognitive modules simulate authored mechanisms; they do not detect hidden cognition or establish that a real person has a bias.

## Code organization

`mechanisms/<id>.py` implements one concept. `tests/test_<id>.py` tests its equations and boundaries. `specs/<id>.json` preserves its source definitions; `specs/<id>_implementation.md` documents the assumed model. `tests/test_engine_contract.py` enforces exact scope, deterministic non-mutating results, matched inputs and staged Mesa activation.

`legacy_mesa_model.py` retains the earlier demonstration separately. Its plotting option needs Matplotlib, as before. The new runner does not require plotting dependencies.

`export_single_file.py` refuses to export unless all 138 executable contracts pass. Exported code is fixed and embedded by the developer; user-supplied context JSON remains data.

## Validation boundary

Passing tests demonstrate that the implemented formulas and scenario contracts execute as authored. They do not prove expert agreement, causal validity, empirical effect size, realistic populations, or detector accuracy. Positive and boundary cases are synthetic and implementation-authored. Strong behavioral claims require independently adjudicated tasks, human data, calibration, and external validation. Particularly narrow or contested effects are labeled illustrative in their module limitations.

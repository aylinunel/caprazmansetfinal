# Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Seed `caprazmansetfinal` from Çapraz Manşet 8.1 with its provenance recorded and every existing test suite running in CI.

**Architecture:** The 8.1 tree is copied in one attributed commit; no code is changed. CI, which today runs only the pipeline tests, also runs the BiasGuard and site-logic tests that already exist.

**Tech Stack:** Python 3.12, `unittest`, Node 22 (`node --test`), GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-14-capraz-final-integration-design.md`

## Global Constraints

- Source snapshot: `aylinunel/caprazmansetnov26`, branch `claude/sleepy-goodall-sd1d9r` @
  `49b60bc4fd0407f8f979c08cd7e5ab0641ad040d` (owner's choice; not `main`). The source repo is read-only.
- No source file from the snapshot is modified in this plan.
- Tests are offline: no network, no credentials.
- The workflow keeps `permissions: contents: read`, a `timeout-minutes` on every job, and uses no secrets.
- Develop on branch `claude/zen-ptolemy-7bvru2`. No pull request unless the owner asks.
- The Claude Code controls (guard, check runner, reviewer) are out of scope; see
  `parked/2026-11-14-claude-code-controls.md`.
- Follow the owner's standing instructions: `ponytail` and `anthropic-skills:karpathy-guidelines`.

## Review Focus

1. A file present in the source but missing after the copy (for example a dot-directory such as
   `.github/` or `.10x/`) → the seed test fails and names it. (Task 1)
2. A binary data pack altered by the copy (line-ending or encoding conversion) → the seed test fails on
   its checksum. (Task 1)
3. An inherited test that already fails in 8.1 → recorded by name in `docs/provenance/seed.json`
   under `inherited_failures`, not silently fixed or skipped. (Task 1)
4. A CI job that passes because it ran zero tests → each job's command is asserted to exist in the
   workflow and is run locally first, with the test count noted. (Task 2)
5. The existing design documents in `docs/superpowers/` being overwritten by the copy → both the
   source's and this repo's files are present afterwards. (Task 1)

---

### Task 1: Seed the repository from 8.1

**Files:**
- Create: the full tree of the source snapshot at the repo root
- Create: `docs/provenance/seed.json`, `docs/provenance/seed-manifest.json`
- Create: `tests_repo/__init__.py`, `tests_repo/test_seed.py`

**Interfaces:**
- Produces: the existing commands, unchanged:
  `cd pipeline && python -m unittest discover -s tests -v`,
  `python -m unittest biasguard.test_news -v`, `node --test site/tests/logic.test.cjs`.
- `seed-manifest.json` is `{"<relative path>": "<sha256>"}` for every tracked file of the source at the
  pinned commit, generated from the source checkout with `git ls-files`.

- [ ] **Step 1: Write the failing test**

```python
# tests_repo/test_seed.py
import hashlib, json, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

class SeedTest(unittest.TestCase):
    def test_provenance_names_the_source_commit(self):
        seed = json.loads((ROOT / "docs/provenance/seed.json").read_text(encoding="utf-8"))
        self.assertEqual(seed["source_repo"], "aylinunel/caprazmansetnov26")
        self.assertEqual(seed["source_commit"], "49b60bc4fd0407f8f979c08cd7e5ab0641ad040d")
        self.assertEqual(seed["source_branch"], "claude/sleepy-goodall-sd1d9r")
        self.assertIn("inherited_failures", seed)

    def test_every_source_file_is_still_present(self):
        manifest = json.loads((ROOT / "docs/provenance/seed-manifest.json").read_text(encoding="utf-8"))
        self.assertGreater(len(manifest), 1300)
        self.assertEqual([rel for rel in manifest if not (ROOT / rel).is_file()], [])

    def test_data_packs_are_byte_identical_to_the_seed(self):
        manifest = json.loads((ROOT / "docs/provenance/seed-manifest.json").read_text(encoding="utf-8"))
        packs = {rel: h for rel, h in manifest.items() if rel.startswith("public/data/")}
        self.assertEqual(len(packs), 7)
        for rel, expected in packs.items():
            self.assertEqual(hashlib.sha256((ROOT / rel).read_bytes()).hexdigest(), expected, rel)

    def test_this_repos_design_documents_survive(self):
        self.assertTrue((ROOT / "docs/superpowers/specs/2026-11-14-capraz-final-integration-design.md").is_file())
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `python -m unittest tests_repo.test_seed -v`
Expected: FAIL, `seed.json` not found.

- [ ] **Step 3: Copy the snapshot**

In a separate directory, check out the source at the pinned commit. Generate `seed-manifest.json` from
it. Copy every tracked file with `git -C <src> archive <commit> | tar -x -C <repo root>`. Do not copy
`.git`. Write `seed.json` with `source_repo`, `source_branch`, `source_commit`, `seeded_on` (the execution date),
`inherited_failures: []`, `verified_files` (the count of files whose checksum matched the source right
after copying; later plans edit seeded files, so the lasting test checks presence and the data packs) and `"note": "Snapshot copy; history remains in the source repository."`.

- [ ] **Step 4: Run every inherited suite**

Run: `python -m pip install -r pipeline/requirements.txt`
Run: `python -m unittest tests_repo.test_seed -v` — expected PASS.
Run: `cd pipeline && python -m unittest discover -s tests -v` — expected PASS.
Run: `python -m unittest biasguard.test_news -v` — expected PASS.
Run: `node --test site/tests/logic.test.cjs` — expected PASS.
If any inherited test fails, add its name to `inherited_failures` and report it; do not change it here.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "chore: seed from caprazmansetnov26@49b60bc"
```

---

### Task 2: Run every existing suite in CI

**Files:**
- Modify: `.github/workflows/checks.yml`
- Test: `tests_repo/test_ci.py`

**Interfaces:**
- Produces: jobs `pipeline` (unchanged), `biasguard`, `site-logic`, `repo`, each with
  `timeout-minutes: 10`.
  | job | command |
  |---|---|
  | `biasguard` | `python -m unittest biasguard.test_news -v` |
  | `site-logic` | `node --test site/tests/logic.test.cjs` |
  | `repo` | `python -m unittest discover -s tests_repo -t . -v` |

- [ ] **Step 1: Write the failing test**

```python
WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/checks.yml"

def test_every_suite_has_a_ci_step(self):
    text = WORKFLOW.read_text(encoding="utf-8")
    for command in ("python -m unittest discover -s tests -v",
                    "python -m unittest biasguard.test_news -v",
                    "node --test site/tests/logic.test.cjs",
                    "python -m unittest discover -s tests_repo -t . -v"):
        self.assertIn(command, text, command)

def test_workflow_is_read_only_and_secret_free(self):
    text = WORKFLOW.read_text(encoding="utf-8")
    self.assertIn("contents: read", text)
    self.assertNotIn("secrets.", text)
```

- [ ] **Step 2: Run and confirm failure** — `python -m unittest tests_repo.test_ci -v`.
- [ ] **Step 3: Add the three jobs.**
- [ ] **Step 4: Run and confirm pass; run all four commands locally and note each test count in the commit message.**
- [ ] **Step 5: Commit and push**

```bash
git commit -am "ci: run biasguard, site logic and repo tests"
git push -u origin claude/zen-ptolemy-7bvru2
```

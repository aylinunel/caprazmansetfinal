# Claude Code Controls Implementation Plan — ON HOLD

> **Do not execute.** On 14 November 2026 the owner asked to skip this part: the source report was
> written against the old `caprazmanset-oct26` codebase, and an updated version for the November
> repository is coming. This draft is kept only as a starting point for that rewrite. Task 1 (seeding)
> has moved to `../2026-11-14-foundation.md`; ignore the copy below.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Seed `caprazmansetfinal` from Çapraz Manşet 8.1 and add a safety guard, an explicit check runner and a read-only reviewer that fit this codebase.

**Architecture:** The 8.1 tree is copied in one attributed commit. A single check contract module is the source of truth for which commands are routine; the guard (a pure classifier behind a `PreToolUse` hook) and the plan-first check runner both import it. A no-shell reviewer agent carries this repo's analysis contracts.

**Tech Stack:** Python 3.12 standard library, `unittest`, Node 22 (`node --test`), GitHub Actions, Claude Code hooks/skills/agents.

**Spec:** `docs/superpowers/specs/2026-11-14-capraz-final-integration-design.md`

## Global Constraints

- Source snapshot: `aylinunel/caprazmansetnov26` @ `49b60bc4fd0407f8f979c08cd7e5ab0641ad040d`.
- New Python code uses the standard library only. No new runtime dependencies in this plan.
- Tests are `unittest`, runnable offline, with no network and no real credentials. Fake secrets only.
- Guard outcomes are exactly `deny`, `ask`, `normal`. `normal` adds no decision; it is not approval.
- The guard never executes, expands or shells out the command it classifies.
- The runner never installs a package and never edits a source file.
- Hook, skill and agent frontmatter must be checked against the current Claude Code documentation at
  execution time (`https://code.claude.com/docs/en/hooks`, `/skills`, `/sub-agents`). The source report
  states `onFailure: "block"` needs Claude Code v2.1.295 or later; confirm before relying on it.
- Develop on branch `claude/zen-ptolemy-7bvru2`. No pull request unless the owner asks.
- Follow the owner's standing instructions: `ponytail` and `anthropic-skills:karpathy-guidelines` on
  every coding task.

## Review Focus

1. A path that reaches a credential through `..`, a symlink or mixed case (`.ENV`) → deny, same as the
   plain path. (Task 3)
2. A shell line that hides a consequential command after `;`, `&&`, `|`, `$(…)` or backticks → ask,
   never normal. (Task 4)
3. Hook input that is empty, not JSON, over the size cap or missing `tool_input` → the hook exits
   non-zero with a generic message, so the tool call is blocked. (Task 5)
4. A change set containing a deleted workflow or a deleted test file → the runner plans without trying
   to open or run the deleted path. (Task 7)
5. A check that exceeds its timeout or whose executable is missing → reported `incomplete`, never
   `passed` and never `failed`. (Task 8)

---

### Task 1: Seed the repository from 8.1

**Files:**
- Create: the full tree of the source snapshot at the repo root
- Create: `docs/provenance/seed.json`
- Create: `tests_repo/test_seed.py`, `tests_repo/__init__.py`

**Interfaces:**
- Produces: the existing commands, unchanged:
  `cd pipeline && python -m unittest discover -s tests -v`,
  `python -m unittest biasguard.test_news -v`, `node --test site/tests/logic.test.cjs`.

- [ ] **Step 1: Write the failing test**

```python
# tests_repo/test_seed.py
import json, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

class SeedTest(unittest.TestCase):
    def test_provenance_names_the_source_commit(self):
        seed = json.loads((ROOT / "docs/provenance/seed.json").read_text(encoding="utf-8"))
        self.assertEqual(seed["source_repo"], "aylinunel/caprazmansetnov26")
        self.assertEqual(seed["source_commit"], "49b60bc4fd0407f8f979c08cd7e5ab0641ad040d")
        self.assertEqual(seed["seeded_on"], "2026-11-14")

    def test_seeded_packages_are_present(self):
        for rel in ("biasguard/engine.py", "pipeline/capraz_pipeline/build.py",
                    "site/js/v7/logic.js", "public/data/core.bin", "data/reference/registry.json"):
            self.assertTrue((ROOT / rel).is_file(), rel)
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `python -m unittest tests_repo.test_seed -v`
Expected: FAIL, `seed.json` not found.

- [ ] **Step 3: Copy the snapshot**

Check out the source at the pinned commit in a separate directory and copy every tracked file
(`git -C <src> archive 49b60bc5 | tar -x -C <repo root>`). Do not copy `.git`. Keep
`docs/superpowers/` files already in this repo. Write `docs/provenance/seed.json` with the three keys
above plus `"note": "Snapshot copy; history remains in the source repository."`.

- [ ] **Step 4: Run every inherited suite**

Run: `python -m pip install -r pipeline/requirements.txt`
Run: `python -m unittest tests_repo.test_seed -v` — expected PASS.
Run: `cd pipeline && python -m unittest discover -s tests -v` — expected PASS.
Run: `python -m unittest biasguard.test_news -v` — expected PASS.
Run: `node --test site/tests/logic.test.cjs` — expected PASS.
Record any inherited failure by name in the commit message; do not fix it in this task.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "chore: seed from caprazmansetnov26@49b60bc"
```

---

### Task 2: The check contract

**Files:**
- Create: `scripts/__init__.py`, `scripts/check_contract.py`
- Test: `tests_repo/test_check_contract.py`

**Interfaces:**
- Produces:
  ```python
  @dataclass(frozen=True)
  class Check:
      id: str                    # "pipeline", "biasguard", "site-logic", "repo", "lab", "mesa"
      argv: tuple[str, ...]      # fixed argument vector, no shell
      cwd: str                   # relative to repo root, "." for root
      timeout_seconds: int
      triggers: tuple[str, ...]  # path prefixes that select this check

  CHECKS: tuple[Check, ...]
  def routine_argvs() -> frozenset[tuple[str, ...]]   # argv of every check
  def select(changed_paths: Iterable[str]) -> tuple[Check, ...]
  ```
- Values:
  | id | argv | cwd | timeout | triggers |
  |---|---|---|---|---|
  | `pipeline` | `python -m unittest discover -s tests -v` | `pipeline` | 600 | `pipeline/`, `shared/analysis/`, `data/reference/` |
  | `biasguard` | `python -m unittest biasguard.test_news -v` | `.` | 300 | `biasguard/` |
  | `site-logic` | `node --test site/tests/logic.test.cjs` | `.` | 300 | `site/` |
  | `repo` | `python -m unittest discover -s tests_repo -t . -v` | `.` | 300 | `scripts/`, `.claude/`, `tests_repo/`, `.github/` |
  | `lab` | `python -m unittest discover -s validation/tests -t . -v` | `.` | 600 | `validation/biaslab/`, `validation/tests/`, `validation/reference/`, `biasguard/` |
  | `mesa` | `python -m pytest -q` | `validation/mesa_bias_expanded` | 1800 | `validation/mesa_bias_expanded/` |

- [ ] **Step 1: Write the failing tests**

```python
from scripts.check_contract import CHECKS, routine_argvs, select

def test_ids_are_unique_and_argvs_are_tuples(self):
    self.assertEqual(len({c.id for c in CHECKS}), len(CHECKS))
    self.assertTrue(all(isinstance(c.argv, tuple) and c.argv for c in CHECKS))

def test_select_by_prefix(self):
    self.assertEqual([c.id for c in select(["biasguard/engine.py"])], ["biasguard", "lab"])
    self.assertEqual([c.id for c in select(["site/js/v7/logic.js"])], ["site-logic"])

def test_unmatched_path_selects_nothing(self):
    self.assertEqual(select(["README.md"]), ())

def test_routine_argvs_equals_contract(self):
    self.assertEqual(routine_argvs(), frozenset(c.argv for c in CHECKS))
```

- [ ] **Step 2: Run and confirm failure** — `python -m unittest tests_repo.test_check_contract -v`, expected `ModuleNotFoundError`.
- [ ] **Step 3: Implement `scripts/check_contract.py`** with the table above; `select` preserves `CHECKS` order.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat: single check contract for guard and runner"`.

---

### Task 3: Guard classifier, file tools

**Files:**
- Create: `.claude/hooks/guard.py`
- Test: `tests_repo/test_guard_paths.py`

**Interfaces:**
- Produces:
  ```python
  @dataclass(frozen=True)
  class Decision:
      outcome: Literal["deny", "ask", "normal"]
      reason: str          # generic category, never echoes file content or full command

  def classify(tool_name: str, tool_input: dict, project_root: Path) -> Decision
  ```
- Path fields per tool: `Read`/`Edit`/`Write` → `file_path`; `NotebookEdit` → `notebook_path`.
- Rules, in this order: (1) credential pattern on the lexical path or the resolved path → `deny`;
  (2) resolved path outside `project_root` → `ask`; (3) `Edit`/`Write`/`NotebookEdit` to
  `public/index.html` → `deny`; (4) write to an ask-listed prefix from the spec's policy map → `ask`;
  (5) otherwise `normal`. `Read` of a non-credential project file is always `normal`.
- Credential patterns (case-insensitive basename): `.env`, `.env.*`, `*.pem`, `*.key`, `id_rsa*`,
  `id_ed25519*`, `.netrc`, `.npmrc`, `.pypirc`, `settings.local.json`; any path under `~/.ssh`,
  `~/.aws`, `~/.config/gh`. Exception: `.env.example` is not exempt (the report's permission note).
- The module is loaded in tests with `importlib.util.spec_from_file_location` because `.claude` is not a
  package. Put that loader in `tests_repo/_guard.py` as `load_guard()`.

- [ ] **Step 1: Write the failing tests** (each uses a `tempfile.TemporaryDirectory()` as `project_root`)

```python
def test_reading_env_is_denied(self):
    self.assertEqual(g.classify("Read", {"file_path": str(root / ".env")}, root).outcome, "deny")

def test_env_reached_through_dotdot_is_denied(self):
    self.assertEqual(g.classify("Read", {"file_path": str(root / "site/../.env")}, root).outcome, "deny")

def test_env_reached_through_symlink_is_denied(self):
    (root / ".env").write_text("FAKE=1"); (root / "notes.txt").symlink_to(root / ".env")
    self.assertEqual(g.classify("Read", {"file_path": str(root / "notes.txt")}, root).outcome, "deny")

def test_uppercase_env_is_denied(self):
    self.assertEqual(g.classify("Read", {"file_path": str(root / ".ENV")}, root).outcome, "deny")

def test_secret_outside_root_is_denied_not_asked(self):
    self.assertEqual(g.classify("Read", {"file_path": str(Path.home() / ".ssh/id_ed25519")}, root).outcome, "deny")

def test_other_path_outside_root_asks(self):
    self.assertEqual(g.classify("Read", {"file_path": "/etc/hostname"}, root).outcome, "ask")

def test_editing_generated_index_is_denied(self):
    self.assertEqual(g.classify("Edit", {"file_path": str(root / "public/index.html")}, root).outcome, "deny")

def test_ask_listed_writes(self):
    for rel in ("data/reference/registry.json", "runs/bg/x.json", "biasguard/data/cards.json",
                ".github/workflows/checks.yml", ".claude/hooks/guard.py", "scripts/safe_check.py",
                "pipeline/requirements.txt", "pipeline/capraz_pipeline/config.py",
                "validation/biaslab/crosswalk.json", "validation/mesa_bias_expanded/expanded_mesa.py"):
        self.assertEqual(g.classify("Write", {"file_path": str(root / rel)}, root).outcome, "ask", rel)

def test_ordinary_source_edit_is_normal(self):
    self.assertEqual(g.classify("Edit", {"file_path": str(root / "biasguard/engine.py")}, root).outcome, "normal")

def test_reading_an_ask_listed_file_is_normal(self):
    self.assertEqual(g.classify("Read", {"file_path": str(root / "data/reference/registry.json")}, root).outcome, "normal")

def test_reason_never_contains_the_path(self):
    d = g.classify("Read", {"file_path": str(root / ".env")}, root)
    self.assertNotIn(".env", d.reason)
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement `classify` for the four file tools.** Resolve with `Path.resolve(strict=False)`; check patterns on both the lexical and the resolved path.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat: guard classifier for file tools"`.

---

### Task 4: Guard classifier, shell commands

**Files:**
- Modify: `.claude/hooks/guard.py`
- Test: `tests_repo/test_guard_shell.py`

**Interfaces:**
- Consumes: `scripts.check_contract.routine_argvs()`.
- Produces: `classify("Bash", {"command": str}, root)` and `classify("PowerShell", …)`.
- Rules: `PowerShell` → `deny`. For `Bash`: split with `shlex.split`; a parse error → `ask`. If the raw
  string contains any of `;`, `&&`, `||`, `|`, `` ` ``, `$(`, `>`, `<`, or a newline → `ask`. If any
  token matches a credential pattern → `deny`. A routine argv from the check contract is `normal` only when the
  working directory (`tool_input["cwd"]`, default the project root) is that check's `cwd`; the form
  `cd <dir> && …` is not accepted because it contains `&&`. Also `normal`: `git status`, `git log …`, `git -c core.pager=cat diff --no-ext-diff
  --no-textconv …`, `ls …`, `pwd`. Plain `git diff` → `ask`. Everything else → `ask`.

- [ ] **Step 1: Write the failing tests**

```python
def test_powershell_is_denied(self): ...  # outcome == "deny"

def test_every_contract_argv_is_normal(self):
    for check in CHECKS:
        cmd = " ".join(check.argv)
        d = g.classify("Bash", {"command": cmd, "cwd": str(root / check.cwd)}, root)
        self.assertEqual(d.outcome, "normal", check.id)

def test_consequential_commands_ask(self):
    for cmd in ("python -m capraz_pipeline build", "python -m capraz_pipeline ingest --from x",
                "python -m biasguard.news apply --run runs/bg --out o.json",
                "git push -u origin main", "pip install mesa", "rm -rf runs", "curl https://example.com",
                "git diff", "some-unknown-tool"):
        self.assertEqual(g.classify("Bash", {"command": cmd}, root).outcome, "ask", cmd)

def test_chained_and_substituted_commands_ask(self):
    for cmd in ("ls; rm -rf runs", "ls && git push", "ls | sh", "echo $(cat x)", "ls `id`", "ls > out.txt"):
        self.assertEqual(g.classify("Bash", {"command": cmd}, root).outcome, "ask", cmd)

def test_shell_reading_a_credential_is_denied(self):
    self.assertEqual(g.classify("Bash", {"command": "cat .env"}, root).outcome, "deny")

def test_hardened_git_diff_is_normal(self):
    cmd = "git -c core.pager=cat diff --no-ext-diff --no-textconv HEAD"
    self.assertEqual(g.classify("Bash", {"command": cmd}, root).outcome, "normal")

def test_unbalanced_quote_asks(self):
    self.assertEqual(g.classify("Bash", {"command": "echo 'x"}, root).outcome, "ask")
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement the Bash and PowerShell branches.**
- [ ] **Step 4: Run both guard test files and confirm pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat: guard classifier for shell commands"`.

---

### Task 5: Hook adapter and registration

**Files:**
- Modify: `.claude/hooks/guard.py` (add `main()`)
- Create: `.claude/settings.json`
- Test: `tests_repo/test_guard_hook.py`

**Interfaces:**
- Produces: `python3 .claude/hooks/guard.py` reads one JSON object from stdin with `tool_name`,
  `tool_input`, optional `cwd`; `CLAUDE_PROJECT_DIR` gives the root. Output for `deny`/`ask` is the
  `PreToolUse` decision JSON in the shape the current hooks documentation specifies
  (`hookSpecificOutput.permissionDecision` = `"deny"` or `"ask"` with `permissionDecisionReason`),
  exit 0. For `normal`: no output, exit 0. Any error: one generic line on stderr, exit 2.
- Input cap: 1,000,000 bytes.
- `.claude/settings.json` registers the hook exactly as in the report's Step 3 fragment: matcher
  `Read|Edit|Write|NotebookEdit|Bash|PowerShell`, `command: "python3"`,
  `args: ["${CLAUDE_PROJECT_DIR}/.claude/hooks/guard.py"]`, `timeout: 5`, `onFailure: "block"`.

- [ ] **Step 1: Write the failing tests** (run the script with `subprocess.run`, `input=…`)

```python
def test_deny_emits_decision_json(self):
    out = run({"tool_name": "Read", "tool_input": {"file_path": ".env"}})
    self.assertEqual(out.returncode, 0)
    self.assertEqual(json.loads(out.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

def test_normal_emits_nothing(self):
    out = run({"tool_name": "Read", "tool_input": {"file_path": "README.md"}})
    self.assertEqual((out.returncode, out.stdout), (0, ""))

def test_bad_input_blocks(self):
    for raw in ("", "not json", "[]", json.dumps({"tool_name": "Read"}), "x" * 1_000_001):
        out = run_raw(raw)
        self.assertEqual(out.returncode, 2, raw[:20])
        self.assertNotIn("Traceback", out.stderr)

def test_settings_registers_blocking_guard(self):
    hook = json.loads(Path(".claude/settings.json").read_text())["hooks"]["PreToolUse"][0]
    self.assertEqual(hook["matcher"], "Read|Edit|Write|NotebookEdit|Bash|PowerShell")
    self.assertEqual(hook["hooks"][0]["onFailure"], "block")
    self.assertEqual(hook["hooks"][0]["timeout"], 5)
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Read the current hooks documentation**, confirm the decision JSON shape, the `args`
  exec form and `onFailure`. If any differs from this plan, follow the documentation and update the
  tests in this task to match before implementing.
- [ ] **Step 4: Implement `main()` and write `.claude/settings.json`.**
- [ ] **Step 5: Run and confirm pass.**
- [ ] **Step 6: Runtime check in a throwaway session.** Start Claude Code in a disposable clone and
  record in `docs/provenance/guard-runtime-check.md` what happened for: reading `.env` (blocked),
  `git push` (prompt), a routine check (no prompt), and the hook file renamed away (tool call blocked).
  State the Claude Code version. If "ask" stalls an unattended cloud session, record that and stop;
  the owner decides whether unknown commands ask or pass in that environment.
- [ ] **Step 7: Commit** — `git commit -m "feat: register blocking PreToolUse guard"`.

---

### Task 6: Runner, change set and credential refusal

**Files:**
- Create: `scripts/safe_check.py`
- Test: `tests_repo/test_safe_check_plan.py`

**Interfaces:**
- Produces:
  ```python
  GIT = ("git", "-c", "core.pager=cat", "-c", "diff.external=", "-c", "core.fsmonitor=false")

  @dataclass(frozen=True)
  class ChangeSet:
      base: str
      changed: tuple[str, ...]     # tracked, still present
      deleted: tuple[str, ...]
      untracked: tuple[str, ...]   # not ignored

  class CredentialPresent(Exception): ...   # message lists nothing but a count

  def change_set(repo: Path, base: str) -> ChangeSet
  def refuse_credentials(cs: ChangeSet) -> None          # raises CredentialPresent
  def fingerprint(repo: Path, cs: ChangeSet) -> str      # sha256 over (path, content sha) of changed+untracked
  ```
- `change_set` runs `GIT + ("diff", "--no-ext-diff", "--no-textconv", "--name-status", base)` and
  `GIT + ("ls-files", "--others", "--exclude-standard")`. It compares directly with `base`; it does not
  compute a merge-base.
- `refuse_credentials` uses the guard's credential patterns (import the guard through the same loader)
  and must be called before `fingerprint`.

- [ ] **Step 1: Write the failing tests** (each builds a temporary Git repo)

```python
def test_change_set_separates_deleted_and_untracked(self): ...
    # commit a.py, b.yml; delete b.yml, edit a.py, add c.py  →
    # changed == ("a.py",), deleted == ("b.yml",), untracked == ("c.py",)

def test_credential_in_change_set_is_refused_before_any_read(self):
    (repo / ".env").write_text("FAKE=1")
    cs = change_set(repo, "HEAD")
    with mock.patch("builtins.open", side_effect=AssertionError("opened a file")):
        with self.assertRaises(CredentialPresent):
            refuse_credentials(cs)

def test_fingerprint_changes_when_content_changes(self): ...
def test_fingerprint_ignores_deleted_paths(self): ...
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement the three functions.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat: check runner change set with credential refusal"`.

---

### Task 7: Runner, planning

**Files:**
- Modify: `scripts/safe_check.py`
- Test: `tests_repo/test_safe_check_plan.py`

**Interfaces:**
- Consumes: `check_contract.select`, `ChangeSet`.
- Produces:
  ```python
  def plan(repo: Path, base: str) -> dict
  ```
  returning
  `{"base", "mode": "plan", "checks": [{"id", "argv", "cwd", "timeout_seconds"}], "skipped":
  [{"id", "reason"}], "deleted_in_scope": [...], "fingerprint", "observed": None, "limits": LIMITS}`.
  Selection uses `changed + deleted + untracked`, so a deletion still selects its check; no deleted path
  is ever opened. `LIMITS` is a constant list of the five sentences in the spec's correction table rows
  4 and 5, starting "Fingerprint covers the selected change set only".
- CLI: `python3 scripts/safe_check.py --base <rev>` prints the plan as JSON and exits 0; exits 3 on
  `CredentialPresent`.

- [ ] **Step 1: Write the failing tests**

```python
def test_plan_is_the_default_and_runs_nothing(self):
    with mock.patch("subprocess.run", wraps=subprocess.run) as run:
        p = plan(repo, "HEAD")
    self.assertEqual(p["mode"], "plan"); self.assertIsNone(p["observed"])
    self.assertTrue(all(call.args[0][0] == "git" for call in run.call_args_list))

def test_deleted_workflow_stays_in_scope_without_being_opened(self):
    # delete .github/workflows/checks.yml
    p = plan(repo, "HEAD")
    self.assertIn(".github/workflows/checks.yml", p["deleted_in_scope"])
    self.assertIn("repo", [c["id"] for c in p["checks"]])

def test_unselected_checks_are_listed_as_skipped(self):
    # change only site/js/v7/logic.js
    self.assertIn({"id": "pipeline", "reason": "no changed path matches"}, plan(repo, "HEAD")["skipped"])

def test_cli_exits_3_when_a_credential_is_present(self): ...
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement `plan` and the CLI.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat: plan-first check runner"`.

---

### Task 8: Runner, execution

**Files:**
- Modify: `scripts/safe_check.py`
- Test: `tests_repo/test_safe_check_run.py`

**Interfaces:**
- Produces: `def run(repo: Path, base: str, confirm_isolated: bool) -> dict` and CLI flags `--run`,
  `--confirm-isolated`, `--report <new file>`.
- `--run` without `--confirm-isolated` → exit 4, nothing executed. The report carries
  `"isolation": "human attestation only; no sandbox is enforced"`.
- Each check runs with `subprocess.run(argv, cwd=…, shell=False, timeout=…, stdout=DEVNULL,
  stderr=DEVNULL)`. Result per check: `passed` (exit 0), `failed` (non-zero exit), `incomplete`
  (timeout, `FileNotFoundError`, or any other launch error).
- After the checks, `fingerprint` is recomputed; a difference sets `"workspace_changed": true` and the
  overall result is `incomplete`.
- Overall: `passed` only if every selected check passed and the workspace is unchanged; `failed` if any
  check failed and none is incomplete; otherwise `incomplete`. Exit codes: 0 passed, 1 failed, 2 incomplete.
- `--report` refuses an existing path and any path not ignored by Git (exit 5).

- [ ] **Step 1: Write the failing tests** (patch `check_contract.CHECKS` with fixture checks that run
  `python -c …`)

```python
def test_run_requires_confirmation(self): ...           # exit 4, no subprocess for checks
def test_all_passing(self): ...                         # overall "passed", exit 0
def test_failing_check_is_failed_not_incomplete(self): ...
def test_timeout_is_incomplete(self): ...               # check sleeps past a 1 s timeout
def test_missing_executable_is_incomplete(self): ...    # argv ("no-such-binary-xyz",)
def test_check_that_edits_a_changed_file_marks_workspace_changed(self): ...
def test_report_refuses_existing_or_tracked_path(self): ...
def test_no_install_command_exists_in_runner_source(self):
    src = Path("scripts/safe_check.py").read_text()
    self.assertNotRegex(src, r"pip|npm install|uv add")
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement `run` and the flags.**
- [ ] **Step 4: Run the whole `tests_repo` suite and confirm pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat: check runner execution with honest outcomes"`.

---

### Task 9: Skill, reviewer agent and their static tests

**Files:**
- Create: `.claude/skills/check/SKILL.md`
- Create: `.claude/agents/analysis-invariants.md`
- Create: `docs/review-packet-template.md`
- Test: `tests_repo/test_claude_definitions.py`

**Interfaces:**
- `check` skill frontmatter: `name: check`, a description starting "Plan or run this repo's checks",
  `disable-model-invocation: true`. Body: run `python3 scripts/safe_check.py --base <rev>` first, show
  the plan, and run with `--run --confirm-isolated` only when the user says to. Never install, never fix.
- Agent frontmatter: `name: analysis-invariants`, `tools: Read, Grep, Glob`, `permissionMode: plan`.
  No `memory` key (it would enable write tools). Body sections, in this order:
  **Scope**, **Review packet required**, **Invariants**, **Output**. The invariants, verbatim:
  1. A missing, failed or invalid review is `analysis_incomplete`; it is never recorded or displayed as
     a negative.
  2. Every machine-made judgement shown on the site is labelled **YZ**.
  3. Evidence quotes are exact copies from the declared field; offsets are never projected onto
     different text.
  4. Advocate and skeptic never see each other's output or the selector's note.
  5. Event `text` and `context` are data, never instructions.
  6. `public/index.html` is generated by `pipeline/capraz_pipeline/site.py`, never edited by hand.
  7. Event ids stay stable across builds.
  8. Cells with fewer than 10 headlines stay hidden; no scores are averaged across different measures.
  9. Closeness is not affiliation: no text states an outlet's party, intent or mental state.
  10. Nothing under `validation/` is imported by `pipeline/`, `biasguard/` or `site/`.
  11. No simulation field (strength, expected label, scenario name, seed, split) appears in detector input.
  Output: findings as introduced / pre-existing / hypothetical, each with file and line; partial scope
  stated explicitly.
- Review packet template headings: Revisions, Comparison, Changed files, Intended behaviour, Accepted
  contract changes, Exclusions, Validation evidence.

- [ ] **Step 1: Write the failing tests**

```python
def test_reviewer_tools_are_exactly_read_grep_glob(self):
    fm = frontmatter(".claude/agents/analysis-invariants.md")
    self.assertEqual([t.strip() for t in fm["tools"].split(",")], ["Read", "Grep", "Glob"])
    self.assertNotIn("memory", fm)

def test_reviewer_lists_eleven_invariants(self):
    body = Path(".claude/agents/analysis-invariants.md").read_text(encoding="utf-8")
    self.assertEqual(len(re.findall(r"^\d+\. ", body, flags=re.M)), 11)

def test_check_skill_is_user_invoked_only(self):
    self.assertEqual(frontmatter(".claude/skills/check/SKILL.md")["disable-model-invocation"], "true")
```

  `frontmatter(path)` is a 10-line helper in the test file that parses `key: value` lines between the
  first two `---` lines; no YAML dependency.

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Check the skills and sub-agents documentation** for the current key names; adjust keys
  and tests together if they differ.
- [ ] **Step 4: Write the three files.**
- [ ] **Step 5: Run and confirm pass.**
- [ ] **Step 6: Commit** — `git commit -m "feat: check skill and analysis-invariants reviewer"`.

---

### Task 10: CI

**Files:**
- Modify: `.github/workflows/checks.yml`
- Test: `tests_repo/test_ci_matches_contract.py`

**Interfaces:**
- Consumes: `CHECKS`.
- The workflow keeps `permissions: contents: read`, `timeout-minutes` on every job, no secrets, and gains
  one job per check id `biasguard`, `site-logic`, `repo`. (`lab` and `mesa` jobs are added by Plan 2.)

- [ ] **Step 1: Write the failing test**

```python
def test_every_contract_check_except_lab_and_mesa_has_a_ci_step(self):
    text = Path(".github/workflows/checks.yml").read_text()
    for check in CHECKS:
        if check.id in ("lab", "mesa"):
            continue
        self.assertIn(" ".join(check.argv), text, check.id)

def test_workflow_is_read_only_and_secret_free(self):
    text = Path(".github/workflows/checks.yml").read_text()
    self.assertIn("contents: read", text); self.assertNotIn("secrets.", text)
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Add the three jobs.**
- [ ] **Step 4: Run the full `tests_repo` suite and all inherited suites; confirm pass.**
- [ ] **Step 5: Commit and push**

```bash
git commit -am "ci: run biasguard, site logic and repo control tests"
git push -u origin claude/zen-ptolemy-7bvru2
```

---

## Deferred from the source report

| Control | Decision | Reason |
|---|---|---|
| A04 formatting hook | Deferred | The repo has no formatter configuration; adding one reformats 8.1 and hides real diffs |
| A05 TypeScript LSP | Dropped | Four small `.ts` files, no TypeScript build |
| A06 compatibility reviewer | Deferred to after Plan 2 | Its contracts (pack format, event ids, Turkish scorer) are better written once the lab exists |
| A07 release preflight | Becomes the publication gate in Plan 3 | The release decision here is about labels, not deployment |
| A08–A10 MCPs and plugin | Dropped | Duplicate tools already available in the owner's sessions |

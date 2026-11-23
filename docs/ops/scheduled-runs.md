# Scheduled runs: daily data release, weekly AI review

Two scheduled Claude Code sessions keep Çapraz Manşet 9 current. Each starts fresh in the cloud environment, on
branch `claude/gallant-noether-sz2o7v`, and publishes to the Çapraz Manşet 9 artifact
(https://claude.ai/artifact/HqTtSNGaw4D4spWpFpB4rq). A run that fails a test commits and publishes nothing and
reports what failed.

## Setup (both runs)

1. Attach the collector repository `aylinunel/turkish-news-scraper` (read access) so its `backfill-data` branch can
   be fetched. No clone is needed: `capraz_pipeline.daily` fetches that branch itself.
2. Check out `claude/gallant-noether-sz2o7v` and pull it.
3. Install dependencies:

```bash
python -m pip install -r pipeline/requirements.txt -r biasguard/requirements.txt -r validation/requirements.txt
```

## Daily (rule-based)

1. Run the release. It takes about 35 minutes and ends with a JSON summary.

```bash
cd pipeline && python -m capraz_pipeline.daily
```

It ingests the collector through yesterday (Türkiye time), keeps every known event id, rebuilds every rule-based
analysis, keeps AI reviews only for events whose headlines and context are unchanged, recomputes AIX, the lens and
9'da yeni, and writes `public/` and `dist/artifact/`. Events without reviews show as not attempted until the weekly
run.

2. Test. Every line must pass:

```bash
python -m pytest -q validation/tests biasguard tests_repo
```

```bash
cd pipeline && python -m pytest -q tests
```

```bash
node site/tests/logic.test.cjs
```

```bash
node site/tests/smoke.cjs public /tmp/smoke
```

```bash
NODE_PATH=$(npm root -g) node site/tests/blind.cjs public /tmp/blind
```

3. Commit `public runs/bg9 runs/bgm9 data/reference docs/provenance/packs.json docs/build-report.json` (use
   `git add -A` on those paths: the run deletes outputs of changed events) with the message
   `daily: data through <until>`, and push to `claude/gallant-noether-sz2o7v`. Nothing changed: stop here.
4. Publish `dist/artifact/index.html` to the artifact URL, with `root: dist/artifact`, in several publishes
   (one publish takes at most 64 MB). First read the artifact with the Artifact tool (`action: "read"`). Send every
   file in `dist/artifact/data/`: a pack over 12 MB is written as a one-line index (`<pack>.bin.txt`) plus parts
   (`<pack>.bin.txt.0`, `.1`, …), and every part must be sent. Send the newest month's files first, then the older
   months, and `data/core.bin.txt` in the last publish, so the page never pairs new totals with old packs. Do not
   pass `capabilities` or `icon`; the stored ones carry over.
5. Report in a few lines: the day reached, headline and event counts, how many top events await review, and the
   test results.

## Weekly (AI review and Anlatı haritası), Saturday

Run the daily steps 1–2 first (fresh data). Then:

1. **BiasGuard.** Write tasks only for events without reviews, in the same event order for both passes. The media
   pass uses its run's own catalogue.

```bash
python - <<'EOF'
import json
from pathlib import Path
import biasguard.news as N
from biasguard.engine import BiasGuard
from biasguard.catalog import validate_cards
orig = N._inputs
N._inputs = lambda run: [i for i in orig(run) if not (run / "selections" / f"{i['event']}.json").exists()]
N.write_tasks(Path("runs/bg9"), "select", 10)
N.write_tasks(Path("runs/bgm9"), "select", 10, bg=BiasGuard(cards=validate_cards(json.loads(Path("runs/bgm9/catalog.json").read_text(encoding="utf-8")))))
EOF
```

   Clear old task folders first (`rm -rf runs/bg9/tasks runs/bgm9/tasks`). Dispatch one selector agent per batch
   with `runs/AGENT_SELECT9.md`. Then write review tasks the same way (`"review"`, filtering on
   `reviews/advocate/<event>.json`) and dispatch one advocate and one skeptic agent per batch with
   `runs/AGENT_REVIEW9.md`. Check every batch with `python runs/check_out.py`. If a usage limit stops agents,
   resume them later; never mark a missing review as done.

2. **Anlatı haritası.** Add the week that ended yesterday (Saturday–Friday) to `WEEKS` in
   `pipeline/capraz_pipeline/narratives.py`, with key `w<n+1>` and a Turkish label such as `"21–27 Kasım"`.
   Write its candidates with `python -m capraz_pipeline.narratives candidates --build <daily work dir>/build --out <tmp>`
   (the daily work dir is printed by the daily run; the default is under the system temp folder,
   `capraz-daily/build`). Append only the new week's rows to `runs/narr/candidates.json`, and write coding tasks
   for them with `capraz_pipeline.narratives.tasks` into `runs/narr<week>/tasks`. Dispatch one coding agent per
   batch with `runs/narr/PROMPT.md`; batch path and output path are as in `runs/narr12/CODER.md`. Check that each
   coded file has the four q texts and one row per outlet, then run
   `python -m capraz_pipeline.narratives finalize --out ../runs/narr`.

3. Rerun the daily release (step 1). The reviewed events now keep their reviews and the new week is merged. Then
   test, commit, push and publish as in daily steps 2–4, with message `weekly: AI review and Anlatı <week>`. The
   commit also takes the narrative work, or the next fresh session loses the new week:
   `git add -A pipeline/capraz_pipeline/narratives.py data/reference/narratives-7.json runs/narr runs/narr*`.

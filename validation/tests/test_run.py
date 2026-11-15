import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from biasguard import news
from biasguard.engine import BiasGuard
from validation.biaslab import configs
from validation.biaslab.renderer import assert_no_leak
from validation.biaslab.run import build, score, tasks
from validation.tests._stub import assessment


def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class RunTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.master = tempfile.TemporaryDirectory()
        build(Path(cls.master.name) / "lab", seed=42, salt="fixed-salt")

    @classmethod
    def tearDownClass(cls):
        cls.master.cleanup()

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.run = Path(self.dir.name) / "lab"
        shutil.copytree(Path(self.master.name) / "lab", self.run)   # each test gets its own copy of one build
        self.inputs = jsonl(self.run / "inputs.jsonl")
        self.private = {r["case_id"]: r for r in jsonl(self.run / "private" / "cases.jsonl")}

    def tearDown(self):
        self.dir.cleanup()

    def test_build_writes_only_text_and_context_for_the_detector(self):
        self.assertTrue(all(set(r) == {"event", "title", "outlets", "text", "context"} for r in self.inputs))
        self.assertTrue(all(re.fullmatch(r"c-[0-9a-f]{12}", r["event"]) for r in self.inputs))

    def test_private_records_are_separate_and_complete(self):
        self.assertEqual({r["event"] for r in self.inputs}, set(self.private))
        for p in self.private.values():
            self.assertTrue({"concept", "kind", "family_id", "split", "variant", "perturbation", "base_case_id"} <= set(p))

    def test_case_ids_are_unique(self):
        self.assertEqual(len({r["event"] for r in self.inputs}), len(self.inputs))

    def test_all_variants_of_a_family_share_a_split(self):
        by_family = {}
        for p in self.private.values():
            by_family.setdefault(p["family_id"], set()).add(p["split"])
        self.assertGreaterEqual(len(by_family), 5)
        self.assertTrue(all(len(s) == 1 for s in by_family.values()))

    def test_both_pilot_concepts_and_all_kinds_are_present(self):
        seen = {(p["concept"], p["kind"]) for p in self.private.values()}
        self.assertIn(("selective_statistics", "missing_context"), seen)
        self.assertIn(("illusory_truth_effect", "boundary_control"), seen)
        self.assertIn(("selective_statistics", "inactive_control"), seen)

    def test_perturbed_cases_point_at_their_base_case(self):
        perturbed = [p for p in self.private.values() if p["perturbation"] != "none"]
        self.assertTrue(perturbed)
        self.assertTrue(all(p["base_case_id"] in self.private for p in perturbed))

    def test_offline_score_reports_everything_unassessed_or_ineligible(self):
        report, code = score(self.run, mode="offline")
        self.assertEqual(set(report["baseline"]["counts_by_status"]), {"unassessed", "ineligible"})
        self.assertEqual(set(report["candidate"]["counts_by_status"]), {"unassessed"})
        # Unassessed positives are end-to-end misses; with no decisions, conditional recall is not estimable.
        self.assertEqual(report["baseline"]["end_to_end_recall"]["value"], 0.0)
        self.assertIsNone(report["baseline"]["conditional_recall"]["value"])
        self.assertIsNone(report["baseline"]["strict_precision"]["value"])
        self.assertEqual(report["scope"], "synthetic, implementation-authored cases; not detector accuracy")
        self.assertEqual(code, 0)

    def test_score_with_no_reviewer_files_is_error_and_exits_2(self):
        report, code = score(self.run, mode="ai")
        self.assertEqual(set(report["candidate"]["counts_by_status"]), {"error"})
        self.assertEqual(set(report["baseline"]["counts_by_status"]), {"error", "ineligible"})
        self.assertEqual(code, 2)

    def test_task_batches_pass_the_leak_check(self):
        paths = tasks(self.run, "candidate", "select", batch=10)
        self.assertTrue(paths)
        for p in paths:
            events = json.loads(p.read_text(encoding="utf-8"))["events"]
            for concept in ("selective_statistics", "illusory_truth_effect"):
                assert_no_leak({"events": events, "file": p.name}, concept, None, "no-family")

    def test_score_with_stub_reviewer_files_end_to_end(self):
        case = next(c for c, p in self.private.items() if p["concept"] == "selective_statistics"
                    and p["kind"] == "positive" and p["variant"] == 0 and p["perturbation"] == "none")
        item = next(r for r in self.inputs if r["event"] == case)
        tasks(self.run, "candidate", "select", batch=10)
        cfg = self.run / "candidate"
        cards = configs.catalog("candidate")
        bg = BiasGuard(cards=cards)
        (cfg / "selections").mkdir(parents=True, exist_ok=True)
        (cfg / "selections" / f"{case}.json").write_text(json.dumps(
            {"candidate_ids": ["selective-statistics"], "selection_uncertainty": [], "selection_note": ""}))
        ids = news.selected_cards(bg, cfg, item)
        by_id = {c["id"]: c for c in cards}
        quote = item["text"].split("] ", 1)[1].split(" — ")[0]
        for role in ("advocate", "skeptic"):
            (cfg / "reviews" / role).mkdir(parents=True, exist_ok=True)
            out = [assessment(by_id[i], "supported" if i == "selective-statistics" else "not_supported",
                              quote if i == "selective-statistics" else "") for i in ids]
            (cfg / "reviews" / role / f"{case}.json").write_text(
                json.dumps({"role": role, "assessments": out}, ensure_ascii=False))
        report, code = score(self.run, mode="ai")
        ledger = jsonl(self.run / "ledger.jsonl")
        status = {(a["config"], a["case_id"]): a["status"] for a in ledger if a["attempt"] == 1}
        self.assertEqual(status[("candidate", case)], "supported")
        self.assertEqual(status[("baseline", case)], "ineligible")
        self.assertEqual(report["candidate"]["strict_precision"]["value"], 1.0)
        self.assertEqual(code, 2)   # every other case is still unreviewed
        self.assertTrue((self.run / "report.json").is_file())

    def test_rescoring_keeps_first_attempts(self):
        score(self.run, mode="ai")
        report, _ = score(self.run, mode="offline")
        self.assertIn("error", report["candidate"]["counts_by_status"])

    def test_build_refuses_to_overwrite_an_existing_run(self):
        with self.assertRaises(FileExistsError):
            build(self.run, seed=42)


if __name__ == "__main__":
    unittest.main()

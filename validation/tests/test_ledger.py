import tempfile
import unittest
from pathlib import Path

from validation.biaslab.adapter import Assessment, Span
from validation.biaslab.ledger import Ledger

AUDIT = {"card_hash_sha256": "h", "prompts_version": "p"}


def a(status):
    return Assessment("card-x", status, "r", (Span("text", "q", 0, 1),), "review_complete", None)


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name) / "ledger.jsonl"

    def tearDown(self):
        self.dir.cleanup()

    def test_second_write_is_kept_and_numbered(self):
        led = Ledger(self.path)
        led.record("c-1", "baseline", a("error"), AUDIT)
        second = led.record("c-1", "baseline", a("supported"), AUDIT)
        self.assertEqual(second.attempt, 2)
        self.assertEqual(len(led.attempts()), 2)

    def test_first_attempt_is_the_scored_one(self):
        led = Ledger(self.path)
        led.record("c-1", "baseline", a("error"), AUDIT)
        led.record("c-1", "baseline", a("supported"), AUDIT)
        self.assertEqual(led.first_attempts("baseline")["c-1"].status, "error")

    def test_configs_are_numbered_separately(self):
        led = Ledger(self.path)
        led.record("c-1", "baseline", a("error"), AUDIT)
        self.assertEqual(led.record("c-1", "candidate", a("supported"), AUDIT).attempt, 1)
        self.assertEqual(set(led.first_attempts("candidate")), {"c-1"})

    def test_ledger_survives_reopen(self):
        Ledger(self.path).record("c-1", "baseline", a("supported"), AUDIT)
        again = Ledger(self.path)
        self.assertEqual(again.attempts()[0].spans[0]["quote"], "q")
        self.assertEqual(again.record("c-1", "baseline", a("supported"), AUDIT).attempt, 2)

    def test_ledger_never_contains_private_keys(self):
        Ledger(self.path).record("c-1", "baseline", a("supported"), AUDIT)
        self.assertNotRegex(self.path.read_text(encoding="utf-8"), r"family|split|strength|expected|kind")

    def test_corrupt_line_raises_with_line_number(self):
        Ledger(self.path).record("c-1", "baseline", a("supported"), AUDIT)
        with self.path.open("a", encoding="utf-8") as f:
            f.write("{not json\n")
        with self.assertRaisesRegex(ValueError, "line 2"):
            Ledger(self.path).attempts()


if __name__ == "__main__":
    unittest.main()

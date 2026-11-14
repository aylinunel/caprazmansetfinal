import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/checks.yml"


class CiTest(unittest.TestCase):
    def test_every_suite_has_a_ci_step(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        for command in ("python -m unittest discover -s tests -v",
                        "python -m unittest biasguard.test_news -v",
                        "python -m unittest biasguard.test_routing -v",
                        "node --test site/tests/logic.test.cjs",
                        "python -m unittest discover -s tests_repo -t . -v",
                        "python -m unittest discover -s validation/tests -t . -v",
                        "python -m pytest -q"):
            self.assertIn(command, text, command)

    def test_workflow_is_read_only_and_secret_free(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("contents: read", text)
        self.assertNotIn("secrets.", text)


if __name__ == "__main__":
    unittest.main()

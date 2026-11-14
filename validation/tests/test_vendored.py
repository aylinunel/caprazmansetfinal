import hashlib
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "validation" / "mesa_bias_expanded"
EXCLUDED = ("results/sweep/", "results/sweep_first_attempt/", "results/pytest_results.xml")


class VendoredTest(unittest.TestCase):
    def test_every_vendored_file_matches_its_checksum(self):
        sums = json.loads((ROOT / "SHA256SUMS.json").read_text(encoding="utf-8"))
        kept = {p: h for p, h in sums.items() if not p.startswith(EXCLUDED)}
        self.assertGreater(len(kept), 400)
        for rel, expected in kept.items():
            self.assertEqual(hashlib.sha256((ROOT / rel).read_bytes()).hexdigest(), expected, rel)

    def test_scope_is_138_synthetic_only(self):
        meta = json.loads((ROOT / "runtime_metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["expected_new_plugins"], 138)
        self.assertIs(meta["empirically_validated"], False)

    def test_reference_adapter_smoke_tests_pass_against_the_vendored_package(self):
        out = subprocess.run([sys.executable, str(REPO / "validation/reference_adapter/reference_adapter.py")],
                             env={**os.environ, "MESA_BIAS_ROOT": str(ROOT)}, capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr[-400:])
        self.assertTrue(json.loads(out.stdout)["smoke_tests"].startswith("PASS"))


if __name__ == "__main__":
    unittest.main()

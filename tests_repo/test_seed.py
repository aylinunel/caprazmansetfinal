import hashlib
import json
import unittest
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
        # Checksums were verified for all files at seeding (seed.json: verified_files). Later work edits
        # seeded files on purpose, so the lasting check is that none has gone missing.
        manifest = json.loads((ROOT / "docs/provenance/seed-manifest.json").read_text(encoding="utf-8"))
        self.assertGreater(len(manifest), 1300)
        missing = [rel for rel in manifest if not (ROOT / rel).is_file()]
        self.assertEqual(missing, [])

    def test_data_packs_are_byte_identical_to_the_seed(self):
        manifest = json.loads((ROOT / "docs/provenance/seed-manifest.json").read_text(encoding="utf-8"))
        packs = {rel: h for rel, h in manifest.items() if rel.startswith("public/data/")}
        self.assertEqual(len(packs), 7)
        for rel, expected in packs.items():
            self.assertEqual(hashlib.sha256((ROOT / rel).read_bytes()).hexdigest(), expected, rel)

    def test_this_repos_design_documents_survive(self):
        self.assertTrue((ROOT / "docs/superpowers/specs/2026-11-14-capraz-final-integration-design.md").is_file())


if __name__ == "__main__":
    unittest.main()

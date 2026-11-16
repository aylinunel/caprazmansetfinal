import gzip
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

    def test_headline_and_lede_packs_are_byte_identical_to_the_seed(self):
        # core.bin is repacked when BiasGuard results change (python -m biasguard.news pack); the monthly
        # headline and lede packs only change with a full pipeline build. Since 8.2 a headline pack is split in
        # two (capraz_pipeline/urlpack.py): a-*.bin for startup and u-*.bin for URLs. Joined back in the seed's
        # field order they must give the seed's bytes exactly.
        manifest = json.loads((ROOT / "docs/provenance/seed-manifest.json").read_text(encoding="utf-8"))
        packs = {rel: h for rel, h in manifest.items()
                 if rel.startswith("public/data/") and not rel.endswith("core.bin")}
        self.assertEqual(len(packs), 6)
        for rel, expected in packs.items():
            path = ROOT / rel
            data = path.read_bytes()
            url_pack = path.with_name("u-" + path.name[2:])
            if path.name.startswith("a-") and url_pack.exists():
                slim, urls = (json.loads(gzip.decompress(p.read_bytes())) for p in (path, url_pack))
                joined = {"hosts": urls["hosts"]}
                for k, v in slim.items():
                    if k == "nu":
                        continue
                    joined[k] = v
                    if k == "t":
                        joined["h"], joined["u"] = urls["h"], urls["u"]
                data = gzip.compress(json.dumps(joined, ensure_ascii=False, separators=(",", ":")).encode(),
                                     compresslevel=9, mtime=0)
            self.assertEqual(hashlib.sha256(data).hexdigest(), expected, rel)

    def test_this_repos_design_documents_survive(self):
        self.assertTrue((ROOT / "docs/superpowers/specs/2026-11-14-capraz-final-integration-design.md").is_file())


if __name__ == "__main__":
    unittest.main()

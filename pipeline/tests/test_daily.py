import base64
import gzip
import tempfile
import unittest
from pathlib import Path

from capraz_pipeline import site
from capraz_pipeline.daily import same_case


class SameCaseTest(unittest.TestCase):
    def test_active_outlet_list_does_not_drop_a_review(self):
        ctx = "Olay: x\nKurumlar ve verilen yerleşimler: a: sol (40)\nOlayı vermeyen etkin kurumlar: "
        old = {"text": "[a · 10:00] Başlık", "context": ctx + "aydinlik"}
        self.assertTrue(same_case(old, {**old, "context": ctx + "aydinlik, birgun"}))
        self.assertFalse(same_case(old, {**old, "text": "[a · 10:00] Başka başlık"}))
        self.assertFalse(same_case(old, {**old, "context": old["context"].replace("sol (40)", "sağ (60)")}))


class ArtifactPartsTest(unittest.TestCase):
    def test_big_pack_is_split_into_parts_that_join_back(self):
        with tempfile.TemporaryDirectory() as d:
            data, out = Path(d) / "data", Path(d) / "art"
            data.mkdir()
            raw = gzip.compress(bytes(range(256)) * 2000)
            (data / "a-2026-12.bin").write_bytes(raw)
            old, site.PART = site.PART, 1000  # small parts so the test file stays small
            try:
                site.assemble(data, out, fragment=True)
            finally:
                site.PART = old
            idx = (out / "data" / "a-2026-12.bin.txt").read_text()
            n = int(idx.removeprefix("PARTS:"))
            joined = b"".join((out / "data" / f"a-2026-12.bin.txt.{i}").read_bytes() for i in range(n))
            self.assertGreater(n, 1)
            self.assertEqual(base64.b64decode(joined), raw)


if __name__ == "__main__":
    unittest.main()

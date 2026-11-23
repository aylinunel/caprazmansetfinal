import base64
import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from capraz_pipeline import daily, site
from capraz_pipeline.daily import check_no_loss, same_case

sys.path.insert(0, str(daily.REPO))  # biasguard lives at the repo root
import biasguard.news  # noqa: E402

CTX = "Olay: x\nKurumlar ve verilen yerleşimler: a: sol (40)\nOlayı vermeyen etkin kurumlar: "


def _pack(path: Path, n: int) -> None:
    path.write_bytes(gzip.compress(json.dumps({"i": list(range(n))}).encode()))


class SameCaseTest(unittest.TestCase):
    def test_active_outlet_list_does_not_drop_a_review(self):
        old = {"text": "[a · 10:00] Başlık", "context": CTX + "aydinlik"}
        self.assertTrue(same_case(old, {**old, "context": CTX + "aydinlik, birgun"}))
        self.assertFalse(same_case(old, {**old, "text": "[a · 10:00] Başka başlık"}))
        self.assertFalse(same_case(old, {**old, "context": old["context"].replace("sol (40)", "sağ (60)")}))


class NoLossTest(unittest.TestCase):
    def test_a_month_with_fewer_articles_stops_the_run(self):
        with tempfile.TemporaryDirectory() as d:
            live, build = Path(d) / "live", Path(d) / "build"
            live.mkdir(), build.mkdir()
            _pack(live / "a-2026-10.bin", 5), _pack(live / "a-2026-11.bin", 5)
            _pack(build / "a-2026-10.bin", 5), _pack(build / "a-2026-11.bin", 6), _pack(build / "a-2026-12.bin", 1)
            check_no_loss(live, build)  # growth and a new month pass
            _pack(build / "a-2026-10.bin", 4)
            with self.assertRaisesRegex(SystemExit, "a-2026-10.bin: 4 articles"):
                check_no_loss(live, build)
            (build / "a-2026-10.bin").unlink()
            with self.assertRaisesRegex(SystemExit, "a-2026-10.bin: 0 articles"):
                check_no_loss(live, build)


class RefreshRunsTest(unittest.TestCase):
    def test_only_unchanged_events_keep_their_agent_files(self):
        old = [{"event": e, "text": f"[a · 10:00] {e}", "context": CTX + "aydinlik"} for e in ("same", "moved", "gone")]
        new = [{**old[0], "context": CTX + "aydinlik, birgun"}, {**old[1], "text": "[a · 10:00] yeni"}]
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            for run, _ in daily.RUNS:
                r = repo / "runs" / run
                (r / "reviews" / "skeptic").mkdir(parents=True)
                (r / "inputs.jsonl").write_text("".join(json.dumps(x) + "\n" for x in old))
                for e in ("same", "moved", "gone"):
                    (r / "reviews" / "skeptic" / f"{e}.json").write_text("{}")
                (r / "explain").mkdir()
                (r / "explain" / "same__framing-effect.json").write_text("{}")
            with mock.patch.object(daily, "REPO", repo), mock.patch.object(biasguard.news, "event_inputs", lambda build, n: new):
                out = daily.refresh_runs(repo)
            r = repo / "runs" / "bg9"
            self.assertEqual(sorted(f.name for f in r.rglob("*.json")), ["same.json", "same__framing-effect.json"])
            self.assertEqual(out["bg9"], {"kept": 1, "to_review": 1, "files_removed": 2})
            self.assertEqual([json.loads(l)["event"] for l in (r / "inputs.jsonl").read_text().splitlines()], ["same", "moved"])


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

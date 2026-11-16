import json
import re
import unittest
from pathlib import Path

from capraz_pipeline.urlpack import NOTICE_URL, split

LAYER = Path(__file__).resolve().parents[2] / "site" / "js" / "turkish-layer.js"


class UrlPackTest(unittest.TestCase):
    def test_rules_match_the_site(self):
        js = LAYER.read_text(encoding="utf-8")
        site = [json.loads('"' + m + '"') for m in re.findall(r'noticeRules(?:V1)?: \{ url: "((?:[^"\\]|\\.)*)"', js)]
        self.assertEqual(site, NOTICE_URL)

    def test_split_moves_urls_and_flags_notices(self):
        pack = {"i": ["a", "b", "c"], "t": ["x", "y", "z"], "hosts": ["h.com"], "h": [0, 0, 0],
                "u": ["resmi-ilanlar/1", "haber/2", "ilan/3"]}
        slim, urls = split(pack)
        self.assertNotIn("u", slim)
        self.assertEqual(slim["t"], pack["t"])
        self.assertEqual(urls, {"i": pack["i"], "hosts": ["h.com"], "h": [0, 0, 0], "u": pack["u"]})
        # bit 1: current rule (/resmi-ilanlar/ and /ilan/ match), bit 2: V1 rule (resmi-ilan and /ilan/ match)
        self.assertEqual(slim["nu"], [3, 0, 3])


if __name__ == "__main__":
    unittest.main()

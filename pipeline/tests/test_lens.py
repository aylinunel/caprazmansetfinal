import json
import re
import unittest

from capraz_pipeline.config import REPO
from capraz_pipeline.lens import NOTICE_KEYWORDS, big_stories, confirmed_skips, feed_complete, group, is_notice_article, notice_events, season_days


class GroupTest(unittest.TestCase):
    def test_keywords_match_the_browser(self):
        js = (REPO / "site/js/turkish-layer.js").read_text(encoding="utf-8")
        block = re.search(r"noticeRules: \{ url: .*?keywords: (\[[^\]]*\])", js, re.S).group(1)
        self.assertEqual(json.loads(block), NOTICE_KEYWORDS)

    def test_notice_article_needs_all_capitals(self):
        self.assertTrue(is_notice_article({"t": "İSTANBUL 3. ASLİYE HUKUK MAHKEMESİ", "nu": 0}))
        self.assertFalse(is_notice_article({"t": "Mahkemesi kararını verdi", "nu": 0}))
        self.assertTrue(is_notice_article({"t": "Haber", "nu": 1}))

    def test_notice_events_and_season_days(self):
        core = {"E": [{"i": "e1", "a": ["x", "y"]}, {"i": "e2", "a": ["x", "z"]}],
                "meta": {"window": {"start": "2026-09-01T00:00:00.000Z", "end": "2026-09-03T23:59:00.000Z"}}}
        arts = {"x": {"t": "Haber", "nu": 1}, "y": {"t": "Haber", "nu": 1}, "z": {"t": "Haber", "nu": 0}}
        self.assertEqual(notice_events(core, arts), {"e1", "e2"})
        arts["z"]["nu"] = 0; arts["y"]["nu"] = 0
        self.assertEqual(notice_events(core, arts), {"e1", "e2"})  # exactly 0.5 counts
        arts["x"]["nu"] = 0
        self.assertEqual(notice_events(core, arts), set())
        self.assertEqual(season_days(core), ["2026-09-01", "2026-09-02", "2026-09-03"])

    def test_feed_complete(self):
        days = {f"d{i}": 20 + i for i in range(40)}           # its maximum (59) on 1 of 40 days
        self.assertTrue(feed_complete(days, 60)[0])
        capped = {f"d{i}": 6 for i in range(60)}
        ok, st = feed_complete(capped, 60)
        self.assertFalse(ok); self.assertEqual(st["at_max_share"], 1.0)

    def test_group_excludes_listed_and_part_season(self):
        core = {"S": [{"s": "sabah", "t": "print"}, {"s": "aa", "t": "web"}, {"s": "aksam", "t": "web"}],
                "meta": {"window": {"start": "2026-09-01T00:00:00.000Z", "end": "2026-09-10T23:59:00.000Z"}}}
        arts = {f"a{i}": {"s": "sabah", "d": f"2026-09-{1 + i:02d}T10:00"} for i in range(10)}
        arts |= {f"b{i}": {"s": "aa", "d": f"2026-09-{1 + i:02d}T10:00"} for i in range(10)}
        arts |= {"c0": {"s": "aksam", "d": "2026-09-01T10:00"}}
        g = group(core, arts, {"exclude": {"aa": "Haber ajansı: haberleri kurumlara dağıtıyor."}})
        self.assertEqual({k: v["lens"] for k, v in g.items()}, {"sabah": True, "aa": False, "aksam": False})
        self.assertEqual(g["aa"]["reason"], "Haber ajansı: haberleri kurumlara dağıtıyor.")
        self.assertEqual(g["aksam"]["reason"], "Yalnızca sezonun bir kısmında derlendi.")


if __name__ == "__main__":
    unittest.main()


class SkipTest(unittest.TestCase):
    def test_a_matching_headline_outside_the_event_is_not_a_skip(self):
        core = {"E": [{"i": "e1", "a": ["x1", "x2"], "s": ["sabah", "sozcu"], "f": "2026-09-01T10:00"}]}
        arts = {"x1": {"s": "sabah", "t": "Bakan istifa etti", "d": "2026-09-01T10:00"},
                "x2": {"s": "sozcu", "t": "Bakan istifa etti, yerine atama", "d": "2026-09-01T10:05"},
                "y1": {"s": "karar", "t": "Bakan istifa etti ve gitti", "d": "2026-09-01T12:00"},
                "z1": {"s": "birgun", "t": "Hava durumu yağmurlu", "d": "2026-09-01T12:00"}}
        stories = [{"event": "e1", "day": "2026-09-01", "active": ["sabah", "sozcu", "karar", "birgun"], "covered": ["sabah", "sozcu"]}]
        self.assertEqual(confirmed_skips(stories, core, arts, ["karar", "birgun"]), {"karar": set(), "birgun": {"e1"}})

    def test_big_story_needs_half_of_the_active_comparison_outlets(self):
        core = {"E": [{"i": "e1", "a": ["x1"], "f": "2026-09-01T10:00"}, {"i": "e2", "a": ["x2"], "f": "2026-09-01T11:00"}]}
        arts = {"x1": {"s": "a", "d": "2026-09-01T10:00"}, "x2": {"s": "a", "d": "2026-09-01T11:00"},
                "y": {"s": "b", "d": "2026-09-01T09:00"}, "z": {"s": "c", "d": "2026-09-01T09:00"}}
        g = {"a": {"lens": True}, "b": {"lens": True}, "c": {"lens": False}}
        got = big_stories(core, arts, g, {"e2"})
        self.assertEqual(got, [{"event": "e1", "day": "2026-09-01", "active": ["a", "b"], "covered": ["a"]}])

    def test_result_does_not_depend_on_the_other_outlets_in_the_call(self):
        core = {"E": [{"i": "e1", "a": ["x1", "x2"], "s": ["sabah", "sozcu"], "f": "2026-09-01T10:00"}]}
        arts = {"x1": {"s": "sabah", "t": "Bakan istifa etti", "d": "2026-09-01T10:00"},
                "x2": {"s": "sozcu", "t": "Bakan istifa etti, yerine atama", "d": "2026-09-01T10:05"},
                "y1": {"s": "karar", "t": "Bakan istifa etti ve gitti", "d": "2026-09-01T12:00"},
                "z1": {"s": "birgun", "t": "Hava durumu yağmurlu", "d": "2026-09-01T12:00"}}
        stories = [{"event": "e1", "day": "2026-09-01", "active": ["sabah", "sozcu", "karar", "birgun"], "covered": ["sabah", "sozcu"]}]
        for x in ("karar", "birgun"):
            y = "birgun" if x == "karar" else "karar"
            self.assertEqual(confirmed_skips(stories, core, arts, [x])[x], confirmed_skips(stories, core, arts, [x, y])[x])

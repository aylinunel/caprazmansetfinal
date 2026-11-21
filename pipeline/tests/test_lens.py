import json
import re
import unittest

from capraz_pipeline.config import REPO
from capraz_pipeline.lens import (NOTICE_KEYWORDS, big_stories, compute, confirmed_skips, distance, feed_complete, group,
                                  is_notice_article, notice_events, season_days, strata, verdict)


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


def small_fixture():
    """2 lens outlets covering the same 25 stories, one a day; "q" is never loaded, "o" always is."""
    core = {"S": [{"s": "o", "t": "print"}, {"s": "q", "t": "web"}],
            "TP": [{"k": "yargi", "n": "Yargı ve soruşturmalar"}],
            "meta": {"window": {"start": "2026-09-01T00:00:00.000Z", "end": "2026-09-25T23:59:00.000Z"}}, "E": []}
    arts = {}
    for i in range(25):
        day = f"2026-09-{1 + i:02d}"
        arts[f"o{i}"] = {"s": "o", "t": f"Olay {i} oldu", "d": f"{day}T10:00", "v": 30, "p": 1, "lv": 0, "nu": 0}
        arts[f"q{i}"] = {"s": "q", "t": f"Olay {i} yaşandı", "d": f"{day}T12:00", "v": 0, "p": 1, "lv": 0, "nu": 0}
        core["E"].append({"i": f"e{i}", "a": [f"o{i}", f"q{i}"], "s": ["o", "q"], "f": f"{day}T10:00", "tp": ["yargi"]})
    return core, arts, {"exclude": {}}


def complete_fixture():
    """small_fixture with complete feeds (20-44 headlines a day); "o" also has a bare-date copy of every story."""
    core, arts, groups = small_fixture()
    for i in range(25):
        day = f"2026-09-{1 + i:02d}"
        for s in ("o", "q"):
            for k in range(20 + i):
                arts[f"f{s}{i}-{k}"] = {"s": s, "t": f"Dolgu {s} {i} {k}", "d": f"{day}T08:00", "v": 0, "p": 0, "lv": None, "nu": 0}
        arts[f"z{i}"] = {"s": "o", "t": f"Olay {i} oldu", "d": f"{day}T00:00", "v": 30, "p": 1, "lv": 0, "nu": 0}
        arts[f"o{i}"]["d"] = f"{day}T10:30"
        arts[f"q{i}"]["d"] = f"{day}T10:00"
        core["E"][i]["a"].append(f"z{i}")
    return core, arts, groups


class MeasureTest(unittest.TestCase):
    def test_verdict_needs_every_condition(self):
        m = {"n": 40, "rr": 2.4, "q": 0.004}
        months = {"2026-09": {"n": 12, "rr": 2.1}, "2026-10": {"n": 15, "rr": 1.8}, "2026-11": {"n": 3, "rr": 0.5}}
        self.assertTrue(verdict(m, months))                                   # the 3-story month is ignored
        self.assertFalse(verdict({**m, "q": 0.02}, months))
        self.assertFalse(verdict({**m, "rr": 1.9}, months))
        self.assertFalse(verdict(m, {"2026-09": {"n": 12, "rr": 2.1}}))        # only one month with 5+ stories
        self.assertFalse(verdict(m, {**months, "2026-10": {"n": 15, "rr": 1.2}}))

    def test_verdict_downward_and_undefined(self):
        down = {"n": 40, "rr": 0.0, "q": 0.001}
        self.assertTrue(verdict(down, {"2026-09": {"n": 12, "rr": 0.0}, "2026-10": {"n": 9, "rr": 0.6}}))
        self.assertFalse(verdict(down, {"2026-09": {"n": 12, "rr": 0.0}, "2026-10": {"n": 9, "rr": 0.7}}))
        self.assertFalse(verdict({**down, "rr": None}, {"2026-09": {"n": 12, "rr": None}, "2026-10": {"n": 9, "rr": None}}))
        self.assertFalse(verdict({**down, "q": None}, {"2026-09": {"n": 12, "rr": 0.0}, "2026-10": {"n": 9, "rr": 0.0}}))

    def test_distance_clips_and_needs_three_measures(self):
        self.assertAlmostEqual(distance({"a": {"n": 30, "rr": 8.0}, "b": {"n": 30, "rr": 0.5}, "c": {"n": 30, "rr": 1.0}}), 2 ** ((2 + 1 + 0) / 3))
        self.assertIsNone(distance({"a": {"n": 30, "rr": 2.0}, "b": {"n": 30, "rr": 2.0}, "c": {"n": 10, "rr": 2.0}}))

    def test_no_ledes_means_no_harsher_measure(self):
        arts = {"x": {"s": "o", "v": 30, "lv": None, "p": 1, "d": "2026-09-01T10:00"}}
        self.assertEqual(strata("harsher", "o", [{"event": "e1", "first": {"o": "x", "q": "y"}}], arts | {"y": {"s": "q", "v": 0, "lv": 0, "p": 1, "d": "2026-09-01T10:00"}}, ["q"]), [])

    def test_eligibility_political_and_timed(self):
        arts = {"x": {"s": "o", "v": 30, "lv": 0, "p": 0, "d": "2026-09-01T00:00"}, "y": {"s": "q", "v": 30, "lv": 0, "p": 1, "d": "2026-09-01T10:00"}}
        st = [{"event": "e1", "first": {"o": "x", "q": "y"}}]
        self.assertEqual(strata("loaded", "o", st, arts, ["q"]), [])          # the outlet's headline is not political
        self.assertEqual(strata("first", "o", st, arts, ["q"]), [])           # its time is a bare date

    def test_first_counts_from_the_earliest_timed_comparison_headline(self):
        arts = {"x": {"s": "o", "d": "2026-09-01T11:01"}, "y": {"s": "q", "d": "2026-09-01T10:00"},
                "z": {"s": "r", "d": "2026-09-01T00:00"}, "w": {"s": "u", "d": "2026-09-01T10:59"}}
        st = [{"event": "e1", "first": {"o": "x", "q": "y", "r": "z", "u": "w", "agency": "y"}}]
        # reference 10:00 (q); r has a bare date and is not eligible; o is 61 minutes late, u is within the hour
        self.assertEqual(strata("first", "o", st, arts, ["q", "r", "u"]), [(0, 1, 2, 2)])
        self.assertEqual(strata("first", "u", st, arts, ["q", "r", "o"]), [(1, 1, 1, 2)])

    def test_first_uses_the_earliest_timed_headline(self):
        arts = {"x0": {"s": "o", "d": "2026-09-01T00:00"}, "x1": {"s": "o", "d": "2026-09-01T10:30"},
                "y": {"s": "q", "d": "2026-09-01T10:00"}}
        st = [{"event": "e1", "first": {"o": "x0", "q": "y"}, "timed": {"o": "x1", "q": "y"}}]
        self.assertEqual(strata("first", "o", st, arts, ["q"]), [(1, 1, 1, 1)])
        st = [{"event": "e1", "first": {"o": "x0", "q": "y"}, "timed": {"q": "y"}}]  # only bare dates from o
        self.assertEqual(strata("first", "o", st, arts, ["q"]), [])

    def test_first_only_for_complete_feeds_and_judged_by_timed_headlines(self):
        res = compute(*complete_fixture())
        o = res["outlets"]["o"]
        self.assertTrue(o["feed"]["complete"])
        # o's earliest headline in every story is 00:00; its timed one (10:30) is within the hour of q (10:00)
        self.assertEqual((o["slices"]["all"]["measures"]["first"]["n"], o["slices"]["all"]["measures"]["first"]["rr"]), (25, 1.0))
        self.assertIn("skip", o["slices"]["all"]["measures"])

    def test_skip_compares_only_outlets_active_that_day(self):
        st = [{"event": "e1", "first": {}, "active": ["o", "q", "r"], "skipped": {"o", "r"}},
              {"event": "e2", "first": {}, "active": ["q", "r"], "skipped": set()},
              {"event": "e3", "first": {}}]
        self.assertEqual(strata("skip", "o", st, {}, ["q", "r", "z"]), [(1, 1, 1, 2)])

    def test_loaded_and_harsher_strata(self):
        arts = {"x": {"s": "o", "v": 30, "lv": 10, "p": 1, "d": "2026-09-01T10:00"},
                "y": {"s": "q", "v": 25, "lv": 20, "p": 1, "d": "2026-09-01T10:00"},
                "z": {"s": "r", "v": 40, "lv": None, "p": 1, "d": "2026-09-01T10:00"}}
        st = [{"event": "e1", "first": {"o": "x", "q": "y", "r": "z"}}]
        self.assertEqual(strata("loaded", "o", st, arts, ["q", "r"]), [(1, 1, 2, 2)])
        self.assertEqual(strata("harsher", "o", st, arts, ["q", "r"]), [(1, 1, 0, 1)])

    def test_compute_writes_json_safe_output(self):
        res = compute(*small_fixture())
        json.dumps(res, allow_nan=False)
        self.assertEqual([s["k"] for s in res["slices"]], ["all", "2026-09", "tp:yargi"])
        self.assertEqual(res["slices"][2]["l"], "Yargı ve soruşturmalar")
        o, q = res["outlets"]["o"]["slices"]["all"]["measures"], res["outlets"]["q"]["slices"]["all"]["measures"]
        self.assertEqual(q["loaded"]["rr"], 0.0)                              # q never loaded while o always is
        self.assertIsNone(o["loaded"]["rr"])                                  # only o does it
        self.assertEqual(o["loaded"]["n"], 25)
        self.assertIn("q", o["loaded"]); self.assertIn("strong", o["loaded"])
        self.assertNotIn("q", res["outlets"]["o"]["slices"]["2026-09"]["measures"]["loaded"])
        self.assertNotIn("skip", o)                                           # neither feed is complete
        self.assertNotIn("first", o)                                          # so no first-to-report either
        self.assertEqual(res["outlets"]["o"]["missed"], [])
        self.assertFalse(res["outlets"]["o"]["feed"]["complete"])

    def test_nobody_doing_it_is_undefined_not_zero(self):
        core, arts, groups = small_fixture()
        for a in arts.values():
            a["v"] = 0
        m = compute(core, arts, groups)["outlets"]["o"]["slices"]["all"]["measures"]["loaded"]
        self.assertEqual((m["n"], m["rr"], m["lo"], m["hi"], m["p"]), (25, None, None, None, None))


if __name__ == "__main__":
    unittest.main()

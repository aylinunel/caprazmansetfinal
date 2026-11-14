import unittest

from validation.biaslab.sim import realize, scenario


class SimTest(unittest.TestCase):
    def test_positive_selective_statistics_has_active_and_inactive_agents(self):
        rs = realize("selective_statistics", scenario("selective_statistics", "positive"))
        self.assertEqual(len(rs), 12)
        self.assertTrue(any(r.active for r in rs))
        self.assertTrue(any(not r.active for r in rs))

    def test_active_agent_reports_the_narrow_denominator(self):
        r = next(r for r in realize("selective_statistics", scenario("selective_statistics", "positive")) if r.active)
        self.assertEqual((r.state["last_denominator_used"], r.metric, r.reference_metric), (20, 50.0, 10.0))

    def test_inactive_agent_reports_the_reference_denominator(self):
        r = next(r for r in realize("selective_statistics", scenario("selective_statistics", "positive")) if not r.active)
        self.assertEqual((r.state["last_denominator_used"], r.metric), (100, 10.0))

    def test_boundary_is_never_active(self):
        rs = realize("selective_statistics", scenario("selective_statistics", "boundary"))
        self.assertFalse(any(r.active for r in rs))

    def test_same_seed_is_deterministic(self):
        s = scenario("selective_statistics", "positive")
        self.assertEqual(realize("selective_statistics", s, seed=7), realize("selective_statistics", s, seed=7))

    def test_scenario_is_not_mutated_and_is_copied(self):
        s = scenario("selective_statistics", "positive")
        r = realize("selective_statistics", s)[0]
        r.scenario["contexts"][0]["event_count"] = 999
        self.assertEqual(s["contexts"][0]["event_count"], 10)

    def test_unknown_concept_raises(self):
        with self.assertRaises(Exception):
            realize("no_such_concept", {"name": "x", "initial_state": {}, "contexts": [{}], "expectation": "equal"})

    def test_unknown_scenario_name_raises_keyerror(self):
        with self.assertRaises(KeyError):
            scenario("selective_statistics", "nope")


if __name__ == "__main__":
    unittest.main()

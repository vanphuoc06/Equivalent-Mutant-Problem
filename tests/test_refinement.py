import unittest

from src.core.refinement import RefinementEngine


class TestNSEVRefinement(unittest.TestCase):
    def setUp(self):
        self.engine = RefinementEngine(max_budget=3)

    def test_syntax_refinement_trigger(self):
        prompt = self.engine.analyze_z3_feedback(solver_status="error", error_log="unknown constant x")
        self.assertIn("REFINE_PROMPT", prompt)
        self.assertIn("syntax/type", prompt)
        self.assertEqual(self.engine.current_attempt, 1)

    def test_unknown_refinement_trigger(self):
        prompt = self.engine.analyze_z3_feedback(solver_status="unknown")
        self.assertIn("UNKNOWN", prompt)
        self.assertEqual(self.engine.current_attempt, 1)

    def test_sat_is_not_refinement_trigger(self):
        prompt = self.engine.analyze_z3_feedback(solver_status="sat", model="[n = 1]")
        self.assertIsNone(prompt)
        self.assertEqual(self.engine.current_attempt, 0)

    def test_candidate_counterexample_refinement_trigger(self):
        prompt = self.engine.analyze_z3_feedback(solver_status="candidate_counterexample", model="[i = -1]")
        self.assertIn("candidate counterexample", prompt)
        self.assertEqual(self.engine.current_attempt, 1)

    def test_budget_exhaustion(self):
        for _ in range(3):
            self.engine.analyze_z3_feedback(solver_status="unknown")
        self.assertTrue(self.engine.is_budget_exceeded())
        self.assertEqual(self.engine.current_attempt, 3)


if __name__ == "__main__":
    unittest.main()

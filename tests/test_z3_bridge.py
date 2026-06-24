import unittest

from src.core.verdicts import Verdict
from src.solvers.z3_bridge import Z3Bridge


class TestZ3Bridge(unittest.TestCase):
    def test_equivalent_unsat(self):
        code = """
from z3 import *
x = Int('x')
solver = Solver()
solver.add((x + 1) != (1 + x))
"""
        result = Z3Bridge().verify(code)
        self.assertEqual(result.verdict, Verdict.EQUIVALENT)

    def test_non_equivalent_sat(self):
        code = """
from z3 import *
x = Int('x')
solver = Solver()
solver.add((x + 1) != (x + 2))
"""
        result = Z3Bridge().verify(code)
        self.assertEqual(result.verdict, Verdict.NON_EQUIVALENT)
        self.assertIsNotNone(result.model)

    def test_bounded_unsat(self):
        code = """
from z3 import *
x = Int('x')
solver = Solver()
nsev_bounded = True
solver.add(x >= 0, x <= 10)
solver.add((x + 1) != (1 + x))
"""
        result = Z3Bridge().verify(code)
        self.assertEqual(result.verdict, Verdict.EQUIVALENT_UNDER_BOUND)
        self.assertTrue(result.bounded)

    def test_invalid_code_is_indeterminate(self):
        result = Z3Bridge().verify("solver = 'not a solver'")
        self.assertEqual(result.verdict, Verdict.INDETERMINATE)


if __name__ == "__main__":
    unittest.main()

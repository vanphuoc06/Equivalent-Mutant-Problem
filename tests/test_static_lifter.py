import unittest

from src.core.static_lifter import StaticSemanticLifter
from src.core.verdicts import Verdict
from src.solvers.z3_bridge import Z3Bridge


class TestStaticSemanticLifter(unittest.TestCase):
    def test_loop_sum_equivalence(self):
        original = """
def compute_sum(n):
    total = 0
    for i in range(n):
        total += i
    return total
"""
        mutant = """
def compute_sum(n):
    if n <= 0:
        return 0
    return (n * (n - 1)) // 2
"""
        spec = StaticSemanticLifter().lift(original, mutant)
        self.assertIsNotNone(spec)
        self.assertEqual(Z3Bridge().verify(spec.code).verdict, Verdict.EQUIVALENT)

    def test_non_equivalence(self):
        original = "def f(n):\n    return n + 1\n"
        mutant = "def f(n):\n    return n + 2\n"
        spec = StaticSemanticLifter().lift(original, mutant)
        self.assertIsNotNone(spec)
        self.assertEqual(Z3Bridge().verify(spec.code).verdict, Verdict.NON_EQUIVALENT)

    def test_unsupported_matrix_signature(self):
        original = "def f(a, n):\n    return n\n"
        mutant = "def f(a, n):\n    return n\n"
        self.assertIsNone(StaticSemanticLifter().lift(original, mutant))


if __name__ == "__main__":
    unittest.main()

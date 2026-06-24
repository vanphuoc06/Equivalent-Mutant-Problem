import unittest

from src.core.analyzer import CodeAnalyzer


class TestCodeAnalyzer(unittest.TestCase):
    def test_loop_detection(self):
        code = "for i in range(10):\n    print(i)"
        metadata = CodeAnalyzer(code).analyze()
        self.assertEqual(len(metadata["loops"]), 1)
        self.assertEqual(metadata["loops"][0]["type"], "For")

    def test_nested_loop_depth(self):
        code = """
for i in range(3):
    for j in range(4):
        print(i, j)
"""
        metadata = CodeAnalyzer(code).analyze()
        self.assertEqual(metadata["nested_loop_depth"], 2)

    def test_function_strategy(self):
        code = """
def local_func(x):
    return x + 1

y = local_func(5)
z = external_lib_func(10)
"""
        metadata = CodeAnalyzer(code).analyze()
        local_call = next(f for f in metadata["functions"] if f["name"] == "local_func")
        ext_call = next(f for f in metadata["functions"] if f["name"] == "external_lib_func")
        self.assertEqual(local_call["strategy"], "Inlining")
        self.assertEqual(ext_call["strategy"], "Contract/UninterpretedFunction")

    def test_dynamic_constructs_are_flagged(self):
        code = "def f(x):\n    return eval(x)"
        metadata = CodeAnalyzer(code).analyze()
        self.assertEqual(metadata["dynamic_constructs"][0]["name"], "eval")

    def test_concurrency_detection(self):
        code = "import threading\ndef task():\n    pass"
        metadata = CodeAnalyzer(code).analyze()
        self.assertTrue(metadata["concurrency_flags"])

    def test_branch_detection(self):
        code = "def f(x):\n    if x > 0:\n        return True\n    return False"
        metadata = CodeAnalyzer(code).analyze()
        self.assertEqual(len(metadata["branches"]), 1)
        self.assertEqual(metadata["branches"][0]["type"], "If")


if __name__ == "__main__":
    unittest.main()

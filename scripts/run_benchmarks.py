"""Run offline NSEV smoke benchmarks."""
from __future__ import annotations

import os
import sys
import tempfile
import textwrap
import time
from pathlib import Path

from tabulate import tabulate

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))
from main import run_nsev_pipeline  # noqa: E402


def _write_temp_pair(original_source: str, mutant_source: str):
    tmpdir = tempfile.TemporaryDirectory()
    base = Path(tmpdir.name)
    orig = base / "orig.py"
    mut = base / "mut.py"
    orig.write_text(textwrap.dedent(original_source).strip() + "\n", encoding="utf-8")
    mut.write_text(textwrap.dedent(mutant_source).strip() + "\n", encoding="utf-8")
    return tmpdir, orig, mut


def execute_suite() -> None:
    benchmarks = [
        {
            "name": "Loop sum closed form",
            "category": "Phase 2: induction/summary",
            "pair": (
                """
                def compute_sum(n):
                    total = 0
                    for i in range(n):
                        total += i
                    return total
                """,
                """
                def compute_sum(n):
                    if n <= 0:
                        return 0
                    return (n * (n - 1)) // 2
                """,
            ),
        },
        {
            "name": "Parity modulo vs bitwise",
            "category": "Phase 6: bit-vector-sensitive expression",
            "pair": (
                """
                def is_even(n):
                    return n % 2 == 0
                """,
                """
                def is_even(n):
                    return (n & 1) == 0
                """,
            ),
        },
        {
            "name": "Non-equivalent arithmetic",
            "category": "Phase 6: counterexample",
            "pair": (
                """
                def f(n):
                    return n + 1
                """,
                """
                def f(n):
                    return n + 2
                """,
            ),
        },
    ]

    rows = []
    print("Starting NSEV offline smoke benchmark...\n")
    for item in benchmarks:
        tmpdir, orig, mut = _write_temp_pair(*item["pair"])
        try:
            start = time.time()
            result = run_nsev_pipeline(str(orig), str(mut))
            duration = time.time() - start
            rows.append([item["name"], item["category"], result.verdict.value, f"{duration:.3f}s", result.reason])
        finally:
            tmpdir.cleanup()

    print("\n--- NSEV Smoke Benchmark Results ---")
    print(tabulate(rows, headers=["Benchmark", "Focus", "Verdict", "Time", "Reason"], tablefmt="grid"))


if __name__ == "__main__":
    execute_suite()

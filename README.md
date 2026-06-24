# Introduction
Dự án xử lý một số vấn đề về **Equivalent Mutant Problem (EMP)**
Hiện tại dự án vẫn đang được phát triển bởi nhóm nghiên cứu của chúng tôi.Nó giải quyết một số vấn đề về **Equivalent Mutant Problem (EMP)** 

## What this repository implements

The offline code in this repository implements a small, testable subset of the full framework:

1. **Structural analysis** for loops, branches, function calls, dynamic constructs, and bounded-concurrency flags.
2. **Offline semantic lifting** for small Python examples, so the repository can be tested without hosted LLM access.
3. **Formal bridge / VC execution** through `z3-solver==4.12.2.0`.
4. **Conservative verdicts** matching the paper: `Equivalent`, `Non-equivalent`, `Equivalent under Bound`, and `Indeterminate`.
5. **Phase 8 refinement prompts** for validation errors, UNKNOWN results, and candidate counterexamples.

The full paper evaluation uses a larger mutant-level manifest and Java/Defects4J front-end. Unsupported constructs in this public prototype return `Indeterminate` rather than being silently approximated as equivalent.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python3 src/main.py --original benchmarks/sample_p.py --mutant benchmarks/sample_m.py
```

Expected result for the sample pair:

```text
VERDICT: Equivalent
Reason: UNSAT negated equivalence condition
```

## Tests

Run all unit tests:

```bash
python3 -m unittest discover tests
```

Run smoke benchmarks:

```bash
python3 scripts/run_benchmarks.py
```

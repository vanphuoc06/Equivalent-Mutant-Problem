# NSEV: Neuro-Symbolic Equivalence Verifier

NSEV is a research prototype for the **Equivalent Mutant Problem (EMP)**. It follows the paper's conservative neuro-symbolic design: LLMs may propose candidate semantic artefacts, but only the typed verification bridge and Z3 solver may justify a verdict.

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

## Relation to the paper

This code is aligned with the paper's revised claims:

- LLM output is not treated as a final classification.
- Preconditions, invariants, summaries, and contracts must be validated before affecting a verdict.
- SAT produces `Non-equivalent`; UNKNOWN, unsupported translation, or validation failure produces `Indeterminate`.
- Bounded reasoning is reported separately as `Equivalent under Bound`.

The paper reports the full 150-mutant benchmark results. This repository's smoke benchmarks are only executable examples, not a replacement for the full replication package.

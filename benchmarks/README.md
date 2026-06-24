# NSEV Benchmark Suite

[cite_start]This directory contains a curated set of 150 functions designed to evaluate the precision and efficiency of the **NSEV** framework[cite: 256, 257]. Each benchmark focuses on a specific challenge in formal verification and mutation testing.

## 📂 Benchmark Categories

### 1. Parity Check (Bitwise vs. Modulo)
- **File:** `parity_check.py`
- **Challenge:** Semantic equivalence with syntactic divergence.
- **Description:** Verifies that a bitwise optimization `(n & 1 == 0)` is semantically identical to the standard parity check `(n % 2 == 0)`.
- **Z3 Theory:** Bit-Vector Arithmetic.

### 2. Matrix Summation (Hierarchical Abstraction)
- **File:** `matrix_sum.py`
- **Challenge:** State-space explosion in nested loops.
- **Description:** Uses Phase 3 (Hierarchical Abstraction) to reduce $O(N \times M)$ complexity into independent inductive summaries.
- **Z3 Theory:** Array Theory and Quantifiers.

### 3. Loop-to-Formula Optimization
- **File:** `math_opt.py`
- **Challenge:** Proving equivalence between iterative and analytical solutions.
- **Description:** A case study where an iterative summation loop is proven equivalent to a closed-form mathematical formula using Phase 2 induction.
- **Z3 Theory:** Non-linear Integer Arithmetic.

## 🚀 How to Run Benchmarks

To execute the verification for a specific benchmark, use the following command from the root directory:

```bash
python src/main.py --original benchmarks/[filename]_original.py --mutant benchmarks/[filename]_mutant.py
```

## 📊 Interpreting Z3 Verdicts
The output of the NSEV pipeline will provide one of the following mathematical verdicts:

The output of the NSEV pipeline provides one of the following mathematical verdicts based on the symbolic analysis of the original and mutant code:

| Verdict | Meaning | Logical Z3 Result |
| :--- | :--- | :--- |
| **EQUIVALENT** | The mutant is semantically identical to the original code. | Z3 returned `UNSAT` for the negation. |
| **NON-EQUIVALENT** | The mutant changes the program behavior. | Z3 returned `SAT` and generated a counter-example. |
| **INDETERMINATE** | Verification could not be finalized within the budget. | Z3 returned `UNKNOWN` or Refinement failed. |

## 🛠 Counter-Example Analysis

For **NON-EQUIVALENT** mutants, NSEV leverages Z3's ability to generate a satisfying assignment (SAT). This provides a concrete set of input values that distinguish the mutant from the original program, effectively creating a test case to "kill" the mutant.

### Example Output:
If a mutation in a summation loop changes the boundary condition, NSEV might output:
`Counter-example found: [n = 5, res = 10, mutant_res = 15]`

**Interpretation:**
- For an input of `n = 5`, the original program produces `10`.
- For the same input, the mutant program produces `15`.
- Therefore, the mutant is **NOT equivalent** and can be killed by a test case where `n = 5`.

## 🔄 Self-Correction Log (Phase 8)

If the framework initiates a refinement loop, you will see logs indicating the reason for the retry:
- **Syntax Error:** The LLM generated an invalid Z3 API call, which was caught and corrected.
- **Weak Invariant:** Z3 found a counter-example that was logically possible but code-unreachable, prompting the LLM to strengthen the inductive invariant.

---

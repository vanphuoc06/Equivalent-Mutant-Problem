"""Command-line entry point for the NSEV prototype."""
from __future__ import annotations

import argparse
import os
import sys
from typing import Optional

# Allow `python src/main.py` without installing the package.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core import CodeAnalyzer, NSEV_LLM_Client, RefinementEngine, StaticSemanticLifter, VerificationResult, Verdict
from solvers import Z3Bridge


def run_nsev_pipeline(orig_path: str, mut_path: str, *, use_llm: bool = False, max_refinements: int = 3) -> VerificationResult:
    with open(orig_path, "r", encoding="utf-8") as f:
        orig_code = f.read()
    with open(mut_path, "r", encoding="utf-8") as f:
        mut_code = f.read()

    original_metadata = CodeAnalyzer(orig_code).analyze()
    mutant_metadata = CodeAnalyzer(mut_code).analyze()
    merged_metadata = {
        "original": original_metadata,
        "mutant": mutant_metadata,
        "loops": original_metadata.get("loops", []) + mutant_metadata.get("loops", []),
    }

    print(f"[*] Structural analysis: {len(merged_metadata['loops'])} loop(s) detected.")

    bridge = Z3Bridge()
    refiner = RefinementEngine(max_budget=max_refinements)
    lifter = StaticSemanticLifter()
    llm = NSEV_LLM_Client()

    lifted = lifter.lift(orig_code, mut_code, merged_metadata)
    prompt: Optional[str] = None
    if lifted is None and use_llm:
        if original_metadata.get("nested_loop_depth", 0) > 1:
            prompt = llm.generate_nested_loop_prompt(original_metadata.get("loops", []), orig_code)
        else:
            prompt = llm.generate_initial_prompt(orig_code, mut_code, context=str(merged_metadata))
        generated_code = llm.query_model(prompt)
        if generated_code:
            lifted = type("Lifted", (), {"code": generated_code})()

    if lifted is None:
        result = VerificationResult(
            Verdict.INDETERMINATE,
            reason="unsupported construct or no validated semantic artefact was available",
            metadata={"analysis": merged_metadata},
        )
        _print_result(result)
        return result

    result = bridge.verify(lifted.code)
    # Only validation/unknown errors trigger refinement. SAT is a real Non-equivalent verdict.
    while result.verdict == Verdict.INDETERMINATE and not refiner.is_budget_exceeded() and use_llm:
        feedback = refiner.analyze_z3_feedback("validation_failed", error_log=result.reason)
        if not feedback or prompt is None:
            break
        generated_code = llm.query_model(llm.generate_refinement_prompt(prompt, feedback))
        if not generated_code:
            break
        result = bridge.verify(generated_code)

    _print_result(result)
    return result


def _print_result(result: VerificationResult) -> None:
    icon = {
        Verdict.EQUIVALENT: "✅",
        Verdict.EQUIVALENT_UNDER_BOUND: "🟨",
        Verdict.NON_EQUIVALENT: "❌",
        Verdict.INDETERMINATE: "⚪",
    }[result.verdict]
    print(f"{icon} VERDICT: {result.verdict.value}")
    if result.reason:
        print(f"   Reason: {result.reason}")
    if result.model:
        print(f"   Counterexample: {result.model}")


def main() -> None:
    parser = argparse.ArgumentParser(description="NSEV: Neuro-Symbolic Equivalence Verifier")
    parser.add_argument("--original", required=True, help="Path to original Python file")
    parser.add_argument("--mutant", required=True, help="Path to mutant Python file")
    parser.add_argument("--use-llm", action="store_true", help="Enable optional LLM integration if configured")
    parser.add_argument("--max-refinements", type=int, default=3, help="Phase 8 refinement budget")
    args = parser.parse_args()
    run_nsev_pipeline(args.original, args.mutant, use_llm=args.use_llm, max_refinements=args.max_refinements)


if __name__ == "__main__":
    main()

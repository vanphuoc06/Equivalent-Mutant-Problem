"""Phase 8 refinement support."""
from __future__ import annotations

from typing import Any, Optional


class RefinementEngine:
    """Turns validator/Z3 feedback into a bounded sequence of refinement prompts."""

    def __init__(self, max_budget: int = 3):
        if max_budget < 0:
            raise ValueError("max_budget must be non-negative")
        self.max_budget = max_budget
        self.current_attempt = 0

    def analyze_z3_feedback(self, solver_status: str, model: Optional[Any] = None, error_log: Optional[str] = None) -> Optional[str]:
        if self.is_budget_exceeded():
            return None

        if error_log:
            self.current_attempt += 1
            return self._generate_syntax_feedback(error_log)

        if solver_status == "unknown":
            self.current_attempt += 1
            return (
                "REFINE_PROMPT: Z3 returned UNKNOWN. Split the verification condition, "
                "avoid unsupported theories where possible, or provide a stronger validated invariant."
            )

        if solver_status == "validation_failed":
            self.current_attempt += 1
            return (
                "REFINE_PROMPT: The candidate artefact failed syntactic, type, or admissibility validation. "
                "Regenerate a well-typed precondition, invariant, summary, or contract and do not strengthen "
                "the input domain unless the context entails it."
            )

        if solver_status == "candidate_counterexample" and model is not None:
            self.current_attempt += 1
            return self._generate_cegar_feedback(model)

        # A real SAT result for the negated equivalence condition is Non-equivalent,
        # not a refinement trigger. This matches the verdict semantics in the paper.
        return None

    def _generate_syntax_feedback(self, error: str) -> str:
        return (
            f"REFINE_PROMPT: A Z3 syntax/type error occurred: {error}. "
            "Declare all symbols with unique sorts, use BitVec for bitwise or overflow-sensitive code, "
            "and emit a solver named 'solver'."
        )

    def _generate_cegar_feedback(self, model: Any) -> str:
        return (
            f"REFINE_PROMPT: A candidate counterexample was observed: {model}. "
            "If this state is infeasible in the source program, strengthen the invariant or precondition and "
            "prove/context-justify the added assumption. Otherwise report Non-equivalent."
        )

    def is_budget_exceeded(self) -> bool:
        return self.current_attempt >= self.max_budget

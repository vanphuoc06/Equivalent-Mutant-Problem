"""Z3 bridge for NSEV Phase 6."""
from __future__ import annotations

from typing import Any, Dict, Tuple

import z3

try:
    from core.verdicts import Verdict, VerificationResult
except ModuleNotFoundError:  # package import path used by tests
    from src.core.verdicts import Verdict, VerificationResult


class Z3Bridge:
    """Executes validated Python-Z3 artefacts and maps solver output to NSEV verdicts."""

    def __init__(self, timeout_ms: int = 30_000):
        self.timeout_ms = timeout_ms
        self.last_model = None

    def verify(self, generated_code: str) -> VerificationResult:
        if not generated_code or not generated_code.strip():
            return VerificationResult(Verdict.INDETERMINATE, reason="empty generated artefact")

        local_scope: Dict[str, Any] = {}
        safe_globals = self._z3_namespace()
        try:
            exec(generated_code, safe_globals, local_scope)
            solver = local_scope.get("solver")
            if not isinstance(solver, z3.Solver):
                return VerificationResult(Verdict.INDETERMINATE, reason="artefact did not define a Z3 solver named 'solver'")
            solver.set(timeout=self.timeout_ms)
            result = solver.check()
            bounded = bool(local_scope.get("nsev_bounded", False))
            metadata = {
                "bounded": bounded,
                "observation": local_scope.get("nsev_observation", "return_value"),
            }
            if result == z3.unsat:
                verdict = Verdict.EQUIVALENT_UNDER_BOUND if bounded else Verdict.EQUIVALENT
                reason = "UNSAT negated equivalence condition"
                if bounded:
                    reason += " under documented bound"
                return VerificationResult(verdict, reason=reason, bounded=bounded, metadata=metadata)
            if result == z3.sat:
                self.last_model = solver.model()
                return VerificationResult(
                    Verdict.NON_EQUIVALENT,
                    reason="SAT negated equivalence condition",
                    model=self.get_counter_example_values(),
                    bounded=bounded,
                    metadata=metadata,
                )
            return VerificationResult(Verdict.INDETERMINATE, reason="Z3 returned UNKNOWN", bounded=bounded, metadata=metadata)
        except Exception as exc:
            return VerificationResult(Verdict.INDETERMINATE, reason=f"Formal bridge execution error: {exc}")

    def legacy_verify(self, generated_code: str) -> Tuple[str, Any]:
        """Compatibility helper for older tests/scripts."""
        result = self.verify(generated_code)
        if result.verdict == Verdict.EQUIVALENT:
            return "unsat", None
        if result.verdict == Verdict.EQUIVALENT_UNDER_BOUND:
            return "bounded_unsat", None
        if result.verdict == Verdict.NON_EQUIVALENT:
            return "sat", result.model
        return "unknown", result.reason

    def get_counter_example_values(self):
        if self.last_model is None:
            return None
        return {str(d): self.last_model[d] for d in self.last_model.decls()}

    def _z3_namespace(self) -> Dict[str, Any]:
        namespace = {name: getattr(z3, name) for name in dir(z3) if not name.startswith("_")}
        namespace["z3"] = z3
        namespace["__builtins__"] = {"True": True, "False": False, "None": None, "range": range, "len": len, "__import__": __import__}
        return namespace

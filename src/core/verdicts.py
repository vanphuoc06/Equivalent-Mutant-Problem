"""Verdict labels used by the NSEV prototype.

The labels mirror the terminology used in the paper:
- Equivalent: UNSAT negated equivalence condition under the unbounded sequential model.
- Non-equivalent: SAT negated equivalence condition with a model/counterexample.
- Equivalent under Bound: UNSAT only under an explicit finite/bounded model.
- Indeterminate: unsupported translation, validation failure, UNKNOWN, or budget exhaustion.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class Verdict(str, Enum):
    EQUIVALENT = "Equivalent"
    NON_EQUIVALENT = "Non-equivalent"
    EQUIVALENT_UNDER_BOUND = "Equivalent under Bound"
    INDETERMINATE = "Indeterminate"


@dataclass(frozen=True)
class VerificationResult:
    verdict: Verdict
    reason: str = ""
    model: Optional[Dict[str, Any]] = None
    bounded: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_proven(self) -> bool:
        return self.verdict in {Verdict.EQUIVALENT, Verdict.EQUIVALENT_UNDER_BOUND}

"""Prompt construction and optional LLM interface for NSEV.

The production paper uses LLMs as candidate artefact generators only. This module
therefore builds prompts that ask for preconditions, invariants, summaries, and
contracts, while making clear that final verdicts must be controlled by the Z3
bridge. The offline repository does not require API access; query_model returns
None unless an integration is added by the user.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Iterable, List, Optional


@dataclass(frozen=True)
class PromptBundle:
    prompt: str
    sha256: str


class NSEV_LLM_Client:
    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.0, top_p: float = 1.0):
        self.model_name = model_name
        self.temperature = temperature
        self.top_p = top_p
        self.api_key = os.getenv("OPENAI_API_KEY")

    def generate_initial_prompt(self, original_code: str, mutant_code: str, context: str = "") -> str:
        prompt = f"""
ROLE: You are a verification engineer preparing candidate artefacts for SMT validation.

INPUT ORIGINAL (P_orig):
```
{original_code}
```

INPUT MUTANT (P_mut):
```
{mutant_code}
```

OPTIONAL FRONT-END CONTEXT:
{context}

TASK:
1. Identify symbolic inputs and assign Z3 sorts. Use BitVec for bitwise or overflow-sensitive code.
2. Propose candidate preconditions only when they are entailed by caller/path/type/API context.
3. Propose loop invariants, closed-form summaries, or contracts when needed.
4. Emit Python-Z3 code that defines a solver named `solver` and asserts the negated observational-equivalence condition.
5. Do not output a final equivalence verdict. The solver result and NSEV bridge decide the verdict.

REQUIRED SAFETY RULES:
- Unsupported side effects, dynamic execution, unresolved aliasing, or unmodelled concurrency must be marked as unsupported.
- Bounded loops, finite domains, and bounded schedules must set `nsev_bounded = True` in the emitted code.
- Any candidate precondition must include a separate admissibility check or a documented context source.
""".strip()
        return prompt

    def generate_nested_loop_prompt(self, loop_metadata: Iterable[dict], source_code: str) -> str:
        num_loops = len(list(loop_metadata))
        prompt = f"""
PHASE 3: HIERARCHICAL LOOP ABSTRACTION
Detected loop count: {num_loops}

SOURCE:
```
{source_code}
```

TASK:
- Summarize inner loops bottom-up.
- If an invariant relation or loop function is available, use it as a candidate summary.
- Validate initiation, consecution, and postcondition obligations in Z3.
- Use `nsev_bounded = True` for fixed-depth unrolling or finite-domain checks.
- Do not claim unbounded equivalence unless the inductive proof obligations are discharged.
""".strip()
        return prompt

    def generate_refinement_prompt(self, original_prompt: str, feedback_log: str) -> str:
        return f"""
{original_prompt}

PHASE 8 REFINEMENT FEEDBACK:
The previous candidate failed validation or solving with:
```
{feedback_log}
```
Regenerate only the candidate artefacts needed to repair the failure. Do not strengthen the input domain unless the new assumption is proved or explicitly documented.
""".strip()

    def prompt_bundle(self, prompt: str) -> PromptBundle:
        return PromptBundle(prompt=prompt, sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest())

    def query_model(self, prompt: str) -> Optional[str]:
        """Optional integration point for hosted/local LLMs.

        The repository test path is offline and deterministic. Returning None prevents
        placeholder Z3 code from being mistaken for a validated artefact.
        """
        return None

    def ensemble_consensus(self, prompts: List[str]) -> Optional[str]:
        """Placeholder hook for multi-model candidate generation.

        Agreement between LLMs is not treated as evidence of equivalence; all returned
        candidates must still pass the formal bridge.
        """
        return None

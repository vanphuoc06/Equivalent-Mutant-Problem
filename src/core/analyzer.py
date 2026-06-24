"""Structural analyzer for the NSEV prototype.

The analyzer intentionally reports unsupported constructs instead of silently
approximating them. This follows the paper's conservative policy: unsupported
reflection, dynamic execution, unmodelled I/O, native behaviour, or unresolved
aliasing must lead to Indeterminate unless an explicit validated contract exists.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, asdict
from typing import Any, Dict, List


@dataclass
class NodeInfo:
    type: str
    lineno: int
    end_lineno: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CodeAnalyzer:
    """Extracts metadata used by the eight NSEV phases."""

    CONCURRENCY_MODULES = {"threading", "multiprocessing", "concurrent"}
    DYNAMIC_NAMES = {"eval", "exec", "setattr", "getattr", "__import__", "compile", "open"}

    def __init__(self, source_code: str):
        self.source_code = source_code
        self.tree = ast.parse(source_code)
        self.local_defs = {node.name for node in ast.walk(self.tree) if isinstance(node, ast.FunctionDef)}
        self.metadata: Dict[str, Any] = {
            "loops": [],
            "branches": [],
            "functions": [],
            "concurrency_flags": False,
            "dynamic_constructs": [],
            "unsupported_constructs": [],
            "nested_loop_depth": 0,
        }

    def analyze(self) -> Dict[str, Any]:
        self.metadata["nested_loop_depth"] = self._max_loop_depth(self.tree)
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.For, ast.While)):
                self.metadata["loops"].append(self._get_node_info(node).to_dict())
            elif isinstance(node, (ast.If, ast.Match)):
                self.metadata["branches"].append(self._get_node_info(node).to_dict())
            elif isinstance(node, ast.Call):
                self._analyze_function_call(node)
            elif self._is_concurrency_construct(node):
                self.metadata["concurrency_flags"] = True
            elif isinstance(node, (ast.With, ast.AsyncWith, ast.AsyncFunctionDef, ast.Yield, ast.YieldFrom)):
                self.metadata["unsupported_constructs"].append(self._get_node_info(node).to_dict())
        return self.metadata

    def _get_node_info(self, node: ast.AST) -> NodeInfo:
        return NodeInfo(
            type=type(node).__name__,
            lineno=getattr(node, "lineno", -1),
            end_lineno=getattr(node, "end_lineno", getattr(node, "lineno", -1)),
        )

    def _analyze_function_call(self, node: ast.Call) -> None:
        name = self._call_name(node)
        if not name:
            return
        strategy = "Inlining" if name in self.local_defs else "Contract/UninterpretedFunction"
        if name in self.DYNAMIC_NAMES:
            self.metadata["dynamic_constructs"].append({"name": name, **self._get_node_info(node).to_dict()})
            strategy = "IndeterminateUnlessContracted"
        self.metadata["functions"].append({"name": name, "strategy": strategy})

    def _call_name(self, node: ast.Call) -> str:
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute):
            return node.func.attr
        return ""

    def _is_concurrency_construct(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Import):
            return any(alias.name.split(".")[0] in self.CONCURRENCY_MODULES for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            return (node.module or "").split(".")[0] in self.CONCURRENCY_MODULES
        return False

    def _max_loop_depth(self, node: ast.AST, depth: int = 0) -> int:
        is_loop = isinstance(node, (ast.For, ast.While))
        next_depth = depth + 1 if is_loop else depth
        child_depths = [self._max_loop_depth(child, next_depth) for child in ast.iter_child_nodes(node)]
        return max([next_depth, *child_depths])

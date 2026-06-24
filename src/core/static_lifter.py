"""Offline semantic lifting for small Python examples.

This deterministic lifter is intentionally conservative. It covers the toy Python
benchmarks in this repository so tests and demos run without an external LLM. It is
not a replacement for the paper's Java front-end or LLM-based artefact generation.
Unsupported constructs return Indeterminate through the bridge/pipeline.
"""
from __future__ import annotations

import ast
import textwrap
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class LiftedSpec:
    code: str
    bounded: bool = False
    reason: str = ""


class StaticSemanticLifter:
    def lift(self, original_code: str, mutant_code: str, metadata: Optional[dict] = None) -> Optional[LiftedSpec]:
        try:
            orig_func = self._select_function(ast.parse(original_code), prefer_suffix="original")
            mut_func = self._select_function(ast.parse(mutant_code), prefer_suffix="mutant")
            use_bitvec = self._has_bitwise(orig_func) or self._has_bitwise(mut_func)
            orig_expr, orig_pre = self._function_to_expr(orig_func)
            mut_expr, mut_pre = self._function_to_expr(mut_func)
            arg_names = [arg.arg for arg in orig_func.args.args]
            if not arg_names or [a.arg for a in mut_func.args.args] != arg_names:
                return None
            if len(arg_names) != 1:
                # Keep the offline lifter conservative for arrays/matrices/heap objects.
                return None
            var = arg_names[0]
            preconditions = sorted(set(orig_pre + mut_pre))
            code = self._emit_z3(var, orig_expr, mut_expr, preconditions, use_bitvec=use_bitvec)
            return LiftedSpec(code=code, bounded=False, reason="offline supported Python subset")
        except UnsupportedConstruct:
            return None
        except Exception:
            return None

    def _select_function(self, tree: ast.Module, prefer_suffix: str) -> ast.FunctionDef:
        funcs = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
        if not funcs:
            raise UnsupportedConstruct("no function definitions")
        for fn in funcs:
            if fn.name.endswith(prefer_suffix):
                return fn
        return funcs[0]

    def _function_to_expr(self, fn: ast.FunctionDef) -> Tuple[str, List[str]]:
        preconditions: List[str] = []
        body = self._body_without_docstring(fn)
        if self._is_sum_loop_function(fn):
            n = fn.args.args[0].arg
            return f"(({n} * ({n} - 1)) / 2)", [f"{n} >= 0"]

        # Pattern: if cond: return a; return b  -> If(cond, a, b)
        if len(body) >= 2 and isinstance(body[0], ast.If):
            first = body[0]
            if len(first.body) == 1 and isinstance(first.body[0], ast.Return):
                else_expr = self._find_final_return(body[1:])
                cond = self._expr_to_z3(first.test)
                then_expr = self._expr_to_z3(first.body[0].value)
                return f"If({cond}, {then_expr}, {else_expr})", preconditions

        return_expr = self._find_final_return(body)
        return return_expr, preconditions

    def _find_final_return(self, statements: List[ast.stmt]) -> str:
        assignments: Dict[str, ast.AST] = {}
        for stmt in statements:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                assignments[stmt.targets[0].id] = stmt.value
            elif isinstance(stmt, ast.Return):
                if isinstance(stmt.value, ast.Name) and stmt.value.id in assignments:
                    return self._expr_to_z3(assignments[stmt.value.id])
                return self._expr_to_z3(stmt.value)
        raise UnsupportedConstruct("function has no return")

    def _is_sum_loop_function(self, fn: ast.FunctionDef) -> bool:
        # Recognizes: total = 0; for i in range(n): total += i; return total
        if len(fn.args.args) != 1:
            return False
        n = fn.args.args[0].arg
        body = self._body_without_docstring(fn)
        if len(body) < 3:
            return False
        if not (isinstance(body[0], ast.Assign) and len(body[0].targets) == 1 and isinstance(body[0].targets[0], ast.Name)):
            return False
        acc = body[0].targets[0].id
        if not (isinstance(body[0].value, ast.Constant) and body[0].value.value == 0):
            return False
        loop = body[1]
        if not isinstance(loop, ast.For) or not isinstance(loop.target, ast.Name):
            return False
        i = loop.target.id
        if not self._is_range_n(loop.iter, n):
            return False
        if len(loop.body) != 1 or not isinstance(loop.body[0], ast.AugAssign):
            return False
        aug = loop.body[0]
        if not (isinstance(aug.target, ast.Name) and aug.target.id == acc and isinstance(aug.op, ast.Add)):
            return False
        if not (isinstance(aug.value, ast.Name) and aug.value.id == i):
            return False
        final = body[-1]
        return isinstance(final, ast.Return) and isinstance(final.value, ast.Name) and final.value.id == acc

    def _is_range_n(self, node: ast.AST, n: str) -> bool:
        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "range"
            and len(node.args) == 1
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id == n
        )

    def _body_without_docstring(self, fn: ast.FunctionDef) -> List[ast.stmt]:
        body = list(fn.body)
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
            return body[1:]
        return body

    def _has_bitwise(self, fn: ast.FunctionDef) -> bool:
        return any(isinstance(node, ast.BinOp) and isinstance(node.op, (ast.BitAnd, ast.BitOr, ast.BitXor, ast.LShift, ast.RShift)) for node in ast.walk(fn))

    def _expr_to_z3(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return "True" if node.value else "False"
            if isinstance(node.value, int):
                return str(node.value)
            raise UnsupportedConstruct("unsupported constant")
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return f"(-{self._expr_to_z3(node.operand)})"
        if isinstance(node, ast.BinOp):
            left = self._expr_to_z3(node.left)
            right = self._expr_to_z3(node.right)
            op_map = {
                ast.Add: "+",
                ast.Sub: "-",
                ast.Mult: "*",
                ast.FloorDiv: "/",
                ast.Div: "/",
                ast.Mod: "%",
                ast.BitAnd: "&",
                ast.BitOr: "|",
                ast.BitXor: "^",
            }
            op = op_map.get(type(node.op))
            if op is None:
                raise UnsupportedConstruct("unsupported binary operator")
            return f"({left} {op} {right})"
        if isinstance(node, ast.BoolOp):
            fn = "And" if isinstance(node.op, ast.And) else "Or" if isinstance(node.op, ast.Or) else None
            if fn is None:
                raise UnsupportedConstruct("unsupported bool operator")
            return f"{fn}({', '.join(self._expr_to_z3(v) for v in node.values)})"
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and len(node.comparators) == 1:
            left = self._expr_to_z3(node.left)
            right = self._expr_to_z3(node.comparators[0])
            op_map = {
                ast.Eq: "==",
                ast.NotEq: "!=",
                ast.Lt: "<",
                ast.LtE: "<=",
                ast.Gt: ">",
                ast.GtE: ">=",
            }
            op = op_map.get(type(node.ops[0]))
            if op is None:
                raise UnsupportedConstruct("unsupported comparison")
            return f"({left} {op} {right})"
        if isinstance(node, ast.IfExp):
            return f"If({self._expr_to_z3(node.test)}, {self._expr_to_z3(node.body)}, {self._expr_to_z3(node.orelse)})"
        raise UnsupportedConstruct(f"unsupported expression: {ast.dump(node)}")

    def _emit_z3(self, var: str, original_expr: str, mutant_expr: str, preconditions: List[str], use_bitvec: bool = False) -> str:
        precondition_lines = "\n".join(f"solver.add({p})" for p in preconditions)
        var_decl = f"{var} = BitVec('{var}', 32)" if use_bitvec else f"{var} = Int('{var}')"
        return textwrap.dedent(
            f"""
            from z3 import *
            {var_decl}
            solver = Solver()
            nsev_bounded = False
            nsev_observation = 'return_value'
            {precondition_lines}
            original_observation = {original_expr}
            mutant_observation = {mutant_expr}
            solver.add(original_observation != mutant_observation)
            """
        ).strip()


class UnsupportedConstruct(Exception):
    pass

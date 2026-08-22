import ast
import operator
import re
import math
import logging

logger = logging.getLogger(__name__)

# Supported safe operators
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

def _eval_expr(node):
    if isinstance(node, ast.Constant):  # Number
        return node.value
    elif isinstance(node, ast.BinOp):
        left = _eval_expr(node.left)
        right = _eval_expr(node.right)
        op_type = type(node.op)
        if op_type in SAFE_OPERATORS:
            return SAFE_OPERATORS[op_type](left, right)
        raise ValueError(f"Unsupported operator: {op_type.__name__}")
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_expr(node.operand)
        op_type = type(node.op)
        if op_type in SAFE_OPERATORS:
            return SAFE_OPERATORS[op_type](operand)
        raise ValueError(f"Unsupported operator: {op_type.__name__}")
    else:
        raise ValueError(f"Unsupported AST node: {type(node).__name__}")

def calculate(query: str) -> str:
    """Evaluate mathematical expression from query string."""
    try:
        # Preprocess percentage queries e.g. "17% of 8500" -> "8500 * (17 / 100)"
        pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*of\s*(\d+(?:\.\d+)?)", query, re.IGNORECASE)
        if pct_match:
            pct, val = float(pct_match.group(1)), float(pct_match.group(2))
            res = val * (pct / 100.0)
            return f"Result: {res:g}"

        # Extract mathematical expression from string e.g. "calculate 25 * 48" -> "25 * 48"
        expr = re.sub(r"[^0-9\+\-\*\/\%\(\)\.\^]", "", query).strip()
        expr = expr.replace("^", "**")

        if not expr:
            return "Could not find a valid math expression to calculate."

        node = ast.parse(expr, mode='eval').body
        res = _eval_expr(node)
        return f"Result: {res:g}"
    except Exception as e:
        logger.error(f"Calculator error: {e}")
        return f"Could not calculate expression: {e}"

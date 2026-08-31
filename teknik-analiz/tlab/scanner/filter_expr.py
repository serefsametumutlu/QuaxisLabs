"""Güvenli karşılaştırma dilbilgisi — `config/scans.yaml` preset'lerinin
`expr:` alanı için. `eval()`/`exec()` KULLANILMAZ (görev metninin AÇIKÇA
yasakladığı şey) — Python'ın `ast` modülüyle KISITLI bir düğüm kümesi
(karşılaştırma, `and`/`or`/`not`, sayı/metin/bool sabitleri, isim
başvuruları) doğrulanıp yorumlanır. Herhangi bir fonksiyon çağrısı,
öznitelik erişimi, indeksleme, import vb. `FilterExprError` fırlatır.

Örnek: `"score >= 0.7 and rank_pct <= 10"` — `score`/`rank_pct` sinyalin
`payload`sındaki (veya `last_state`teki) alanlara karşılık gelir; namespace
`_signal_passes_filter`'ın verdiği düz `dict[str, Any]`dir."""

from __future__ import annotations

import ast
from typing import Any

_ALLOWED_COMPARE_OPS = (
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.In, ast.NotIn,
)


class FilterExprError(ValueError):
    pass


def _eval_node(node: ast.AST, namespace: dict[str, Any]) -> Any:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body, namespace)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float, str, bool)) or node.value is None:
            return node.value
        raise FilterExprError(f"Desteklenmeyen sabit türü: {type(node.value)}")
    if isinstance(node, ast.Name):
        return namespace.get(node.id)
    if isinstance(node, (ast.Tuple, ast.List)):
        return tuple(_eval_node(el, namespace) for el in node.elts)
    if isinstance(node, ast.BoolOp):
        values = [_eval_node(v, namespace) for v in node.values]
        if isinstance(node.op, ast.And):
            return all(bool(v) for v in values)
        if isinstance(node.op, ast.Or):
            return any(bool(v) for v in values)
        raise FilterExprError(f"Desteklenmeyen mantıksal operatör: {node.op}")
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return not bool(_eval_node(node.operand, namespace))
    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, namespace)
        for op, comparator in zip(node.ops, node.comparators, strict=True):
            if not isinstance(op, _ALLOWED_COMPARE_OPS):
                raise FilterExprError(f"Desteklenmeyen karşılaştırma operatörü: {op}")
            right = _eval_node(comparator, namespace)
            if left is None or right is None:
                result = isinstance(op, (ast.Eq,)) and left == right
                result = result or (isinstance(op, ast.NotEq) and left != right)
                if not result:
                    return False
                left = right
                continue
            try:
                ok = _compare(op, left, right)
            except TypeError:
                return False
            if not ok:
                return False
            left = right
        return True
    raise FilterExprError(f"Desteklenmeyen ifade düğümü: {type(node).__name__}")


def _compare(op: ast.cmpop, left: Any, right: Any) -> bool:
    if isinstance(op, ast.Eq):
        return bool(left == right)
    if isinstance(op, ast.NotEq):
        return bool(left != right)
    if isinstance(op, ast.Lt):
        return bool(left < right)
    if isinstance(op, ast.LtE):
        return bool(left <= right)
    if isinstance(op, ast.Gt):
        return bool(left > right)
    if isinstance(op, ast.GtE):
        return bool(left >= right)
    if isinstance(op, ast.In):
        return left in right
    if isinstance(op, ast.NotIn):
        return left not in right
    raise FilterExprError(f"Desteklenmeyen karşılaştırma operatörü: {op}")


def eval_filter_expr(expr: str, namespace: dict[str, Any]) -> bool:
    """`expr`i `namespace` (ör. `signal.payload` + birkaç standart alan)
    sözlüğüne karşı değerlendirir. Sözdizimi hatası veya izin verilmeyen bir
    düğüm bulunursa `FilterExprError` fırlatır — çağıran (bkz. `cli.py::
    _signal_passes_filter`) bunu preset YAML'ında bir yapılandırma hatası
    olarak ele almalı, sessizce yutmamalı."""
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise FilterExprError(f"Sözdizimi hatası: {exc}") from exc
    return bool(_eval_node(tree, namespace))

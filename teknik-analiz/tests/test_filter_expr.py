"""tlab.scanner.filter_expr — güvenli karşılaştırma dilbilgisi."""

from __future__ import annotations

import pytest

from tlab.scanner.filter_expr import FilterExprError, eval_filter_expr


def test_basic_comparison() -> None:
    ns = {"score": 0.8}
    assert eval_filter_expr("score >= 0.7", ns) is True
    assert eval_filter_expr("score < 0.5", ns) is False


def test_and_or_not() -> None:
    ns = {"a": 1, "b": 2}
    assert eval_filter_expr("a == 1 and b == 2", ns) is True
    assert eval_filter_expr("a == 1 and b == 3", ns) is False
    assert eval_filter_expr("a == 1 or b == 3", ns) is True
    assert eval_filter_expr("not (a == 2)", ns) is True


def test_string_equality_and_in() -> None:
    ns = {"event": "alpha_entry"}
    assert eval_filter_expr("event == 'alpha_entry'", ns) is True
    assert eval_filter_expr("event in ('alpha_entry', 'alpha_exit')", ns) is True
    assert eval_filter_expr("event in ('alpha_exit',)", ns) is False


def test_missing_field_treated_as_none_not_error() -> None:
    ns = {"score": 0.8}
    # `unknown` namespace'te yok -> None; sayısal karşılaştırmada False'a düşer,
    # hata FIRLATMAZ (bkz. eval_filter_expr docstring'i — None güvenli ele alınır).
    assert eval_filter_expr("unknown >= 5", ns) is False


@pytest.mark.parametrize(
    "expr",
    [
        "__import__('os').system('echo pwned')",
        "score.bit_length()",
        "score.__class__",
        "[x for x in range(3)]",
        "lambda: 1",
        "score = 5",
    ],
)
def test_dangerous_or_unsupported_expressions_are_blocked(expr: str) -> None:
    with pytest.raises(FilterExprError):
        eval_filter_expr(expr, {"score": 0.8})


def test_syntax_error_raises_filter_expr_error() -> None:
    with pytest.raises(FilterExprError):
        eval_filter_expr("score >=", {"score": 0.8})

"""Statik lookahead/repaint denetimi.

`tlab/features` ve `tlab/indicators` altındaki kodu ast ile tarar, riskli
desenleri raporlar.

Ciddiyet:
- error: kesin lookahead deseni (df.shift(negatif), rolling(center=True))
- warning: riskli ama bağlama bağlı desen (argrelextrema/find_peaks import'u,
  .iloc[i+...] deseni, index[-1] ötesine datetime üretimi şüphesi)
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

SCAN_DIRS = ("tlab/features", "tlab/indicators")

_FIND_PEAKS_NAMES = {"find_peaks", "argrelextrema"}


@dataclass(frozen=True)
class LintIssue:
    file: str
    lineno: int
    code: str
    message: str
    severity: str  # "error" | "warning"

    def __str__(self) -> str:
        return f"{self.file}:{self.lineno}: [{self.severity}] {self.code}: {self.message}"


class _LookaheadVisitor(ast.NodeVisitor):
    def __init__(self, file: str) -> None:
        self.file = file
        self.issues: list[LintIssue] = []

    def _add(self, node: ast.AST, code: str, message: str, severity: str) -> None:
        self.issues.append(LintIssue(self.file, getattr(node, "lineno", 0), code, message, severity))

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        attr = func.attr if isinstance(func, ast.Attribute) else None
        name = func.id if isinstance(func, ast.Name) else None

        if attr == "shift":
            arg = node.args[0] if node.args else next(
                (kw.value for kw in node.keywords if kw.arg == "periods"), None
            )
            if isinstance(arg, ast.UnaryOp) and isinstance(arg.op, ast.USub):
                self._add(node, "LA001", "shift(negatif) — geleceğe bakış (lookahead)", "error")

        if attr == "rolling":
            for kw in node.keywords:
                if kw.arg == "center" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    self._add(node, "LA002", "rolling(center=True) — merkezi pencere, geleceğe bakar", "error")

        if name in _FIND_PEAKS_NAMES or attr in _FIND_PEAKS_NAMES:
            self._add(
                node,
                "LA003",
                "find_peaks/argrelextrema sonucunu doğrudan sinyal barına yazma; "
                "onay barına (pivot + right) kaydır",
                "warning",
            )

        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        target = node.value
        is_iloc = isinstance(target, ast.Attribute) and target.attr == "iloc"
        if is_iloc and self._contains_add(node.slice):
            self._add(
                node, "LA004", ".iloc[i+...] deseni riskli — ileri indeksleme şüphesi", "warning"
            )
        self.generic_visit(node)

    @staticmethod
    def _contains_add(node: ast.AST) -> bool:
        return any(isinstance(sub, ast.BinOp) and isinstance(sub.op, ast.Add) for sub in ast.walk(node))

    def visit_BinOp(self, node: ast.BinOp) -> None:
        if isinstance(node.op, ast.Add):
            left = node.left
            is_index_expr = (
                isinstance(left, ast.Subscript)
                and isinstance(left.value, ast.Attribute)
                and left.value.attr == "index"
            )
            if is_index_expr:
                self._add(
                    node,
                    "LA005",
                    "df.index[...] + ... — index[-1] ötesine datetime üretimi şüphesi",
                    "warning",
                )
        self.generic_visit(node)


def lint_file(path: Path) -> list[LintIssue]:
    """Tek bir .py dosyasını tarar."""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    visitor = _LookaheadVisitor(str(path))
    visitor.visit(tree)
    return visitor.issues


def lint_paths(root: Path, scan_dirs: tuple[str, ...] = SCAN_DIRS) -> list[LintIssue]:
    """root altında scan_dirs dizinlerindeki tüm .py dosyalarını tarar."""
    issues: list[LintIssue] = []
    for rel in scan_dirs:
        target = root / rel
        if not target.exists():
            continue
        for py_file in sorted(target.rglob("*.py")):
            issues.extend(lint_file(py_file))
    return issues


def has_errors(issues: list[LintIssue]) -> bool:
    return any(i.severity == "error" for i in issues)

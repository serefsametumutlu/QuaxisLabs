"""Sahne protokolü -- her `tlab/viz/svg/scenes/*.py` bu şekli döner.

`SceneOut.panels` (tek/çoklu dikey panel) veya `SceneOut.two_up` (iki yan
yana panel, artifact'in `twoUp` karşılığı) -- ikisi birden DOLU olmaz."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import pandas as pd

from tlab.core.types import IndicatorResult
from tlab.viz.svg.theme import SVGTheme


@dataclass(frozen=True)
class PanelOut:
    vb: tuple[float, float]
    svg: str


@dataclass(frozen=True)
class TwoUpOut:
    vb: tuple[float, float]
    svg: str
    cap: str


@dataclass(frozen=True)
class SceneOut:
    title: str
    subtitle: str | None
    badge: str | None
    panels: list[PanelOut] | None = None
    two_up: list[TwoUpOut] | None = None
    side: PanelOut | None = None


class Scene(Protocol):
    def build(self, result: IndicatorResult, df: pd.DataFrame, theme: SVGTheme) -> SceneOut: ...

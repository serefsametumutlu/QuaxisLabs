"""Faz 0, İş 3 — görsel gerileme (golden) testi.

Kökeni: `docs/TANI_VE_YOL_HARITASI_v2.md` Bölüm 1.6 — tasarım gerilemeleri şu
ana kadar ancak kullanıcı fark edince yakalanıyordu (bilanco-radar tarafında
`kart-tasarim-sistemi` skill'inin dayattığı "PNG üret -> gör -> düzelt" döngüsünün
grafik tarafındaki karşılığı hiç yoktu). Bu dosya o boşluğu kapatıyor: sabit,
SENTETİK (deterministik, ağdan bağımsız) bir OHLCV üzerinde üç göstergenin
render çıktısını onaylı bir referansla karşılaştırıyor.

Şu an renderer Plotly kullandığı (`tlab/viz/renderer.py::render` bir
`plotly.graph_objects.Figure` döner) için karşılaştırma `fig.to_dict()`'in
KARARLI (sıralanmış, yuvarlanmış) bir JSON metni üzerinden yapılıyor. Faz
3'te renderer saf SVG motoruna geçtiğinde YALNIZCA `normalize_figure()`
değişecek (SVG metnini döndürecek şekilde) -- geri kalan her şey (dosya
okuma/yazma, `--update-golden`, karşılaştırma mesajı) AYNI kalır; bu yüzden
karşılaştırma mantığı bilinçli olarak `normalize_figure()`'dan AYRI tutuldu.

`pytest --update-golden tests/test_viz/test_golden.py` ile referanslar
yeniden üretilir -- bayrak OLMADAN hiçbir test golden dosyayı YAZMAZ."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from tests.test_harmonics.fixtures import build_gartley_ohlcv
from tlab.indicators.harmonics.scanner_indicator import HarmonicIndicator, HarmonicParams
from tlab.indicators.patterns.double_top_bottom import (
    DoubleTopBottomIndicator,
    DoubleTopBottomParams,
)
from tlab.indicators.structure.price_structure import PriceStructure, PriceStructureParams
from tlab.indicators.structure.swing_fib_abcd import SwingFibABCD, SwingFibABCDParams
from tlab.testing.fixtures import make_trend
from tlab.viz.renderer import render
from tlab.viz.svg import render_svg

GOLDEN_DIR = Path(__file__).parent / "golden"


def _json_default(obj: Any) -> Any:
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    raise TypeError(f"JSON'a çevrilemeyen tip: {type(obj)}")


def _round_floats(obj: Any) -> Any:
    """`json.dumps`'un `default`'u yalnızca JSON'un KENDİSİNİN serileştiremediği
    tiplerde çağrılır -- sıradan Python `float`'lar (ör. numpy `.tolist()`
    çıktısı) bu yoldan YUVARLANMAZ. Platformlar/ numpy sürümleri arası ondalık
    basamak gürültüsüne karşı, golden karşılaştırmasından ÖNCE ayrıca
    yuvarlıyoruz (6 basamak -- grafik koordinatları için fazlasıyla yeterli
    hassasiyet, gürültüyü ise eler)."""
    if isinstance(obj, float):
        return round(obj, 6)
    if isinstance(obj, dict):
        return {k: _round_floats(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round_floats(v) for v in obj]
    return obj


def normalize_figure(fig: Any) -> str:
    """Plotly `Figure` -> kararlı (deterministik, anahtara göre sıralanmış)
    JSON metni.

    FAZ 3 NOTU: bu fonksiyon golden karşılaştırmasının render-motoruna BAĞIMLI
    TEK yeri. SVG motorüne geçildiğinde `fig.to_dict()` yerine üretilen SVG
    metni (whitespace-normalize edilmiş) döndürülecek şekilde DEĞİŞTİRİLECEK;
    bu dosyadaki geri kalan her şey (dosya okuma/yazma, `--update-golden`
    bayrağı, karşılaştırma/hata mesajı) DEĞİŞMEYECEK."""
    raw = fig.to_dict()
    # `layout.template` taşıdığı ~50 iz tipinin (bar/barpolar/carpet/...) TAMAMI
    # için Plotly'nin KENDİ genel varsayılan stilini gömer -- bunların neredeyse
    # tamamını biz hiç kullanmıyoruz ve içerikleri `pio.templates.default`'a
    # (SÜREÇ genelinde paylaşılan, testler arası mutasyona açık global bir
    # ayar) bağlı; bizim çizdiğimiz hiçbir şeyi YANSITMAZ. Golden karşılaştırması
    # yalnızca BU projenin ürettiği çizimi hedeflediği için atılıyor -- gerçek
    # renk/stil kararlarımız zaten iz (trace) düzeyinde ayrı ayrı seçiliyor.
    raw.get("layout", {}).pop("template", None)
    normalized = _round_floats(json.loads(json.dumps(raw, default=_json_default)))
    return json.dumps(normalized, sort_keys=True, indent=2, ensure_ascii=False)


def _assert_matches_golden(
    actual: str, name: str, request: pytest.FixtureRequest, ext: str = "json",
) -> None:
    path = GOLDEN_DIR / f"{name}.{ext}"
    if request.config.getoption("--update-golden"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(actual, encoding="utf-8")
        return
    if not path.exists():
        pytest.fail(
            f"Golden dosyası yok: {path}. İlk kez oluşturmak için "
            f"`pytest --update-golden tests/test_viz/test_golden.py` çalıştır."
        )
    expected = path.read_text(encoding="utf-8")
    assert actual == expected, (
        f"'{name}' golden karşılaştırması BAŞARISIZ -- görsel çıktı değişti. "
        "Kasıtlı bir tasarım değişikliğiyse `pytest --update-golden "
        "tests/test_viz/test_golden.py` ile referansı yeniden üret ve NEDEN "
        "değiştiğini yaz; değilse bu bir GÖRSEL GERİLEME, düzelt."
    )


def test_golden_price_structure_dark(request: pytest.FixtureRequest) -> None:
    df = make_trend(n=250, slope=0.15, noise=1.0, seed=42)
    result = PriceStructure(PriceStructureParams())(df)
    result.symbol = "GOLDEN"
    fig = render(result, df, theme="dark")
    _assert_matches_golden(normalize_figure(fig), "price_structure_dark", request)


def test_golden_swing_fib_abcd_light(request: pytest.FixtureRequest) -> None:
    df = make_trend(n=250, slope=0.15, noise=1.0, seed=42)
    result = SwingFibABCD(SwingFibABCDParams())(df)
    result.symbol = "GOLDEN"
    fig = render(result, df, theme="light")
    _assert_matches_golden(normalize_figure(fig), "swing_fib_abcd_light", request)


def test_golden_harmonic_carney_light(request: pytest.FixtureRequest) -> None:
    df = build_gartley_ohlcv()
    params = HarmonicParams(
        left=2, right=2, zigzag_method="fixed",
        confirmation_policy="close_reversal", reversal_bars=1,
    )
    result = HarmonicIndicator("carney", params)(df)
    result.symbol = "GOLDEN"
    fig = render(result, df, theme="light")
    _assert_matches_golden(normalize_figure(fig), "harmonic_carney_light", request)


_DTB_ROWS: list[tuple[float, float, float, float]] = [
    (105, 104, 106, 103), (104, 101, 105, 100), (101, 98, 102, 97),
    (98, 100, 101, 98.5), (100, 103, 104, 99.5), (103, 108, 109, 102),
    (108, 113, 114, 107), (113, 116, 117, 112), (116, 113, 117, 112),
    (113, 110, 114, 109), (110, 105, 111, 104), (105, 101, 106, 100),
    (101, 97, 102, 96), (97, 100, 101, 96.5), (100, 104, 105, 99.5),
    (104, 100, 104.5, 99), (100, 98, 101, 97.5), (98, 103, 104, 97),
    (103, 110, 111, 102), (110, 118, 119, 109), (118, 123, 124, 117),
    (123, 128, 129, 122), (128, 132, 133, 127), (132, 138, 139, 131),
]


def _double_bottom_ohlcv() -> pd.DataFrame:
    """`tests/test_patterns/test_double_top_bottom.py`deki AYNI (pivotları
    `find_pivots`/`alternate_pivots` ile doğrulanmış) küçük çift-dip
    senaryosu -- burada Faz 3'ün SVG motoru için golden referans olarak
    kullanılır (network'ten bağımsız, deterministik)."""
    idx = pd.date_range(
        "2024-01-02", periods=len(_DTB_ROWS), freq="1D", tz="Europe/Istanbul",
    )
    rows = [
        {"open": c, "close": c, "high": h, "low": lo, "volume": 1000.0}
        for _o, c, h, lo in _DTB_ROWS
    ]
    return pd.DataFrame(rows, index=idx)


def test_golden_svg_double_top_bottom_classic(request: pytest.FixtureRequest) -> None:
    df = _double_bottom_ohlcv()
    params = DoubleTopBottomParams(
        left=2, right=2, zigzag_method="fixed",
        min_bars_between=10, prior_trend_lookback=3, prior_trend_min_tstat=0.5,
        min_rise_between_pct=0.0, min_depth_pct=0.0, min_depth_atr=0.0,
    )
    result = DoubleTopBottomIndicator(params)(df)
    result.symbol = "GOLDEN"
    svg_text = render_svg(result, df, theme="classic")
    _assert_matches_golden(svg_text, "svg_double_top_bottom_classic", request, ext="svg")

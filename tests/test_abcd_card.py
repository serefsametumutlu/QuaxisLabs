"""src/render/abcd_card.py testleri (Faz 5 -- ABCD Formasyon kartı).

build_abcd_card_context() saf bir fonksiyondur -- hiçbir ağ/DB isteği
atmaz, elle kurulmuş bir `Signal` + sentetik bir OHLC bar listesi kullanılır
(Kural 11, technical_card.py testleriyle AYNI ilke). Playwright render testi
KASITLI OLARAK YOK -- bu dosya sadece koordinat/formatlama SAF mantığını
doğrular (bkz. görev talimatı: mevcut testlerde ağır Playwright render
testi yok, technical_card.py testleri de aynı şekilde SAF context testleri
+ AYRI, açıkça işaretli birkaç render testinden ibaret; ABCD kartı için
görsel doğrulama scripts/demo_abcd_card.py ile YAPILDI, PNG elle incelendi).
"""

from __future__ import annotations

from datetime import datetime, timedelta

from src.analysis.abcd_pattern import Signal
from src.render import abcd_card


def _bars(n: int = 50, with_open: bool = True) -> list[dict]:
    start = datetime(2026, 1, 1)
    bars = []
    for i in range(n):
        # Basit, monoton olmayan ama negatif olmayan bir seri -- testler
        # gerçek fiyat şeklinden bağımsız, sadece anchor barların
        # üzerine YAZILAN (bkz. _bull_signal/_bear_signal) değerlere bakar.
        base = 50.0 + (i % 7)
        bar = {
            "time": start + timedelta(days=i),
            "high": base + 1.0,
            "low": base - 1.0,
            "close": base,
            "volume": 1000 + i,
        }
        bar["open"] = base - 0.5 if with_open else None
        bars.append(bar)
    return bars


def _bull_signal(bars: list[dict]) -> Signal:
    a_bar, b_bar, c_bar, d_bar = 5, 15, 25, 35
    a_price, b_price, c_price, d_price = 100.0, 80.0, 92.0, 72.0
    bars[a_bar]["high"] = a_price
    bars[b_bar]["low"] = b_price
    bars[c_bar]["high"] = c_price
    bars[d_bar]["low"] = d_price
    signal_bar = d_bar + 5
    return Signal(
        direction=1,
        a_bar=a_bar,
        b_bar=b_bar,
        c_bar=c_bar,
        d_bar=d_bar,
        a_price=a_price,
        b_price=b_price,
        c_price=c_price,
        d_price=d_price,
        signal_bar=signal_bar,
        signal_time=bars[signal_bar]["time"],
        entry_ref=bars[d_bar]["close"],
        fill_ref=bars[signal_bar + 1]["open"] if signal_bar + 1 < len(bars) else float("nan"),
        tp1=d_price + abs(a_price - d_price) * 0.382,
        tp2=c_price,
        sl=d_price - 3.0,
        bc_ratio=abs(c_price - b_price) / abs(a_price - b_price),
        cd_ratio=abs(d_price - c_price) / abs(a_price - b_price),
    )


def _bear_signal(bars: list[dict]) -> Signal:
    a_bar, b_bar, c_bar, d_bar = 5, 15, 25, 35
    a_price, b_price, c_price, d_price = 60.0, 80.0, 68.0, 88.0
    bars[a_bar]["low"] = a_price
    bars[b_bar]["high"] = b_price
    bars[c_bar]["low"] = c_price
    bars[d_bar]["high"] = d_price
    signal_bar = d_bar + 5
    return Signal(
        direction=-1,
        a_bar=a_bar,
        b_bar=b_bar,
        c_bar=c_bar,
        d_bar=d_bar,
        a_price=a_price,
        b_price=b_price,
        c_price=c_price,
        d_price=d_price,
        signal_bar=signal_bar,
        signal_time=bars[signal_bar]["time"],
        entry_ref=bars[d_bar]["close"],
        fill_ref=float("nan"),
        tp1=d_price - abs(a_price - d_price) * 0.382,
        tp2=c_price,
        sl=d_price + 3.0,
        bc_ratio=abs(c_price - b_price) / abs(a_price - b_price),
        cd_ratio=abs(d_price - c_price) / abs(a_price - b_price),
    )


# --- Temel yapı / hiç çökmez -------------------------------------------


def test_context_has_expected_top_level_keys():
    bars = _bars()
    ctx = abcd_card.build_abcd_card_context(bars, _bull_signal(bars), ticker="THYAO", market="BIST", tf="1d")
    for key in (
        "ticker", "market_label", "tf_label", "direction", "direction_label", "direction_class",
        "entry_display", "tp1_display", "tp2_display", "sl_display", "bc_ratio_display", "cd_ratio_display",
        "abcd_table", "chart", "disclaimer", "experimental_note",
    ):
        assert key in ctx


def test_bull_direction_labels():
    bars = _bars()
    ctx = abcd_card.build_abcd_card_context(bars, _bull_signal(bars), ticker="THYAO", market="BIST", tf="1d")
    assert ctx["direction"] == "BUY"
    assert ctx["direction_class"] == "bull"
    assert "AL" in ctx["direction_label"]


def test_bear_direction_labels():
    bars = _bars()
    ctx = abcd_card.build_abcd_card_context(bars, _bear_signal(bars), ticker="THYAO", market="BIST", tf="1d")
    assert ctx["direction"] == "SELL"
    assert ctx["direction_class"] == "bear"
    assert "SAT" in ctx["direction_label"]


# --- Fiyat biçimlendirme -------------------------------------------------


def test_price_display_bist_uses_lira_suffix():
    # entry_ref, D barının GERÇEK kapanışıdır (d_price pivot değeriyle
    # KARIŞTIRILMAZ, bkz. abcd_pattern.Signal docstring'i) -- _bars()'taki
    # d_bar=35 barının "close"u değiştirilmedi, base = 50.0 + (35 % 7) = 50.0.
    bars = _bars()
    ctx = abcd_card.build_abcd_card_context(bars, _bull_signal(bars), ticker="THYAO", market="BIST", tf="1d")
    assert ctx["entry_display"].endswith("₺")
    assert ctx["entry_display"] == "50,00 ₺"


def test_price_display_nasdaq_uses_dollar_prefix():
    bars = _bars()
    ctx = abcd_card.build_abcd_card_context(bars, _bull_signal(bars), ticker="AAPL", market="NASDAQ", tf="1d")
    assert ctx["entry_display"].startswith("$")
    assert ctx["entry_display"] == "$50,00"


def test_ratio_display_scales_to_percent():
    bars = _bars()
    signal = _bull_signal(bars)
    ctx = abcd_card.build_abcd_card_context(bars, signal, ticker="THYAO", market="BIST", tf="1d")
    # bc_ratio = |92-80|/|100-80| = 0.6 -> %60,0
    assert ctx["bc_ratio_display"] == "%60,0"
    # cd_ratio = |72-92|/|100-80| = 1.0 -> %100,0
    assert ctx["cd_ratio_display"] == "%100,0"


# --- ABCD tablo satırları -------------------------------------------------


def test_abcd_table_has_four_ordered_rows_with_correct_prices():
    bars = _bars()
    signal = _bull_signal(bars)
    ctx = abcd_card.build_abcd_card_context(bars, signal, ticker="THYAO", market="BIST", tf="1d")
    labels = [row["label"] for row in ctx["abcd_table"]]
    assert labels == ["A", "B", "C", "D"]
    prices = [row["price_display"] for row in ctx["abcd_table"]]
    assert prices == ["100,00 ₺", "80,00 ₺", "92,00 ₺", "72,00 ₺"]


# --- Grafik koordinatları (candlestick + ABCD noktaları) ------------------


def test_chart_has_data_for_sufficient_bars():
    bars = _bars()
    signal = _bull_signal(bars)
    ctx = abcd_card.build_abcd_card_context(bars, signal, ticker="THYAO", market="BIST", tf="1d")
    assert ctx["chart"]["has_data"] is True


def test_chart_has_no_data_for_insufficient_bars():
    ctx = abcd_card.build_abcd_card_context([], _minimal_signal(), ticker="THYAO", market="BIST", tf="1d")
    assert ctx["chart"]["has_data"] is False


def _minimal_signal() -> Signal:
    return Signal(
        direction=1, a_bar=0, b_bar=0, c_bar=0, d_bar=0,
        a_price=1.0, b_price=1.0, c_price=1.0, d_price=1.0,
        signal_bar=0, signal_time=datetime(2026, 1, 1), entry_ref=1.0, fill_ref=float("nan"),
        tp1=1.0, tp2=1.0, sl=1.0, bc_ratio=0.5, cd_ratio=1.0,
    )


def test_candle_count_matches_bar_count():
    bars = _bars(n=42)
    signal = _bull_signal(bars)
    ctx = abcd_card.build_abcd_card_context(bars, signal, ticker="THYAO", market="BIST", tf="1d")
    assert len(ctx["chart"]["candles"]) == 42


def test_candle_x_positions_are_monotonically_increasing():
    bars = _bars()
    signal = _bull_signal(bars)
    ctx = abcd_card.build_abcd_card_context(bars, signal, ticker="THYAO", market="BIST", tf="1d")
    xs = [float(c["x"]) for c in ctx["chart"]["candles"]]
    assert xs == sorted(xs)
    assert len(set(xs)) == len(xs)  # her bar kendi tekil x'ine sahip


def test_higher_price_maps_to_smaller_y_svg_top_is_high_price():
    """SVG'de y ekseni aşağı doğru artar -- yüksek fiyat KÜÇÜK y (ekranın
    üstü) demektir. A(100) > C(92) > B(80) > D(72) olduğu için
    y(A) < y(C) < y(B) < y(D) olmalı."""
    bars = _bars()
    signal = _bull_signal(bars)
    ctx = abcd_card.build_abcd_card_context(bars, signal, ticker="THYAO", market="BIST", tf="1d")
    points = {p["label"]: float(p["y"]) for p in ctx["chart"]["abcd_points"]}
    assert points["A"] < points["C"] < points["B"] < points["D"]


def test_abcd_point_above_below_matches_pine_alternation_bull():
    bars = _bars()
    signal = _bull_signal(bars)
    ctx = abcd_card.build_abcd_card_context(bars, signal, ticker="THYAO", market="BIST", tf="1d")
    above = {p["label"]: p["above"] for p in ctx["chart"]["abcd_points"]}
    assert above == {"A": True, "B": False, "C": True, "D": False}


def test_abcd_point_above_below_matches_pine_alternation_bear():
    bars = _bars()
    signal = _bear_signal(bars)
    ctx = abcd_card.build_abcd_card_context(bars, signal, ticker="THYAO", market="BIST", tf="1d")
    above = {p["label"]: p["above"] for p in ctx["chart"]["abcd_points"]}
    assert above == {"A": False, "B": True, "C": False, "D": True}


def test_level_lines_present_for_entry_tp1_tp2_sl():
    bars = _bars()
    signal = _bull_signal(bars)
    ctx = abcd_card.build_abcd_card_context(bars, signal, ticker="THYAO", market="BIST", tf="1d")
    chart = ctx["chart"]
    for key in ("entry_line", "tp1_line", "tp2_line", "sl_line"):
        assert chart[key] is not None
        assert chart[key]["price_display"]


def test_open_none_bars_fall_back_to_doji_without_crashing():
    """Karar 3 (BIST günlük veri open=None) senaryosu -- kart ÇÖKMEMELİ,
    mum gövdesi kapanışa (veya önceki kapanışa) düşmelidir."""
    bars = _bars(with_open=False)
    signal = _bull_signal(bars)
    ctx = abcd_card.build_abcd_card_context(bars, signal, ticker="THYAO", market="BIST", tf="1d")
    assert ctx["chart"]["has_data"] is True
    assert len(ctx["chart"]["candles"]) == len(bars)
    for candle in ctx["chart"]["candles"]:
        assert float(candle["body_height"]) >= 1.4  # minimum görünür gövde

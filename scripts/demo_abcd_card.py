"""ABCD Formasyon kartı (Faz 5 — kart tasarımı) için doğrulama demo'su.

Gerçek yfinance/DB bağımlılığı YOKTUR -- sentetik ama YAPISAL OLARAK
GEÇERLİ (Fibonacci oranları tutan) bir A-B-C-D zigzag OHLC serisi + elle
kurulmuş bir `Signal` nesnesiyle `render_card()` uçtan uca çalıştırılır.
`kart-tasarim-sistemi` skill'inin doğrulama döngüsü (SKILL.md madde 1)
gereği: PNG üretilir, `Read` ile açılıp incelenir.

Kullanım:
    python scripts/demo_abcd_card.py            # BUY (bullish) örneği
    python scripts/demo_abcd_card.py --direction sell
    python scripts/demo_abcd_card.py --direction both
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402
from src.analysis.abcd_pattern import Signal  # noqa: E402
from src.render import abcd_card, card  # noqa: E402

config.setup_logging()

_N_BARS = 56
_PIVOT_LOOKBACK = 5


def _build_bars(anchors: dict[int, float], base: float) -> list[dict]:
    """Belirtilen bar indekslerinde (anchors) TAM OLARAK istenen tepe/dip
    değerlerinden geçen, aralarında düz (lineer) rampalarla bağlanan,
    diğer barlarda hafif gürültülü bir OHLC serisi üretir -- sadece
    GÖRSEL DOĞRULAMA amaçlı sentetik veri, gerçek piyasa verisi değildir."""
    keys = sorted(anchors)
    closes: list[float] = []
    for i in range(_N_BARS):
        if i <= keys[0]:
            v = anchors[keys[0]]
        elif i >= keys[-1]:
            v = anchors[keys[-1]]
        else:
            lo = max(k for k in keys if k <= i)
            hi = min(k for k in keys if k >= i)
            if lo == hi:
                v = anchors[lo]
            else:
                t = (i - lo) / (hi - lo)
                v = anchors[lo] + (anchors[hi] - anchors[lo]) * t
        closes.append(v)

    start = datetime(2026, 1, 1)
    bars = []
    prev_close = base
    for i, close in enumerate(closes):
        open_ = prev_close
        noise = 0.4 if i % 2 == 0 else -0.3
        high = max(open_, close) + abs(noise)
        low = min(open_, close) - abs(noise)
        bars.append(
            {
                "time": start + timedelta(days=i),
                "open": round(open_, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(close, 2),
                "volume": 1_000_000 + i * 5_000,
            }
        )
        prev_close = close

    # Pivot fiyatları (a/b/c/d) tam olarak anchor barının high/low'una
    # OTURSUN diye ilgili uçları hassas biçimde üzerine yazılır (yukarıdaki
    # lineer interpolasyon + gürültü, ara noktalarda tam anchor değerine
    # denk gelmeyebilir).
    for idx, value in anchors.items():
        bars[idx]["close"] = round(value, 2)
    return bars


def _build_signal(bars: list[dict], direction: int) -> Signal:
    a_bar, b_bar, c_bar, d_bar = 10, 20, 30, 40
    if direction == 1:  # bullish: A yüksek, B düşük, C yüksek, D düşük
        a_price, b_price, c_price, d_price = 100.0, 80.0, 92.0, 72.0
    else:  # bearish: A düşük, B yüksek, C düşük, D yüksek (aynasal)
        a_price, b_price, c_price, d_price = 60.0, 80.0, 68.0, 88.0

    bars[a_bar]["high" if direction == 1 else "low"] = a_price
    bars[b_bar]["low" if direction == 1 else "high"] = b_price
    bars[c_bar]["high" if direction == 1 else "low"] = c_price
    bars[d_bar]["low" if direction == 1 else "high"] = d_price

    ad_range = abs(a_price - d_price)
    if direction == 1:
        tp1 = d_price + ad_range * 0.382
        sl = d_price - 3.0
    else:
        tp1 = d_price - ad_range * 0.382
        sl = d_price + 3.0
    tp2 = c_price

    signal_bar = d_bar + _PIVOT_LOOKBACK
    fill_bar = signal_bar + 1

    return Signal(
        direction=direction,
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
        fill_ref=bars[fill_bar]["open"] if fill_bar < len(bars) else float("nan"),
        tp1=tp1,
        tp2=tp2,
        sl=sl,
        bc_ratio=abs(c_price - b_price) / abs(a_price - b_price),
        cd_ratio=abs(d_price - c_price) / abs(a_price - b_price),
    )


def _render_one(direction: int, ticker: str, market: str) -> str:
    label = "buy" if direction == 1 else "sell"
    anchors_base = 65.0 if direction == 1 else 55.0
    if direction == 1:
        anchors = {0: 65.0, 10: 100.0, 20: 80.0, 30: 92.0, 40: 72.0, 55: 90.0}
    else:
        anchors = {0: 55.0, 10: 60.0, 20: 80.0, 30: 68.0, 40: 88.0, 55: 70.0}

    bars = _build_bars(anchors, anchors_base)
    signal = _build_signal(bars, direction)

    print(f"\n[{label.upper()}] {len(bars)} sentetik bar, sinyal onay barı: {signal.signal_time}")
    print(f"  A={signal.a_price} B={signal.b_price} C={signal.c_price} D={signal.d_price}")
    print(f"  Entry={signal.entry_ref:.2f}  TP1={signal.tp1:.2f}  TP2={signal.tp2:.2f}  SL={signal.sl:.2f}")
    print(f"  BC oranı={signal.bc_ratio:.3f}  CD oranı={signal.cd_ratio:.3f}")

    context = abcd_card.build_abcd_card_context(
        bars, signal, ticker=ticker, market=market, tf="1d", company_name="Türk Hava Yolları A.O." if ticker == "THYAO" else None
    )

    out_path = config.DATA_DIR / "cards" / f"{ticker}_abcd_{label}.png"
    result_path = card.render_card(context, str(out_path), template_name="abcd_card.html", screenshot_selector="#abcd-card")
    print(f"  PNG üretildi: {result_path}")
    return result_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--direction", choices=["buy", "sell", "both"], default="buy")
    parser.add_argument("--ticker", default="THYAO")
    parser.add_argument("--market", choices=["BIST", "NASDAQ"], default="BIST")
    args = parser.parse_args()

    if args.direction in ("buy", "both"):
        _render_one(1, args.ticker, args.market)
    if args.direction in ("sell", "both"):
        _render_one(-1, args.ticker, args.market)

    print(f"\nDebug HTML: {card._debug_html_path('abcd_card.html')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

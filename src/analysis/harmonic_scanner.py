"""Coklu-sembol, coklu-formasyon Harmonik (Anlik D / V2.2) tarayicisi.

`abcd_scanner.py` ile AYNI mimari (ThreadPoolExecutor, DB'ye/dosyaya
KAYDEDILMEZ, sembol-basina hata toleransi) ama iki farkla:

  1. Detektor `harmonic_xabcd.detect_prz()` -- `pine/harmonic_formations_v1_
     indicator.pine` V2.2'nin ("anlik D", D kendi pivot onayini BEKLEMEDEN
     istatistiksel bolgeye canli girer girmez sinyal) Python karsiligi.
     `abcd_scanner.py`nin kullandigi `abcd_pattern.detect()` (klasik, D
     KENDI pivot onayini bekler) ile KARISTIRILMAZ -- iki ayri, kasitli
     farkli mekanizma (kullanici kararlarina bkz. harmonic_xabcd.py ust notu).
  2. TEK sembolde AYNI ANDA birden fazla formasyon (ABCD + Gartley/Bat/
     Butterfly/Crab) taranabilir -- kullanici talebi (2026-08-19): "abcd
     gartley grab gibi tum formasyonlari secebileyim ... birde hepsi
     secenegi olsun ... her formasyon cesidinde ne sinyali oldugunu liste
     liste yazsin". Verimlilik icin sembol basina TEK fetch yapilir, secilen
     TUM formasyonlar o veri uzerinde taranir (ayri ayri fetch YAPILMAZ).

Guven etiketleri `docs/spec/HARMONIC_INSTANT_D_BACKTEST.md` (tam BIST, 657
sembol, ~2 yil, R-multiple bazli) SONUCLARINA dayanir -- TABLO SABIT
KODLANMISTIR (o rapor yeniden uretilirse bu tablo da elle guncellenmeli,
otomatik okuma YOK -- basitlik icin bilincli tercih). `min_trades_trustworthy`
esigi (100) o raporda TUM hucreler icin zaten gecilmisti, dolayisiyla burada
"orneklem kucuk" etiketi YOK -- sadece "gecmiste karli/karsiz" ayrimi var,
sinyal HICBIR ZAMAN gizlenmez (abcd_scanner.py ile AYNI ilke).
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from src.analysis import harmonic_xabcd
from src.analysis.harmonic_xabcd import Params, PrzEvent, detect_prz
from src.fetchers.abcd_data import fetch_ohlcv_abcd

ALL_FORMATIONS: dict[str, Params] = {"ABCD": harmonic_xabcd.ABCD_PRESET, **harmonic_xabcd.HARMONIC_XABCD_PRESETS}
FORMATION_NAMES: tuple[str, ...] = tuple(ALL_FORMATIONS.keys())  # ("ABCD","GARTLEY","BAT","BUTTERFLY","CRAB")

# `docs/spec/HARMONIC_INSTANT_D_BACKTEST.md` tablosu -- (formasyon, yon, tf) -> profit factor.
# Sadece 1D/240 backtest edildi; baska bir tf istenirse `_PF_TABLE`de YOK,
# `guven_etiketi()` bunu acikca "dogrulanmadi" olarak isaretler (gizlemez).
_PF_TABLE: dict[tuple[str, str, str], float] = {
    ("CRAB", "LONG", "1D"): 1.40,
    ("ABCD", "LONG", "1D"): 1.20,
    ("GARTLEY", "LONG", "1D"): 1.10,
    ("BUTTERFLY", "LONG", "240"): 1.06,
    ("BUTTERFLY", "LONG", "1D"): 0.99,
    ("BUTTERFLY", "SHORT", "1D"): 0.95,
    ("ABCD", "SHORT", "1D"): 0.94,
    ("BAT", "LONG", "240"): 0.89,
    ("GARTLEY", "LONG", "240"): 0.86,
    ("BAT", "SHORT", "1D"): 0.85,
    ("ABCD", "LONG", "240"): 0.84,
    ("GARTLEY", "SHORT", "1D"): 0.84,
    ("BAT", "SHORT", "240"): 0.81,
    ("CRAB", "SHORT", "240"): 0.75,
    ("CRAB", "LONG", "240"): 0.71,
    ("BAT", "LONG", "1D"): 0.67,
    ("BUTTERFLY", "SHORT", "240"): 0.63,
    ("ABCD", "SHORT", "240"): 0.62,
    ("CRAB", "SHORT", "1D"): 0.56,
    ("GARTLEY", "SHORT", "240"): 0.51,
}


def guven_etiketi(formation: str, tf: str, direction: int) -> str:
    """(formasyon, tf, yon) icin `HARMONIC_INSTANT_D_BACKTEST.md`e dayanan
    guven etiketi. Sinyali GIZLEMEZ, sadece gecmiste bu kombinasyonun karli
    cikip cikmadigini bildirir (abcd_scanner.guven_etiketi ile AYNI ilke)."""
    yon = "LONG" if direction > 0 else "SHORT"
    pf = _PF_TABLE.get((formation, yon, tf))
    if pf is None:
        return "◻ DOĞRULANMADI (bu zaman diliminde backtest yok, ⚠️ D anlık = repaint edebilir)"
    if pf >= 1.10:
        return f"✅ GÜVENİLİR (backtest PF={pf:.2f}, kârlı)"
    if pf >= 0.95:
        return f"◻ NÖTR (backtest PF={pf:.2f}, başabaş civarı)"
    return f"⚠️ ZAYIF (backtest PF={pf:.2f}, kârsız çıktı)"


@dataclass
class ScannedPrz:
    symbol: str
    formation: str
    event: PrzEvent
    bars_ago: int  # 0 = bu bar (en guncel) icinde D bolgesine deydi
    confidence: str


@dataclass
class HarmonicScanResult:
    tf: str
    scanned_at: datetime
    lookback_bars: int
    formations: tuple[str, ...]  # taranan formasyonlar (siralamasi rapor sirasi)
    buys: dict[str, list[ScannedPrz]]  # formasyon adi -> sinyaller
    sells: dict[str, list[ScannedPrz]]
    errors: dict[str, str]


def _scan_one_symbol(
    symbol: str, tf: str, formation_names: tuple[str, ...], lookback_bars: int, n_bars: int
) -> dict[str, tuple[list[ScannedPrz], list[ScannedPrz]]]:
    """Sembolu TEK KEZ ceker, secilen TUM formasyonlari ayni veri uzerinde
    tarar (verimlilik -- bkz. modul ust notu)."""
    df = fetch_ohlcv_abcd(symbol, tf, n_bars)
    if df.empty:
        raise RuntimeError("veri donmedi (bos DataFrame)")

    n = len(df)
    out: dict[str, tuple[list[ScannedPrz], list[ScannedPrz]]] = {}
    for formation in formation_names:
        params = ALL_FORMATIONS[formation]
        events = detect_prz(df, params)
        buys: list[ScannedPrz] = []
        sells: list[ScannedPrz] = []
        for ev in events:
            bars_ago = (n - 1) - ev.signal_bar
            if bars_ago < 0 or bars_ago >= lookback_bars:
                continue
            scanned = ScannedPrz(
                symbol=symbol,
                formation=formation,
                event=ev,
                bars_ago=bars_ago,
                confidence=guven_etiketi(formation, tf, ev.direction),
            )
            (buys if ev.direction > 0 else sells).append(scanned)
        out[formation] = (buys, sells)
    return out


def scan(
    symbols: list[str],
    tf: str,
    formation_names: tuple[str, ...],
    lookback_bars: int,
    n_bars: int = 1000,
    workers: int = 8,
    on_progress: Callable[[int, int], None] | None = None,
) -> HarmonicScanResult:
    """`symbols` evreninde, `formation_names`teki HER formasyonu (ABCD ve/
    veya Gartley/Bat/Butterfly/Crab) `tf`de tarar, son `lookback_bars` bar
    icinde D bolgesine deymis (anlik) sinyalleri formasyon basina toplar.

    `formation_names = harmonic_scanner.FORMATION_NAMES` (5 formasyonun
    TAMAMI) verilirse -- Telegram'daki "Hepsi" secenegi budur."""
    buys: dict[str, list[ScannedPrz]] = {f: [] for f in formation_names}
    sells: dict[str, list[ScannedPrz]] = {f: [] for f in formation_names}
    errors: dict[str, str] = {}
    total = len(symbols)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_scan_one_symbol, symbol, tf, formation_names, lookback_bars, n_bars): symbol
            for symbol in symbols
        }
        completed = 0
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                per_formation = future.result()
                for formation, (f_buys, f_sells) in per_formation.items():
                    buys[formation].extend(f_buys)
                    sells[formation].extend(f_sells)
            except Exception as exc:  # sembol-basina toplanir, ASLA firlatilmaz
                errors[symbol] = str(exc)
            completed += 1
            if on_progress:
                on_progress(completed, total)

    for formation in formation_names:
        buys[formation].sort(key=lambda s: (s.bars_ago, s.symbol))
        sells[formation].sort(key=lambda s: (s.bars_ago, s.symbol))

    return HarmonicScanResult(
        tf=tf,
        scanned_at=datetime.now(timezone.utc),
        lookback_bars=lookback_bars,
        formations=formation_names,
        buys=buys,
        sells=sells,
        errors=errors,
    )


_MDV2_SPECIAL = r"_*[]()~`>#+-=|{}.!"


def _escape_mdv2(text: str) -> str:
    return "".join(f"\\{c}" if c in _MDV2_SPECIAL else c for c in text)


def _escape_code_block(text: str) -> str:
    return text.replace("\\", "\\\\").replace("`", "\\`")


def _fmt_line(item: ScannedPrz) -> str:
    ev = item.event
    ago = "bu bar" if item.bars_ago == 0 else f"{item.bars_ago} bar once"
    return (
        f"{item.symbol} | D bolgesine giris: {ago} | giris {ev.entry_ref:.4g} | "
        f"TP1 {ev.tp1:.4g} | TP2 {ev.tp2:.4g} | SL {ev.sl:.4g} | {item.confidence}"
    )


def format_report(result: HarmonicScanResult, markdown: bool = False) -> str:
    """Her formasyon icin AYRI baslik + BUY/SELL listesi (kullanici talebi:
    'her formasyon cesidinde ne sinyali oldugunu liste liste yazsin')."""
    title = f"Harmonik Anlik-D Tarama -- {result.tf} (son {result.lookback_bars} bar)"
    header = f"*{_escape_mdv2(title)}*" if markdown else title

    body_lines = [
        "⚠️ D anlik/onaysiz -- REPAINT EDEBILIR. Guven etiketleri gecmis backtest "
        "sonucuna gore (sinyal gizlenmez, sadece bilgilendirir).",
        "",
    ]
    for formation in result.formations:
        body_lines.append(f"── {formation} ──")
        f_buys = result.buys.get(formation, [])
        f_sells = result.sells.get(formation, [])
        body_lines.append("BUY:")
        body_lines.extend((_fmt_line(s) for s in f_buys) if f_buys else ["  (yok)"])
        body_lines.append("SELL:")
        body_lines.extend((_fmt_line(s) for s in f_sells) if f_sells else ["  (yok)"])
        body_lines.append("")

    if markdown:
        body = "\n".join(_escape_code_block(line) for line in body_lines)
        parts = [header, f"```\n{body}\n```"]
    else:
        parts = [header, "\n".join(body_lines)]

    if result.errors:
        err_text = f"{len(result.errors)} sembol basarisiz oldu"
        parts.append(_escape_mdv2(err_text) if markdown else err_text)

    return "\n".join(parts)

"""Coklu-sembol Momentum Confluence (V1/V2) tarayicisi.

`harmonic_scanner.py` ile AYNI mimari (ThreadPoolExecutor, DB'ye/dosyaya
KAYDEDILMEZ, sembol-basina hata toleransi) -- tek fark: `momentum_confluence`
kaynakta SADECE LONG uretir (bkz. o modulun ust notu), bu yuzden BUY/SELL
ayrimi degil TEK bir sinyal listesi doner.

Guven etiketleri `docs/spec/MOMENTUM_CONFLUENCE_OPTIMIZASYON.md` (tam BIST,
657 sembol, ~2 yil, R-multiple bazli -- V1_BASELINE/V2_BASELINE satirlari)
SONUCLARINA dayanir -- TABLO SABIT KODLANMISTIR (`harmonic_scanner._PF_TABLE`
ile AYNI ilke: o rapor yeniden uretilirse burasi da elle guncellenmeli).

BILINEN SINIR (2026-08-19, canli kullanici karsilastirmasi -- kapatilmadi,
kullanici kararla kabul etti): bazi sembollerde (orn. AKBNK, GWIND) taranan
sinyal TradingView'in gercek Pine calistirmasinda GORUNMUYOR, digerlerinde
(ISMEN, TURSG) BIREBIR eslesiyor. Kok neden ARANDI -- Pine kaynagiyla
(`pine/momentum confluence 1.txt`) satir satir karsilastirma YAPILDI, port
hatasi BULUNAMADI; AKBNK'de TradingView'in gosterdigi EMA5/8/13 (68.01/
68.13/68.12) ile bizim hesabimiz (68.03/68.16/68.15) ARASINDA kucuk (~0.03
puan) ama GERCEK bir fark var -- temettu duzeltmesinden KAYNAKLANMIYOR
(AKBNK'nin son temettusu 2026-03-26, ~900 4H bar once -- EMA5/8/13'un
etkin hafizasinin COK otesinde). En olasi aciklama: yfinance (ucretsiz/
gayriresmi BIST kaynagi) ile TradingView'in kendi veri saglayicisi arasinda
ufak, sistemik fiyat farklari var; bunlar tek basina esik-disi kalsa da
(sikisma/hacim/kirilim marjlarimiz BU ornekte rahat, sinirda DEGIL), TRF'nin
KUMULATIF/MANDALLI upward/downward/flip durum makinesi gecmiste bir yerde
BU farklara duyarli sekilde ayrisabilir. Tek bir kod hatasi DEGIL -- ucretsiz
veri kaynaginin dogal bir sinirlamasi. Sinyaller "guclu aday" olarak
degerlendirilmeli, TradingView'de gorsel teyit onerilir.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from src.analysis.momentum_confluence import Params, Signal, detect
from src.fetchers.abcd_data import fetch_ohlcv_abcd

VARIANT_LABELS: dict[str, str] = {"v1": "Momentum Confluence V1", "v2": "Momentum Confluence V2"}

# docs/spec/MOMENTUM_CONFLUENCE_OPTIMIZASYON.md -- V1_BASELINE/V2_BASELINE
# satirlari (profit factor). Sadece 1D/240 backtest edildi.
_PF_TABLE: dict[tuple[str, str], float] = {
    ("v1", "240"): 1.25,
    ("v1", "1D"): 1.18,
    ("v2", "240"): 1.41,
    ("v2", "1D"): 1.01,
}


def guven_etiketi(variant: str, tf: str) -> str:
    """(varyant, tf) icin `MOMENTUM_CONFLUENCE_OPTIMIZASYON.md`e dayanan guven
    etiketi. Sinyali GIZLEMEZ, sadece gecmiste bu kombinasyonun karli cikip
    cikmadigini bildirir (`harmonic_scanner.guven_etiketi` ile AYNI ilke)."""
    pf = _PF_TABLE.get((variant, tf))
    if pf is None:
        return "◻ DOĞRULANMADI (bu zaman diliminde backtest yok)"
    if pf >= 1.10:
        return f"✅ GÜVENİLİR (backtest PF={pf:.2f}, kârlı)"
    if pf >= 0.95:
        return f"◻ NÖTR (backtest PF={pf:.2f}, başabaş civarı)"
    return f"⚠️ ZAYIF (backtest PF={pf:.2f}, kârsız çıktı)"


@dataclass
class ScannedSignal:
    symbol: str
    signal: Signal
    bars_ago: int  # 0 = bu bar (en guncel) icinde sinyal olustu


@dataclass
class MomentumScanResult:
    tf: str
    variant: str
    scanned_at: datetime
    lookback_bars: int
    signals: list[ScannedSignal]
    errors: dict[str, str]


def _scan_one_symbol(
    symbol: str, tf: str, variant: str, params: Params, lookback_bars: int, n_bars: int
) -> list[ScannedSignal]:
    """TEK GECIS, HER ZAMAN TAM DOGRULUK (`skip_recent_30m=False`, varsayilan).

    GERI ALINAN DENEY (2026-08-19): bir onceki surum "ucuz ilk gecis"
    (`skip_recent_30m=True`, SADECE 1sa kaynak) yapip SADECE aday bulunan
    sembolu dogru veriyle yeniden cekiyordu -- ag hacmini yariya indiriyordu
    AMA YANLIS bir varsayima dayaniyordu: 1sa-SADECE veri sadece son 1-2
    bari degil, SON ~55 GUNUN TAMAMINI farkli (30dk hibrit YOK) insa ediyor,
    bu da EMA/TRF'nin recursive durumunu o pencerede GENISCE degistirip hem
    SAHTE sinyal (HURGZ, eski bug) hem SESSIZCE KACAN GERCEK sinyal (ISMEN,
    canli kullanici raporu -- ucuz gecis HICBIR sinyal bulmuyordu, dogru
    veriyle VARDI) uretebiliyordu. "Ucuz gecis'te aday yoksa dogru veriyle de
    yoktur" varsayimi YANLIS -- ucuz/dogru veri arasinda GUVENILIR bir
    korelasyon yok, iki-asamali yaklasim TERK EDILDI. Ag hacmi yerine
    `n_bars` (bkz. `_execute_ind_scan`daki tarama-ozel kucuk deger) ile
    kontrol edilir -- daha az bar istemek, `_fetch_native`in "1sa" icin
    HER ZAMAN 730 gun istemesi degismedikce ag yukunu azaltmaz (bilinen
    sinir, `abcd_data.py`de AYRI bir performans isi)."""
    df = fetch_ohlcv_abcd(symbol, tf, n_bars, skip_recent_30m=False)
    if df.empty:
        raise RuntimeError("veri donmedi (bos DataFrame)")

    n = len(df)
    signals = detect(df, params, variant=variant)

    out: list[ScannedSignal] = []
    for sig in signals:
        bars_ago = (n - 1) - sig.signal_bar
        if bars_ago < 0 or bars_ago >= lookback_bars:
            continue
        out.append(ScannedSignal(symbol=symbol, signal=sig, bars_ago=bars_ago))
    return out


def scan(
    symbols: list[str],
    tf: str,
    variant: str,
    lookback_bars: int,
    n_bars: int = 1000,
    workers: int = 8,
    on_progress: Callable[[int, int], None] | None = None,
    params: Params | None = None,
) -> MomentumScanResult:
    """`symbols` evreninde `variant`i ("v1" veya "v2") `tf`de tarar, son
    `lookback_bars` bar icinde olusmus sinyalleri toplar."""
    params = params or Params()
    signals: list[ScannedSignal] = []
    errors: dict[str, str] = {}
    total = len(symbols)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_scan_one_symbol, symbol, tf, variant, params, lookback_bars, n_bars): symbol
            for symbol in symbols
        }
        completed = 0
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                signals.extend(future.result())
            except Exception as exc:  # sembol-basina toplanir, ASLA firlatilmaz
                errors[symbol] = str(exc)
            completed += 1
            if on_progress:
                on_progress(completed, total)

    signals.sort(key=lambda s: (s.bars_ago, s.symbol))

    return MomentumScanResult(
        tf=tf,
        variant=variant,
        scanned_at=datetime.now(timezone.utc),
        lookback_bars=lookback_bars,
        signals=signals,
        errors=errors,
    )


_MDV2_SPECIAL = r"_*[]()~`>#+-=|{}.!"


def _escape_mdv2(text: str) -> str:
    return "".join(f"\\{c}" if c in _MDV2_SPECIAL else c for c in text)


def _escape_code_block(text: str) -> str:
    return text.replace("\\", "\\\\").replace("`", "\\`")


def _fmt_line(item: ScannedSignal) -> str:
    sig = item.signal
    ago = "bu bar" if item.bars_ago == 0 else f"{item.bars_ago} bar once"
    return (
        f"{item.symbol} | sinyal: {ago} | giris {sig.entry_ref:.4g} | "
        f"TP1 {sig.tp1:.4g} | TP2 {sig.tp2:.4g} | SL {sig.sl:.4g}"
    )


def format_report(result: MomentumScanResult, markdown: bool = False) -> str:
    label = VARIANT_LABELS.get(result.variant, result.variant)
    title = f"{label} Tarama -- {result.tf} (son {result.lookback_bars} bar)"
    header = f"*{_escape_mdv2(title)}*" if markdown else title

    body_lines = [guven_etiketi(result.variant, result.tf), "", "SİNYAL (LONG):"]
    body_lines.extend((_fmt_line(s) for s in result.signals) if result.signals else ["  (yok)"])

    if markdown:
        body = "\n".join(_escape_code_block(line) for line in body_lines)
        parts = [header, f"```\n{body}\n```"]
    else:
        parts = [header, "\n".join(body_lines)]

    if result.errors:
        err_text = f"{len(result.errors)} sembol basarisiz oldu"
        parts.append(_escape_mdv2(err_text) if markdown else err_text)

    return "\n".join(parts)

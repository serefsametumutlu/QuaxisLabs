"""Coklu-sembol AB=CD tarayicisi: BIST evreninde detektoru calistirir, son
N bar icinde onaylanmis sinyalleri toplar (Faz 4).

Kaynak: `C:\\Users\\Samet\\Desktop\\abcd-project\\abcd\\scanner.py` -- bu
projeye adapte edilmis (birebir kopya DEGIL). Pine parity'nin bir parcasi
DEGIL -- bu modul sadece veri cekme + `abcd_pattern.detect()`'i sembol
basina orkestre eder ve sonucu formatlar; tespit mantigina hicbir ek filtre
eklemez (Pine kaynaginda olmayan bir filtre eklenmez ilkesi, bkz.
`abcd_pattern.py` modul notu).

Mimari kararlar: `docs/spec/spec_abcd_mimari_kararlar.md`.

  Karar 2 -- Decimal istisnasi: `abcd_pattern.py`/`abcd_data.py`/
  `abcd_backtest.py` ile AYNI gerekceyle bu modul de TAMAMEN float +
  pandas kullanir (ayni float64 sinyal/fiyat zincirinin devami). Float
  deger BURADAN hicbir zaman Decimal tipli dataclass'lara/`scorer.py`'ye/
  `calculator.py`'ye SIZMAZ.

  Sembol evreni: abcd-project'in kendi `abcd/universe.py`'si (resmi olmayan
  tradingview-screener API'sine bagimli, Karar 3'un ilkesiyle celisir)
  KULLANILMAZ. Bunun yerine `get_bist_universe()` mevcut
  `src/db/repository.py`'deki `Company.market == "BIST"` sorgusuyla ayni
  mantigi kullanir -- repository.py'nin KENDISI DEGISTIRILMEDI, sadece
  oradan (`get_session`) ve `src.db.models.Company`'den import/sorgu yapilir.

Katman disiplini -- bu modul SAF DEGILDIR (`abcd_pattern.py` gibi degil,
`abcd_backtest.py::run_grid` ile AYNI ilke): `scan()` coklu sembolu
`src.fetchers.abcd_data.fetch_ohlcv_abcd` ile veri cekerek, `get_bist_universe()`
ise `src.db.repository`/`src.db.models` ile DB sorgulayarak orkestre eder --
ikisi de gercek I/O gerektirir, bu yuzden saf olamazlar. `_scan_one`/`_is_late`/
`format_report` kendileri SAF kalir (girdi olarak zaten cekilmis/hesaplanmis
degerler alir).

Sonuc kalicilik ilkesi (spec, "Sonuc" bolumu -- KESIN karar): bu modulun
urettigi `ScanResult` DB'ye VEYA dosyaya KAYDEDILMEZ -- mevcut
`MarketScanResult` tablosuna (bkz. `src/db/models.py`) HICBIR sekilde
DOKUNULMAZ. `scan()`'in donus degeri SADECE cagiran Telegram katmaninin
o oturumunun omru kadar yasar (abcd-project `scanner.py`'deki
`save_result`/`result_to_dict`/JSON-dosya-kalicilik ozellikle buraya
TASINMADI -- bilincli bir kapsam daraltmasi, eksiklik degil).

`ScannedSignal.bars_ago`/`late` alanlari (abcd-project ile ayni): Pine
parity'nin bir parcasi degil, sadece tarama-raporu kolayligi -- `late`,
onaydan bu yana son kapanisin zaten TP1/SL'e ulasip ulasmadigini isaretler
(formasyonun ongordugu hareket zaten oynanmis/gecersiz kalinmis demektir).
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.analysis.abcd_pattern import Params, Signal, detect
from src.db.models import Company
from src.db.repository import get_session
from src.fetchers.abcd_data import fetch_ohlcv_abcd

# Telegram Bot API MarkdownV2 rezerve karakterleri -- SADECE code-block
# DISINDA kalan metin (bkz. `_escape_mdv2`) icin gerekir.
_MDV2_SPECIAL = r"_*[]()~`>#+-=|{}.!"


@dataclass
class ScannedSignal:
    """Tarama baglaminda etiketlenmis tek bir `Signal` (Pine parity'nin
    parcasi degil).

    KULLANICI KAFA KARISIKLIGI (canli test, 2026-08-18): `bars_ago`
    D pivotunun kendisinin degil, ONAY barinin (`signal_bar = d_bar +
    pivot_lookback`) kac bar once oldugunu olcer -- bu, Pine-parity
    look-ahead-siz tasarimin DOGRUDAN sonucudur (bkz. abcd_pattern.py modul
    notu: bir pivot, olustuktan `pivot_lookback` bar SONRA bilinir hale
    gelir, TradingView'in ta.pivothigh/pivotlow'u ile AYNI). Bir kullanici
    "D BUY tam su mumda gelmis" deyip grafikte D'nin kendisini (`d_bar`)
    bulup `bars_ago` ile KARSILASTIRDIGINDA fark var gibi gorunuyor ama
    ikisi FARKLI seyler olcuyor -- bug degil. Bu karisikligi onlemek icin
    `d_bars_ago` (D pivotunun kendisinin kac bar once OLUSTUGU, salt
    `bars_ago + pivot_lookback` aritmetigiyle, ek bir df/network erisimi
    GEREKMEZ) ayri bir alan olarak eklendi -- raporlar ARTIK ikisini de
    acikca gosterir."""

    symbol: str
    signal: Signal
    bars_ago: int  # 0 = en son barda ONAYLANDI (signal_bar'a gore)
    d_bars_ago: int  # D pivotunun KENDISI kac bar once OLUSTU (= bars_ago + pivot_lookback)
    late: bool  # onaydan bu yana kapanis zaten TP1/SL'e ulasti mi


@dataclass
class ScanResult:
    """`scan()`'in donus degeri -- KAYDEDILMEZ, sadece cagiranin elinde yasar."""

    tf: str
    scanned_at: datetime
    lookback_bars: int
    buys: list[ScannedSignal]
    sells: list[ScannedSignal]
    errors: dict[str, str]


def get_bist_universe(session: Session | None = None) -> list[str]:
    """`src/db/repository.py`deki (satir ~568) `Company.market == "BIST"`
    sorgusuyla AYNI mantikla BIST ticker listesini alfabetik sirali doner.

    `session` verilmezse (uretim kullanim yolu) `repository.get_session()`
    ile kendi kisa omurlu session'ini acar/kapatir -- `repository.py`nin
    kendisi DEGISTIRILMEDI, DI ilkesi (bkz. o modulun ust notu) sadece bu
    ust-katman orkestrasyon fonksiyonuna tasindi (testler `session` parametresiyle
    izole bir SQLite'a baglanarak gercek DB'ye DOKUNMADAN calisir).

    Olu/islem gormeyen birkac ticker olasi ama `scan()`in sembol-basina hata
    toleransi (`errors` sozlugu) bunu zaten sessizce eler -- burada ekstra
    bir filtre (orn. `last_updated` tazeligi) UYGULANMAZ (bkz. spec "Sembol
    evreni" notu, kod-gelistirici canli dogrulamasi).
    """
    if session is not None:
        rows = session.execute(select(Company.ticker).where(Company.market == "BIST")).scalars().all()
        return sorted(rows)

    with get_session() as db_session:
        rows = db_session.execute(select(Company.ticker).where(Company.market == "BIST")).scalars().all()
    return sorted(rows)


def _is_late(last_close: float, signal: Signal) -> bool:
    if signal.direction > 0:
        return last_close >= signal.tp1 or last_close <= signal.sl
    return last_close <= signal.tp1 or last_close >= signal.sl


def _scan_one(
    symbol: str, tf: str, params: Params, lookback_bars: int, n_bars: int
) -> tuple[list[ScannedSignal], list[ScannedSignal]]:
    """Tek bir sembolu ceker + tarar. Veri bos donerse (ag hatasi, desteklenmeyen
    tf, olu ticker -- `fetch_ohlcv_abcd` bunlarin hicbirinde FIRLATMAZ, bkz.
    o modulun Kural 9 notu) burada bilincli olarak `RuntimeError` firlatilir --
    `scan()`in ThreadPoolExecutor sarmalayicisi bunu yakalayip `errors`e
    yazar, diger sembolleri ETKILEMEZ."""
    df = fetch_ohlcv_abcd(symbol, tf, n_bars)
    if df.empty:
        raise RuntimeError("veri donmedi (bos DataFrame)")

    signals = detect(df, params)
    n = len(df)
    last_close = float(df["close"].iloc[-1])

    buys: list[ScannedSignal] = []
    sells: list[ScannedSignal] = []
    for sig in signals:
        bars_ago = (n - 1) - sig.signal_bar
        if bars_ago < 0 or bars_ago >= lookback_bars:
            continue
        scanned = ScannedSignal(
            symbol=symbol,
            signal=sig,
            bars_ago=bars_ago,
            d_bars_ago=bars_ago + params.pivot_lookback,
            late=_is_late(last_close, sig),
        )
        (buys if sig.direction > 0 else sells).append(scanned)
    return buys, sells


def scan(
    symbols: list[str],
    tf: str,
    params: Params,
    lookback_bars: int,
    n_bars: int = 1000,
    workers: int = 8,
    on_progress: Callable[[int, int], None] | None = None,
) -> ScanResult:
    """`symbols` evreninde `tf` zaman diliminde detektoru calistirir, son
    `lookback_bars` bar icinde onaylanmis sinyalleri toplar. Is I/O-agirlikli
    (ag cekimi + parquet onbellek) oldugundan `ThreadPoolExecutor` kullanilir
    (abcd-project `scanner.py::scan()` ile birebir ayni orkestrasyon).

    `on_progress(completed, total)`, verilmisse, her sembol bittiginde
    (basarili ya da hatali) bu fonksiyonun kendi thread'inden SENKRON
    cagirilir -- orn. Telegram katmani bunu `run_coroutine_threadsafe` ile
    "Taraniyor... N/toplam" durum mesajini duzenlemeye baglayabilir.
    """
    buys: list[ScannedSignal] = []
    sells: list[ScannedSignal] = []
    errors: dict[str, str] = {}
    total = len(symbols)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_scan_one, symbol, tf, params, lookback_bars, n_bars): symbol for symbol in symbols
        }
        completed = 0
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                sym_buys, sym_sells = future.result()
                buys.extend(sym_buys)
                sells.extend(sym_sells)
            except Exception as exc:  # sembol-basina toplanir, ASLA firlatilmaz
                errors[symbol] = str(exc)
            completed += 1
            if on_progress:
                on_progress(completed, total)

    buys.sort(key=lambda s: (s.bars_ago, s.symbol))
    sells.sort(key=lambda s: (s.bars_ago, s.symbol))

    return ScanResult(
        tf=tf,
        scanned_at=datetime.now(timezone.utc),
        lookback_bars=lookback_bars,
        buys=buys,
        sells=sells,
        errors=errors,
    )


def _escape_mdv2(text: str) -> str:
    """Code-block DISINDA kalan metin icin tam MarkdownV2 kacisi."""
    return "".join(f"\\{c}" if c in _MDV2_SPECIAL else c for c in text)


def _escape_code_block(text: str) -> str:
    """Telegram MarkdownV2 code-block (```...```) entity'si icinde SADECE
    backslash ve backtick kacislanmalidir (Telegram Bot API dokumantasyonu) --
    diger tum MDV2 rezerve karakterleri (`._-()!*` vb.) code block icinde
    literal metin olarak islenir. Gecmis proje hatasi (abcd-project prod
    hatasi, bkz. modul ust notu): rapor govdesi ONCEDEN `_escape_mdv2` ile
    tek tek kacislaniyordu -- fiyat/oran metinlerindeki `.`/`-`/`(` yogunlugu
    kacis hatasina/okunmaz mesaja yol aciyordu. Cozum: govdeyi bir fenced
    code block'a alip SADECE bu iki karakteri kacislamak."""
    return text.replace("\\", "\\\\").replace("`", "\\`")


def _fmt_line(item: ScannedSignal) -> str:
    """D'nin KENDISININ kac bar once olustugunu (`d_bars_ago`) VE onay
    barinin kac bar once oldugunu (`bars_ago`) AYRI AYRI gosterir --
    ikisini TEK bir "X bar once" ifadesine indirgemek kullanici karisikligina
    yol acmisti (bkz. `ScannedSignal` modul notu, canli test 2026-08-18)."""
    sig = item.signal
    d_ago = "bu bar" if item.d_bars_ago == 0 else f"{item.d_bars_ago} bar once"
    confirm_ago = "bu bar" if item.bars_ago == 0 else f"{item.bars_ago} bar once"
    line = (
        f"{item.symbol} | D olustu: {d_ago} (onay: {confirm_ago}) | giris {sig.entry_ref:.4g} | "
        f"TP1 {sig.tp1:.4g} | TP2 {sig.tp2:.4g} | SL {sig.sl:.4g}"
    )
    if item.late:
        line += " | GEC (LATE)"
    return line


def format_report(result: ScanResult, markdown: bool = False) -> str:
    """Telegram-dostu kompakt rapor: baslik (code-block DISINDA, bold +
    `_escape_mdv2`) + BUY/SELL govdesi (fenced code block ICINDE, sadece
    `_escape_code_block`) + hata ozeti (code-block DISINDA).

    `markdown=False` iken duz metin doner (loglama/CLI/test kolayligi icin).
    """
    title = f"AB=CD Tarama -- {result.tf} (son {result.lookback_bars} bar)"
    header = f"*{_escape_mdv2(title)}*" if markdown else title

    body_lines = ["BUY:"]
    if result.buys:
        body_lines.extend(_fmt_line(s) for s in result.buys)
    else:
        body_lines.append("  (yok)")
    body_lines.append("")
    body_lines.append("SELL:")
    if result.sells:
        body_lines.extend(_fmt_line(s) for s in result.sells)
    else:
        body_lines.append("  (yok)")

    if markdown:
        body = "\n".join(_escape_code_block(line) for line in body_lines)
        parts = [header, f"```\n{body}\n```"]
    else:
        parts = [header, "\n".join(body_lines)]

    if result.errors:
        err_text = f"{len(result.errors)} sembol basarisiz oldu"
        parts.append(_escape_mdv2(err_text) if markdown else err_text)

    return "\n".join(parts)

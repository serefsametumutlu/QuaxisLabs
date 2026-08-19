"""ABCD harmonik formasyon taraması için OHLCV veri katmanı (Faz 1 — veri).

`src/fetchers/isyatirim.py::fetch_price_history` SADECE günlük bar döner ve
`open` HER ZAMAN `None`'dır (bkz. o modülün üst notu, ve
`src/fetchers/price_history.py`'nin bunu belgeleyen notu) -- ABCD formasyon
tespiti (A/B/C/D pivot dizisi + Fibonacci oran doğrulaması) 60/120/240
dakikalık intraday barlara VE gerçek açılış fiyatına ihtiyaç duyar; isyatirim
bunu hiç sağlayamaz. Bu yüzden bu modül `src/fetchers/`'ın geri kalanından
BAĞIMSIZ, kendi parquet önbelleğine sahip AYRI bir veri katmanıdır (bkz.
`docs/spec/spec_abcd_mimari_kararlar.md`, Karar 3) -- gereksiz bir tekrar
değil, gerçek bir veri boşluğunun doldurulmasıdır.

Kaynak: `C:\\Users\\Samet\\Desktop\\abcd-project\\abcd\\data.py::
YFinanceProvider` + `fetch_cached()`'in adapte edilmiş/taşınmış hali. Proje
sahibinin kararıyla (spec Karar 3) SADECE yfinance kullanılır -- tvDatafeed
KULLANILMAZ (git-bağımlılığı + resmi olmayan API riski istenmiyor).

quaxis-mimari Kural 3'e (Decimal-only) kapsamı sınırlı, gerekçeli bir
istisnadır (bkz. spec Karar 2): bu modül TAMAMEN float + pandas/numpy
kullanır -- Pine-parity zorunluluğu (ABCD formasyon tespiti zaten test
edilmiş TradingView float64 aritmetiğiyle bar-bar eşleşmelidir; Decimal'e
çevirmek sessiz sapma riski taşır). Bu modülün ürettiği float değerler
HİÇBİR ZAMAN Decimal tipli dataclass'lara/`scorer.py`'ye/`calculator.py`'ye
sızmaz; Decimal'e dönüşüm SADECE render sınırında (ileride
`src/render/abcd_card.py`) yapılacaktır.

BIST 4H/2H resample notu (abcd-project'ten BİREBİR taşınan, canlı
doğrulanmış gerçek): TradingView'in BIST 4H barları 09:00/13:00/17:00
Europe/Istanbul'da açılır (10:00/14:00 DEĞİL, yaygın varsayılan BIST seans
başlangıcına rağmen, kullanıcı canlı TradingView kontrolüyle 2026-08-19'da
YENİDEN doğruladı). yfinance'in BIST intraday barları ise 09:30'dan başlar
(09:00-09:30 açılış seansı yfinance'te hiç YOK, interval="30m" ile
doğrulandı) -- bu yüzden 1H barlardan 120/240dk'ya resample edilirken
origin günün 09:00'ına SABİTLENİR (`_resample_to_hours`).

DÜZELTILEN BUG (2026-08-19, canlı tarama raporu: HURGZ 240 V1 taraması
TradingView'de VAR OLMAYAN bir mum/fiyat gösterdi): eski docstring
"günün SONRAKİ her barı TAM eşleşir" derdi -- bu YANLIŞTI. yfinance'in 1H
barları saat başından 30dk KAYIKTIR (09:30/10:30/.../16:30/17:30, 09:00/
10:00/... DEĞİL); bu barlar TAM 1 saat genişliğinde olduğu için 4H sınırını
(örn. 17:00) İÇTEN BÖLER -- örn. "16:30" etiketli bar gerçekte [16:30,17:30)
aralığını kapsar ve pandas resample onu TAMAMEN 13:00 kovanına atar, oysa
içindeki 17:00-17:30 dakikaları GERÇEKTE 17:00 kovanına aittir. 1 dakikalık
yfinance verisiyle doğrulandı (HURGZ, 2026-08-18): gerçek 13:00 TradingView
mumu ~7.57'de kapanmalıyken, eski resample close=7.84 üretiyordu (17:00
sonrası fiyat sızıntısı).

DÜZELTME: yfinance'in 30dk barları GERÇEKTEN saat/yarım-saat sınırına
hizalıdır (09:30/10:00/10:30/... -- 1sa'lık barlar gibi kaymaz, doğrulandı).
Ama Yahoo 30dk geçmişi ~60 günle sınırlı (1sa'nın ~730 gün sınırının
AKSİNE). Bu yüzden HİBRİT bir yaklaşım kullanılır (`_fetch_raw_ohlcv`,
kullanıcı kararı 2026-08-19): son `_RECENT_INTRADAY_DAYS` gün 30dk
veriden (sınır kayması YOK, canlı tarama için en kritik kısım) resample
edilir; daha eski barlar (backtest derinliği için) eski 1sa'lık veriden
(bilinen ~30dk sınır bulanıklığıyla, kabul edilebilir -- istatistiksel
backtest sonuçlarını görünür şekilde etkilemez) resample edilip, 30dk
kaynaklı en eski barın ÖNCESİNDE kesilerek birleştirilir. USDTRY=X için
AYNI anchoring/hibrit yaklaşım uygulanmaz (abcd-project
`backtest.py::_usdtry_provider` ile aynı mantık) -- FX piyasası BIST'in
seans/açılış-müzayedesi yapısına sahip değildir.

Bilinen sınır (blocker DEĞİL, dokümante edilir -- bkz. spec "Bilinen
sınır" notu): yfinance'in intraday (1h ve türevi 120/240dk) geçmişi ~730
günle sınırlıdır (bkz. `_period_for`) -- 60/120/240dk zaman dilimlerinde
backtest derinliği ~2 yılla sınırlı kalır; sadece 1D/1W tam derinlik alır.
Kart/rapor metinlerinde bu sınır belirtilmelidir.

Hata toleransı: `src/fetchers/price_history.py::fetch_ohlcv` ile AYNI ilke
(Kural 9) -- bu deneysel bir özelliktir, ağ hatası/boş veri/desteklenmeyen
zaman dilimi durumunda dışa açık hiçbir fonksiyon FIRLATMAZ, boş DataFrame
döner. Çağıran taraf (ileride `abcd_pattern.py`/tarama akışı) bunun için
ASLA bloke OLMAMALIDIR.
"""

from __future__ import annotations

import json
import logging
import time as _time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance

import config

logger = logging.getLogger(__name__)

TZ_ISTANBUL = ZoneInfo("Europe/Istanbul")
OHLCV_COLUMNS = ["time", "open", "high", "low", "close", "volume"]
USDTRY_COLUMNS = ["time", "close"]
TIMEFRAMES = ("60", "120", "240", "1D", "1W")
_SESSION_START_HOUR = 9  # bkz. modul ust notu -- canli TradingView dogrulamasi (2026-08-17)

# config.DATA_DIR'den turetilir, hardcode edilmez (bkz. src/render/card.py'nin
# ayni ilkesi: config.DATA_DIR).
_CACHE_DIR = config.DATA_DIR / "abcd_cache"

# Onbellekte eksik bar sayisini KABACA kestirmek icin (fazla istemek sorun
# degil, sadece birkac fazladan bar ister -- asla hataya yol acmaz).
_APPROX_BAR_SECONDS = {"60": 3_600, "120": 7_200, "240": 14_400, "1D": 86_400, "1W": 604_800}

_INTERVAL_FOR_TF = {"60": "1h", "120": "1h", "240": "1h", "1D": "1d", "1W": "1wk"}

# Yahoo'nun 30dk gecmis siniri ~60 gun -- guvenli pay icin dusuk tutulur
# (bkz. modul ust notu, "DUZELTME" bolumu: 120/240dk'nin SON bu kadar
# gununde sinir-kaymasi olmayan 30dk veri, daha eskisinde 1sa'lik veri
# kullanilir).
_RECENT_INTRADAY_DAYS = 55


def _yf_symbol(symbol: str) -> str:
    """BIST sembolune yfinance sonekini ekler (YFinanceProvider._yf_symbol ile ayni mantik)."""
    return f"{symbol}.IS"


def _period_for(interval: str, n_bars: int) -> str:
    if interval == "1h":
        # `n_bars` ile OLCEKLENIR (2026-08-19 performans notu): eskiden
        # HER ZAMAN sabit 730 gun isteniyordu (istenen n_bars ne olursa
        # olsun) -- backtest scriptleri icin doğru (derin gecmis ister),
        # ama canli TARAMA (bkz. `momentum_scanner.py`, kisa omurlu EMA/TRF
        # gostergeleri icin 300 bar warmup FAZLASIYLA yeterli, ampirik
        # dogrulandi) icin gereksiz yere BUYUK yfinance istekleri = daha
        # yavas ag cevaplari. ~9 bar/is-gunu varsayimiyla KABACA gun
        # sayisina cevrilir, 730 gunu ASLA GECMEZ (yfinance'in kendi siniri).
        days = min(max(int(n_bars * 0.2), 10), 730)
        return f"{days}d"
    if interval == "1d":
        days = min(max(n_bars * 2, 60), 3650)
        return f"{days}d"
    return "max"  # "1wk"


def _yf_history(yf_symbol: str, interval: str, period: str) -> pd.DataFrame:
    """Bu modulun yfinance'e dokundugu TEK nokta -- testler bunu monkeypatch
    eder, gercek ag cagrisi YAPILMAZ (bkz. tests/test_abcd_data.py).

    Ag/parse hatasinda ISTISNA FIRLATIR (yutmaz) -- boylece cagiran
    `_cached_fetch` icindeki `_retry` gercekten yeniden deneyebilir; nihai
    FIRLATMAMA garantisi sadece disa acik `fetch_ohlcv_abcd`/`fetch_usdtry`
    sinirinda uygulanir (Kural 9).

    `timeout=6` (yfinance varsayilani 10) -- canli tarama performans notu
    (2026-08-19, "657/657'de takili" raporu): tam-BIST tarama tek istekte
    657 sembol x (240dk icin 1sa+30dk =) iki ag cagrisi yapiyor, sunucunun
    Yahoo Finance'e agi yavas/limitliyken HER istek varsayilan 10s'yi
    doldurunca toplam sure dakikalar mertebesine cikabiliyor -- daha kisa
    timeout, YAVAS/limitli sembollerde daha hizli vazgecip bir sonraki
    denemeye/sembole gecilmesini saglar (bkz. `_retry`)."""
    ticker = yfinance.Ticker(yf_symbol)
    return ticker.history(period=period, interval=interval, auto_adjust=False, timeout=6)


def _fetch_native(yf_symbol: str, interval: str, n_bars: int) -> pd.DataFrame:
    """yfinance'ten dogrudan (resample gerektirmeyen) bir zaman dilimini ceker."""
    raw = _yf_history(yf_symbol, interval, _period_for(interval, n_bars))
    if raw is None or raw.empty:
        return pd.DataFrame(columns=OHLCV_COLUMNS)

    df = raw.reset_index()
    time_col = df.columns[0]  # "Date" (1d/1wk) veya "Datetime" (intraday)
    df = df.rename(
        columns={
            time_col: "time",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )
    df["time"] = pd.to_datetime(df["time"]).dt.tz_convert(TZ_ISTANBUL)
    return df[OHLCV_COLUMNS].sort_values("time").tail(n_bars).reset_index(drop=True)


def _fetch_recent_30m(yf_symbol: str) -> pd.DataFrame:
    """Son `_RECENT_INTRADAY_DAYS` gunun 30dk barlarini ceker -- bu barlar
    GERCEKTEN saat/yarim-saat sinirina hizalidir (1sa'lik barlarin AKSINE,
    bkz. modul ust notu "DUZELTILEN BUG" notu -- 2026-08-19 canli
    dogrulama). `_fetch_native`in n_bars/tail kirpmasi burada YOK --
    caller (`_fetch_raw_ohlcv`) resample SONRASI kendi kirpmasini yapar."""
    raw = _yf_history(yf_symbol, "30m", f"{_RECENT_INTRADAY_DAYS}d")
    if raw is None or raw.empty:
        return pd.DataFrame(columns=OHLCV_COLUMNS)

    df = raw.reset_index()
    time_col = df.columns[0]
    df = df.rename(
        columns={
            time_col: "time",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )
    df["time"] = pd.to_datetime(df["time"]).dt.tz_convert(TZ_ISTANBUL)
    return df[OHLCV_COLUMNS].sort_values("time").reset_index(drop=True)


def _resample_to_hours(df: pd.DataFrame, hours: int) -> pd.DataFrame:
    """1H barlardan 2H/4H turetir, origin gunun 09:00 Europe/Istanbul'una
    sabitlenir (bkz. modul ust notu -- abcd-project `_resample_to_hours` ile
    birebir ayni mantik)."""
    if df.empty:
        return df
    origin = (
        pd.Timestamp(df["time"].iloc[0].date())
        .tz_localize(TZ_ISTANBUL)
        .replace(hour=_SESSION_START_HOUR)
    )
    agg = (
        df.set_index("time")
        .resample(f"{hours}h", origin=origin)
        .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
        .dropna(subset=["open"])
    )
    return agg.reset_index()[OHLCV_COLUMNS]


def _fetch_raw_ohlcv(yf_symbol: str, tf: str, n_bars: int, skip_recent_30m: bool = False) -> pd.DataFrame:
    """Tek bir yfinance sembolu icin `tf` zaman diliminde ham OHLCV ceker
    (onbellek katmani olmadan).

    `skip_recent_30m` (2026-08-19, canli tarama performans notu -- bkz.
    `fetch_ohlcv_abcd` docstring'i): tam-BIST tarama olceginde (657 sembol)
    30dk hibrit kaynagi HER sembolde istemek (657x2 ag cagrisi) Yahoo
    Finance rate-limit'ine carpip taramanin PRATIKTE hic bitmemesine yol
    acti (canli kullanici raporu: "50-100 sembolde hata", "657/657'de
    takili"). `True` iken eski (SADECE 1sa, bilinen ~30dk sinir bulanikligi
    ile) yola duser -- caller'lar (bkz. `momentum_scanner._scan_one_symbol`)
    bunu 'ucuz ilk gecis' icin kullanip SADECE aday sinyal bulunan az
    sayida sembolu `skip_recent_30m=False` ile YENIDEN cekip dogrulayarak
    hem ag hacmini dusuk tutar HEM raporlanan sonuclarda tam dogrulugu korur."""
    if tf == "1D":
        return _fetch_native(yf_symbol, interval="1d", n_bars=n_bars)
    if tf == "1W":
        return _fetch_native(yf_symbol, interval="1wk", n_bars=n_bars)
    if tf == "60":
        return _fetch_native(yf_symbol, interval="1h", n_bars=n_bars)
    if tf in ("120", "240"):
        # Hibrit kaynak (bkz. modul ust notu "DUZELTME"): eski derinlik 1sa'lik
        # veriden (bilinen ~30dk sinir bulanikligiyla), SON `_RECENT_INTRADAY_DAYS`
        # gun ise sinir-kaymasi OLMAYAN 30dk veriden resample edilir, ikisi
        # 30dk kaynagin ilk barindan KESILEREK birlestirilir.
        hours = int(tf) // 60
        hourly = _fetch_native(yf_symbol, interval="1h", n_bars=n_bars * hours + 20)
        old_resampled = _resample_to_hours(hourly, hours)

        if skip_recent_30m:
            return old_resampled.tail(n_bars).reset_index(drop=True)

        recent_30m = _fetch_recent_30m(yf_symbol)
        recent_resampled = _resample_to_hours(recent_30m, hours)
        if recent_resampled.empty:
            return old_resampled.tail(n_bars).reset_index(drop=True)

        cutover = recent_resampled["time"].iloc[0]
        combined = pd.concat(
            [old_resampled[old_resampled["time"] < cutover], recent_resampled], ignore_index=True
        )
        return combined.tail(n_bars).reset_index(drop=True)
    raise ValueError(f"Desteklenmeyen zaman dilimi: {tf!r}")


def _fetch_raw_usdtry(tf: str, n_bars: int) -> pd.DataFrame:
    """USDTRY=X icin ham [time, close] serisini ceker (onbellek katmani
    olmadan) -- abcd-project `backtest.py::_usdtry_provider`'in yfinance
    kismiyla AYNI mantik: sadece kapanis gerekir (TL fiyatlarini USD'ye
    cevirmek icin), origin anchoring UYGULANMAZ (bkz. modul ust notu)."""
    interval = _INTERVAL_FOR_TF[tf]
    raw = _yf_history("USDTRY=X", interval, _period_for(interval, n_bars))
    if raw is None or raw.empty:
        return pd.DataFrame(columns=USDTRY_COLUMNS)

    df = raw.reset_index()
    time_col = df.columns[0]
    df = df.rename(columns={time_col: "time", "Close": "close"})
    df["time"] = pd.to_datetime(df["time"]).dt.tz_convert(TZ_ISTANBUL)
    df = df[USDTRY_COLUMNS].sort_values("time")

    if tf in ("120", "240"):
        hours = int(tf) // 60
        df = df.set_index("time").resample(f"{hours}h").last().dropna().reset_index()

    return df.tail(n_bars).reset_index(drop=True)


def _cache_path(cache_key: str, tf: str) -> Path:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR / f"{cache_key}_{tf}.parquet"


# --- Negatif onbellek (olu/veri-yok sembol-tf ciftleri) --------------------
#
# GECE NOBETI BULGUSU (2026-08-18): BIST evreninde ~657 tickerin ~65'i
# yfinance'te hic veri DONDURMUYOR (borsadan cikmis/yeni halka arz/hic
# kapsanmiyor -- "possibly delisted" hatasi). Her arastirma kosusu (5-10
# ayri run_grid cagrisi, her biri TUM evreni tarayan) bu AYNI ~65 sembolu
# TEKRAR TEKRAR agdan denemek zorunda kaliyordu (basarisiz cekim hic
# onbelleklenmiyordu) -- tek bir gece nobetinde AYNI hatalar 4+ kez
# tekrarlandi, saatlerce bosa harcanan ag/retry suresi. Bu sozluk, bir
# (symbol,tf) cifti ag/parse hatasiyla (VE onceden HIC basarili onbellegi
# yokken) basarisiz olduğunda `_DEAD_TTL_DAYS` gun boyunca ATLANMASINI
# saglar -- eger sembol yeniden listelenirse/yfinance kapsama alirsa,
# TTL dolunca otomatik yeniden denenir (kalici bir "kara liste" DEGIL).
_DEAD_TTL_DAYS = 30


def _dead_symbols_path() -> Path:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR / "_dead_symbols.json"


def _load_dead_symbols() -> dict[str, str]:
    path = _dead_symbols_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # bozuk/kismi yazilmis dosya -- sessizce sifirdan basla, FIRLATMA
        return {}


def _save_dead_symbols(data: dict[str, str]) -> None:
    try:
        _dead_symbols_path().write_text(json.dumps(data), encoding="utf-8")
    except Exception as exc:  # disk/izin hatasi -- onbellek yazilamasa da akis DEVAM eder
        logger.warning("abcd_data: negatif onbellek diske yazilamadi: %s", exc)


def _is_marked_dead(cache_key: str, tf: str) -> bool:
    entry = _load_dead_symbols().get(f"{cache_key}_{tf}")
    if entry is None:
        return False
    marked_at = datetime.fromisoformat(entry)
    return datetime.now(timezone.utc) - marked_at < timedelta(days=_DEAD_TTL_DAYS)


def is_marked_dead(symbol: str, tf: str) -> bool:
    """`_is_marked_dead`nin PUBLIC sarmalayicisi -- tarayicilarin (bkz.
    `momentum_scanner.py`/`telegram_bot.py`) bilinen-olu sembolleri ag'a hic
    gitmeden ONCEDEN evrenden elemesi icin (2026-08-19, kullanici istegi:
    "hata veren hisseleri cikarip kalanlari tarasak"). Zaten `_cached_fetch`
    ayni kontrolu kendi ici yapiyor -- bu sadece cagiran tarafin universe
    listesini KUCULTUP ilerleme sayacini/thread havuzu baskisini azaltmasini
    saglar, davranissal bir fark YARATMAZ (ayni sembol yine BOS donerdi)."""
    return _is_marked_dead(symbol, tf)


def _mark_dead(cache_key: str, tf: str) -> None:
    data = _load_dead_symbols()
    data[f"{cache_key}_{tf}"] = datetime.now(timezone.utc).isoformat()
    _save_dead_symbols(data)


def _estimate_new_bars(tf: str, last_time: pd.Timestamp) -> int:
    elapsed = (pd.Timestamp.now(tz=TZ_ISTANBUL) - last_time).total_seconds()
    return max(int(elapsed // _APPROX_BAR_SECONDS[tf]) + 5, 10)


def _retry(fn: Callable[[], pd.DataFrame], *, attempts: int = 2, base_delay: float = 1.0) -> pd.DataFrame:
    """Ag hatalarinda ussel geri cekilmeyle yeniden dener; tum denemeler
    tukenirse SON istisnayi yeniden firlatir (cagiran `_cached_fetch` bunu
    yakalayip onbellege/BOS DataFrame'e duser -- Kural 9 disariya boyle
    sizar, asla ham istisna disa acik fonksiyondan cikmaz).

    `attempts=2` (eskiden 3) -- canli tarama performans notu (2026-08-19,
    bkz. `_yf_history`teki AYNI not): 240dk tarama sembol basina IKI ag
    cagrisi (1sa+30dk) yapiyor, ucuncu bir yeniden deneme (+eski onceki
    backoff bekleme suresi) tam-BIST olcekte toplam sureyi anlamli sekilde
    uzatiyordu, kazanci (gecici ag hatalarinin bir KISMINI daha kurtarma)
    bu bedele degmedi."""
    last_exc: Exception | None = None
    for attempt in range(attempts):
        try:
            return fn()
        except Exception as exc:  # yeniden denenir; tukenirse asagida yeniden firlatilir
            last_exc = exc
            if attempt < attempts - 1:
                _time.sleep(base_delay * (2**attempt))
    assert last_exc is not None
    raise last_exc


def _cached_fetch(
    cache_key: str,
    tf: str,
    n_bars: int,
    raw_fetch: Callable[[int], pd.DataFrame],
    columns: list[str],
    *,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """abcd-project'in `fetch_cached()`'inin adapte edilmis hali --
    incremental refresh + dedupe-on-time + retry-with-backoff.

    Tum yeniden denemeler tukenip hala hata olursa, onbellekte ne varsa onu
    (yoksa BOS DataFrame) doner -- ASLA firlatmaz, cagiran ust fonksiyona
    (`fetch_ohlcv_abcd`/`fetch_usdtry`) ham istisna sizdirmaz."""
    path = _cache_path(cache_key, tf)
    cached = pd.read_parquet(path) if path.exists() and not force_refresh else pd.DataFrame(columns=columns)

    if cached.empty and not force_refresh and _is_marked_dead(cache_key, tf):
        # Negatif onbellek: daha once (n gun icinde) hicbir onbellegi
        # olmadan basarisiz olmustu -- ag'a HIC gitmeden hizlica bos don
        # (bkz. modul-ici "Negatif onbellek" notu).
        return pd.DataFrame(columns=columns)

    try:
        if cached.empty:
            combined = _retry(lambda: raw_fetch(n_bars))
        else:
            want = max(_estimate_new_bars(tf, cached["time"].iloc[-1]), n_bars - len(cached) + 5)
            fresh = _retry(lambda: raw_fetch(want))
            combined = pd.concat([cached, fresh], ignore_index=True) if not fresh.empty else cached
    except Exception as exc:  # tum retry denemeleri tukendi -- Kural 9, FIRLATMA
        logger.warning("abcd_data: %s (%s) yenilenemedi, mevcut onbellek donuluyor: %s", cache_key, tf, exc)
        combined = cached

    if cached.empty and combined.empty:
        # DUZELTILEN BUG (2026-08-19, canli tarama raporu: "657/657'de
        # takili kaliyor" -- momentum confluence 240 taramasi ~120s
        # suruyordu): negatif onbellek ESKIDEN SADECE `raw_fetch` istisna
        # FIRLATTIGINDA isaretleniyordu -- ama yfinance "possibly delisted"
        # sembollerde ISTISNA FIRLATMAZ, sessizce BOS DataFrame doner (Kural
        # 9 zaten `_fetch_native`/`_fetch_recent_30m` icinde bunu boyle
        # ele aliyor). Sonuc: ~32 olu/kapsam-disi BIST sembolu HICBIR ZAMAN
        # negatif onbelleklenmiyordu, HER taramada (ABCD/Harmonik/Momentum
        # Confluence, HER zaman dilimi) agdan tekrar tekrar denenip
        # bosa zaman harcaniyordu -- 120/240dk icin (2026-08-19 hibrit
        # duzeltmesi SONRASI) bu maliyet 1sa+30dk CIFT cagriyla katlanmisti.
        # Simdi: onceki onbellek YOKKEN bu deneme de bos donduyse (istisna
        # OLSUN OLMASIN) negatif onbellege isaretlenir.
        _mark_dead(cache_key, tf)
        return combined

    combined = combined.drop_duplicates(subset="time", keep="last").sort_values("time").reset_index(drop=True)
    try:
        combined.to_parquet(path, index=False)
    except Exception as exc:  # disk/izin hatasi -- onbellek yazilamasa da veri donulmeli
        logger.warning("abcd_data: %s (%s) onbellek diske yazilamadi: %s", cache_key, tf, exc)
    return combined.tail(n_bars).reset_index(drop=True)


def fetch_ohlcv_abcd(symbol: str, tf: str, n_bars: int = 1000, *, skip_recent_30m: bool = False) -> pd.DataFrame:
    """`symbol` (BIST ticker, orn. "THYAO") icin `tf` zaman diliminde son
    `n_bars` OHLCV barini doner, `data/abcd_cache/{symbol}_{tf}.parquet`
    ile onbelleklenir. Kolonlar [time, open, high, low, close, volume];
    `time` tz-aware Europe/Istanbul, artan sirada, UNADJUSTED (auto_adjust=
    False, TradingView ile eslessin diye -- bkz. modul ust notu).

    `skip_recent_30m` -- bkz. `_fetch_raw_ohlcv` docstring'i (SADECE
    tf="120"/"240" icin anlamli, digerlerinde etkisiz): tam-evren taramada
    ag hacmini yariya indirmek icin 'ucuz ilk gecis' amaciyla eklendi.
    Onbellek PAYLAŞILIR (ayrı bir dosya YOK) -- `skip_recent_30m=False` ile
    yapilan SONRAKI herhangi bir cagri (bu fonksiyonun HER cagirilisinda
    -- `_cached_fetch` her zaman TAZE veri ceker, bkz. o fonksiyonun ust
    notu -- 'incremental' olsa da 120/240 icin HER SEFERINDE tam derinlik
    yeniden cekilir) onbellekteki daha az hassas barlari OTOMATIK duzeltir
    (dedup keep="last").

    Desteklenmeyen zaman dilimi, ag hatasi veya bos veri durumunda BOS
    DataFrame doner. FIRLATMAZ (Kural 9, bkz. modul ust notu).
    """
    if tf not in TIMEFRAMES:
        logger.warning("abcd_data.fetch_ohlcv_abcd: desteklenmeyen zaman dilimi %r", tf)
        return pd.DataFrame(columns=OHLCV_COLUMNS)

    yf_symbol = _yf_symbol(symbol)
    try:
        return _cached_fetch(
            symbol,
            tf,
            n_bars,
            lambda nb: _fetch_raw_ohlcv(yf_symbol, tf, nb, skip_recent_30m=skip_recent_30m),
            OHLCV_COLUMNS,
        )
    except Exception as exc:  # son savunma hatti -- Kural 9, hicbir kosulda firlatma
        logger.warning("abcd_data.fetch_ohlcv_abcd: %s (%s) icin beklenmeyen hata: %s", symbol, tf, exc)
        return pd.DataFrame(columns=OHLCV_COLUMNS)


def fetch_usdtry(tf: str, n_bars: int = 1000) -> pd.DataFrame:
    """USDTRY=X icin son `n_bars` [time, close] serisini doner (abcd-project
    `backtest.py::_usdtry_provider`'in yfinance kismiyla AYNI mantik -- TL
    fiyatlarini USD'ye cevirmek icin sadece kapanis gerekir, tam OHLCV
    degil). `data/abcd_cache/USDTRY_{tf}.parquet` ile onbelleklenir.

    Ag hatasi/bos veri durumunda BOS DataFrame doner. FIRLATMAZ.
    """
    if tf not in TIMEFRAMES:
        logger.warning("abcd_data.fetch_usdtry: desteklenmeyen zaman dilimi %r", tf)
        return pd.DataFrame(columns=USDTRY_COLUMNS)

    try:
        return _cached_fetch("USDTRY", tf, n_bars, lambda nb: _fetch_raw_usdtry(tf, nb), USDTRY_COLUMNS)
    except Exception as exc:  # son savunma hatti -- Kural 9, hicbir kosulda firlatma
        logger.warning("abcd_data.fetch_usdtry: (%s) icin beklenmeyen hata: %s", tf, exc)
        return pd.DataFrame(columns=USDTRY_COLUMNS)

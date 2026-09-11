"""Boyun çizgili dönüş formasyonları: çift tepe/dip ve OBO.

Kullanıcının en sert şikâyeti buydu: *"çift dip diye sinyal verdiği
grafikte alakası olmayan şeyler var, hiç çift dip göremiyorum"*.

Sebebi, eski tespit edicinin yalnızca "birbirine yakın iki pivot" araması,
formasyonun ASIL şartlarını aramamasıydı. Bulkowski'nin ölçütleri:

  - Formasyondan ÖNCE ters yönde bir trend olmalı (çift dip için düşüş).
  - İki dip/tepe birbirine yakın olmalı (varsayılan %3).
  - Aralarında ANLAMLI bir toparlanma olmalı (Bulkowski: ≥%10; burada
    parametre, ayrıca ATR ile de doğrulanıyor).
  - İki dip/tepe arasında yeterli ZAMAN olmalı — Lo-Mamaysky-Wang (2000)
    çift tepe için en az 22 işlem günü şart koşuyor.
  - Onay, boyun çizgisinin KAPANIŞLA kırılmasıdır; formasyonun kendisi
    değil.

OBO'da boyun çizgisi EĞİMLİ olabilir. Bulkowski: boyun yukarı eğimliyse
tetik, boyun çizgisi değil SAĞ KOLTUKALTI tepesinin kapanışla aşılmasıdır
— yoksa eğimli boyun sonsuza kadar kaçar ve sinyal hiç gelmez.

Hesap yapar, çizmez.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tlab.features.swings import alternate_pivots, find_pivots


@dataclass(frozen=True)
class NecklinePoint:
    t: pd.Timestamp
    price: float
    label: str          # "T1","T2","B1","B2","SOL OMUZ","BAŞ","SAĞ OMUZ"


@dataclass(frozen=True)
class Hologram:
    """Formasyonun uçları arasındaki GERÇEK kapanış yolu.

    Kullanıcı: çift dip grafiğinde *"aşağıda 2 üçgen şeklinde ve hologram
    ile resmedilmiyordu"*. Hologram, formasyonun idealize edilmiş
    iskeletini değil, fiyatın O ARALIKTA gerçekten izlediği yolu gösterir
    — böylece "bu gerçekten çift dip mi" sorusu gözle cevaplanabilir.
    """

    times: tuple[pd.Timestamp, ...]
    prices: tuple[float, ...]


@dataclass(frozen=True)
class NecklinePattern:
    kind: str                       # "cift_dip"|"cift_tepe"|"obo"|"ters_obo"
    direction: str                  # "long" | "short"
    points: tuple[NecklinePoint, ...]
    neckline: tuple[tuple[pd.Timestamp, float], tuple[pd.Timestamp, float]]
    trigger_price: float            # onay seviyesi (eğimli boyunda koltukaltı)
    trigger_note: str
    breakout: NecklinePoint | None  # kapanışla kırılma barı
    target: float | None
    state: str                      # "olusuyor"|"onaylandi"|"gecersiz"
    bars_ago: int | None
    separation_bars: int
    depth_pct: float
    hologram: Hologram | None = None
    # Kırılım sonrası boyun çizgisine dönüş — girişin ikinci fırsatı
    retest: NecklinePoint | None = None
    # Gövdenin dış uçları (boyun kesişimleri). İskelet buradan başlar
    # ve burada biter; omuzların DIŞ kanatları da çizilmiş olur.
    outer: tuple[NecklinePoint, NecklinePoint] | None = None

    def __post_init__(self) -> None:
        if self.direction not in ("long", "short"):
            raise ValueError(f"yön 'long'/'short' olmalı — alınan {self.direction!r}")


def _path_bounds(
    df: pd.DataFrame, first_idx: int, last_idx: int, neck: float, below: bool,
    *, max_extend: int = 40,
) -> tuple[int, int]:
    """Formasyon gövdesinin GERÇEK sınırları.

    Gövde, uç pivotlardan değil, fiyatın boyun çizgisini kestiği yerden
    başlar ve kestiği yerde biter. Uçlardan başlatılırsa omuzların /
    diplerin DIŞ YARISI gövdenin dışında kalır ve şekil "yarım" görünür —
    kullanıcının 2026-09-09'daki bildirimi tam olarak buydu.

    `below=True`: formasyon boyun çizgisinin ALTINDA (TOBO, çift dip).
    """
    close = df["close"].to_numpy()
    start = first_idx
    for i in range(first_idx, max(first_idx - max_extend, 0) - 1, -1):
        if (close[i] >= neck) if below else (close[i] <= neck):
            start = i
            break
        start = i
    end = last_idx
    n = len(close)
    for i in range(last_idx, min(last_idx + max_extend, n)):
        if (close[i] >= neck) if below else (close[i] <= neck):
            end = i
            break
        end = i
    return start, end


def _find_retest(
    df: pd.DataFrame, brk: NecklinePoint | None, level: float, up: bool,
    *, tol: float = 0.012, max_bars: int = 30,
) -> NecklinePoint | None:
    """Kırılım sonrası boyun çizgisine DÖNÜŞ (retest).

    Referans görselde kırılım ve retest AYRI iki işaret: kırılım seviyeyi
    aşan bar, retest ise fiyatın o seviyeye geri gelip tuttuğu bar.
    Retest, girişin ikinci ve genelde daha güvenli fırsatıdır.

    Yalnızca kırılımdan SONRAKİ barlarda aranır; geriye yazılmaz.
    """
    if brk is None:
        return None
    after = df.loc[df.index > brk.t].head(max_bars)
    if after.empty:
        return None
    band = abs(level) * tol
    for t, row in after.iterrows():
        touched = (row["low"] <= level + band) if up else (row["high"] >= level - band)
        held = (row["close"] >= level) if up else (row["close"] <= level)
        if touched and held:
            return NecklinePoint(t, float(row["close"]), "RETEST")
    return None


def _atr(df: pd.DataFrame, period: int = 14) -> float:
    h, low, c = df["high"], df["low"], df["close"]
    prev = c.shift(1)
    tr = pd.concat([h - low, (h - prev).abs(), (low - prev).abs()], axis=1).max(axis=1)
    return float(tr.ewm(alpha=1 / period, adjust=False).mean().iloc[-1])


def detect_double(
    df: pd.DataFrame,
    *,
    left: int = 3,
    right: int = 3,
    eq_tol: float = 0.04,
    min_separation_bars: int = 22,
    min_depth_pct: float = 0.08,
    prior_trend_pct: float = 0.10,
) -> NecklinePattern | None:
    """Çift dip / çift tepe. Şartların HEPSİ sağlanmazsa `None`."""
    if len(df) < 80:
        return None

    zig = alternate_pivots(find_pivots(df, left=left, right=right))
    if len(zig) < 4:
        return None

    close = df["close"]
    atr = _atr(df)

    # En SON tamamlanmış üçlü: P1 (uç) - orta (boyun) - P2 (uç)
    for i in range(len(zig) - 3, -1, -1):
        p1, mid, p2 = zig[i], zig[i + 1], zig[i + 2]
        if p1.kind != p2.kind or mid.kind == p1.kind:
            continue

        sep = p2.bar_idx - p1.bar_idx
        if sep < min_separation_bars:
            continue                                     # LMW: ≥22 gün

        # Bulkowski çift dipte iki dibin birbirine ~%4 içinde olmasını
        # kabul ediyor. Lo-Mamaysky-Wang'in FORMAL tanımı daha katı
        # (ortalamalarının %1.5'i); daha seçici bir tarama isteniyorsa
        # `eq_tol=0.015` verilir.
        if abs(p2.price - p1.price) / max(p1.price, 1e-9) > eq_tol:
            continue

        depth = abs(mid.price - (p1.price + p2.price) / 2)
        if depth / max(p1.price, 1e-9) < min_depth_pct or depth < 1.5 * atr:
            continue                                     # aradaki hareket anlamsız

        is_bottom = p1.kind == "low"

        # ÖNCEKİ TREND şartı: çift dipten önce düşüş, çift tepeden önce yükseliş
        pre = close.iloc[max(0, p1.bar_idx - 60) : p1.bar_idx + 1]
        if len(pre) < 10:
            continue
        pre_move = (float(pre.iloc[-1]) - float(pre.max() if is_bottom else pre.min())) / max(
            float(pre.iloc[0]), 1e-9
        )
        if is_bottom and pre_move > -prior_trend_pct:
            continue
        if not is_bottom and pre_move < prior_trend_pct:
            continue

        neck = float(mid.price)
        trigger = neck
        after = df.iloc[p2.confirmed_idx + 1 :]
        brk = None
        state = "olusuyor"
        if len(after):
            hit = after[after["close"] > trigger] if is_bottom else after[after["close"] < trigger]
            if len(hit):
                b = hit.iloc[0]
                brk = NecklinePoint(hit.index[0], float(b["close"]), "KIRILIM")
                state = "onaylandi"

        height = abs(neck - (p1.price + p2.price) / 2)
        target = neck + height if is_bottom else neck - height

        anchor = brk.t if brk else p2.bar_time
        bars_ago = int((df.index > anchor).sum())

        retest = _find_retest(df, brk, trigger, up=is_bottom)

        # Hologram: boyun kesişiminden boyun kesişimine GERÇEK kapanış yolu
        ps, pe = _path_bounds(df, p1.bar_idx, p2.bar_idx, neck, below=is_bottom)
        path = df["close"].iloc[ps : pe + 1]
        outer = (
            NecklinePoint(df.index[ps], float(df["close"].iloc[ps]), ""),
            NecklinePoint(df.index[pe], float(df["close"].iloc[pe]), ""),
        )
        holo = Hologram(
            times=tuple(path.index), prices=tuple(float(v) for v in path),
        )

        return NecklinePattern(
            kind="cift_dip" if is_bottom else "cift_tepe",
            direction="long" if is_bottom else "short",
            points=(
                NecklinePoint(p1.bar_time, float(p1.price), "B1" if is_bottom else "T1"),
                NecklinePoint(mid.bar_time, neck, "BOYUN"),
                NecklinePoint(p2.bar_time, float(p2.price), "B2" if is_bottom else "T2"),
            ),
            # Boyun çizgisi formasyonun KENDİ aralığını tanımlar; sağa
            # uzatmak çizim katmanının işi. Son bara kadar tanımlanırsa
            # gövde dolgusunun üst kenarı doğru interpole edilemiyor.
            neckline=((p1.bar_time, neck), (p2.bar_time, neck)),
            trigger_price=trigger,
            trigger_note="Boyun çizgisi kapanışla kırılmalı",
            breakout=brk, retest=retest, target=target, state=state, bars_ago=bars_ago,
            separation_bars=int(sep),
            depth_pct=float(depth / max(p1.price, 1e-9)),
            hologram=holo,
            outer=outer,
        )
    return None


def detect_head_shoulders(
    df: pd.DataFrame,
    *,
    left: int = 3,
    right: int = 3,
    shoulder_tol: float = 0.10,
    min_head_excess: float = 0.08,
    neck_slope_max_total: float = 0.15,
) -> NecklinePattern | None:
    """Omuz-Baş-Omuz ve Ters OBO.

    Bulkowski kuralları:
      - Baş, iki omuzdan da belirgin biçimde daha uçta olmalı.
      - Omuzlar birbirine yakın olmalı (kesin eşit değil).
      - **Boyun çizgisi EĞİMLİ olabilir.** `hs_pattern.py`'deki eski
        uygulama eğim sınırını BAR BAŞINA uyguluyordu; 40 barda ~%40
        toplam kayma serbest kalıyordu. Burada sınır TOPLAM kaymaya
        konur.
      - **Boyun yukarı eğimliyse tetik, boyun çizgisi DEĞİL, sağ
        KOLTUKALTI tepesinin kapanışla aşılmasıdır** — yoksa eğimli boyun
        fiyattan kaçar ve sinyal hiç gelmez.
    """
    if len(df) < 90:
        return None

    zig = alternate_pivots(find_pivots(df, left=left, right=right))
    if len(zig) < 5:
        return None

    close = df["close"]

    for i in range(len(zig) - 5, -1, -1):
        l1, t1, head, t2, l3 = zig[i : i + 5]
        # OBO: tepe-dip-TEPE-dip-tepe ; ters OBO: dip-tepe-DİP-tepe-dip
        if not (l1.kind == head.kind == l3.kind and t1.kind == t2.kind and t1.kind != head.kind):
            continue

        top = head.kind == "high"
        shoulders = (float(l1.price), float(l3.price))
        avg_sh = sum(shoulders) / 2

        if abs(shoulders[0] - shoulders[1]) / max(avg_sh, 1e-9) > shoulder_tol:
            continue                                    # omuzlar birbirine uzak

        # Baş, omuz ortalamasından belirgin biçimde uçta olmalı. Eşik
        # gevşek olursa gürültüden bir "OBO" uydurulur: ilk denemede
        # %3'lük eşikle baş 80.5 / omuzlar 78.6-77.6 olan sahte bir yapı
        # seçildi, gerçek formasyon (baş %14 çıkıntılı) atlandı.
        excess = (head.price - avg_sh) / max(avg_sh, 1e-9)
        if top and excess < min_head_excess:
            continue
        if not top and -excess < min_head_excess:
            continue

        # Boyun çizgisi: iki koltukaltı
        n0, n1 = float(t1.price), float(t2.price)
        total_slope = abs(n1 - n0) / max(abs((n0 + n1) / 2), 1e-9)
        if total_slope > neck_slope_max_total:
            continue                                    # boyun fazla eğimli

        rising_neck = (n1 > n0) if top else (n1 < n0)
        armpit = max(n0, n1) if top else min(n0, n1)
        if rising_neck:
            trigger = armpit
            note = "Boyun eğimli — tetik SAĞ KOLTUKALTI seviyesi"
        else:
            trigger = n1
            note = "Boyun çizgisi kapanışla kırılmalı"

        after = df.iloc[l3.confirmed_idx + 1 :]
        brk, state = None, "olusuyor"
        if len(after):
            hit = after[after["close"] < trigger] if top else after[after["close"] > trigger]
            if len(hit):
                brk = NecklinePoint(hit.index[0], float(hit.iloc[0]["close"]), "KIRILIM")
                state = "onaylandi"

        retest = _find_retest(df, brk, float(trigger), up=not top)

        height = abs(float(head.price) - (n0 + n1) / 2)
        target = trigger - height if top else trigger + height

        ps, pe = _path_bounds(
            df, l1.bar_idx, l3.bar_idx, (n0 + n1) / 2, below=not top
        )
        path = close.iloc[ps : pe + 1]
        outer = (
            NecklinePoint(df.index[ps], float(close.iloc[ps]), ""),
            NecklinePoint(df.index[pe], float(close.iloc[pe]), ""),
        )
        anchor = brk.t if brk else l3.bar_time

        return NecklinePattern(
            kind="obo" if top else "ters_obo",
            direction="short" if top else "long",
            # İskelet TÜM pivotlardan geçmeli. Yalnızca üç uç bağlanırsa
            # koltukaltları atlanır ve formasyon dev bir üçgen gibi
            # görünür ("yarım üçgen" şikâyeti tam olarak buydu).
            points=(
                NecklinePoint(l1.bar_time, float(l1.price), "SOL OMUZ"),
                NecklinePoint(t1.bar_time, n0, ""),
                NecklinePoint(head.bar_time, float(head.price), "BAŞ"),
                NecklinePoint(t2.bar_time, n1, ""),
                NecklinePoint(l3.bar_time, float(l3.price), "SAĞ OMUZ"),
            ),
            neckline=((t1.bar_time, n0), (t2.bar_time, n1)),
            trigger_price=float(trigger), trigger_note=note,
            breakout=brk, retest=retest, target=float(target), state=state,
            bars_ago=int((df.index > anchor).sum()),
            separation_bars=int(l3.bar_idx - l1.bar_idx),
            depth_pct=float(abs(excess)),
            hologram=Hologram(
                times=tuple(path.index), prices=tuple(float(v) for v in path)
            ),
            outer=outer,
        )
    return None

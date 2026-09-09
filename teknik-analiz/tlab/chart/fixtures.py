"""Deterministik sentetik OHLCV — YALNIZCA test/demo içindir.

Görsel regresyon testleri (altın-görsel karşılaştırması) sabit bir girdi
ister; canlı veri kullanılırsa test her gün kendiliğinden kırılır. Bu modül
üretim yolunda ASLA çağrılmaz.

Üreteç, çizimi denemek istediğimiz YAPIYI kasten kurar (yatay sıkışma,
yükselen kanal, ...) — böylece göstergenin o formasyonu GERÇEKTEN bulup
bulmadığı da sınanmış olur.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _ohlc_from_close(close: np.ndarray, rng: np.random.Generator) -> pd.DataFrame:
    """Kapanış serisinden TUTARLI OHLC üret: high >= max(open,close),
    low <= min(open,close). (`core.types.validate_ohlcv` bunu şart koşuyor;
    tutarsız bar üreten bir fikstür indikatörleri yanlış yerde patlatır.)"""
    n = len(close)
    open_ = np.r_[close[0], close[:-1]] * (1 + rng.normal(0, 0.002, n))
    body_hi = np.maximum(open_, close)
    body_lo = np.minimum(open_, close)
    high = body_hi * (1 + np.abs(rng.normal(0, 0.006, n)))
    low = body_lo * (1 - np.abs(rng.normal(0, 0.006, n)))
    vol = rng.lognormal(mean=15.0, sigma=0.55, size=n)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": vol}
    )


def range_market(n: int = 320, seed: int = 11) -> pd.DataFrame:
    """Önce trend, sonra NET bir yatay sıkışma (destek ve dirence birden
    çok kez dokunan). Referans: HRjNKRZWAAAhfSy."""
    rng = np.random.default_rng(seed)
    n_trend = n // 3
    n_range = n - n_trend

    trend = 40 * np.exp(np.cumsum(rng.normal(0.0035, 0.016, n_trend)))
    base = float(trend[-1])
    support, resistance = base * 0.92, base * 1.08
    mid, half = (support + resistance) / 2, (resistance - support) / 2

    # sınırlara tekrar tekrar dokunan, ama DÜZENLİ OLMAYAN salınım:
    # her bacağın uzunluğu ve derinliği rastgele -- gerçek bir sıkışma
    # mükemmel bir sinüs gibi görünmez.
    segs: list[np.ndarray] = []
    level = mid
    up_next = True
    while sum(len(s_) for s_ in segs) < n_range:
        leg = int(rng.integers(14, 42))
        depth = float(rng.uniform(0.62, 1.02))
        target = (resistance if up_next else support)
        target = mid + (target - mid) * depth
        seg = np.linspace(level, target, leg) + rng.normal(0, base * 0.006, leg)
        segs.append(seg)
        level = float(seg[-1])
        up_next = not up_next
    rangepart = np.concatenate(segs)[:n_range]
    rangepart = np.clip(rangepart, support * 0.985, resistance * 1.015)

    close = np.r_[trend, rangepart]
    df = _ohlc_from_close(close, rng)
    df.index = pd.bdate_range("2024-01-02", periods=n, tz="UTC")
    return df


def rising_channel(n: int = 260, seed: int = 23) -> pd.DataFrame:
    """Paralel yükselen kanal — alt banda birkaç kez dokunan.
    Referans: HRiOTwUbQAA9WKw."""
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    trend = 15.5 * np.exp(0.0022 * t)
    width = trend * 0.055
    osc = np.sin(np.linspace(0, 4 * np.pi * 1.3, n))
    close = trend + osc * width + rng.normal(0, 1, n) * width * 0.16
    df = _ohlc_from_close(close, rng)
    df.index = pd.bdate_range("2025-09-01", periods=n, tz="UTC")
    return df


def impulse_retrace(n: int = 200, seed: int = 31) -> pd.DataFrame:
    """Güçlü bir yukarı itiş + ardından düzeltme — fibo/altın bölge için.
    Kullanıcının golden_zone şikâyetinin doğru karşılığı: düzeltme BASKIN
    hareketin üzerine kurulmalı, son küçük salınımın değil."""
    rng = np.random.default_rng(seed)
    n_up = int(n * 0.55)
    n_dn = n - n_up
    up = 100 * np.exp(np.cumsum(rng.normal(0.0075, 0.013, n_up)))
    peak = float(up[-1])
    low0 = float(up[0])
    target = low0 + (peak - low0) * 0.45          # ~0.55 geri çekilme
    dn = np.linspace(peak, target, n_dn) * (1 + rng.normal(0, 0.008, n_dn))
    close = np.r_[up, dn]
    df = _ohlc_from_close(close, rng)
    df.index = pd.bdate_range("2025-11-03", periods=n, tz="UTC")
    return df


def harmonic_shape(n: int = 220, seed: int = 47) -> pd.DataFrame:
    """Net bir X-A-B-C-D iskeleti taşıyan seri (yükseliş harmoniği).

    Bacaklar Fibonacci oranlarına YAKIN kurulur ki gerçek harmonik motor
    bunu aday olarak kabul edebilsin. Referans: HRhIeAdbcAAL2_B.
    """
    rng = np.random.default_rng(seed)
    x, a = 100.0, 148.0
    b = a - (a - x) * 0.618
    c = b + (a - b) * 0.786
    d = a - (a - x) * 1.272
    # X'TEN ÖNCE bir bacak şart: X serinin ilk barındaysa `find_pivots`
    # onu pivot olarak GÖREMEZ (sol tarafında karşılaştıracak bar yok) ve
    # formasyon yanlış noktalardan kurulur -- ilk denemede tam olarak bu
    # oldu (AB/XA = 2.364 çıktı, harmonik aralığın çok dışı).
    legs = [(x + 26.0, x, 20), (x, a, 34), (a, b, 22), (b, c, 26), (c, d, 30)]
    parts = [np.array([x + 26.0])]
    for p0, p1, k in legs:
        seg = np.linspace(p0, p1, k)
        seg = seg + rng.normal(0, abs(p1 - p0) * 0.035, k)
        parts.append(seg)
    # D'den SONRA tepki şart. Harmonik bir DÖNÜŞ formasyonu; D'yi düz bir
    # kuyruk izlerse `significant_pivots` onu pivot olarak kesinleştirmez
    # ve formasyon D'siz kalır (ilk denemede tam olarak bu oldu: 5 pivot
    # bulundu, D listede yoktu).
    bounce = d + (c - d) * 0.45
    parts.append(np.linspace(d, bounce, 26)[1:])
    body = np.concatenate(parts)
    pad = n - len(body)
    if pad > 0:
        tail = bounce + np.cumsum(rng.normal(0.0, 0.7, pad))
        body = np.r_[body, tail]
    close = body[:n]
    df = _ohlc_from_close(close, rng)
    df.index = pd.bdate_range("2025-10-01", periods=len(df), tz="UTC")
    return df


def double_bottom(n: int = 260, seed: int = 61) -> pd.DataFrame:
    """Bulkowski ölçütlerini SAĞLAYAN bir çift dip.

    Önce düşüş trendi (%>10), sonra birbirine yakın iki dip, aralarında
    anlamlı bir toparlanma, dipler arası ≥22 bar (LMW), ardından boyun
    çizgisinin kapanışla kırılması.
    """
    rng = np.random.default_rng(seed)
    start, bottom = 200.0, 120.0
    neck = bottom * 1.20
    legs = [
        (start, bottom, 60),        # önceki düşüş trendi
        (bottom, neck, 26),         # ilk toparlanma -> boyun
        (neck, bottom * 1.01, 28),  # ikinci dip (ilkine yakın)
        (bottom * 1.01, neck * 1.14, 34),   # boyun kırılımı ve ötesi
    ]
    parts = [np.array([start])]
    for p0, p1, k in legs:
        seg = np.linspace(p0, p1, k) + rng.normal(0, abs(p1 - p0) * 0.045, k)
        parts.append(seg)
    body = np.concatenate(parts)
    pad = n - len(body)
    if pad > 0:
        body = np.r_[body, body[-1] + np.cumsum(rng.normal(0.05, 1.4, pad))]
    df = _ohlc_from_close(body[:n], rng)
    df.index = pd.bdate_range("2025-06-02", periods=len(df), tz="UTC")
    return df


def flag_after_pole(n: int = 180, seed: int = 73) -> pd.DataFrame:
    """Dik bir direk + kısa konsolidasyon + kırılım.

    Konsolidasyon boyunca hacim DARALIR (Bulkowski: vakaların ~%79'unda),
    direk ve kırılım barlarında artar -- hacim filtresinin sınanabilmesi
    için gerçekçi olması şart.
    """
    rng = np.random.default_rng(seed)
    base = 30.0
    pre = base + np.cumsum(rng.normal(0.01, 0.28, 40))
    p0 = float(pre[-1])
    p1 = p0 * 1.32
    pole = np.linspace(p0, p1, 14) + rng.normal(0, p0 * 0.006, 14)
    flag = np.linspace(p1, p1 * 0.93, 11) + rng.normal(0, p0 * 0.005, 11)
    brk = np.linspace(float(flag[-1]), p1 * 1.22, 26) + rng.normal(0, p0 * 0.008, 26)
    close = np.r_[pre, pole, flag, brk]
    pad = n - len(close)
    if pad > 0:
        close = np.r_[close, close[-1] + np.cumsum(rng.normal(0.0, 0.35, pad))]
    df = _ohlc_from_close(close[:n], rng)

    # hacim profili: direkte yüksek, bayrakta düşük, kırılımda yüksek
    v = np.full(len(df), 2.0)
    v[40:54] = 5.5                      # direk
    v[54:65] = 1.4                      # bayrak -- daralma
    v[65:75] = 4.8                      # kırılım
    df["volume"] = v * 1e6 * rng.lognormal(0, 0.22, len(df))
    df.index = pd.bdate_range("2026-01-05", periods=len(df), tz="UTC")
    return df


def head_shoulders(n: int = 300, seed: int = 89, inverse: bool = False) -> pd.DataFrame:
    """Omuz-Baş-Omuz (veya ters OBO) — Bulkowski ölçütlerini sağlayan.

    Boyun çizgisi kasten HAFİF EĞİMLİ kurulur: eğimli boyun, tetiğin
    sağ koltukaltına kayması kuralını sınamak için gerekli.
    """
    rng = np.random.default_rng(seed)
    base = 80.0
    sh1, head_p, sh2 = base * 1.22, base * 1.38, base * 1.20
    n0, n1 = base * 1.04, base * 1.08          # boyun hafif YUKARI eğimli
    legs = [
        (base, n0, 30),          # önceki yükseliş
        (n0, sh1, 20),           # sol omuz
        (sh1, n0 * 1.01, 16),    # ilk koltukaltı
        (n0 * 1.01, head_p, 24), # baş
        (head_p, n1, 20),        # ikinci koltukaltı
        (n1, sh2, 18),           # sağ omuz
        (sh2, n1 * 0.93, 26),    # boyun kırılımı
    ]
    parts = [np.array([base])]
    for p0, p1, k in legs:
        parts.append(np.linspace(p0, p1, k) + rng.normal(0, abs(p1 - p0) * 0.05, k))
    body = np.concatenate(parts)
    pad = n - len(body)
    if pad > 0:
        body = np.r_[body, body[-1] + np.cumsum(rng.normal(-0.02, 0.7, pad))]
    close = body[:n]
    if inverse:
        close = 2 * base - close
    df = _ohlc_from_close(close, rng)
    df.index = pd.bdate_range("2025-04-01", periods=len(df), tz="UTC")
    return df

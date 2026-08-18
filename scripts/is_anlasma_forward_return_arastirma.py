"""BIST yeni is anlasmalari -- "yeni is >= onceki yil hasilatinin %20 fazlasi"
esiginin FORWARD-RETURN (sonraki donem hisse performansi) validasyonu.

Karar (2026-08-18, kullanici: "sen karar ver en iyisine" -- is anlasmalari
entegrasyonunun bir sonraki adimi icin): mevcut oran/%20 esigi anlamli
GORUNUYORDU (ASELS/ASTOR gibi bilinen buyuk siparisli sirketler dogru cikti)
ama HENUZ bu sinyalin GERCEKTEN sonraki hisse performansini ONGORUP
ONGORMEDIGI test EDILMEMISTI -- bu script TAM O soruyu cevaplar: eşiği
GECEN sirketlerin (2025 yili, TEK tam-yil kesin veri -- 2026 henuz tamamlanmadigi
icin forward-return HENUZ olculemez, DAHIL EDILMEDI) sonraki ~6 ay (126 islem
gunu) getirisi, esigi GECMEYEN sirketlerinkinden ISTATISTIKSEL olarak farkli mi?

Metodoloji (projenin geri kalaniyla AYNI disiplin -- Mann-Whitney U, kucuk
n'de "GUVENSIZ" etiketi, NEDENSELLIK dili YASAK):
  - Olcum tarihi: 31.12.2025 (yil sonu) kapanisi -- entry.
  - Ileri pencere: 126 islem gunu (~6 ay) SONRAKI en yakin kapanis -- exit.
    (12 aylik pencere bugun -- 2026-08-18 -- icin HENUZ TAM gerceklesmedi,
    6 ay muhafazakar/tam gerceklesmis bir secim.)
  - forward_return_pct = (exit/entry - 1) * 100.
  - Grup karsilastirmasi: esigi GECEN vs GECMEYEN (`is_anlasmalari_yillik.csv`
    zaten hesaplanmis `esik_gecti_mi` sutunu, DEGISTIRILMEDEN kullanilir).

Kullanim:
    python scripts/is_anlasma_forward_return_arastirma.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import pandas as pd  # noqa: E402
from scipy import stats as scipy_stats  # noqa: E402

import config  # noqa: E402
from src.fetchers.abcd_data import fetch_ohlcv_abcd  # noqa: E402

config.setup_logging()

_IN_CSV = config.DATA_DIR / "abcd_cache" / "is_anlasmalari_yillik.csv"
_OUT_MD = BASE_DIR / "docs" / "spec" / "IS_ANLASMALARI_FORWARD_RETURN.md"
_OUT_CSV = config.DATA_DIR / "abcd_cache" / "is_anlasmalari_forward_return.csv"
_MEASURE_DATE = date(2025, 12, 31)
_FORWARD_BARS = 126
_MIN_SHOW = 10


def _forward_return(ticker: str) -> float | None:
    df = fetch_ohlcv_abcd(ticker, "1D", 500)
    if df.empty:
        return None
    times = pd.to_datetime(df["time"]).dt.tz_localize(None).dt.date
    entry_idx_candidates = [i for i, t in enumerate(times) if t <= _MEASURE_DATE]
    if not entry_idx_candidates:
        return None
    entry_idx = entry_idx_candidates[-1]
    exit_idx = entry_idx + _FORWARD_BARS
    if exit_idx >= len(df):
        return None  # ileri pencere henuz TAM gerceklesmedi (yetersiz gelecek veri)
    entry_price = float(df["close"].iloc[entry_idx])
    exit_price = float(df["close"].iloc[exit_idx])
    if entry_price <= 0:
        return None
    return (exit_price / entry_price - 1.0) * 100.0


def main() -> int:
    print(f"Girdi okunuyor: {_IN_CSV}")
    df = pd.read_csv(_IN_CSV)
    rows_2025 = df[(df["yil"] == 2025) & df["oran"].notna()].copy()
    print(f"2025 yili, oran hesaplanabilen (ticker,yil) hucresi: {len(rows_2025)}")

    forward_returns = []
    for _, row in rows_2025.iterrows():
        fr = _forward_return(row["ticker"])
        forward_returns.append(fr)
    rows_2025["forward_return_pct"] = forward_returns

    computed = rows_2025[rows_2025["forward_return_pct"].notna()].copy()
    n_skipped = len(rows_2025) - len(computed)
    print(f"Forward-return hesaplanan: {len(computed)} (atlanan: {n_skipped}, veri yetersiz)")

    out_csv = _OUT_CSV
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    computed.to_csv(out_csv, index=False)
    print(f"Ham CSV kaydedildi: {out_csv}")

    gecen = computed[computed["esik_gecti_mi"] == True]["forward_return_pct"]  # noqa: E712
    gecmeyen = computed[computed["esik_gecti_mi"] == False]["forward_return_pct"]  # noqa: E712

    lines = [
        "# BIST Yeni Is Anlasmalari -- Esik (>=%20) Forward-Return Validasyonu\n",
        "\n## Metodoloji\n",
        f"\n- Olcum tarihi: {_MEASURE_DATE.isoformat()} kapanisi (entry) -> {_FORWARD_BARS} islem gunu "
        "(~6 ay) SONRAKI kapanis (exit). SADECE 2025 yili (tek TAM gerceklesmis yil, forward-pencere "
        "bugune -- 2026-08-18 -- kadar TAMAMEN gerceklesmis).\n",
        f"- Toplam (ticker,2025) hucresi: {len(rows_2025)}, forward-return hesaplanan: {len(computed)} "
        f"({n_skipped} atlandi -- fiyat verisi yetersiz).\n",
        f"- Esigi GECEN: n={len(gecen)} · Esigi GECMEYEN: n={len(gecmeyen)}\n",
        "\n> **NEDENSELLIK YASAK:** bulgular ILISKISEL dildedir -- 'esigi gecmek getiriyi artirir' turu "
        "ifadeler KULLANILMAZ, sadece 'esigi gecen grupta forward-return farkli/ayni dagilimda, n=.., p=..' "
        "turu ifadeler kullanilir. n cok kucuk (134 sirketlik statik dokumun SADECE 2025 alt-kumesi) -- "
        "bu KESIN bir kanit DEGIL, bir ILK ISARETTIR.\n",
    ]

    if len(gecen) >= 2 and len(gecmeyen) >= 2:
        u_stat, p_value = scipy_stats.mannwhitneyu(gecen, gecmeyen, alternative="two-sided")
        lines.append("\n## Sonuc\n")
        lines.append(
            f"\n| Grup | n | Medyan Forward-Return % | Ortalama Forward-Return % | Pozitif Getiri Orani % |\n"
            "|---|---|---|---|---|\n"
        )
        for label, series in (("Esigi GECEN", gecen), ("Esigi GECMEYEN", gecmeyen)):
            pos_pct = float((series > 0).mean() * 100.0) if len(series) else float("nan")
            lines.append(f"| {label} | {len(series)} | {series.median():.2f} | {series.mean():.2f} | {pos_pct:.1f} |\n")
        lines.append(f"\nMann-Whitney U testi: p = {p_value:.4f}")
        if len(gecen) < _MIN_SHOW or len(gecmeyen) < _MIN_SHOW:
            lines.append(f" -- **GUVENSIZ** (bir grup n<{_MIN_SHOW}, kucuk orneklemde sahte kesinlik riski)")
        elif p_value < 0.05:
            lines.append(" -- iki grup dagilimi istatistiksel olarak FARKLI (p<0.05)")
        else:
            lines.append(" -- iki grup dagilimi arasinda ISTATISTIKSEL OLARAK ANLAMLI FARK bulunamadi (p>=0.05)")
        lines.append("\n")
    else:
        lines.append("\n## Sonuc\n\n_Bir grupta (esigi gecen/gecmeyen) 2'den az gozlem var, test yapilamadi._\n")

    lines.append("\n## Ham Veri\n")
    lines.append(f"\n`{out_csv}`\n")

    out_path = _OUT_MD
    out_path.write_text("".join(lines), encoding="utf-8")
    print(f"Rapor kaydedildi: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

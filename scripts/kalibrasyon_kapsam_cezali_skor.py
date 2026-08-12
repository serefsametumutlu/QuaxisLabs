"""Kalibrasyon scripti -- docs/spec/spec_kapsam_cezali_skor.md.

SADECE OKUR: `data/bilanco_radar.db`'deki (config.DATABASE_URL)
`MarketScanResult` tablosunda ZATEN biriktirilmiş (scripts/tarama_toplu.py
tarafından yazılmış) GERÇEK tarama sonuçlarını kullanır. DB'ye HİÇBİR
YAZMA yapmaz.

Amaç: mevcut "efektif ağırlık yeniden dağıtımı" skoru (`{lens}_score`,
`_agirlik_dagit_ve_hesapla`'nın ürettiği S) ile önerilen "nominal ağırlık,
eksik=sıfır" skoru (S' = S * coverage_pct/100 -- bkz. spec §Formüller,
matematiksel özdeşliğin ispatı) arasındaki farkı GERÇEK evren üzerinde
ölçer:
  1. Her mercek için kapsam (coverage_pct) dağılımı (persentil tablosu +
     <%25/<%50/<%75/<%100/=%100 bant sayımı) -- "büyük çoğunluk zaten
     düşük kapsamlı mı" sorusuna somut cevap.
  2. S -> S' geçişinde rozet bandı (SAĞLAM/DENGELİ/KARIŞIK/RİSKLİ) kaç
     şirkette DEĞİŞİYOR -- kapsam eşiğine göre kırılımlı (>=%50 vs <%50).
  3. >=%50 kapsamlı alt-kümede S ile S' NE KADAR yakın (ortalama/medyan
     mutlak fark) -- "mevcut davranışla pratikte aynı mı" iddiasının
     doğrulaması.

Kullanım:
    python scripts/kalibrasyon_kapsam_cezali_skor.py
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import select  # noqa: E402

from src.db import repository  # noqa: E402
from src.db.models import MarketScanResult  # noqa: E402

LENSLER = ["deger", "kalite", "buyume", "guvenlik"]
LENS_ETIKET = {"deger": "Değer", "kalite": "Kalite", "buyume": "Büyüme", "guvenlik": "Güvenlik"}

ROZET_ESIKLERI = {"SAĞLAM": Decimal(8), "DENGELİ": Decimal(6), "KARIŞIK": Decimal(4)}


def _badge(score: Decimal) -> str:
    if score >= ROZET_ESIKLERI["SAĞLAM"]:
        return "SAĞLAM"
    if score >= ROZET_ESIKLERI["DENGELİ"]:
        return "DENGELİ"
    if score >= ROZET_ESIKLERI["KARIŞIK"]:
        return "KARIŞIK"
    return "RİSKLİ"


def _percentile(sorted_vals: list[float], pct: float) -> float:
    if not sorted_vals:
        raise ValueError("bos liste")
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (pct / 100) * (len(sorted_vals) - 1)
    lo = int(k)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = k - lo
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * frac


@dataclass
class LensRow:
    ticker: str
    market: str
    score: Decimal
    coverage: Decimal
    badge_eski: str


def _rows_for_lens(scan_rows: list[MarketScanResult], lens: str) -> list[LensRow]:
    out = []
    for r in scan_rows:
        score = getattr(r, f"{lens}_score")
        coverage = getattr(r, f"{lens}_coverage_pct")
        badge = getattr(r, f"{lens}_badge")
        if score is None or coverage is None:
            continue
        out.append(LensRow(ticker=r.ticker, market=r.market, score=score, coverage=coverage, badge_eski=badge))
    return out


def report_coverage_distribution(rows: list[LensRow], etiket: str) -> None:
    n = len(rows)
    print(f"\n### {etiket} -- kapsam (coverage_pct) dağılımı (n={n})")
    if n == 0:
        print("  (veri yok)")
        return
    covs = sorted(float(r.coverage) for r in rows)
    pcts = {p: _percentile(covs, p) for p in (10, 25, 50, 75, 90)}
    print(
        f"  min={covs[0]:.1f}  p10={pcts[10]:.1f}  p25={pcts[25]:.1f}  medyan={pcts[50]:.1f}  "
        f"p75={pcts[75]:.1f}  p90={pcts[90]:.1f}  max={covs[-1]:.1f}"
    )
    bantlar = [
        ("<%25 (çok düşük)", 0, 25),
        ("%25-%50 (düşük)", 25, 50),
        ("%50-%75 (orta)", 50, 75),
        ("%75-<%100 (yüksek)", 75, 100),
        ("=%100 (tam)", 100, 100.01),
    ]
    for label, lo, hi in bantlar:
        count = sum(1 for c in covs if lo <= c < hi)
        print(f"    {label}: {count} şirket (%{count/n*100:.1f})")


def report_badge_shift(rows: list[LensRow], etiket: str) -> None:
    n = len(rows)
    print(f"\n### {etiket} -- rozet bandı kayması (S = mevcut efektif-ağırlıklı, S' = S*kapsam/100)")
    if n == 0:
        print("  (veri yok)")
        return

    degisen = 0
    degismeyen = 0
    alt50 = [r for r in rows if r.coverage < 50]
    ust50 = [r for r in rows if r.coverage >= 50]

    for r in rows:
        s_yeni = r.score * r.coverage / 100
        badge_yeni = _badge(s_yeni)
        if badge_yeni != r.badge_eski:
            degisen += 1
        else:
            degismeyen += 1

    print(f"  Toplam {n} şirket: {degisen} rozet DEĞİŞTİ, {degismeyen} rozet AYNI KALDI.")
    print(f"  Kapsam <%50 olan {len(alt50)} şirket (zaten YETERSİZ VERİ rozetli), kapsam >=%50 olan {len(ust50)} şirket.")

    if ust50:
        farklar = [abs(float(r.score - (r.score * r.coverage / 100))) for r in ust50]
        farklar.sort()
        n2 = len(farklar)
        ort = sum(farklar) / n2
        med = _percentile(farklar, 50)
        degisen_ust50 = sum(1 for r in ust50 if _badge(r.score * r.coverage / 100) != _badge(r.score))
        print(
            f"  >=%50 kapsamlı alt-kümede (n={n2}): |S-S'| ortalama={ort:.2f} puan, medyan={med:.2f} puan, "
            f"p90={_percentile(farklar, 90):.2f} puan -- {degisen_ust50} şirkette (%{degisen_ust50/n2*100:.1f}) "
            f"rozet BANDI DEĞİŞİYOR (>=%50 kapsamda bile)."
        )

    print("\n  Örnek satırlar (kapsam artan sırada, ilk 8):")
    for r in sorted(rows, key=lambda r: r.coverage)[:8]:
        s_yeni = r.score * r.coverage / 100
        print(
            f"    {r.ticker:<8} kapsam=%{float(r.coverage):>5.1f}  S={float(r.score):>5.2f} ({r.badge_eski:<9})"
            f"  ->  S'={float(s_yeni):>5.2f} ({_badge(s_yeni)})"
        )


def report_ayes_style_examples(rows: list[LensRow], etiket: str, esik: float = 30.0) -> None:
    """Kullanıcının AYES şikayetine benzer (çok düşük kapsam + yüksek eski
    skor) somut örnekleri listeler -- kapsam<%esik VE eski skor>=7."""
    adaylar = [r for r in rows if float(r.coverage) < esik and r.score >= Decimal(7)]
    print(f"\n### {etiket} -- AYES-benzeri örnekler (kapsam<%{esik:.0f} AMA eski skor>=7,0): {len(adaylar)} şirket")
    for r in sorted(adaylar, key=lambda r: r.coverage)[:15]:
        s_yeni = r.score * r.coverage / 100
        print(f"    {r.ticker:<8} kapsam=%{float(r.coverage):>5.1f}  eski S={float(r.score):.2f}  yeni S'={float(s_yeni):.2f}")


def main() -> None:
    with repository.get_session() as session:
        scan_rows = session.execute(
            select(MarketScanResult).where(MarketScanResult.scan_status == "ok")
        ).scalars().all()

    print(f"# Kapsam-Cezalı Skor Kalibrasyonu -- {len(scan_rows)} 'ok' taranmış şirket üzerinde")
    print(f"# BİST: {sum(1 for r in scan_rows if r.market=='BIST')}  NASDAQ: {sum(1 for r in scan_rows if r.market=='NASDAQ')}")

    for lens in LENSLER:
        rows = _rows_for_lens(scan_rows, lens)
        etiket = LENS_ETIKET[lens]
        report_coverage_distribution(rows, etiket)
        report_badge_shift(rows, etiket)
        report_ayes_style_examples(rows, etiket)
        print("\n" + "-" * 78)


if __name__ == "__main__":
    main()

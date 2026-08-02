"""Teslim kriteri demo: ornek bir AnalysisResult uzerinden puanlama motorunu
calistirir, bileşen tablosunu ve toplam skoru konsola basar.

Kullanim: python scripts/demo_score.py
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.analysis import calculator, scorer
from src.formatting import format_number_tr

_LATEST = (2026, 3)
_YOY_PRIOR = (2025, 3)
_QOQ_PRIOR = (2025, 12)
_TTM_3 = (2025, 9)
_TTM_4 = (2025, 6)


def _donem(revenue, gross, op, dep, net, cash, tr, assets, debt, equity, ca, stl) -> dict:
    return {
        "revenue": Decimal(revenue),
        "gross_profit": Decimal(gross),
        "operating_profit": Decimal(op),
        "depreciation_amortization": Decimal(dep),
        "net_income": Decimal(net),
        "cash": Decimal(cash),
        "trade_receivables": Decimal(tr),
        "total_assets": Decimal(assets),
        "financial_debt": Decimal(debt),
        "equity": Decimal(equity),
        "current_assets": Decimal(ca),
        "short_term_liabilities": Decimal(stl),
    }


def _ornek_finansallar() -> calculator.FinancialsByPeriod:
    """Guclu FAVOK marji, dusuk kaldirac, pozitif buyume/karlilik olan ornek sanayi sirketi."""
    return {
        _LATEST: _donem(1200, 500, 350, 60, 260, 400, 150, 5000, 600, 3000, 1800, 900),
        _QOQ_PRIOR: _donem(1100, 460, 320, 58, 230, 380, 140, 4800, 620, 2850, 1700, 880),
        _YOY_PRIOR: _donem(1000, 400, 260, 55, 180, 300, 130, 4500, 700, 2600, 1600, 850),
        _TTM_3: _donem(1050, 430, 280, 56, 200, 320, 135, 4600, 680, 2700, 1650, 860),
        _TTM_4: _donem(980, 390, 250, 54, 175, 290, 125, 4400, 690, 2550, 1580, 840),
    }


def _tabloyu_yazdir(sonuc: scorer.ScoreResult) -> None:
    print(f"\n{sonuc.ticker} -- {sonuc.period[0]}/Ç{sonuc.period[1] // 3} -- Şablon: {sonuc.template}")
    print("=" * 100)
    baslik = f"{'Bileşen':<28}{'Skor':>7}{'Ağırlık(nom.)':>15}{'Ağırlık(efek.)':>16}{'Katkı':>8}  Gerekçe"
    print(baslik)
    print("-" * 100)
    for c in sonuc.components:
        skor_str = format_number_tr(c.score, decimals=1) if c.score is not None else "  -  "
        print(
            f"{c.name:<28}{skor_str:>7}{format_number_tr(c.weight_nominal, decimals=0) + '%':>15}"
            f"{format_number_tr(c.weight_effective, decimals=1) + '%':>16}"
            f"{format_number_tr(c.contribution, decimals=2):>8}  {c.reasoning_tr}"
        )
    print("-" * 100)
    print(f"TOPLAM SKOR: {format_number_tr(sonuc.total_score, decimals=2)} / 10   ROZET: {sonuc.badge}")


def main() -> None:
    analiz = calculator.analyze("TESTAS", _ornek_finansallar())

    print("### Senaryo 1: fiyat verisi YOK -> Değerleme bileşeni atlanır, ağırlık yeniden dağıtılır ###")
    sonuc_fiyatsiz = scorer.score_industrial(analiz)
    _tabloyu_yazdir(sonuc_fiyatsiz)

    print("\n\n### Senaryo 2: fiyat verisi VAR (F/K=10, PD/DD=1,5) -> tüm 6 bileşen hesaplanır ###")
    sonuc_fiyatli = scorer.score_industrial(
        analiz, valuation=scorer.ValuationInput(pe_ratio=Decimal("10"), pb_ratio=Decimal("1.5"))
    )
    _tabloyu_yazdir(sonuc_fiyatli)


if __name__ == "__main__":
    main()

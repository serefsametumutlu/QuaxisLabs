"""Teslim kriteri demo: sahte bir AnalysisResult + ScoreResult ile
generate_commentary() cagirir ve uretilen Commentary'yi konsola basar.

- GEMINI_API_KEY .env icinde tanimliysa GERCEK bir Gemini API cagrisi yapilir.
- Tanimli degilse LLM'siz yedek mod devreye girer (bu da ayrica gosterilir).

Kullanim: python scripts/demo_commentary.py
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from src.ai import commentary
from src.analysis import calculator, scorer
from src.fetchers import kap
from datetime import datetime

config.setup_logging()

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
    """Net kar YoY zarardan kara donen, hasilat/FAVOK guclu buyuyen ornek
    sirket -- ozel gecis etiketinin oncelik kuralini da gosterir."""
    return {
        _LATEST: _donem(1200, 500, 350, 60, 260, 400, 150, 5000, 600, 3000, 1800, 900),
        _QOQ_PRIOR: _donem(1100, 460, 320, 58, 230, 380, 140, 4800, 620, 2850, 1700, 880),
        _YOY_PRIOR: _donem(1000, 400, 260, 55, -80, 300, 130, 4500, 700, 2600, 1600, 850),
        _TTM_3: _donem(1050, 430, 280, 56, 200, 320, 135, 4600, 680, 2700, 1650, 860),
        _TTM_4: _donem(980, 390, 250, 54, 175, 290, 125, 4400, 690, 2550, 1580, 840),
    }


def _ornek_kap_bildirimleri() -> list[kap.Disclosure]:
    return [
        kap.Disclosure(
            date=datetime(2026, 7, 15),
            title="Kuveyt Terminal 2 İhalesi Sonuçlandı",
            category="İhale Süreci / Sonucu",
            summary="Kuveyt Terminal 2 İhalesi Sonuçlandı",
            url="https://kap.org.tr/tr/Bildirim/1234567",
            importance=kap.IMPORTANCE_HIGH,
            is_late=False,
            disclosure_index=1234567,
            stock_codes="TESTAS",
        ),
    ]


def main() -> None:
    analiz = calculator.analyze("TESTAS", _ornek_finansallar())
    skor = scorer.score_industrial(analiz)
    bildirimler = _ornek_kap_bildirimleri()

    api_key_durumu = "evet" if config.GEMINI_API_KEY else "hayır -> LLM'siz yedek mod beklenir"
    print(f"GEMINI_API_KEY tanımlı mı: {api_key_durumu}")
    print()

    yorum = commentary.generate_commentary(analiz, skor, bildirimler)

    print(f"### Commentary (kaynak: {yorum.source}) ###")
    print(f"Başlık   : {yorum.headline}")
    print(f"Özet     : {yorum.summary}")
    print("Olumlu   :")
    for p in yorum.positives:
        print(f"  - {p}")
    print("Olumsuz  :")
    for n in yorum.negatives:
        print(f"  - {n}")
    print(f"KAP Notu : {yorum.kap_note}")


if __name__ == "__main__":
    main()

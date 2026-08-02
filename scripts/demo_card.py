"""Teslim kriteri demo: sahte ama gercekci bir context ile PNG kart uretir.

Gercek boru hattini (calculator -> scorer) kullanir ama LLM'i (Gemini) AG
ISTEGI GONDERMEDEN, elle yazilmis gercekci bir Commentary ile besler --
boylece demo hizli, deterministik ve API anahtarindan bagimsizdir.

Kullanim: python scripts/demo_card.py
Cikti   : data/cards/demo_TESTAS.png (ayrica debug icin data/last_card.html)
"""

from __future__ import annotations

import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from src.ai.commentary import Commentary
from src.analysis import calculator, scorer
from src.fetchers import kap
from src.render import card

config.setup_logging()

_LATEST = (2026, 3)
_YOY_PRIOR = (2025, 3)
_QOQ_PRIOR = (2025, 12)
_TTM_3 = (2025, 9)
_TTM_4 = (2025, 6)


# Gercek Is Yatirim verisi mutlak TL cinsindendir (bkz. thyao_items_readable.txt,
# orn. sermaye 1.380.000.000 TL); demo'nun F/K, PD/DD gibi carpanlari
# gercekci gorunsun diye kucuk ornek rakamlar bu olcekle carpilir.
_SCALE = Decimal("1000000")


def _donem(revenue, gross, op, dep, net, cash, tr, assets, debt, equity, ca, stl) -> dict:
    # "_cum" (kumulatif/YTD) alanlari da ceyreklik alanla AYNI deger tasir --
    # bu ornek verideki her donem birbirinden bagimsiz (gercek YTD toplama
    # ihtiyaci yok), ama calculator.analyze() GELIR TABLOSU ozet tablosunu
    # KASITLI olarak "_cum" alanlarindan okur (bkz. calculator.py analyze()
    # ici not); bu alanlar eksik olursa Hasılat/Brüt Kâr/vb. satirlari "veri
    # yok" gosterir (bkz. tests/test_scorer.py::_donem'deki ayni not).
    return {
        "revenue": Decimal(revenue) * _SCALE,
        "revenue_cum": Decimal(revenue) * _SCALE,
        "gross_profit": Decimal(gross) * _SCALE,
        "gross_profit_cum": Decimal(gross) * _SCALE,
        "operating_profit": Decimal(op) * _SCALE,
        "operating_profit_cum": Decimal(op) * _SCALE,
        "depreciation_amortization": Decimal(dep) * _SCALE,
        "depreciation_amortization_cum": Decimal(dep) * _SCALE,
        "net_income": Decimal(net) * _SCALE,
        "net_income_cum": Decimal(net) * _SCALE,
        "cash": Decimal(cash) * _SCALE,
        "trade_receivables": Decimal(tr) * _SCALE,
        "total_assets": Decimal(assets) * _SCALE,
        "financial_debt": Decimal(debt) * _SCALE,
        "equity": Decimal(equity) * _SCALE,
        "current_assets": Decimal(ca) * _SCALE,
        "short_term_liabilities": Decimal(stl) * _SCALE,
    }


def _ornek_finansallar() -> calculator.FinancialsByPeriod:
    """Net kar YoY zarardan kara donen, hasilat/FAVOK guclu buyuyen, bilancosu
    saglam bir ornek sirket -- kartin tum bolumlerini (ozel gecis etiketi,
    pozitif/negatif bulgular, guclu skor) anlamli sekilde doldurmasi icin."""
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
        kap.Disclosure(
            date=datetime(2026, 7, 2),
            title="Yönetim Kurulu Temettü Dağıtım Kararı Aldı",
            category="Kâr Payı Dağıtım Önerisi",
            summary="Yönetim Kurulu Temettü Dağıtım Kararı Aldı",
            url="https://kap.org.tr/tr/Bildirim/1234321",
            importance=kap.IMPORTANCE_HIGH,
            is_late=False,
            disclosure_index=1234321,
            stock_codes="TESTAS",
        ),
    ]


def _ornek_commentary() -> Commentary:
    """Gercek bir Gemini yanitina benzeyen, elle yazilmis Commentary --
    ag istegi yok, demo hizli ve deterministik kalsin diye."""
    return Commentary(
        headline="TESTAS 2026/Ç1 DÖNEMİNDE ZARARDAN KÂRA GEÇTİ",
        summary=(
            "TESTAS, 2026/Ç1 döneminde net dönem kârını önceki yılın aynı döneminde açıkladığı "
            "zarardan kâra geçirdi. Hasılat yıllık %20,0 artışla güçlenirken, FAVÖK marjı %34,2 "
            "seviyesine yükseldi. Şirket 9,6/10 toplam puanla SAĞLAM rozeti kazandı."
        ),
        positives=[
            "Net dönem kârı önceki yılın aynı dönemindeki zarardan kâra geçti.",
            "FAVÖK yıllık %30,2 güçlü artışla 410,0 mn ₺ seviyesine ulaştı.",
            "Esas faaliyet kârı yıllık %34,6 güçlü artış gösterdi.",
            "Hasılat yıllık %20,0 artışla 1,2 mr ₺ seviyesine çıktı.",
        ],
        negatives=[
            "Finansal borçlar çeyreklik bazda %3,2 azaldı ancak seviyesini korudu.",
        ],
        kap_note="15.07.2026 tarihli KAP bildirimine göre Kuveyt Terminal 2 İhalesi sonuçlanmıştır.",
        disclaimer_context=None,
        source="llm",
    )


def main() -> None:
    analiz = calculator.analyze("TESTAS", _ornek_finansallar())
    fiyat = Decimal("142.50")
    sermaye = Decimal("50000000")  # odenmis sermaye (TL) = varsayilan pay adedi
    degerleme = calculator.compute_valuation(analiz, fiyat, sermaye)
    skor = scorer.score_industrial(
        analiz,
        valuation=scorer.ValuationInput(pe_ratio=degerleme.pe_ratio, pb_ratio=degerleme.pb_ratio),
    )
    yorum = _ornek_commentary()
    bildirimler = _ornek_kap_bildirimleri()

    context = card.build_card_context(
        analiz,
        skor,
        yorum,
        bildirimler,
        company_name="Test Sanayi A.Ş.",
        sector="Sanayi / Holding",
        price=fiyat,
        valuation=degerleme,
    )

    out_path = config.DATA_DIR / "cards" / "demo_TESTAS.png"
    result_path = card.render_card(context, str(out_path))

    print(f"PNG üretildi: {result_path}")
    print(f"Debug HTML  : {card._debug_html_path('card.html')}")


if __name__ == "__main__":
    main()

"""Kart Tasarım Sistemi doğrulama döngüsü -- SENARYO B: N/A'lı eksik veri.

`demo_card.py`'nin (bol veri) YANINDA -- amortisman verisi HİÇ yok (FAVÖK/
Kaldıraç bileşenleri "veri yok"), fiyat/sermaye HİÇ verilmiyor (Değerleme
bileşeni + üst bant DEĞERLEME şeridi tamamen gizli). Cevaplanan bileşenlerin
nominal ağırlık toplamı %50 eşiğinin ALTINDA kalır (bkz. scorer.CONFIG
"min_veri_agirlik_yuzdesi") -- bu senaryo AYRICA "YETERSİZ VERİ" rozeti
yolunu da (kahraman katmanda büyük sayı yerine rozet metni) doğrular.

Kullanım: python scripts/demo_card_na.py
Çıktı   : data/cards/demo_NAKTAS.png
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from src.ai.commentary import Commentary
from src.analysis import calculator, scorer
from src.render import card

config.setup_logging()

_LATEST = (2026, 3)
_YOY_PRIOR = (2025, 3)


# Gercek Is Yatirim verisi mutlak TL cinsindendir (bkz. demo_card.py'deki
# ayni not) -- kucuk ornek rakamlar gercekci gorunsun diye bu olcekle carpilir.
_SCALE = Decimal("1000000")


def _donem_eksik(revenue, gross, op, net, cash, tr, assets, debt, equity, ca, stl) -> dict:
    # depreciation_amortization BİLEREK YOK -- FAVÖK hesaplanamaz (§B17
    # senaryosu, bkz. tests/test_card.py::_banka_finansallari ile AYNI ilke).
    return {
        "revenue": Decimal(revenue) * _SCALE, "revenue_cum": Decimal(revenue) * _SCALE,
        "gross_profit": Decimal(gross) * _SCALE, "gross_profit_cum": Decimal(gross) * _SCALE,
        "operating_profit": Decimal(op) * _SCALE, "operating_profit_cum": Decimal(op) * _SCALE,
        "net_income": Decimal(net) * _SCALE, "net_income_cum": Decimal(net) * _SCALE,
        "cash": Decimal(cash) * _SCALE, "trade_receivables": Decimal(tr) * _SCALE,
        "total_assets": Decimal(assets) * _SCALE, "financial_debt": Decimal(debt) * _SCALE, "equity": Decimal(equity) * _SCALE,
        "current_assets": Decimal(ca) * _SCALE, "short_term_liabilities": Decimal(stl) * _SCALE,
    }


def _ornek_finansallar() -> calculator.FinancialsByPeriod:
    return {
        _LATEST: _donem_eksik(300, 90, 40, 25, 60, 30, 900, 120, 400, 300, 220),
        _YOY_PRIOR: _donem_eksik(280, 82, 35, 20, 55, 28, 860, 130, 380, 280, 210),
    }


def _ornek_commentary() -> Commentary:
    return Commentary(
        headline="NAKTAS 2026/Ç1 DÖNEMİNDE SINIRLI VERİYLE RAPORLANDI",
        hook="Amortisman ve fiyat verisi eksik -- skor bileşenlerinin çoğu değerlendirilemedi.",
        summary=(
            "NAKTAS için amortisman ve pay fiyatı verisi bulunmadığından FAVÖK, Kaldıraç ve "
            "Değerleme bileşenleri hesaplanamadı. Mevcut sınırlı veriyle hasılat yıllık %7,1 arttı."
        ),
        positives=["Hasılat yıllık %7,1 artışla 300,0 mn ₺ seviyesine çıktı."],
        negatives=["Amortisman ve fiyat verisi eksik olduğu için bileşenlerin çoğu değerlendirilemedi."],
        kap_note=None,
        disclaimer_context=None,
        source="llm",
    )


def main() -> None:
    analiz = calculator.analyze("NAKTAS", _ornek_finansallar())
    skor = scorer.score_industrial(analiz)  # valuation VERİLMEDİ -- Değerleme bileşeni N/A
    yorum = _ornek_commentary()

    context = card.build_card_context(
        analiz, skor, yorum,
        company_name="Naktaş Sanayi A.Ş.",
        sector="Sanayi",
    )

    print(f"score_data_sufficient={context['score_data_sufficient']} badge={context['score_badge']}")

    out_path = config.DATA_DIR / "cards" / "demo_NAKTAS.png"
    result_path = card.render_card(context, str(out_path))

    print(f"PNG üretildi: {result_path}")


if __name__ == "__main__":
    main()

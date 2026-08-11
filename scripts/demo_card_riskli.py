"""Kart Tasarım Sistemi doğrulama döngüsü -- SENARYO C: RİSKLİ rozet/uyarı.

`demo_card.py` (bol veri) + `demo_card_na.py` (N/A) ile BİRLİKTE üçüncü
zorunlu senaryo (bkz. SKILL.md doğrulama döngüsü madde 2): daralan hasılat,
derinleşen zarar, yüksek kaldıraç, zayıf likidite -- toplam skor RİSKLİ
eşiğinin (scorer.CONFIG["rozet_esikleri"]["karisik"]=4) ALTINDA kalacak
şekilde kurgulandı. Kırmızı/negatif renklerin (tablo değişimi, rozet chip,
mini grafik) token sistemiyle dökülmeden nasıl göründüğünü doğrular.

Kullanım: python scripts/demo_card_riskli.py
Çıktı   : data/cards/demo_ZARARAS.png
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
_QOQ_PRIOR = (2025, 12)
_YOY_PRIOR = (2025, 3)
_TTM_3 = (2025, 9)
_TTM_4 = (2025, 6)


# Gercek Is Yatirim verisi mutlak TL cinsindendir (bkz. demo_card.py'deki
# ayni not) -- kucuk ornek rakamlar gercekci gorunsun diye bu olcekle carpilir.
_SCALE = Decimal("1000000")


def _donem(revenue, gross, op, dep, net, cash, tr, assets, debt, equity, ca, stl) -> dict:
    return {
        "revenue": Decimal(revenue) * _SCALE, "revenue_cum": Decimal(revenue) * _SCALE,
        "gross_profit": Decimal(gross) * _SCALE, "gross_profit_cum": Decimal(gross) * _SCALE,
        "operating_profit": Decimal(op) * _SCALE, "operating_profit_cum": Decimal(op) * _SCALE,
        "depreciation_amortization": Decimal(dep) * _SCALE, "depreciation_amortization_cum": Decimal(dep) * _SCALE,
        "net_income": Decimal(net) * _SCALE, "net_income_cum": Decimal(net) * _SCALE,
        "cash": Decimal(cash) * _SCALE, "trade_receivables": Decimal(tr) * _SCALE,
        "total_assets": Decimal(assets) * _SCALE, "financial_debt": Decimal(debt) * _SCALE, "equity": Decimal(equity) * _SCALE,
        "current_assets": Decimal(ca) * _SCALE, "short_term_liabilities": Decimal(stl) * _SCALE,
    }


def _ornek_finansallar() -> calculator.FinancialsByPeriod:
    """Daralan hasılat, derinleşen zarar, yüksek kaldıraç (net borç/FAVÖK
    çok yüksek), zayıf likidite (dönen varlık < kısa vadeli yükümlülük) --
    her bileşenin kötü tarafına düşmesi için kasıtlı olarak kurgulandı."""
    return {
        _LATEST: _donem(700, 60, -90, 15, -180, 40, 90, 3200, 2100, 350, 650, 950),
        _QOQ_PRIOR: _donem(760, 75, -60, 15, -130, 55, 100, 3300, 2050, 480, 700, 920),
        _YOY_PRIOR: _donem(900, 140, 20, 14, -40, 90, 130, 3400, 1900, 600, 800, 880),
        _TTM_3: _donem(820, 100, -20, 14, -80, 70, 110, 3350, 1980, 540, 750, 900),
        _TTM_4: _donem(870, 120, 5, 14, -20, 80, 120, 3380, 1930, 580, 780, 890),
    }


def _ornek_commentary() -> Commentary:
    return Commentary(
        headline="ZARARAS 2026/Ç1 DÖNEMİNDE ZARARINI DERİNLEŞTİRDİ",
        hook="Hasılat yıllık %22,2 daraldı, zarar derinleşti, kaldıraç kritik seviyede!",
        summary=(
            "ZARARAS, 2026/Ç1 döneminde net dönem zararını önceki yılın aynı dönemine göre "
            "derinleştirdi. Hasılat yıllık %22,2 daralırken, yüksek kaldıraç ve zayıf likidite "
            "şirketin bilanço sağlığını riske sokuyor. Şirket 1,8/10 toplam puanla RİSKLİ rozeti aldı."
        ),
        positives=[],
        negatives=[
            "Net dönem zararı yıllık bazda derinleşerek -180,0 mn ₺ seviyesine ulaştı.",
            "Hasılat yıllık %22,2 daralarak 700,0 mn ₺ seviyesine geriledi.",
            "Esas faaliyet zararı yıllık bazda kâra karşın zarara döndü.",
            "Net borç/FAVÖK oranı kritik seviyede yüksek, yüksek kaldıraç riski taşıyor.",
        ],
        kap_note=None,
        disclaimer_context=None,
        source="llm",
    )


def main() -> None:
    analiz = calculator.analyze("ZARARAS", _ornek_finansallar())
    fiyat = Decimal("4.80")
    sermaye = Decimal("120000000")
    degerleme = calculator.compute_valuation(analiz, fiyat, sermaye)
    skor = scorer.score_industrial(
        analiz,
        valuation=scorer.ValuationInput(pe_ratio=degerleme.pe_ratio, pb_ratio=degerleme.pb_ratio),
    )
    yorum = _ornek_commentary()

    context = card.build_card_context(
        analiz, skor, yorum,
        company_name="Zarar Sanayi A.Ş.",
        sector="Sanayi / İmalat",
        price=fiyat,
        valuation=degerleme,
    )

    print(f"score_total={context['score_total_display']} badge={context['score_badge']}")

    out_path = config.DATA_DIR / "cards" / "demo_ZARARAS.png"
    result_path = card.render_card(context, str(out_path))

    print(f"PNG üretildi: {result_path}")


if __name__ == "__main__":
    main()

"""Keşif/doğrulama scripti -- Faz 20.5 (2026-08-07 devamı).

`src/fetchers/ipo_price_report.py`'nin VEYAS (Türker Vangölü Enerji) Fiyat
Tespit Raporu'ndan çektiği rakamları, kullanıcının paylaştığı REFERANS
görseldeki gerçek VEYAS rakamlarıyla rakam rakam karşılaştırır (Kural 3).

Kullanım: python scripts/explore_ipo_price_report.py
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.fetchers import ipo_price_report as ipr  # noqa: E402

_VEYAS_TEXT_PATH = Path(__file__).resolve().parent.parent / "data" / "exploration" / "veyas_fiyat_tespit_raporu_full.txt"

# Kullanıcının paylaştığı VEYAS referans görselindeki "Operasyonel ve
# Finansal Veriler" bölümünün rakamları (bin TL cinsine çevrilmiş) --
# doğrulama kaynağı BUDUR (Kural 3: referans bir kaynakla rakam rakam
# karşılaştırma).
_REFERENCE = {
    "revenue_full_year": Decimal("26652218"),  # 2025 Hasılat: 26.652.218.000 TL
    "revenue_latest_interim": Decimal("5775822"),  # 2026/3A Ciro: 5.775.822.000 TL
    "gross_profit_latest_interim": Decimal("2469357"),  # 2026/3A Brüt Kâr: 2.469.357.000 TL
    "total_assets": Decimal("30121124"),  # Toplam varlıklar (31.03.2026): 30.121.124.000 TL
    "total_equity": Decimal("15590464"),  # Özkaynaklar (31.03.2026): 15.590.464.000 TL
}
_REFERENCE_REVENUE_GROWTH_PCT = Decimal("13.6")  # Ciro artışı: %13,6
_REFERENCE_GROSS_PROFIT_GROWTH_PCT = Decimal("113.5")  # Brüt kâr artışı: %113,5


def main() -> None:
    text = _VEYAS_TEXT_PATH.read_text(encoding="utf-8")
    result = ipr.extract_price_report_financials(text)

    print("Ayrıştırılan sonuç:", result)
    print()
    print("--- Referans görselle karşılaştırma (bin TL) ---")
    all_match = True
    for field, expected in _REFERENCE.items():
        actual = getattr(result, field)
        match = actual == expected
        all_match = all_match and match
        print(f"{field}: beklenen={expected} çekilen={actual} {'✅' if match else '❌'}")

    revenue_growth = None
    if result.revenue_latest_interim and result.revenue_prior_year_interim:
        revenue_growth = (result.revenue_latest_interim - result.revenue_prior_year_interim) / result.revenue_prior_year_interim * 100
    gross_profit_growth = None
    if result.gross_profit_latest_interim and result.gross_profit_prior_year_interim:
        gross_profit_growth = (
            (result.gross_profit_latest_interim - result.gross_profit_prior_year_interim) / result.gross_profit_prior_year_interim * 100
        )

    print(f"Ciro artışı: beklenen≈%{_REFERENCE_REVENUE_GROWTH_PCT} hesaplanan=%{revenue_growth:.1f}" if revenue_growth else "Ciro artışı: hesaplanamadı")
    print(
        f"Brüt kâr artışı: beklenen≈%{_REFERENCE_GROSS_PROFIT_GROWTH_PCT} hesaplanan=%{gross_profit_growth:.1f}"
        if gross_profit_growth
        else "Brüt kâr artışı: hesaplanamadı"
    )
    print()
    print("TÜM alanlar referansla eşleşti ✅" if all_match else "BAZI alanlar UYUŞMUYOR ❌ -- Kural 3 gereği kullanılmadan önce incelenmeli")


if __name__ == "__main__":
    main()

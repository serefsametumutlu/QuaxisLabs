"""HIZLI kalibrasyon sinyali -- `validate_fon_tahmini.py`'nin TAM taraması
(15 aday × discover + 35 gün) çok uzun sürdüğü için (arka planda zaman
aşımına uğradı, 2026-08-06) bu script `_discover_funds()` adımını
ATLAYIP DOĞRUDAN bilinen/zaten çalışan fonlarla (PHE/TLY/PBR/DFI/PUK/KHA)
ve daha KISA bir pencereyle (15 gün) `validate_fon_tahmini._validate_fund()`'i
çağırır -- amaç TAM/resmi bir MAE raporu değil, bir kalibrasyon (bias)
düzeltmesinin YÖNÜNÜ/işe yarayıp yaramayacağını HIZLICA görmek.

Kullanım: python scripts/quick_calibration_check.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402
from scripts import validate_fon_tahmini as vft  # noqa: E402

vft.TEST_WINDOW_DAYS = 15  # ~10 islem gunu -- hizli sinyal icin yeterli

_KNOWN_GOOD = [
    ("PHE", "Hisse Senedi Fonu"),
    ("TLY", "Serbest Fon"),
    ("PBR", "Değişken Fon"),
    ("KHA", "Hisse Senedi Fonu"),
]


def main() -> None:
    config.setup_logging()
    all_results = []
    for code, category in _KNOWN_GOOD:
        try:
            all_results.extend(vft._validate_fund(code, category))
        except Exception as exc:  # noqa: BLE001
            print(f"  {code}: beklenmeyen hata, atlanıyor: {exc}")

    vft._print_report(all_results)

    print("\n" + "=" * 70)
    print("KALİBRASYON SİNYALİ (fon başına ORTALAMA İMZALI hata = gerçekleşen - tahmin)")
    print("=" * 70)
    by_fund: dict[str, list] = {}
    for r in all_results:
        by_fund.setdefault(r.fund_code, []).append(r.realized_return_pct - r.estimated_return_pct)
    for code, signed_errors in by_fund.items():
        mean_signed = sum(signed_errors) / len(signed_errors)
        print(f"  {code:6s}: ortalama_imzali_hata={mean_signed:.4f} puan (n={len(signed_errors)}) -- "
              f"{'tahmin SİSTEMATİK DÜŞÜK çıkıyor (yukarı düzeltilmeli)' if mean_signed > 0 else 'tahmin SİSTEMATİK YÜKSEK çıkıyor (aşağı düzeltilmeli)'}")


if __name__ == "__main__":
    main()

"""Faz 16 teslim kriteri: DB'de zaten kayıtlı BIST şirketlerinin `sector`
alanını KAP'ın Sektörler sayfasından (bkz. src/fetchers/kap.py::fetch_sector_map(),
scripts/explore_kap_sektor.py) tek bir istekle günceller.

Bu script GÜNDE 1 KEZ bir zamanlayıcıyla (Windows Görev Zamanlayıcı / cron)
ya da elle çalıştırılmak üzere tasarlandı -- `refresh_takvim_cache.py` ile
AYNI ilke: Derin Kart'ın "sektör ortalaması" çizgisi ana Bilanço Analizi
pipeline'ını BLOKE ETMEZ (Kural 9), bu yüzden botun kendisi bunu TETİKLEMEZ.

Sektör bilgisi SADECE DB'de ZATEN kayıtlı (daha önce en az bir kez analiz
edilmiş) BIST şirketleri için güncellenir -- yeni bir Company satırı
OLUŞTURULMAZ (henüz hiç sorgulanmamış bir şirketin sektörünü şimdiden
bilmenin bir anlamı yok, o şirket analiz edildiğinde bir sonraki
`refresh_sector_cache.py` koşumunda zaten güncellenecektir).

Kullanım:
    python scripts/refresh_sector_cache.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402
from src.db import repository  # noqa: E402
from src.fetchers import kap  # noqa: E402

config.setup_logging()


def main() -> int:
    print(f"{kap.SEKTORLER_URL} çekiliyor (TÜM BIST şirketleri, tek istek)...")
    sector_map = kap.fetch_sector_map()
    print(f"{len(sector_map)} benzersiz ticker için sektör bulundu.")

    with repository.get_session() as session:
        updated = repository.update_company_sectors(session, sector_map)
    print(f"\nDB'de {updated} şirketin sektör bilgisi güncellendi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

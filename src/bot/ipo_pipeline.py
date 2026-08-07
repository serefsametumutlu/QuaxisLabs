"""Halka arz izahname kartı için orkestrasyon katmanı -- Faz 20 devamı
(2026-08-06). `src.bot.fund_pipeline`/`src.bot.pipeline` ile AYNI ilke: bu
modül SADECE fetcher'ı (`src.fetchers.kap_ipo`) ve saf hesaplayıcıyı
(`src.analysis.ipo_assessment`) birbirine bağlar -- kendi başına HİÇBİR
sayı hesaplamaz, hiçbir Türkçe biçimlendirme yapmaz (bu render katmanının işi).

Kalıcı bir DB önbelleği (fund_pipeline'daki `Fund`/`FundHolding` tablolarının
izahname karşılığı) BİLİNÇLİ olarak bu turda EKLENMEDİ -- halka arzlar (fon
portföyünün aksine) AYDA BİR değil, HAFTADA birkaç kez yeni onaylanan, kısa
ömürlü (talep toplama bitince "eski" sayılan) olaylar; `find_recent_izahnameler()`
her çağrıldığında ~22 aracı kurumu TARAR (CANLI ölçüldü: ~45-60 saniye,
`scripts/demo_halka_arz.py --liste` ile -- tek ticker aramasında ayrıca PDF
indirme/ayrıştırma da eklenir, KARCL ile uçtan uca CANLI ölçüm ~2 dakika;
`fon grup` akışının "~1-2 dakika" kabul edilen gecikmesiyle AYNI mertebede) --
bkz. B26'daki "organik büyüme, ek maliyet/risk yok" kararıyla AYNI pragmatik
tercih. Kalıcı önbellek istenirse `fund_pipeline._cached_or_fresh_portfolio()`
ile AYNI desende bir sonraki fazda eklenebilir.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from src.analysis import ipo_assessment
from src.fetchers import ipo_broker_page, ipo_price_report, kap_ipo

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IpoCardResult:
    """`compute_ipo_card_data()`'nın döndüğü, kart/bot katmanının ihtiyaç
    duyduğu her şeyi taşıyan tek paket. `disclosure`/`facts`/`assessment`
    None ise `reason` KULLANICIYA gösterilecek Türkçe bir açıklama içerir
    (Kural 3/9: hata fırlatılmaz, sebep her zaman anlaşılır bir metindir).

    `supplementary` (2026-08-07, YENİ) -- halkarz.com'dan (İKİNCİL kaynak,
    bkz. `ipo_broker_page.py` modül üst notu) best-effort okunan talep
    toplama tarihi/Katılım Endeksi gibi alanlar. `assessment` dolu olsa
    BİLE bu None olabilir (Kural 9 -- ikincil veri, hata/bulunamama ANA
    kartı ETKİLEMEZ)."""

    ticker: str
    disclosure: kap_ipo.IzahnameDisclosure | None
    facts: kap_ipo.IpoFacts | None
    assessment: ipo_assessment.IpoAssessment | None
    reason: str | None
    supplementary: ipo_broker_page.SupplementaryIpoInfo | None = None
    # (Faz 20.5, 2026-08-07 devamı) Fiyat Tespit Raporu'ndan (İKİNCİL/YARDIMCI
    # kaynak, bkz. ipo_price_report.py) Hasılat/Brüt Kâr/Toplam Varlık/
    # Özkaynak -- `assessment` dolu olsa BİLE bu None olabilir (Kural 9,
    # `supplementary` ile AYNI ilke).
    price_report: ipo_price_report.PriceReportFinancials | None = None


def list_available_ipos(days: int = kap_ipo._DEFAULT_DISCOVERY_DAYS) -> list[kap_ipo.IzahnameDisclosure]:
    """SPK onaylı, henüz işleme başlamamış TÜM izahnameleri (en yeni önce)
    döner -- `kap_ipo.find_recent_izahnameler()`'in doğrudan bir geçişi
    (ince sarmalayıcı, mantık KOPYALANMADI).

    ⚠️ (2026-08-07 düzeltmesi) Varsayılan artık `kap_ipo._DEFAULT_DISCOVERY_DAYS`
    (7) -- eski varsayılan (60) `kap.fetch_all_disclosures()`'ın güvenli
    sınırını (`_MAX_SAFE_ALL_DISCLOSURES_DAYS=10`) AŞIYORDU, ValueError
    fırlatıp demo/CLI kullanımını çökertiyordu (bu turda canlı yakalandı)."""
    return kap_ipo.find_recent_izahnameler(days=days)


def compute_ipo_card_data(ticker: str, days: int = kap_ipo._DEFAULT_DISCOVERY_DAYS) -> IpoCardResult:
    """Bir hedef ticker için uçtan uca izahname analizini üretir:
    `find_izahname_for_ticker()` → `fetch_and_parse_izahname()` →
    `ipo_assessment.compute_ipo_assessment()`.

    Her adımda başarısızlık `reason` ile AÇIKÇA raporlanır -- hiçbir zaman
    istisna fırlatmaz, çağıran taraf (bot) SADECE `result.assessment is
    None` kontrolü yapıp `result.reason`'ı gösterebilir.

    ⚠️ `find_izahname_for_ticker()` -> `find_recent_izahnameler()` artık
    `kap.fetch_all_disclosures()` ile TEK istekte TÜM KAP'ı tarar (~1-2
    saniye, ESKİ ~22-aracı-kurum sıralı taramasının (~45-60 sn) YERİNİ
    aldı, bkz. kap_ipo.py modül üst notu) -- ama bu uç nokta `days`'i
    `_MAX_SAFE_ALL_DISCLOSURES_DAYS` (10) ile SINIRLAR (ValueError
    fırlatır, aşan bir `days` KASITLI olarak geçirilmemeli). Çağıran taraf
    (bot) `disclosure`'ı ZATEN biliyorsa (örn. `list_available_ipos()`
    sonucundan bir buton tıklaması) taramayı TAMAMEN atlamak için
    `compute_ipo_card_data_from_disclosure()`'ı DOĞRUDAN kullanmalı."""
    ticker = ticker.strip().upper()

    try:
        disclosure = kap_ipo.find_izahname_for_ticker(ticker, days=days)
    except Exception:  # noqa: BLE001 -- Kural 9: KAP taraması genel bir hatayla patlarsa kullanıcıya sessizce "bulunamadı" DEĞİL, anlaşılır bir mesaj gitmeli
        logger.warning("%s için izahname taraması başarısız oldu", ticker, exc_info=True)
        return IpoCardResult(ticker, None, None, None, "KAP'a şu an ulaşılamıyor, birkaç dakika sonra tekrar dene.")

    if disclosure is None:
        return IpoCardResult(
            ticker,
            None,
            None,
            None,
            f"'{ticker}' için son {days} günde SPK onaylı, işleme başlamamış bir izahname bulunamadı.",
        )

    return compute_ipo_card_data_from_disclosure(disclosure)


def compute_ipo_card_data_from_disclosure(disclosure: kap_ipo.IzahnameDisclosure) -> IpoCardResult:
    """`compute_ipo_card_data()`'nın devamı -- `disclosure` ZATEN biliniyorsa
    (bkz. yukarıdaki uyarı) 22 aracı kurum taramasını ATLAYIP doğrudan
    PDF indirme/ayrıştırma adımından başlar."""
    ticker = disclosure.target_tickers[0] if disclosure.target_tickers else "-"

    facts = kap_ipo.fetch_and_parse_izahname(disclosure)
    if facts is None:
        return IpoCardResult(
            ticker,
            disclosure,
            None,
            None,
            "İzahname bulundu ama PDF'i indirilip ayrıştırılamadı -- birkaç dakika sonra tekrar dene.",
        )

    # İkincil zenginleştirme (Kural 9): Fiyat Tespit Raporu'ndan Hasılat/Brüt
    # Kâr/Toplam Varlık/Özkaynak best-effort okunur -- `fetch_and_parse_price_report`
    # HERHANGİ bir hatada zaten sessizce None döner (bkz. ipo_price_report.py),
    # bu yüzden ekstra try/except GEREKMEZ. `assessment`'a geçirilir ki YoY
    # büyüme oranları da hesaplansın.
    price_report = ipo_price_report.fetch_and_parse_price_report(disclosure)
    assessment = ipo_assessment.compute_ipo_assessment(facts, price_report=price_report)
    # İkincil zenginleştirme (Kural 9): halkarz.com'dan talep toplama tarihi/
    # Katılım Endeksi gibi KAP izahnamesinde bulunmayan alanlar best-effort
    # okunur -- `fetch_supplementary_ipo_info` HERHANGİ bir hatada zaten
    # sessizce None döner, bu yüzden ekstra try/except GEREKMEZ.
    supplementary = ipo_broker_page.fetch_supplementary_ipo_info(ticker)
    return IpoCardResult(ticker, disclosure, facts, assessment, None, supplementary, price_report)

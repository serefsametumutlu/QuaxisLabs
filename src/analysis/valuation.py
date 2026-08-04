"""Sektöre göre "ucuz mu pahalı mı" değerleme değerlendirmesi + kısa vadeli
fiyat momentumu + ima edilen (kendi hesapladığımız) hedef fiyat -- SAF
matematik, `src.analysis.trends`/`calculator` ile AYNI ilke: bu modül
HİÇBİR I/O yapmaz, `src.fetchers`/`src.db` HİÇBİR modülü import ETMEZ
(01_MIMARI.md katman kuralı).

Kullanıcı isteği (2026-08-04): "bir hissenin bilançosu çok iyi gelmiştir ama
son 1 ayda zaten %50 yükselmiştir ve pahalı denecek noktaya gelmiştir" --
mevcut `scorer._skor_degerleme()` SADECE mutlak F/K, PD/DD eşiklerine bakar
(BIST/ABD piyasasına göre kalibre edilmiş sabit bantlar), şirketin KENDİ
sektörüne göre ya da SON DÖNEMDEKİ fiyat hareketine hiç bakmaz. Bu modül o
boşluğu SKORU DEĞİŞTİRMEDEN (bilinçli tasarım kararı: "şirket iyi mi" ile
"şu an almak mantıklı mı" ayrı sorulardır) YENİ, ayrı bir "Değerleme
Analizi" paneli olarak doldurur.

Neden bir ANALİST HEDEF FİYATI (dış kaynak) DEĞİL, kendi hesapladığımız bir
"ima edilen değer": TradingView/Yahoo Finance gibi kaynakların analist
hedef fiyatı uç noktaları ya resmi/belgeli değil (yarın kırılabilir) ya da
Cloudflare korumalı, BİST için ise böyle bir ücretsiz kaynak neredeyse hiç
yok (bkz. PROJE_HAFIZASI/06_BILINEN_SORUNLAR.md). Kural 3 ("emin olmadığın
veri kalemini varsayımla eşleme") gereği YENİ/doğrulanmamış bir dış kaynağa
bağımlı olmak yerine, ZATEN doğrulanmış kendi verimizden (F/K, PD/DD, aynı
sektördeki DİĞER taranmış şirketlerin ortalama çarpanı) türetilen, AÇIKÇA
"gerçek bir analist tahmini DEĞİL, sektör ortalama çarpanına göre ima edilen
değer" diye etiketlenen bir sayı tercih edildi.

Sektör ortalaması (2. kez, BURADA): `trends.compute_sector_average()`
SADECE marj/oran (TTM bazlı) alanları ortalar, F/K/PD/DD İSE fiyata
bağlıdır (o modül fiyat/I-O bilmez) -- bu yüzden peer'lerin GÜNCEL F/K/PD-DD
çarpanları AYRI, burada (basit ortalama, `trends.compute_sector_average()`
ile AYNI ilke: SADECE gerçek/None-olmayan değerler ortalamaya katılır)
hesaplanır. Girdi (`PeerMultiple` listesi) çağıran tarafın (telegram_bot.py)
her peer için `calculator.compute_valuation()`'ı ÇAĞIRARAK ürettiği HAZIR
F/K/PD-DD değerleridir -- burada YENİDEN hesaplanmaz (Kural: hesaplama
mantığı KOPYALANMAZ).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

# Peer ortalamasına göre +-%20 icinde "makul" sayilir -- scorer._skor_degerleme()'nin
# mutlak F/K/PD-DD bantlarindan BAGIMSIZ, GORECELI (sektore gore) bir esik.
# Sabit bir "dogru" deger yok; %20 --  yatirim literaturunde "peer comp"
# karsilastirmalarinda siklikla kullanilan kaba bir tolerans araligidir.
_CHEAP_THRESHOLD_PCT = Decimal(-20)
_EXPENSIVE_THRESHOLD_PCT = Decimal(20)

# 1 ayda +%25'i asan bir yukselis "kisa vadede isinmis olabilir" notu
# tetikler -- kullanicinin verdigi ornek (%50/1 ay) bunun ACIKCA USTUNDE,
# ama daha erken bir uyari esigi (yarısı) secildi ki sinirda kalan durumlar
# da (orn. %30) sessizce gecilmesin.
_MOMENTUM_FLAG_THRESHOLD_PCT = Decimal(25)


@dataclass(frozen=True)
class PeerMultiple:
    """Bir sektor peer'inin GUNCEL (fiyata bagli) degerleme carpanlari --
    caniran taraf `calculator.compute_valuation()`'in GERCEK, dogrulanmis
    ciktisindan doldurur (bkz. modul ust notu)."""

    ticker: str
    pe_ratio: Decimal | None
    pb_ratio: Decimal | None


@dataclass(frozen=True)
class ValuationAssessment:
    has_data: bool
    peer_count: int

    own_pe: Decimal | None
    own_pb: Decimal | None
    sector_avg_pe: Decimal | None
    sector_avg_pb: Decimal | None
    pe_diff_pct: Decimal | None  # own - sektor, + ise own DAHA PAHALI
    pb_diff_pct: Decimal | None
    verdict: str | None  # "Sektöre Göre Ucuz" | "Sektöre Göre Makul" | "Sektöre Göre Pahalı"
    verdict_reasoning: str | None

    price_change_1m_pct: Decimal | None
    price_change_3m_pct: Decimal | None
    momentum_note: str | None  # SADECE esigi asan hizli bir yukselis varsa dolu (K2: olgu, tavsiye degil)

    implied_target_price: Decimal | None
    implied_target_basis: str | None  # "F/K" | "PD/DD"
    implied_upside_pct: Decimal | None


def _pct_change(new: Decimal, old: Decimal) -> Decimal | None:
    if old == 0:
        return None
    return (new - old) / old * 100


def _average(values: list[Decimal]) -> Decimal | None:
    return (sum(values) / len(values)) if values else None


def compute_valuation_assessment(
    own_pe: Decimal | None,
    own_pb: Decimal | None,
    peer_multiples: list[PeerMultiple],
    current_price: Decimal | None,
    price_30d_ago: Decimal | None,
    price_90d_ago: Decimal | None,
) -> ValuationAssessment:
    """`own_pe`/`own_pb`: taranan hissenin GUNCEL F/K, PD/DD'si (`calculator.
    compute_valuation()` ciktisi). `peer_multiples`: AYNI sektor + AYNI
    financial_group'taki DIGER (zaten taranmis) sirketlerin GUNCEL carpanlari.
    `current_price`/`price_30d_ago`/`price_90d_ago`: fiyat gecmisinden (bkz.
    src.fetchers.price_history) cagiran tarafin sectigi kapanislar -- BURADA
    SADECE yuzde degisim/oranlar hesaplanir, veri CEKILMEZ.

    Peer'ler bos VEYA hicbirinde gecerli (pozitif) F/K, PD/DD yoksa
    sektor-goreli kisim `None` kalir (K4: yeterli veri yoksa uydurma
    yapilmaz); momentum kismi bundan BAGIMSIZ calisir (fiyat gecmisi varsa
    sektor peer'i olmasa da hesaplanir)."""
    valid_pe = [p.pe_ratio for p in peer_multiples if p.pe_ratio is not None and p.pe_ratio > 0]
    valid_pb = [p.pb_ratio for p in peer_multiples if p.pb_ratio is not None and p.pb_ratio > 0]
    sector_avg_pe = _average(valid_pe)
    sector_avg_pb = _average(valid_pb)

    pe_diff_pct: Decimal | None = None
    if own_pe is not None and own_pe > 0 and sector_avg_pe is not None:
        pe_diff_pct = _pct_change(own_pe, sector_avg_pe)

    pb_diff_pct: Decimal | None = None
    if own_pb is not None and own_pb > 0 and sector_avg_pb is not None:
        pb_diff_pct = _pct_change(own_pb, sector_avg_pb)

    diffs = [d for d in (pe_diff_pct, pb_diff_pct) if d is not None]
    verdict: str | None = None
    verdict_reasoning: str | None = None
    if diffs:
        blended = sum(diffs) / len(diffs)
        parts = []
        if pe_diff_pct is not None:
            parts.append(f"F/K sektör ortalamasından %{pe_diff_pct:.1f} {'yüksek' if pe_diff_pct >= 0 else 'düşük'}")
        if pb_diff_pct is not None:
            parts.append(f"PD/DD sektör ortalamasından %{pb_diff_pct:.1f} {'yüksek' if pb_diff_pct >= 0 else 'düşük'}")
        if blended <= _CHEAP_THRESHOLD_PCT:
            verdict = "Sektöre Göre Ucuz"
        elif blended >= _EXPENSIVE_THRESHOLD_PCT:
            verdict = "Sektöre Göre Pahalı"
        else:
            verdict = "Sektöre Göre Makul"
        verdict_reasoning = ", ".join(parts) + "."

    # Ima edilen hedef fiyat: mevcut fiyati "sektor ortalamasi carpani"na
    # YENIDEN OLCEKLER -- current_price = own_pe * eps_ttm oldugu icin
    # current_price * (sector_avg_pe / own_pe) matematiksel olarak
    # eps_ttm * sector_avg_pe ile AYNIDIR, ayri bir EPS hesabi GEREKMEZ.
    implied_target_price: Decimal | None = None
    implied_target_basis: str | None = None
    if current_price is not None and own_pe is not None and own_pe > 0 and sector_avg_pe is not None:
        implied_target_price = current_price * (sector_avg_pe / own_pe)
        implied_target_basis = "F/K"
    elif current_price is not None and own_pb is not None and own_pb > 0 and sector_avg_pb is not None:
        implied_target_price = current_price * (sector_avg_pb / own_pb)
        implied_target_basis = "PD/DD"

    implied_upside_pct: Decimal | None = None
    if implied_target_price is not None and current_price is not None and current_price > 0:
        implied_upside_pct = _pct_change(implied_target_price, current_price)

    price_change_1m_pct: Decimal | None = None
    price_change_3m_pct: Decimal | None = None
    momentum_note: str | None = None
    if current_price is not None and price_30d_ago is not None:
        price_change_1m_pct = _pct_change(current_price, price_30d_ago)
    if current_price is not None and price_90d_ago is not None:
        price_change_3m_pct = _pct_change(current_price, price_90d_ago)
    if price_change_1m_pct is not None and price_change_1m_pct >= _MOMENTUM_FLAG_THRESHOLD_PCT:
        momentum_note = (
            f"Son 1 ayda %{price_change_1m_pct:.1f} yükseldi -- kısa vadede aşırı ısınmış olabilir, "
            "güncel çarpanlar bu artışı henüz tam yansıtmıyor olabilir."
        )

    has_data = bool(diffs) or price_change_1m_pct is not None or price_change_3m_pct is not None

    return ValuationAssessment(
        has_data=has_data,
        peer_count=len(peer_multiples),
        own_pe=own_pe,
        own_pb=own_pb,
        sector_avg_pe=sector_avg_pe,
        sector_avg_pb=sector_avg_pb,
        pe_diff_pct=pe_diff_pct,
        pb_diff_pct=pb_diff_pct,
        verdict=verdict,
        verdict_reasoning=verdict_reasoning,
        price_change_1m_pct=price_change_1m_pct,
        price_change_3m_pct=price_change_3m_pct,
        momentum_note=momentum_note,
        implied_target_price=implied_target_price,
        implied_target_basis=implied_target_basis,
        implied_upside_pct=implied_upside_pct,
    )

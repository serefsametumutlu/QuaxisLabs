"""SPEC: `docs/spec/spec_bilesik_skor.md` -- Bileşik Skor (v2 çok-mercekli
skorlama, 4 merceğin BİRLEŞİMİ) -- SAF MATEMATİK, `src.fetchers`/`src.db`
HİÇBİR modülü import ETMEZ (quaxis-mimari anayasa madde 1).

Bu modül YENİ bir "tek doğru sayı" ÜRETMEZ -- dört merceğin (Değer/Kalite/
Büyüme/Güvenlik) SONUÇLARINI şeffaf, ağırlıklı bir ortalamayla TEK bir
Bileşik Skor'a indirger + kartta MERCEKLERİ AYRI AYRI göstermeyi mümkün
kılan bir veri yapısı üretir (`temel-analiz-cercevesi` skill'in temel
tezi: "kitaplar çelişir, çelişki ÇÖZÜLMEZ, ayrı mercek olur; bileşik skor
merceklerin şeffaf ağırlıklı ortalamasıdır").

Bu, İNCE bir orkestrasyon katmanıdır -- kendi hesaplama mantığı TAŞIMAZ,
4 mercek modülünün (lens_deger/lens_kalite/lens_buyume/lens_guvenlik)
ÜRETTİĞİ `LensSonucu` (=`ScoreResult`) nesnelerini SADECE BİRLEŞTİRİR
(spec §Uygulama notu madde 1).

4 Mercek ağırlıkları (spec §Eşikler ve ağırlıklar, `sanayi`/`abd_sanayi`
varsayılan, toplam %100):
    Değer      %30
    Kalite     %30
    Güvenlik   %25
    Büyüme     %15

GEÇİŞ (persona kural 8, spec §Amaç "Geriye uyumluluk"): v1'in
`scorer.score_industrial()` (vb.) ÜRETTİĞİ `ScoreResult` (tek skor, tek
rozet) BAĞIMSIZ bir fonksiyon olarak ÇALIŞMAYA DEVAM EDER, DEĞİŞTİRİLMEZ.
Bu modül AYRI, YENİ bir giriş noktasıdır -- pipeline.py bir BAYRAKLA
(`use_multi_lens_scoring`) hangisinin (veya İKİSİNİN BİRLİKTE) kullanılacağına
karar verir.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from src.analysis.lens_common import LensSonucu, YETERSIZ_VERI_ROZETI, _badge, _clamp

# spec §Eşikler ve ağırlıklar -- 4 Mercek Ağırlıkları tablosu.
MERCEK_AGIRLIKLARI: dict[str, Decimal] = {
    "değer": Decimal("30"),
    "kalite": Decimal("30"),
    "güvenlik": Decimal("25"),
    "büyüme": Decimal("15"),
}


@dataclass(frozen=True)
class MercekProfili:
    """Kart sunumu için (persona/skill zorunluluğu, spec §Eşikler: "Değer:
    8,2 · Kalite: 4,1 · Büyüme: 6,0 · Güvenlik: 7,5 -> Bileşik: 6,4 DENGELİ"
    formatı) -- TEK bir sayı DEĞİL, 4 mercek + bileşik BİRLİKTE gösterilir."""

    deger: LensSonucu | None
    kalite: LensSonucu | None
    buyume: LensSonucu | None
    guvenlik: LensSonucu | None


@dataclass(frozen=True)
class BilesikSkorSonucu:
    ticker: str
    period: tuple[int, int]
    mercekler: MercekProfili
    total_score: Decimal
    badge: str
    data_sufficient: bool
    # HANGİ mercek(ler)in bileşik skora KATILDIĞI (ağırlığı>0) -- şeffaflık
    # (spec: "Bileşik Skor bu iki merceğin EKSİKLİĞİNİ gizli bir varsayımla
    # TAMAMLAMAZ") için AÇIKÇA taşınır.
    dahil_edilen_mercekler: list[str]


def hesapla_bilesik_skor(
    ticker: str,
    period: tuple[int, int],
    deger: LensSonucu | None,
    kalite: LensSonucu | None,
    buyume: LensSonucu | None,
    guvenlik: LensSonucu | None,
) -> BilesikSkorSonucu:
    """4 merceğin ağırlıklı ortalamasını alır -- mercek SEVİYESİNDEKİ
    `data_sufficient=False` (v1'in `min_veri_agirlik_yuzdesi=%50` ilkesinin
    mercek seviyesine taşınmış hali, spec §Formüller-2) durumunda o mercek
    TAMAMEN dışlanır, ağırlığı KALAN merceklere ORANTISAL yeniden dağıtılır
    (mevcut `_agirlik_dagit_ve_hesapla` ilkesiyle AYNI matematik, 4-mercek
    seviyesine taşınmış hali).

    GUARD (quant_denetim_01.md Y4): Σ(mercek_agirlik_i)=0 ise (TÜM
    mercekler veri-yetersiz VEYA hiç hesaplanmadı) sıfıra bölme OLUŞMAZ --
    "YETERSİZ VERİ" dalına düşülür (mevcut `YETERSIZ_VERI_ROZETI` ile AYNI
    ilke)."""
    mercekler = {"değer": deger, "kalite": kalite, "güvenlik": guvenlik, "büyüme": buyume}
    profil = MercekProfili(deger=deger, kalite=kalite, buyume=buyume, guvenlik=guvenlik)

    dahil_edilen = [
        isim for isim, sonuc in mercekler.items() if sonuc is not None and sonuc.data_sufficient
    ]
    toplam_agirlik = sum(MERCEK_AGIRLIKLARI[isim] for isim in dahil_edilen)

    if toplam_agirlik == 0:
        return BilesikSkorSonucu(
            ticker=ticker, period=period, mercekler=profil, total_score=Decimal(0),
            badge=YETERSIZ_VERI_ROZETI, data_sufficient=False, dahil_edilen_mercekler=[],
        )

    toplam_katki = Decimal(0)
    for isim in dahil_edilen:
        sonuc = mercekler[isim]
        efektif_agirlik = MERCEK_AGIRLIKLARI[isim] / toplam_agirlik * 100
        toplam_katki += sonuc.total_score * efektif_agirlik / 100

    toplam_katki = _clamp(toplam_katki, Decimal(0), Decimal(10))
    return BilesikSkorSonucu(
        ticker=ticker, period=period, mercekler=profil, total_score=toplam_katki,
        badge=_badge(toplam_katki), data_sufficient=True, dahil_edilen_mercekler=dahil_edilen,
    )


def hesapla_veri_kapsam_ozeti(bilesik: BilesikSkorSonucu) -> Decimal | None:
    """docs/spec/spec_dashboard.md §Formüller-0: Σ(lens_i.data_coverage_pct *
    MERCEK_AGIRLIKLARI[i]) / Σ(MERCEK_AGIRLIKLARI[i]) -- SADECE kavramsal
    olarak VAR OLAN (None OLMAYAN) mercekler üzerinden, NOMİNAL ağırlıklarla
    (data_sufficient eşiğiyle YENİDEN dağıtılmış EFEKTİF ağırlıklarla
    DEĞİL -- bu, bilesik_skor'un kendi hesaplamasından KASITLI olarak
    FARKLI bir soru sorar: "genel olarak ne kadar veriye dayanıyoruz",
    "skora kaç mercek katıldı" DEĞİL).

    Tüm mercekler None ise (kavramsal olarak hiç uygulanamıyor -- ÇOK
    NADİR) None döner (dashboard '-' gösterir)."""
    mercekler = {
        "değer": bilesik.mercekler.deger, "kalite": bilesik.mercekler.kalite,
        "güvenlik": bilesik.mercekler.guvenlik, "büyüme": bilesik.mercekler.buyume,
    }
    mevcut = {isim: s for isim, s in mercekler.items() if s is not None}
    if not mevcut:
        return None
    toplam_agirlik = sum(MERCEK_AGIRLIKLARI[isim] for isim in mevcut)
    toplam_katki = sum(s.data_coverage_pct * MERCEK_AGIRLIKLARI[isim] for isim, s in mevcut.items())
    return _clamp(toplam_katki / toplam_agirlik, Decimal(0), Decimal(100))

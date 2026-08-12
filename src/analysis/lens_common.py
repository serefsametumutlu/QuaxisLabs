"""v2 çok-mercekli skorlama (Değer/Kalite/Büyüme/Güvenlik) için ORTAK
altyapı -- SAF MATEMATİK, `src.fetchers`/`src.db` HİÇBİR modülü import
ETMEZ (quaxis-mimari anayasa madde 1).

Bu modül `src.analysis.scorer`'ın (v1, DEĞİŞTİRİLMEDİ) çekirdek yardımcı
fonksiyonlarını (`_lerp_score`, `_asymptote_to`, `_clamp`, `_num_str`,
`_agirlik_dagit_ve_hesapla`, `ComponentScore`, `ScoreResult`) TEKRAR
YAZMAK yerine İTHAL EDER (`spec_bilesik_skor.md` "Uygulama notu" madde 3:
"kod tekrarını önleme" -- 4 mercek modülünün hiçbiri kendi lokal kopyasını
yazmamalı).

KOD-GELİŞTİRİCİ DEVİR NOTU UYGULAMASI (quant_denetim_01.md K1): mevcut
`scorer._seviye_trend_skoru`'nun "bozuluyor" dalı trend işareti sıfırı
geçtiği an ~5+ puanlık sert bir skor uçurumu (cliff) üretiyor VE bant
sınırlarında ([0,4]-[5,7]-[8,10]) ek süreksizlik taşıyor -- bu fonksiyon
v1'in ÜRETTİĞİ `ScoreResult`leri (mevcut 1211+ test) DEĞİŞTİRMEMESİ
ZORUNLU olduğu için (persona kural 8, "v1 davranışı ASLA değişmeyecek")
`scorer._seviye_trend_skoru`'nun KENDİSİ DOKUNULMADAN bırakıldı. Bunun
YERİNE burada YENİ, sürekli (K1-düzeltmeli) bir kardeş fonksiyon
(`seviye_trend_skoru_v2`) tanımlanır -- 4 mercek modülünün TÜMÜ SADECE
BUNU kullanır (spec'in "TEK yerde düzeltilmeli" ilkesi burada v2'ye özgü
TEK bir yerde karşılanır, v1 dokunulmadan kalır -- "genişleyerek taşı,
çöpe atma" kural 8'in doğal bir uzantısı).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from src.analysis.scorer import (  # noqa: F401 -- kasıtlı olarak yeniden dışa açılıyor (lens_*.py bunları buradan alır)
    ComponentScore,
    ScoreResult,
    YETERSIZ_VERI_ROZETI,
    _agirlik_dagit_ve_hesapla,
    _asymptote_to,
    _badge,
    _clamp,
    _lerp_score,
    _num_str,
    _safe_pct,
)
from src.formatting import format_percent_tr

# v2 mercek çıktıları, v1'in `ScoreResult`/`ComponentScore` dataclass'larını
# BİREBİR yeniden kullanır (mercek "kendi içinde 0-10'a normalize edilmiş,
# veri_yeterliligi + rozet üreten" bir birim -- tam olarak ScoreResult'ın
# zaten yaptığı şey, bkz. spec_bilesik_skor.md §Uygulama notu madde 1).
LensSonucu = ScoreResult
LensBileseni = ComponentScore

# sektor-siniflandirma skill madde 1 + spec_mercek_deger.md §Sektör
# ayarlaması madde 1: n<5 -> sektöre-göreli bileşen ATLANIR (n≥3'ten
# YÜKSELTİLDİ, quant_denetim_01.md bulgusu).
MIN_SECTOR_N = 5


@dataclass(frozen=True)
class SektorIstatistigi:
    """Bir `(ust_sektor, sirket_turu)` grubu içindeki bir metriğin robust
    (medyan + MAD) dağılımı -- repository katmanı tarafından DÖNEM BAZLI
    önceden hesaplanır/önbelleklenir (bkz. `src/db/repository.py`
    `get_sector_metric_distribution`), analiz katmanına HAZIR parametre
    olarak gelir (quaxis-mimari: "Sektör istatistikleri parametre olarak
    gelir")."""

    n: int
    medyan: Decimal
    mad: Decimal  # Medyan Mutlak Sapma (winsorize edilmiş örneklemden)


def _medyan(sirali_degerler: list[Decimal]) -> Decimal:
    n = len(sirali_degerler)
    orta = n // 2
    if n % 2 == 1:
        return sirali_degerler[orta]
    return (sirali_degerler[orta - 1] + sirali_degerler[orta]) / 2


def robust_istatistik(degerler: list[Decimal], winsor_pct: Decimal = Decimal(5)) -> tuple[Decimal, Decimal, int] | None:
    """Medyan + MAD (Medyan Mutlak Sapma), %winsor_pct/%(100-winsor_pct)
    uçları kırpılmış (winsorize) -- Damodaran'ın pozitif çarpıklık uyarısına
    (03/BAYRAK-20: ortalama HER ZAMAN medyandan yüksek çıkar) karşı
    ORTALAMA YERİNE kullanılır (quant_denetim_01.md Y2 düzeltmesi: eski
    taslak MAD'ı hesaplayıp SKORLAMADA hiç kullanmıyordu).

    KÜÇÜK ÖRNEKLEM SINIRI (quant_denetim_01.md Y3, kalibrasyonla
    doğrulandı): gerçek DB dağılımında n<10 olan gruplar (BİST sigorta n=4,
    BİST bankalar n=8 gibi) ÇOĞUNLUKTA -- bu gruplarda %5-%95 winsorizasyonu
    PRATİKTE en fazla 0-1 gözlemi etkiler, FİİLEN ETKİSİZDİR. Bu bir hata
    değil, bilinen bir SINIRDIR (burada AÇIKÇA belgelenir).

    `degerler` boşsa None döner. n>=MIN_SECTOR_N kontrolü BURADA YAPILMAZ
    (çağıran taraf sorumludur) -- bu fonksiyon SADECE istatistiği hesaplar.
    """
    if not degerler:
        return None
    sirali = sorted(degerler)
    n = len(sirali)
    if winsor_pct > 0 and n >= 3:
        alt_idx = min(int((winsor_pct / 100) * n), n - 1)
        ust_idx = max(n - alt_idx, alt_idx + 1)
        kirpilmis = sirali[alt_idx:ust_idx]
    else:
        kirpilmis = sirali
    if not kirpilmis:
        kirpilmis = sirali
    medyan = _medyan(kirpilmis)
    sapmalar = sorted(abs(v - medyan) for v in kirpilmis)
    mad = _medyan(sapmalar)
    return medyan, mad, n


def z_skoru(own: Decimal | None, medyan: Decimal | None, mad: Decimal | None) -> Decimal | None:
    """MAD-normalize edilmiş robust z-skoru: `(own - medyan) / (1.4826 * MAD)`
    -- quant_denetim_01.md Y2 düzeltmesi (eski taslağın SADECE düz yüzde
    sapma hesapladığı, MAD'ı hiç kullanmadığı formülün YERİNE). `mad<=0`
    ise (tüm örneklem aynı değerde -- fiilen imkansız ama guard gerekli)
    None döner."""
    if own is None or medyan is None or mad is None or mad == 0:
        return None
    return (own - medyan) / (Decimal("1.4826") * mad)


def oran_str(value: Decimal | None) -> str:
    """x-katı (YÜZDE OLMAYAN) oranlar için biçimlendirme -- quant_denetim_01.md
    K4 düzeltmesi: `format_percent_tr` ile KARIŞTIRILMAMASI için ayrı,
    "1,00x" biçimli (mevcut `scorer._skor_kaldirac` ailesinin `_num_str`+"x"
    deseniyle AYNI ilke)."""
    if value is None:
        return "-"
    return f"{value.quantize(Decimal('0.01'))}".replace(".", ",") + "x"


def seviye_trend_skoru_v2(
    etiket: str,
    seviye: Decimal | None,
    trend_puan: Decimal | None,
    guclu_esik: Decimal,
    orta_esik: Decimal,
    tavan: Decimal,
    taban: Decimal = Decimal(0),
) -> tuple[Decimal | None, str]:
    """`scorer._seviye_trend_skoru`'nun K1-düzeltmeli, SÜREKLİ kardeşi.

    v1'den DEĞİŞEN iki şey (quant_denetim_01.md K1'in önerdiği düzeltme
    BİREBİR uygulanır):
      1. Bant sınırları UÇLARI ÇAKIŞACAK şekilde [0,4]-[4,7]-[7,10] (v1'de
         [0,4]-[5,7]-[8,10] idi, orta_esik/guclu_esik sınırlarında 1
         puanlık sıçrama vardı).
      2. "Bozuluyor" (trend_puan<0) dalı artık SERT bir ikili eşik DEĞİL --
         seviyeye göre hesaplanan "normal" skorla SÜREKLİ bir ceza
         çarpanının (trend_puan=-X'te 0,5x, trend_puan=0'da TAM 1,0x)
         ÇARPILMASIYLA elde edilir. trend_puan=0 civarında böylece
         SÜREKLİLİK garanti edilir (v1'de FAVÖK marjı %40 iken trend
         -0,01->+0,00 arası skor 4,00->9,33 SIÇRIYORDU, somut kanıt:
         quant_denetim_01.md K1).

    X (ceza büyüklüğünün "yarı ömrü"): `(guclu_esik-orta_esik)/2` -- metriğin
    KENDİ ölçeğine göre türetilmiş, en az 0,5 puan tabanlı bir başlangıç
    değeri. Bu, spec'in kodlama fazına AÇIKÇA bıraktığı bir kalibrasyon
    kararıdır ("HANGİ yolun seçildiğini kodlama fazına AÇIKÇA bırakır ama
    mekanizmanın TANIMSIZ kalmaması gerekir") -- literatür kaynaklı
    OLMASA da UYDURMA değildir (metrik ölçeğinden türetilmiştir, burada
    AÇIKÇA belgelenir, gelecek bir kalibrasyon turunda gözden geçirilebilir).
    """
    if seviye is None:
        return None, "veri yok, bileşen atlandı."

    if seviye > guclu_esik:
        seviye_skoru = _asymptote_to(seviye - guclu_esik, tavan - guclu_esik, Decimal(7), Decimal(10))
    elif seviye >= orta_esik:
        seviye_skoru = _lerp_score(seviye, orta_esik, guclu_esik, Decimal(4), Decimal(7))
    else:
        seviye_skoru = _lerp_score(seviye, taban, orta_esik, Decimal(0), Decimal(4))

    if trend_puan is None:
        yon = "trend verisi yok"
        skor = seviye_skoru
    elif trend_puan < 0:
        genislik_x = max((guclu_esik - orta_esik) / 2, Decimal("0.5"))
        ceza_carpani = _lerp_score(trend_puan, -genislik_x, Decimal(0), Decimal("0.5"), Decimal("1.0"))
        skor = seviye_skoru * ceza_carpani
        yon = (
            f"geçen yıla göre {_num_str(trend_puan)} yüzde puan bozuluyor (kötüleşen trend) -- bu gerileme "
            "puanı sürekli/kademeli bir ceza çarpanıyla (sert bir uçurum değil) aşağı çeker"
        )
    elif trend_puan > 0:
        yon = "yükseliyor"
        skor = seviye_skoru
    else:
        yon = "yatay"
        skor = seviye_skoru

    aciklama = f"{etiket} {format_percent_tr(seviye)}, {yon}."
    return _clamp(skor, Decimal(0), Decimal(10)), aciklama


def kapsam_cezali_skor(total_score: Decimal, data_coverage_pct: Decimal) -> Decimal:
    """docs/spec/spec_kapsam_cezali_skor.md §1 -- "nominal ağırlık, eksik=
    sıfır" mercek skoru S′, MEVCUT `_agirlik_dagit_ve_hesapla` skoru S ile
    kapsam yüzdesinin CEBİRSEL ÖZDEŞLİĞİNDEN (S′ = S × kapsam/100) tek
    satırda türetilir -- bileşenlerden SIFIRDAN yeniden hesaplama GEREKMEZ.

    ÖNEMLİ (spec §1/§5): bu özdeşlik SADECE bileşen->mercek (lens içi)
    toplamada geçerlidir, mercek->bileşik (4 mercek -> tek sayı) seviyesine
    TAŞINMAZ (`hesapla_bilesik_skor` farklı, ikili bir dahil-etme mantığı
    kullanır) -- bu fonksiyon SADECE mercek seviyesinde çağrılmalıdır.

    Çağıran taraf (render katmanı, spec §3) `data_coverage_pct == 0` VEYA
    `>= 50` durumlarında bu fonksiyonu HİÇ ÇAĞIRMAMALI/SONUCUNU GÖSTERME-
    MELİDİR -- burada bir eşik KONTROLÜ YAPILMAZ (bu SAF matematik bir
    yardımcıdır, eşik kararı `src.render` katmanının sorumluluğundadır,
    quaxis-mimari anayasa madde 1: "analysis/ modülleri HİÇBİR I/O/sunum
    kararı almaz")."""
    return total_score * data_coverage_pct / Decimal(100)


__all__ = [
    "LensSonucu",
    "LensBileseni",
    "MIN_SECTOR_N",
    "SektorIstatistigi",
    "robust_istatistik",
    "z_skoru",
    "oran_str",
    "seviye_trend_skoru_v2",
    "kapsam_cezali_skor",
    "ComponentScore",
    "ScoreResult",
    "YETERSIZ_VERI_ROZETI",
    "_agirlik_dagit_ve_hesapla",
    "_asymptote_to",
    "_badge",
    "_clamp",
    "_lerp_score",
    "_num_str",
    "_safe_pct",
]

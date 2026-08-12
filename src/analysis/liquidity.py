"""V-05 (docs/spec/spec_veri_tamlik_yol_haritasi.md, "İlk Dalga" madde 8) --
Devir Hızı (turnover) + Amihud İlliquidity köprüsü -- SAF MATEMATİK,
`src.fetchers`/`src.db` HİÇBİR modülü import ETMEZ (quaxis-mimari anayasa
madde 1).

Ölçtüğü soru: bu hisse ne kadar KOLAY alınıp satılabiliyor (likidite) --
03/Ch.14 (Likidite Değeri): halka açık şirketler için, kısıtlı-hisse/QMDM
gibi ÖZEL şirket odaklı yöntemler UYGULANAMAZ (bkz. `bilgi-bankasi/
_ilerleme.md` Kısım 7 notu), bunun yerine turnover (devir hızı) TABANLI bir
PROXY kullanılır -- Amihud (2002) illikidite oranı ile TAMAMLANIR.

SIFIR yeni fetcher: `src/fetchers/price_history.py::fetch_ohlcv()` (günlük
hacim serisi -- BİST'te ZATEN TL cinsinden, NASDAQ'ta ADET, bkz. o modülün
kendi notu) ile `src/analysis/calculator.py`'nin piyasa değeri hesabı
(`price * shares_outstanding`/`share_capital`) arasında bugüne kadar hiç
köprü YOKTU -- bu modül SADECE o köprüdür.

BİLİNÇLİ OLARAK SKORLANMAYAN (ağırlık taşımayan) bir modüldür: roadmap
spec'in kendi metni ("hangi mercege ekleneceği küçük bir spec-eki
gerektirir ama veri TAMAMEN hazır") bu kararın HENÜZ verilmediğini
belirtiyor -- Güvenlik merceğinin (`lens_guvenlik.py`) mevcut Ağırlıklar
tablosu (Kaldıraç 30 + Bilanço Kalitesi 20 + Piotroski 25 + Toplam
Yükümlülük/Özkaynak 15 + Merton 10 = %100) YENİ bir bileşen için ayrılmış
bir pay İÇERMİYOR -- ağırlık İCAT ETMEK (persona kural) yasak. Bu modül
SADECE ham oranı hesaplayıp AÇIĞA ÇIKARIR (bilgi amaçlı, kartta/gelecek bir
mercek-spec revizyonunda kullanılabilir).
"""

from __future__ import annotations

from decimal import Decimal

from src.analysis.technical import PriceBar

_DEFAULT_PERIOD = 20


def _gunluk_islem_degeri_serisi(bars: list[PriceBar], market: str) -> list[Decimal]:
    """Her günün İŞLEM DEĞERİNİ (para birimi cinsinden, TL/USD) döner.

    `market="BIST"`: `bar.volume` ZATEN TL cinsindendir (bkz.
    price_history.py modül notu) -- OLDUĞU GİBİ kullanılır.
    `market="NASDAQ"` (veya BİST DIŞI herhangi bir piyasa): `bar.volume`
    ADET (işlem gören hisse sayısı) cinsindendir -- `bar.close` ile
    ÇARPILARAK para birimine çevrilir."""
    if market == "BIST":
        return [bar.volume for bar in bars]
    return [bar.volume * bar.close for bar in bars]


def ortalama_gunluk_islem_degeri(
    bars: list[PriceBar], market: str, period: int = _DEFAULT_PERIOD
) -> Decimal | None:
    """Son `period` günün ortalama GÜNLÜK İŞLEM DEĞERİ (para birimi
    cinsinden) -- devir hızı VE Amihud illikidite oranının ortak girdisi.

    `len(bars) < period` ise None döner (kısmi/eksik bir pencereyle ortalama
    UYDURULMAZ, Kural 3)."""
    if len(bars) < period:
        return None
    degerler = _gunluk_islem_degeri_serisi(bars[-period:], market)
    return sum(degerler) / len(degerler)


def devir_hizi_pct(ortalama_gunluk_islem_degeri: Decimal | None, piyasa_degeri: Decimal | None) -> Decimal | None:
    """03/Ch.14 (Likidite Değeri): Devir Hızı (turnover ratio) = ortalama
    günlük işlem değeri / piyasa değeri, yüzde olarak -- `_ilerleme.md`
    Kısım 7 notundaki formülün BİREBİR uygulanışı. Yüksek devir hızı =
    likit (kolay alınıp satılabilir), düşük devir hızı = illikit."""
    if ortalama_gunluk_islem_degeri is None or piyasa_degeri is None or piyasa_degeri <= 0:
        return None
    return ortalama_gunluk_islem_degeri / piyasa_degeri * 100


# Amihud'un (2002) kendi makalesindeki konvansiyon: ham oran (|getiri|/hacim)
# okunamayacak kadar küçük sayılar (10^-9 mertebesinde) ürettiği için 10^6
# ile ölçeklenir -- literatürde YAYGIN kullanılan bir sunum tercihi, formülün
# KENDİSİNİ değiştirmez.
_AMIHUD_OLCEK_CARPANI = Decimal("1000000")


def amihud_illikidite(bars: list[PriceBar], market: str, period: int = _DEFAULT_PERIOD) -> Decimal | None:
    """Amihud (2002) illikidite oranı = ortalama(|günlük getiri| / günlük
    işlem değeri), 10^6 ile ölçeklenmiş -- YÜKSEK değer = DÜŞÜK likidite
    (birim işlem hacminin fiyata verdiği etki büyük).

    `bars` artan tarihe sıralı olmalıdır (technical.py'nin genel varsayımı).
    Son `period` GÜNLÜK getiri gerektiği için en az `period+1` bar
    gereklidir; işlem değeri sıfır olan (veya tanımsız) bir gün ATLANIR
    (sıfıra bölme -- o gün için illikidite matematiksel olarak
    tanımsızdır, geri kalan günlerle ortalama YİNE DE hesaplanır)."""
    if len(bars) < period + 1:
        return None
    pencere = bars[-(period + 1):]
    degerler = _gunluk_islem_degeri_serisi(pencere, market)

    gunluk_oranlar: list[Decimal] = []
    for i in range(1, len(pencere)):
        onceki_kapanis = pencere[i - 1].close
        bugunku_kapanis = pencere[i].close
        islem_degeri = degerler[i]
        if onceki_kapanis is None or onceki_kapanis == 0 or islem_degeri is None or islem_degeri == 0:
            continue
        gunluk_getiri = abs((bugunku_kapanis - onceki_kapanis) / onceki_kapanis)
        gunluk_oranlar.append(gunluk_getiri / islem_degeri)

    if not gunluk_oranlar:
        return None
    return (sum(gunluk_oranlar) / len(gunluk_oranlar)) * _AMIHUD_OLCEK_CARPANI


__all__ = [
    "ortalama_gunluk_islem_degeri",
    "devir_hizi_pct",
    "amihud_illikidite",
]

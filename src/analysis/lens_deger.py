"""SPEC: `docs/spec/spec_mercek_deger.md` -- Değer Merceği (v2 çok-mercekli
skorlama, Mercek 1/4) -- SAF MATEMATİK, `src.fetchers`/`src.db` HİÇBİR
modülü import ETMEZ (quaxis-mimari anayasa madde 1).

Ölçtüğü soru: fiyat <-> değer farkı var mı -- hisse ödediğiniz paraya göre
UCUZ mu? Graham'ın "mutlak ucuzluk" disiplinini (01/FORMÜL-02,21,32) ve
Damodaran'ın "göreli/istatistiksel" çerçevesini (03/BAYRAK-20) AYRI AYRI
sunar (00_sentez.md §2.1'deki çelişki BURADA ÇÖZÜLMEZ, iki alt-mercek
olarak yan yana sunulur).

Girdi kaynakları (spec §Girdiler): `calculator.AnalysisResult` +
`calculator.ValuationMetrics` (fiyata bağlı çarpanlar) +
`fundamental_screens.FundamentalScreens` (Graham/Greenblatt/Carlisle,
SADECE BİST XI_29 sanayi) + isteğe bağlı `lens_common.SektorIstatistigi`
(sektör-içi F/K, PD/DD dağılımı, repository katmanından DÖNEM BAZLI
önbellekli gelir) + risksiz faiz oranı (`valuation._RISK_FREE_RATE_PCT`
ile AYNI kaynak, çağıran taraf currency'e göre seçer).

Ağırlıklar (spec §Eşikler ve ağırlıklar, toplam %100):
    Mutlak Ucuzluk (F/K+PD/DD)            %35  -- 01/FORMÜL-02, İLKE-80,133
    Sektöre Göreli Konum (medyan, n>=5)    %20  -- 03/BAYRAK-20
    Kazanç Getirisi vs Risksiz Oran        %15  -- 01/FORMÜL-03,36
    Graham Çarpanı (F/K*PD/DD<=22,5)       %10  -- 01/FORMÜL-21,32
    Greenblatt Kazanç Getirisi (EBIT/FD)   %10  -- Greenblatt "Sihirli Formül"
    Carlisle Acquirer's Multiple (FD/EBIT)  %5  -- Carlisle "Deep Value"
    NCAV / Net-Net Bonus                    %5  -- 01/İLKE-64,66,75, FORMÜL-01,12,14
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from src.analysis import scorer
from src.analysis.calculator import AnalysisResult, ValuationMetrics
from src.analysis.fundamental_screens import AcquirersMultipleResult, FundamentalScreens, GrahamResult, GreenblattResult
from src.analysis.lens_common import (
    MIN_SECTOR_N,
    LensSonucu,
    SektorIstatistigi,
    _agirlik_dagit_ve_hesapla,
    _clamp,
    _lerp_score,
    _num_str,
    oran_str,
    seviye_trend_skoru_v2,
    z_skoru,
)


@dataclass(frozen=True)
class DegerGirdisi:
    """Değer merceği hesaplamasının TÜM girdileri -- pipeline.py bunları
    zaten var olan `calculator`/`fundamental_screens` çağrılarından toplar,
    burada YENİDEN hesaplama YAPILMAZ."""

    analysis: AnalysisResult
    valuation: ValuationMetrics | None = None
    fundamental: FundamentalScreens | None = None  # SADECE BİST XI_29 sanayi
    risk_free_rate_pct: Decimal | None = None  # `valuation._RISK_FREE_RATE_PCT[currency]`
    sektor_pe: SektorIstatistigi | None = None
    sektor_pb: SektorIstatistigi | None = None
    template: str = "sanayi"  # "sanayi" | "abd_sanayi" (CONFIG'te degerleme esikleri olan sablonlar)


def _skor_sektore_goreli(
    own_pe: Decimal | None,
    own_pb: Decimal | None,
    sektor_pe: SektorIstatistigi | None,
    sektor_pb: SektorIstatistigi | None,
) -> tuple[Decimal | None, str]:
    """DÜZELTME (quant_denetim_01.md Y2): eski taslak sadece düz yüzde
    sapma hesaplıyordu, MAD hiç kullanılmıyordu -- burada GERÇEK
    MAD-normalize robust z-skoru kullanılır (bkz. `lens_common.z_skoru`).
    n<MIN_SECTOR_N ise (sektor-siniflandirma skill madde 1, n>=3'ten
    n>=5'e YÜKSELTİLDİ) bileşen ATLANIR."""
    z_degerler: list[Decimal] = []
    parcalar: list[str] = []

    if sektor_pe is not None and sektor_pe.n >= MIN_SECTOR_N and own_pe is not None and own_pe > 0:
        z_pe = z_skoru(own_pe, sektor_pe.medyan, sektor_pe.mad)
        if z_pe is not None:
            z_degerler.append(z_pe)
            sapma_pct = (own_pe - sektor_pe.medyan) / sektor_pe.medyan * 100 if sektor_pe.medyan != 0 else None
            parcalar.append(
                f"F/K sektör medyanından (n={sektor_pe.n}) "
                f"{'%' + _num_str(sapma_pct) if sapma_pct is not None else '-'} sapıyor (z={_num_str(z_pe)})"
            )

    if sektor_pb is not None and sektor_pb.n >= MIN_SECTOR_N and own_pb is not None and own_pb > 0:
        z_pb = z_skoru(own_pb, sektor_pb.medyan, sektor_pb.mad)
        if z_pb is not None:
            z_degerler.append(z_pb)
            sapma_pct = (own_pb - sektor_pb.medyan) / sektor_pb.medyan * 100 if sektor_pb.medyan != 0 else None
            parcalar.append(
                f"PD/DD sektör medyanından (n={sektor_pb.n}) "
                f"{'%' + _num_str(sapma_pct) if sapma_pct is not None else '-'} sapıyor (z={_num_str(z_pb)})"
            )

    if not z_degerler:
        n_bilgi = (sektor_pe.n if sektor_pe is not None else None) or (sektor_pb.n if sektor_pb is not None else None) or 0
        return (
            None,
            f"sektör karşılaştırması için yetersiz örneklem (n={n_bilgi}, gereken n≥{MIN_SECTOR_N}), bileşen atlandı.",
        )

    ortalama_z = sum(z_degerler) / len(z_degerler)
    # z=-2 (2 standart sapma UCUZ) -> 10 puan, z=+2 (2 standart sapma PAHALI) -> 0 puan.
    skor = _lerp_score(ortalama_z, Decimal(2), Decimal(-2), Decimal(0), Decimal(10))
    return skor, ", ".join(parcalar) + "."


def _skor_kazanc_getirisi(own_pe: Decimal | None, risk_free_rate_pct: Decimal | None) -> tuple[Decimal | None, str]:
    """01/FORMÜL-03,36: E/P >= risksiz faiz ZORUNLU minimum, tercihli hedef
    risksiz faizden +2-3 puan yüksek olması (01/İLKE-140,141)."""
    if own_pe is None or own_pe <= 0:
        return None, "kazanç getirisi (E/P) hesaplanamadı (F/K negatif/zarar), bileşen atlandı."
    if risk_free_rate_pct is None:
        return None, "risksiz faiz oranı verilmedi, bileşen atlandı."

    kazanc_getirisi_pct = Decimal(100) / own_pe
    fark_puan = kazanc_getirisi_pct - risk_free_rate_pct
    skor, _ = seviye_trend_skoru_v2(
        "Risksiz faize göre fark", fark_puan, None, guclu_esik=Decimal(2), orta_esik=Decimal(0), tavan=Decimal(10), taban=Decimal(-10)
    )
    aciklama = (
        f"kazanç getirisi (E/P) %{_num_str(kazanc_getirisi_pct)}, risksiz faiz %{_num_str(risk_free_rate_pct)} -- "
        f"fark {_num_str(fark_puan)} yüzde puan."
    )
    return skor, aciklama


def _skor_graham_carpani(graham: GrahamResult | None) -> tuple[Decimal | None, str]:
    """01/FORMÜL-21,32: F/K x PD/DD <= 22,5 (Graham'ın savunmacı yatırımcı
    ölçütü). `fundamental_screens._compute_graham` ve `valuation.py`'nin
    kendi bağımsız Graham hesabı AYNI KAYNAK sayılır (spec §Uygulama notu:
    çift sayılmaz), çağıran taraf hangisini geçtiğine bakılmaksızın."""
    if graham is None or graham.graham_multiple is None or graham.graham_multiple <= 0:
        return None, "Graham Çarpanı hesaplanamadı (F/K veya PD/DD negatif ya da veri yok), bileşen atlandı."
    gc = graham.graham_multiple
    esik = Decimal("22.5")
    if gc <= esik:
        skor = _lerp_score(gc, Decimal(0), esik, Decimal(10), Decimal(6))
    else:
        skor = _lerp_score(gc, esik, esik * 3, Decimal(6), Decimal(0))
    return skor, f"Graham Çarpanı (F/K×PD/DD) {_num_str(gc)}, klasik eşik {_num_str(esik)}."


def _skor_greenblatt_kazanc_getirisi(greenblatt: GreenblattResult | None) -> tuple[Decimal | None, str]:
    """Greenblatt'ın "Sihirli Formül"ünün DEĞER bacağı (EBIT/FD) -- FD-bazlı
    olduğu için borç etkisini F/K'dan daha iyi kapsar. SADECE BİST XI_29
    sanayi için mevcut (`fundamental_screens.py` kapsam sınırı)."""
    if greenblatt is None or greenblatt.earnings_yield_pct is None:
        return None, "Greenblatt Kazanç Getirisi hesaplanamadı (sadece BİST XI_29 sanayi şirketlerinde mevcut), bileşen atlandı."
    return seviye_trend_skoru_v2(
        "Greenblatt Kazanç Getirisi (EBIT/FD)", greenblatt.earnings_yield_pct, None, guclu_esik=Decimal(12), orta_esik=Decimal(6), tavan=Decimal(25)
    )


def _skor_carlisle(acquirers: AcquirersMultipleResult | None) -> tuple[Decimal | None, str]:
    """Carlisle Acquirer's Multiple (FD/EBIT) -- Greenblatt'ın tek-çarpanlı
    sadeleştirmesi, DÜŞÜK=ucuz (x-katı oran, K4 düzeltmesi: `oran_str` ile
    formatlanır, `format_percent_tr` DEĞİL)."""
    if acquirers is None or acquirers.acquirers_multiple is None:
        return None, "Carlisle Acquirer's Multiple hesaplanamadı (sadece BİST XI_29 sanayi şirketlerinde mevcut), bileşen atlandı."
    am = acquirers.acquirers_multiple
    if am <= 0:
        return None, "Carlisle Acquirer's Multiple negatif/tanımsız, bileşen atlandı."
    ucuz, pahali = Decimal(8), Decimal(15)
    if am < ucuz:
        skor = _lerp_score(am, Decimal(0), ucuz, Decimal(10), Decimal(7))
    elif am < pahali:
        skor = _lerp_score(am, ucuz, pahali, Decimal(7), Decimal(3))
    else:
        skor = _lerp_score(am, pahali, pahali * 2, Decimal(3), Decimal(0))
    return skor, f"Carlisle Acquirer's Multiple (FD/EBIT) {oran_str(am)}, ucuz eşiği {oran_str(ucuz)}, pahalı eşiği {oran_str(pahali)}."


def _skor_ncav_bonus(analysis: AnalysisResult, valuation: ValuationMetrics | None) -> tuple[Decimal | None, str]:
    """01/İLKE-64,66,75, FORMÜL-01,12,14: Graham'ın "net-net" bargain testi.

    DÜZELTME (quant_denetim_01.md K2, kalibrasyonla doğrulandı -- BİST
    sanayi'de %52,1 [86/165], NASDAQ sanayi'de %71,4 [15/21] şirkette
    `net_isletme_sermayesi<=0` koşulu tetiklenir): bu SİSTEMİK bir guard'dır,
    "nadir bir kenar durum" DEĞİL -- `net_isletme_sermayesi<=0` ise bonus
    HİÇ TETİKLENMEZ, 0 katkı (CEZA yok), bileşen ATLANIR."""
    ca = analysis.balance_sheet.current_assets.current
    total_assets = analysis.balance_sheet.total_assets.current
    equity = analysis.balance_sheet.equity.current
    if ca is None or total_assets is None or equity is None:
        return None, "NCAV (net işletme sermayesi) hesaplanamadı (bilanço verisi eksik), bileşen atlandı."

    total_liabilities = total_assets - equity
    net_isletme_sermayesi = ca - total_liabilities
    if net_isletme_sermayesi <= 0:
        return (
            None,
            "net işletme sermayesi (dönen varlıklar - toplam yükümlülükler) negatif/sıfır -- NCAV testi bu "
            "şirkette anlamlı değil, bonus tetiklenmez (ceza da yok), bileşen atlandı.",
        )
    if valuation is None or valuation.market_cap is None:
        return None, "piyasa değeri (fiyat) verisi yok, NCAV iskontosu hesaplanamadı, bileşen atlandı."

    net_net_iskonto_pct = (valuation.market_cap - net_isletme_sermayesi) / net_isletme_sermayesi * 100
    skor = _lerp_score(net_net_iskonto_pct, Decimal(-50), Decimal(100), Decimal(10), Decimal(0))
    if net_net_iskonto_pct < 0:
        aciklama = (
            f"piyasa değeri, net işletme sermayesinin (NCAV) %{_num_str(abs(net_net_iskonto_pct))} ALTINDA -- "
            "Graham'ın klasik 'net-net bargain' sinyali."
        )
    else:
        aciklama = f"piyasa değeri NCAV'ın %{_num_str(net_net_iskonto_pct)} üzerinde, net-net bonusu zayıf."
    return skor, aciklama


def hesapla_deger_mercegi(girdi: DegerGirdisi) -> LensSonucu:
    """Değer merceğinin 7 bileşenini `_agirlik_dagit_ve_hesapla` (mevcut,
    v1'den İTHAL edilen orantısal yeniden-dağıtım motoru) ile birleştirir."""
    cfg = scorer.CONFIG[girdi.template]["degerleme"]
    own_pe = girdi.valuation.pe_ratio if girdi.valuation is not None else None
    own_pb = girdi.valuation.pb_ratio if girdi.valuation is not None else None

    mutlak_ucuzluk = scorer._skor_degerleme(scorer.ValuationInput(pe_ratio=own_pe, pb_ratio=own_pb), cfg)
    sektore_goreli = _skor_sektore_goreli(own_pe, own_pb, girdi.sektor_pe, girdi.sektor_pb)
    kazanc_getirisi = _skor_kazanc_getirisi(own_pe, girdi.risk_free_rate_pct)

    graham_kaynagi = girdi.fundamental.graham if girdi.fundamental is not None else None
    greenblatt_kaynagi = girdi.fundamental.greenblatt if girdi.fundamental is not None else None
    carlisle_kaynagi = girdi.fundamental.acquirers_multiple if girdi.fundamental is not None else None

    graham = _skor_graham_carpani(graham_kaynagi)
    greenblatt = _skor_greenblatt_kazanc_getirisi(greenblatt_kaynagi)
    carlisle = _skor_carlisle(carlisle_kaynagi)
    ncav = _skor_ncav_bonus(girdi.analysis, girdi.valuation)

    bilesenler = [
        ("Mutlak Ucuzluk (F/K + PD/DD)", Decimal("35"), mutlak_ucuzluk),
        ("Sektöre Göreli Konum", Decimal("20"), sektore_goreli),
        ("Kazanç Getirisi vs Risksiz Oran", Decimal("15"), kazanc_getirisi),
        ("Graham Çarpanı (F/K×PD/DD)", Decimal("10"), graham),
        ("Greenblatt Kazanç Getirisi (EBIT/FD)", Decimal("10"), greenblatt),
        ("Carlisle Acquirer's Multiple (FD/EBIT)", Decimal("5"), carlisle),
        ("NCAV / Net-Net Bonus", Decimal("5"), ncav),
    ]
    return _agirlik_dagit_ve_hesapla(girdi.analysis.ticker, girdi.analysis.latest_period, "değer", bilesenler)

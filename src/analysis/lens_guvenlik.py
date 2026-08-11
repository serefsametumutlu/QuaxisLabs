"""SPEC: `docs/spec/spec_mercek_guvenlik.md` -- Güvenlik Merceği (v2
çok-mercekli skorlama, Mercek 4/4) -- SAF MATEMATİK, `src.fetchers`/
`src.db` HİÇBİR modülü import ETMEZ (quaxis-mimari anayasa madde 1).

Ölçtüğü soru: muhasebe hilesi + bilanço riski -- bu şirket YAKINDA ZOR
duruma düşer mi, raporlanan rakamlara GÜVENİLEBİLİR mi?

Ağırlıklar (spec §Eşikler ve ağırlıklar, `sanayi`/`abd_sanayi`, toplam %100):
    Kaldıraç (Net Borç/FAVÖK)                  %30  -- kalibre edilmiş çekirdek (v1'den taşınır)
    Bilanço Kalitesi (Cari Oran+Özkaynak/Varlık) %20  -- kalibre edilmiş çekirdek (v1'den taşınır)
    Piotroski F-Skoru                          %25  -- Piotroski (2000)
    Toplam Yükümlülük/Özkaynak (geniş tanım)   %15  -- 02/FORMÜL-16, İLKE-30 [YENİ]
    Merton Temerrüt Olasılığı (EDF)            %10  -- 03/İLKE-441-444 [YENİ orkestrasyon, BAYRAK-79/80]

`financials_by_period` girdisi SADECE Toplam Yükümlülük/Özkaynak (geniş
tanım, `short_term_liabilities`+`long_term_liabilities` ham alanları
`calculator.AnalysisResult`'ta YOKTUR) için gerekir -- `fundamental_
screens.py` ile AYNI "ham dict + aritmetik" deseni, katman kuralını
İHLAL ETMEZ.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from src.analysis import scorer
from src.analysis.calculator import AnalysisResult, FinancialsByPeriod
from src.analysis.fundamental_screens import PiotroskiResult
from src.analysis.lens_common import LensSonucu, _agirlik_dagit_ve_hesapla, _lerp_score, _safe_pct, oran_str, seviye_trend_skoru_v2
from src.analysis.merton import MertonResult


@dataclass(frozen=True)
class GuvenlikGirdisi:
    analysis: AnalysisResult
    financials_by_period: FinancialsByPeriod
    piotroski: PiotroskiResult | None = None  # SADECE BİST XI_29 sanayi
    merton: MertonResult | None = None  # pipeline.py: merton.compute_merton_dd_edf(...) -- BAYRAK-79/80 koprusu
    template: str = "sanayi"


def _skor_piotroski(piotroski: PiotroskiResult | None) -> tuple[Decimal | None, str]:
    """Piotroski F-Skoru'nun SÜREKLİ hali: `score/criteria_evaluated*100`,
    %78~7/9 güçlü, %44~4/9 orta (Piotroski'nin kendi 2000 makalesi bandına
    yakın). `criteria_evaluated<5` ise mevcut `fundamental_screens.py`
    davranışı (band=None, Kural 3: çok az kriterle yorum yapılmaz) KORUNUR."""
    if piotroski is None or piotroski.band is None:
        return (
            None,
            "Piotroski F-Skoru hesaplanamadı (sadece BİST XI_29 sanayi şirketlerinde mevcut veya yeterli kriter "
            "değerlendirilemedi), bileşen atlandı.",
        )
    f_skoru_pct = Decimal(piotroski.score) / Decimal(piotroski.criteria_evaluated) * 100
    return seviye_trend_skoru_v2(
        "Piotroski F-Skoru", f_skoru_pct, None, guclu_esik=Decimal(78), orta_esik=Decimal(44), tavan=Decimal(100)
    )


def _skor_toplam_yukumluluk_ozkaynak(analysis: AnalysisResult, fbp: FinancialsByPeriod) -> tuple[Decimal | None, str]:
    """02/FORMÜL-16, İLKE-30: (Kısa+Uzun Vadeli Toplam Yükümlülük)/Özkaynak
    -- mevcut dar `debt_to_equity`'den (SADECE finansal borç) YAPISAL
    OLARAK FARKLI bir soruya cevap verir, YERİNE GEÇMEZ, YANINA eklenir.

    K3a DÜZELTMESİ (quant_denetim_01.md, KALİBRASYONLA DOĞRULANDI): BİST
    sanayi'de 4/167 şirket negatif özkaynağa sahip, guard OLMADAN oran
    min=-39,70 gibi BÜYÜK NEGATİF değerler üretip YANLIŞLIKLA "<1 güçlü"
    bandına düşüyordu (derin sıkıntıdaki şirket EN YÜKSEK puanı alıyordu) --
    `equity<=0` ise None döner. K4 BİRİM UYARISI: x-katı oran, `oran_str`
    ile formatlanır (YÜZDE DEĞİL)."""
    equity = analysis.balance_sheet.equity.current
    if equity is None or equity <= 0:
        return None, "özkaynak negatif/sıfır, toplam yükümlülük/özkaynak oranı işaretsiz/anlamsız, bileşen atlandı."

    latest = fbp.get(analysis.latest_period, {})
    stl = latest.get("short_term_liabilities")
    ltl = latest.get("long_term_liabilities")
    if stl is None or ltl is None:
        return None, "kısa/uzun vadeli toplam yükümlülük verisi eksik, bileşen atlandı."

    oran = (stl + ltl) / equity
    guclu, zayif = Decimal(1), Decimal(2)
    if oran < guclu:
        skor = _lerp_score(oran, Decimal(0), guclu, Decimal(10), Decimal(7))
    elif oran <= zayif:
        skor = _lerp_score(oran, guclu, zayif, Decimal(7), Decimal(4))
    else:
        skor = _lerp_score(oran, zayif, zayif * 3, Decimal(4), Decimal(0))
    return (
        skor,
        f"toplam yükümlülük/özkaynak (geniş tanım, ticari borç+tahakkuk dahil) {oran_str(oran)} -- mevcut dar "
        "borç/özkaynak oranının YANINA eklenir, YERİNE GEÇMEZ.",
    )


def _skor_merton(merton: MertonResult | None) -> tuple[Decimal | None, str]:
    """03/İLKE-441-444, FORMÜL-171/172: Merton'un opsiyon-teorik özkaynak
    çerçevesi -- kaba bant (EDF<=%2 güçlü, %2-10 izlenmeli, >%10 risk
    sinyali), Damodaran Tablo 17.1 kredi notu-temerrüt eşleşmesiyle KABACA
    hizalı. `merton is None` ise (fiyat oynaklığı serisi eksik/yeni halka
    arz) bileşen atlanır."""
    if merton is None:
        return None, "Merton temerrüt olasılığı hesaplanamadı (fiyat oynaklığı serisi eksik veya yeni halka arz olabilir), bileşen atlandı."
    edf = merton.default_probability_pct
    dusuk, yuksek = Decimal(2), Decimal(10)
    if edf <= dusuk:
        skor = _lerp_score(edf, Decimal(0), dusuk, Decimal(10), Decimal(7))
    elif edf <= yuksek:
        skor = _lerp_score(edf, dusuk, yuksek, Decimal(7), Decimal(3))
    else:
        skor = _lerp_score(edf, yuksek, yuksek * 4, Decimal(3), Decimal(0))
    return (
        skor,
        f"Merton temerrüt olasılığı (EDF, sentetik/dolaylı gösterge -- faiz karşılama oranı verisi eksikliği "
        f"nedeniyle) %{edf.quantize(Decimal('0.01'))} (mesafe-i temerrüt {merton.distance_to_default.quantize(Decimal('0.01'))} std. sapma).",
    )


def hesapla_guvenlik_mercegi(girdi: GuvenlikGirdisi) -> LensSonucu:
    cfg = scorer.CONFIG[girdi.template]
    r = girdi.analysis.ratios
    equity = girdi.analysis.balance_sheet.equity.current
    assets = girdi.analysis.balance_sheet.total_assets.current

    kaldirac = scorer._skor_kaldirac(r.net_debt_to_ebitda, cfg["kaldirac"])
    bilanco = scorer._skor_bilanco_kalitesi(r.current_ratio, _safe_pct(equity, assets), cfg["bilanco_kalitesi"])
    piotroski = _skor_piotroski(girdi.piotroski)
    tyo = _skor_toplam_yukumluluk_ozkaynak(girdi.analysis, girdi.financials_by_period)
    merton = _skor_merton(girdi.merton)

    bilesenler = [
        ("Kaldıraç (Net Borç/FAVÖK)", Decimal("30"), kaldirac),
        ("Bilanço Kalitesi (Cari Oran + Özkaynak/Varlık)", Decimal("20"), bilanco),
        ("Piotroski F-Skoru", Decimal("25"), piotroski),
        ("Toplam Yükümlülük/Özkaynak (geniş tanım)", Decimal("15"), tyo),
        ("Merton Temerrüt Olasılığı (EDF)", Decimal("10"), merton),
    ]
    return _agirlik_dagit_ve_hesapla(girdi.analysis.ticker, girdi.analysis.latest_period, "güvenlik", bilesenler)

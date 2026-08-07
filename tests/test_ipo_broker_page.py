"""src/fetchers/ipo_broker_page.py testleri -- 2026-08-07.

Kural 11: ağ isteği ATILMAZ -- `ipo_broker_page._get` monkeypatch edilir,
GERÇEK halkarz.com HTML yapısından alınmış (data/exploration/halkarz_citas.html,
CANLI doğrulanmış) küçük sabit HTML parçaları kullanılır.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

import httpx
import pytest

from src.fetchers import ipo_broker_page as ibp


def _q1(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

_SEARCH_RESULT_HTML = """
<article class="index-list">
<div class="il-content">
<h2 class="il-bist-kod">CITAS</h2>
<h3 class="il-halka-arz-sirket"><a href="https://halkarz.com/citlekci-magazacilik-gida-a-s/">Çitlekçi</a></h3>
</div>
</article>
<article class="index-list">
<div class="il-content">
<h2 class="il-bist-kod">VEYAS</h2>
<h3 class="il-halka-arz-sirket"><a href="https://halkarz.com/turker-vangolu-enerji/">Türker</a></h3>
</div>
</article>
"""

_DETAIL_PAGE_HTML = """
<table class="sp-table"><tr><td><em>Halka Arz Tarihi : </em></td><td>
<time datetime="10-11-12 Ağustos 2026" title="10-11-12 Ağustos 2026">10-11-12 Ağustos 2026</time>
<small class="c-a9a9a9"><i></i> 09:00-17:00</small></td></tr>
<tr class="font-16 margin-bottom-20"><td><em>Halka Arz Fiyatı/Aralığı : </em></td><td><strong class="f700">73,70 TL</strong></td></tr>
<tr><td><em>Dağıtım Yöntemi : </em></td><td><strong>Eşit Dağıtım **</strong></td></tr>
<tr><td><em>Pay : </em></td><td><strong>36.500.000 Lot</strong></td></tr>
</table>
<article class="sp-arz-extra"><ul class="aex-in">
<li><h5>Halka Arz Şekli</h5><p>
- Sermaye Artırımı : 30.000.000 Lot <br>
- Ortak Satışı : 6.500.000 Lot (Tunçlar Yatırım Holding A.Ş.) <br>
<small>* SPK Bülteni, 2026/49.</small></p></li>
<li><h5>Halka Arz Satış Yöntemi</h5><p>
- Sabit Fiyatla Talep Toplama. <br>
- En İyi Gayret Aracılığı. <br></p></li>
<li><h5>Fiyat İstikrarı</h5><p>
- 30 gün. * Brüt halka arz gelirinin %15'i. <br>
<small>* İzahname, Sayfa 229.</small></p></li>
<li><h5>Tahsisat Grupları</h5><p>
- 14.600.000 Lot (%40) Yurt İçi Bireysel Yatırımcı <br>
- 3.650.000 Lot (%10) Yüksek Başvurulu Yatırımcı <br>
<small>* İzahname, Sayfa 220.</small></p></li>
<li><h5>Dağıtılacak Pay Miktarı (Olası) *</h5><p>
- 500 Bin katılım ~ 29 Lot (2137 TL). <br>
- 700 Bin katılım ~ 21 Lot (1547 TL). <br>
<small>* Bireysel Yatırımcı Grubu.</small></p></li>
<li class="b-esit"><p>
** Bireysele Eşit Dağıtım. <br>
**** Katılım Endeksine uygun. <a href="https://halkarz.com/bist-endeks/xktum/">(XKTUM)</a> <br>
</p></li></ul></article>
"""

_DETAIL_PAGE_HTML_IZAHNAME_OKUNAMAZ = """
<table class="sp-table"><tr><td><em>Halka Arz Tarihi : </em></td><td>
<time datetime="12-13-14 Ağustos 2026" title="12-13-14 Ağustos 2026">12-13-14 Ağustos 2026</time>
<small class="c-a9a9a9"><i></i> 09:00-17:00</small></td></tr>
<tr class="font-16 margin-bottom-20"><td><em>Halka Arz Fiyatı/Aralığı : </em></td><td><strong class="f700">136,00 TL</strong></td></tr>
<tr><td><em>Pay : </em></td><td><strong>65.000.000 Lot</strong></td></tr>
</table>
<article class="sp-arz-extra"><ul class="aex-in">
<li><h5>Halka Arz Büyüklüğü</h5><p>
～ 10,5 Milyar TL. (Ek satış dahil.)</p></li>
<li class="b-esit"><p>
**** Katılım Endeksine uygun değil. <br>
</p></li></ul></article>
"""

_DETAIL_PAGE_HTML_UYGUN_DEGIL = """
<table class="sp-table"><tr><td><em>Halka Arz Tarihi : </em></td><td>
<time datetime="Ertelendi" title="Ertelendi">Ertelendi</time></td></tr></table>
<article class="sp-arz-extra"><ul class="aex-in">
<li><h5>Halka Arz Satış Yöntemi</h5><p>- Sabit Fiyatla Talep Toplama. <br></p></li>
<li class="b-esit"><p>**** Katılım Endeksine uygun değil. <br></p></li></ul></article>
"""


def _fake_response(text: str) -> httpx.Response:
    return httpx.Response(status_code=200, text=text, request=httpx.Request("GET", "https://halkarz.com/"))


def test_fetch_supplementary_ipo_info_tam_alanlarla_dolar(monkeypatch) -> None:
    responses = iter([_fake_response(_SEARCH_RESULT_HTML), _fake_response(_DETAIL_PAGE_HTML)])
    monkeypatch.setattr(ibp, "_get", lambda url, params=None: next(responses))

    info = ibp.fetch_supplementary_ipo_info("CITAS")

    assert info is not None
    assert info.demand_period_display == "10-11-12 Ağustos 2026"
    assert info.demand_period_hours == "09:00-17:00"
    assert info.participation_index_compliant is True
    assert info.participation_index_name == "XKTUM"
    assert "30 gün" in info.price_stabilization_note
    assert "İzahname" not in info.price_stabilization_note  # dipnot ayıklanmış olmalı
    assert "Sabit Fiyatla Talep Toplama" in info.sales_method_note
    assert info.offering_price_text == "73,70 TL"
    assert info.total_lot_text == "36.500.000"  # "Lot" birimi ayıklanmış -- build_ipo_analysis_text() kendi ekliyor
    assert info.allocation_lines == (
        "Yurt İçi Bireysel Yatırımcı: %40 (14.600.000 Lot)",
        "Yüksek Başvurulu Yatırımcı: %10 (3.650.000 Lot)",
    )

    # Sermaye Artırımı (30.000.000) / Ortak Satışı (6.500.000) -- "Halka Arz
    # Şekli" bloğundan LOT cinsinden okunup yüzdeye çevrilir.
    assert _q1(info.capital_increase_pct_fallback) == Decimal("82.2")
    assert _q1(info.partner_sale_pct_fallback) == Decimal("17.8")

    # Tahmini Dağıtım artık halkarz.com'un KENDİ (150 Bin/2,2 Milyon gibi
    # yuvarlak olmayan) senaryo tablosunu KULLANMAZ -- bireysel grup lot
    # sayısını (14.600.000) + fiyatı (73,70) Decimal'e çevirip AYNI standart
    # senaryo listesiyle (300 Bin - 1 Milyon, 100 Binlik adımlarla) yeniden
    # hesaplar (kullanıcı isteği, 2026-08-07 üçüncü tur).
    rows = {p: (lot, tl) for p, lot, tl in info.estimated_retail_distribution}
    assert rows[300_000] == (Decimal("48"), Decimal("3538"))
    assert rows[500_000] == (Decimal("29"), Decimal("2137"))
    assert rows[1_000_000] == (Decimal("14"), Decimal("1032"))
    assert 150_000 not in rows and 2_200_000 not in rows


_DETAIL_PAGE_HTML_SADECE_SERMAYE_ARTIRIMI = """
<table class="sp-table"><tr><td><em>Pay : </em></td><td><strong>25.100.000 Lot</strong></td></tr></table>
<article class="sp-arz-extra"><ul class="aex-in">
<li><h5>Halka Arz Şekli</h5><p>
- Sermaye Artırımı : 25.100.000 Lot <br>
<small>* SPK Bülteni, 2026/49.</small></p></li>
<li class="b-esit"><p>**** Katılım Endeksine uygun. <a href="https://halkarz.com/bist-endeks/xktum/">(XKTUM)</a> <br></p></li>
</ul></article>
"""


def test_fetch_supplementary_ipo_info_sadece_sermaye_artirimi_satiri_varsa_ortak_satisi_sifir_sayilir(monkeypatch) -> None:
    """🚨 CANLI HATA + DÜZELTME (2026-08-07, KPEKS): "Halka Arz Şekli" bloğunda
    SADECE "Sermaye Artırımı" satırı olup "Ortak Satışı" satırı HİÇ
    geçmiyorsa (arzın TAMAMI yeni pay -- KPEKS'in izahnamesinin kendi giriş
    cümlesiyle de doğrulandı) bu "veri eksik" değil "%100 sermaye artırımı,
    %0 ortak satışı" anlamına gelir -- önceden İKİSİ de None olmadıkça hesap
    yapılmadığı için bölümün TAMAMI sessizce gizleniyordu."""
    responses = iter([_fake_response(_SEARCH_RESULT_HTML), _fake_response(_DETAIL_PAGE_HTML_SADECE_SERMAYE_ARTIRIMI)])
    monkeypatch.setattr(ibp, "_get", lambda url, params=None: next(responses))

    info = ibp.fetch_supplementary_ipo_info("CITAS")

    assert info is not None
    assert info.capital_increase_pct_fallback == Decimal("100")
    assert info.partner_sale_pct_fallback == Decimal("0")
    assert info.is_pure_capital_increase_fallback is True


def test_fetch_supplementary_ipo_info_izahname_okunamazsa_fallback_alanlari_dolar(monkeypatch) -> None:
    """VEYAS ile CANLI bulundu (2026-08-07, kullanıcı raporu): izahname
    PDF'i taranmış/OCR'siz olduğunda `total_lot_text`'ten "Lot" birimi
    ayıklanmış (çift birim önlemek için) ve `offering_size_text`
    doldurulmuş olmalı."""
    responses = iter([_fake_response(_SEARCH_RESULT_HTML), _fake_response(_DETAIL_PAGE_HTML_IZAHNAME_OKUNAMAZ)])
    monkeypatch.setattr(ibp, "_get", lambda url, params=None: next(responses))

    info = ibp.fetch_supplementary_ipo_info("VEYAS")

    assert info is not None
    assert info.offering_price_text == "136,00 TL"
    assert info.total_lot_text == "65.000.000"
    assert info.offering_size_text == "10,5 Milyar TL. (Ek satış dahil.)"
    assert info.participation_index_compliant is False


def test_fetch_supplementary_ipo_info_uygun_degil_durumu(monkeypatch) -> None:
    responses = iter([_fake_response(_SEARCH_RESULT_HTML), _fake_response(_DETAIL_PAGE_HTML_UYGUN_DEGIL)])
    monkeypatch.setattr(ibp, "_get", lambda url, params=None: next(responses))

    info = ibp.fetch_supplementary_ipo_info("CITAS")

    assert info is not None
    assert info.participation_index_compliant is False
    assert info.participation_index_name is None
    assert info.demand_period_display == "Ertelendi"


def test_fetch_supplementary_ipo_info_ticker_bulunamazsa_none(monkeypatch) -> None:
    monkeypatch.setattr(ibp, "_get", lambda url, params=None: _fake_response(_SEARCH_RESULT_HTML))
    assert ibp.fetch_supplementary_ipo_info("ZZZZ") is None


def test_fetch_supplementary_ipo_info_ag_hatasinda_sessizce_none_doner(monkeypatch) -> None:
    """Kural 9: ikincil kaynak, hata TÜM kartı ÇÖKERTMEMELİ."""

    def _raise(url, params=None):
        raise httpx.ConnectError("bağlantı yok", request=httpx.Request("GET", url))

    monkeypatch.setattr(ibp, "_get", _raise)
    assert ibp.fetch_supplementary_ipo_info("CITAS") is None


def test_fetch_supplementary_ipo_info_bos_sayfa_none_doner(monkeypatch) -> None:
    responses = iter([_fake_response(_SEARCH_RESULT_HTML), _fake_response("<html><body>boş</body></html>")])
    monkeypatch.setattr(ibp, "_get", lambda url, params=None: next(responses))
    assert ibp.fetch_supplementary_ipo_info("CITAS") is None


# --- _parse_financial_table (2026-08-07, otuz birinci tur, YENİ) --------------------------------


def test_parse_financial_table_ondalik_virgulu_alan_ayraciyla_karismaz() -> None:
    """🚨 CANLI HATA + DÜZELTME (KPEKS): `text.split(",")` (boşluksuz) Türkçe
    ondalık virgülünü ("794,1 Milyon TL") DE bölüyordu -- KPEKS'in gerçek
    verisiyle CANLI yakalandı, "1 Milyon TL" gibi anlamsız bir değer
    üretiyordu."""
    text = (
        "Finansal Tablo, 2026/3, 2025, 2024, Hasılat, 794,1 Milyon TL, "
        "3,8 Milyar TL, 4,1 Milyar TL, Brüt Kâr, 250,0 Milyon TL, "
        "1,2 Milyar TL, 1,3 Milyar TL"
    )

    period, revenue, gross_profit = ibp._parse_financial_table(text)

    assert period == "2025"
    assert revenue == "3,8 Milyar TL"
    assert gross_profit == "1,2 Milyar TL"


def test_parse_financial_table_veyas_ile_birebir_dogru() -> None:
    text = (
        "Finansal Tablo, 2026/3, 2025, 2024, Hasılat, 5,7 Milyar TL, "
        "26,6 Milyar TL, 24,6 Milyar TL, Brüt Kâr, 2,4 Milyar TL, "
        "9,5 Milyar TL, 9,9 Milyar TL"
    )

    period, revenue, gross_profit = ibp._parse_financial_table(text)

    assert period == "2025"
    assert revenue == "26,6 Milyar TL"
    assert gross_profit == "9,5 Milyar TL"


def test_parse_financial_table_beklenmeyen_format_none_doner() -> None:
    assert ibp._parse_financial_table("alakasız bir metin") == (None, None, None)
    assert ibp._parse_financial_table(None) == (None, None, None)

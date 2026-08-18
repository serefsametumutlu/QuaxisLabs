"""src/analysis/is_anlasma_parser.py testleri -- gercek dosyadan alinmis
ornek satirlarla (bist-yeni-is-anlasmalari-2025-2026.md)."""

from __future__ import annotations

from decimal import Decimal

from src.analysis.is_anlasma_parser import is_renewal, parse_amount, parse_deals_table


def test_db_figure_tercih_edilir_kap_metni_degil():
    raw = "KAP: ~19.000.000 USD (KDV dâhil); DB: 15.833.333 USD"
    value, currency = parse_amount(raw)
    assert value == Decimal("15833333")
    assert currency == "USD"


def test_basit_tl_tutar():
    raw = "151.514.040 TL (sözleşme imzalama süreci devam ediyor)"
    value, currency = parse_amount(raw)
    assert value == Decimal("151514040")
    assert currency == "TRY"


def test_ondalikli_tl_tutar():
    raw = "86.241.042 TL (KDV dahil; DB: 71.867.535 TL)"
    value, currency = parse_amount(raw)
    assert value == Decimal("71867535")
    assert currency == "TRY"


def test_milyon_kelimeli_tutar():
    raw = "46,1 milyon USD"
    value, currency = parse_amount(raw)
    assert value == Decimal("46100000")
    assert currency == "USD"


def test_milyar_kelimeli_tutar():
    raw = "1.650.000.000 EUR"
    value, currency = parse_amount(raw)
    assert value == Decimal("1650000000")
    assert currency == "EUR"


def test_avro_esanlamli_tutar():
    raw = "13.000.000 Avro"
    value, currency = parse_amount(raw)
    assert value == Decimal("13000000")
    assert currency == "EUR"


def test_toplam_ifadesi_varsa_kullanilir():
    raw = "111.850.000 USD + 54.600.000 USD (toplam 166.450.000 USD)"
    value, currency = parse_amount(raw)
    assert value == Decimal("166450000")
    assert currency == "USD"


def test_karisik_para_birimi_db_veya_toplam_yoksa_ayristirilamaz():
    raw = "35.004.690,09 TL + 790.600,34 USD"
    value, currency = parse_amount(raw)
    assert value is None
    assert currency is None


def test_ondalikli_virgullu_tutar_dogru_cevrilir():
    raw = "18.602.919,36 TL (434.400 USD, KDV dahil; DB: 6.147.417 TL)"
    value, currency = parse_amount(raw)
    assert value == Decimal("6147417")
    assert currency == "TRY"


def test_hicbir_tutar_yoksa_none_doner():
    value, currency = parse_amount("belirtilmemiş")
    assert value is None
    assert currency is None


def test_is_renewal_tespiti():
    assert is_renewal("Sözleşme yenilenmesi (31.12.2026 tarihine kadar)") is True
    assert is_renewal("Bilgi Teknolojileri Danışmanlık Hizmet Alımı") is False


def test_parse_deals_table_gercekci_ornek():
    md = """# Baslik

| Hisse | Tarih | Karşı Taraf | İş / Proje | Tutar |
|---|---|---|---|---|
| ACSEL | 2025-07-16 | Türkiye Petrolleri Anonim Ortaklığı | Sondaj faaliyetlerinde kullanılmak üzere CMC siparişi | 3.760.800 USD (KDV durumu KAP'ta belirtilmemiş) |
| TUREX | 2025-04-16 | Şişecam | Sözleşme yenilenmesi (31.12.2026 tarihine kadar) | 630.000.000 TL + KDV |
"""
    rows = parse_deals_table(md)
    assert len(rows) == 2

    acsel = rows[0]
    assert acsel.ticker == "ACSEL"
    assert acsel.deal_date.isoformat() == "2025-07-16"
    assert acsel.amount_value == Decimal("3760800")
    assert acsel.amount_currency == "USD"
    assert acsel.is_renewal is False

    turex = rows[1]
    assert turex.ticker == "TUREX"
    assert turex.is_renewal is True
    assert turex.amount_value == Decimal("630000000")
    assert turex.amount_currency == "TRY"


def test_parse_deals_table_baslik_ve_ayirici_satirlari_atlar():
    md = "# X\n\n| Hisse | Tarih | Karşı Taraf | İş / Proje | Tutar |\n|---|---|---|---|---|\n"
    rows = parse_deals_table(md)
    assert rows == []

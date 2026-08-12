"""src/analysis/liquidity.py testleri -- V-05 (docs/spec/spec_veri_tamlik_
yol_haritasi.md, "İlk Dalga" madde 8).

Hicbir ag istegi/I-O yoktur (liquidity.py saf matematik, technical.py ile
AYNI ilke).
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from src.analysis.liquidity import amihud_illikidite, devir_hizi_pct, ortalama_gunluk_islem_degeri
from src.analysis.technical import PriceBar


def _d(value) -> Decimal:
    return Decimal(str(value))


def _bars(closes: list[float], volumes: list[float], start: date = date(2026, 1, 1)) -> list[PriceBar]:
    assert len(closes) == len(volumes)
    return [
        PriceBar(
            trade_date=start + timedelta(days=i),
            high=_d(close) * _d("1.01"),
            low=_d(close) * _d("0.99"),
            close=_d(close),
            volume=_d(volume),
        )
        for i, (close, volume) in enumerate(zip(closes, volumes))
    ]


# --- ortalama_gunluk_islem_degeri -----------------------------------------------------


def test_ortalama_gunluk_islem_degeri_bist_hacim_zaten_tl_oldugu_icin_dogrudan_kullanilir() -> None:
    # BIST: volume ZATEN TL cinsinden -- close ile CARPILMAZ.
    bars = _bars(closes=[100] * 20, volumes=[1000] * 20)
    sonuc = ortalama_gunluk_islem_degeri(bars, market="BIST", period=20)
    assert sonuc == Decimal("1000")


def test_ortalama_gunluk_islem_degeri_nasdaq_hacim_adet_ile_kapanis_carpilir() -> None:
    # NASDAQ: volume ADET -- close ile CARPILARAK para birimine cevrilir.
    bars = _bars(closes=[100] * 20, volumes=[1000] * 20)
    sonuc = ortalama_gunluk_islem_degeri(bars, market="NASDAQ", period=20)
    assert sonuc == Decimal("100000")


def test_ortalama_gunluk_islem_degeri_yetersiz_veri_none_doner() -> None:
    bars = _bars(closes=[100] * 5, volumes=[1000] * 5)
    assert ortalama_gunluk_islem_degeri(bars, market="BIST", period=20) is None


def test_ortalama_gunluk_islem_degeri_sadece_son_pencereyi_kullanir() -> None:
    # Ilk 10 gun farkli hacimli -- sadece SON 20 gun etkilemeli.
    bars = _bars(closes=[100] * 30, volumes=[9999] * 10 + [1000] * 20)
    sonuc = ortalama_gunluk_islem_degeri(bars, market="BIST", period=20)
    assert sonuc == Decimal("1000")


# --- devir_hizi_pct -----------------------------------------------------


def test_devir_hizi_pct_formul() -> None:
    # 03/Ch.14: devir hizi = gunluk islem degeri / piyasa degeri * 100.
    sonuc = devir_hizi_pct(Decimal("1000000"), Decimal("100000000"))
    assert sonuc == Decimal("1")


def test_devir_hizi_pct_piyasa_degeri_yoksa_none_doner() -> None:
    assert devir_hizi_pct(Decimal("1000"), None) is None


def test_devir_hizi_pct_islem_degeri_yoksa_none_doner() -> None:
    assert devir_hizi_pct(None, Decimal("1000")) is None


def test_devir_hizi_pct_piyasa_degeri_sifir_veya_negatifse_none_doner() -> None:
    assert devir_hizi_pct(Decimal("1000"), Decimal("0")) is None
    assert devir_hizi_pct(Decimal("1000"), Decimal("-1")) is None


# --- amihud_illikidite -----------------------------------------------------


def test_amihud_illikidite_sabit_fiyatta_sifir_doner() -> None:
    # Fiyat hic degismiyorsa gunluk getiri her zaman 0 -- oran da 0.
    bars = _bars(closes=[100] * 21, volumes=[1000] * 21)
    sonuc = amihud_illikidite(bars, market="BIST", period=20)
    assert sonuc == Decimal("0")


def test_amihud_illikidite_dusuk_hacimde_yuksek_deger_uretir() -> None:
    # AYNI fiyat degisimi, DUSUK hacimli hissede DAHA YUKSEK illikidite
    # uretmeli (birim hacmin fiyata etkisi buyuk).
    closes = [100, 105] + [105] * 19  # ilk gun %5 artis, sonrasi yatay
    likit = amihud_illikidite(_bars(closes, [1000000] * 21), market="BIST", period=20)
    illikit = amihud_illikidite(_bars(closes, [1000] * 21), market="BIST", period=20)
    assert likit is not None and illikit is not None
    assert illikit > likit


def test_amihud_illikidite_yetersiz_veri_none_doner() -> None:
    bars = _bars(closes=[100] * 10, volumes=[1000] * 10)
    assert amihud_illikidite(bars, market="BIST", period=20) is None


def test_amihud_illikidite_islem_degeri_sifir_olan_gun_atlanir_diger_gunlerle_hesaplanir() -> None:
    closes = [100] * 20 + [110]
    volumes = [1000] * 20 + [0]  # son gun islem hacmi sifir -- o gun ATLANIR
    bars = _bars(closes, volumes)
    sonuc = amihud_illikidite(bars, market="BIST", period=20)
    assert sonuc == Decimal("0")  # kalan tum gunler yatay (getiri=0)


def test_amihud_illikidite_nasdaq_hacim_adet_kapanisla_carpilir() -> None:
    closes = [100, 105] + [105] * 19
    bars = _bars(closes, [10000] * 21)
    sonuc = amihud_illikidite(bars, market="NASDAQ", period=20)
    assert sonuc is not None and sonuc > Decimal("0")

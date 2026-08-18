"""Harmonik formasyon ailesi on-ayarlari (Gartley/Bat/Butterfly/Crab) --
`abcd_pattern.Params` uzerinden, SAF VERI, sifir yeni mantik.

Bu modul KASITLI olarak `abcd_pattern.py`den AYRI: o dosya Pine kaynagiyla
(`pine/abcd_v2_5_indicator.pine`) LOCKSTEP kalmak zorunda (bkz. o modulun
ust notu) -- burdaki on-ayarlar Pine kaynaginin BIR PARCASI DEGIL, harmonik
ticaret literaturunden turetilmis BAGIMSIZ sabitler. Ikisini ayni dosyada
tutmak, gelecekte "Pine guncellendi, bu dosya da guncellenmeli mi?" sorusunu
yanlislikla bu on-ayarlara da bulastirabilirdi.

## Neden sadece Params, yeni bir detector YOK

`abcd_pattern.detect()`in A-B-C-D pivot state machine'i (kesin pivot tipi
alternansi, rolling A/B/C/D) formasyon ailesinden BAGIMSIZDIR -- degisen tek
sey `_is_valid_abcd()`in BC retracement / CD extension bant kontrolleridir,
ve bu banlar zaten `Params.min_bc_retrace/max_bc_retrace/use_exact_cd/
cd_min_ext/cd_max_ext` ile tam parametrik. Yeni bir formasyon ailesi eklemek
= yeni bir `Params` degeri, yeni kod DEGIL.

## KRITIK matematiksel not -- `cd_ratio`in tanimi

`abcd_pattern._is_valid_abcd()`: `cd_r = |D-C| / |A-B|` -- yani CD bacagi,
BC bacaginin DEGIL, AB bacaginin bir kesri olarak olculur. Klasik AB=CD
formasyonu icin bu doğrudan doğru tanimdir (CD ~= AB, `use_exact_cd=True`).

Ama standart harmonik literatur (Gartley/Bat/Butterfly/Crab, bkz. Scott M.
Carney, *Harmonic Trading, Volume One* (2004), Bolum 3-6 formasyon
tablolari) CD uzatmasini BC'nin bir kati olarak tanimlar (orn. "Gartley:
CD = BC'nin 1.272-1.618 kati"), AB'nin degil. Bu kod tabaninda CD'yi
DOGRUDAN BC'ye gore kontrol eden bir alan YOK (5. nokta X olmadigi icin
AD/XA-capa orani da hic kontrol edilemiyor, asagiya bkz.) -- bu yuzden
asagidaki `cd_min_ext`/`cd_max_ext` degerleri, standart CD/BC oranini bu
kod tabaninin CD/AB tanimina donusturen bir MATEMATIKSEL BILESIK SINIR
(compound bound) ile hesaplanir:

    cd_r (bu kod) = (CD/BC) x (BC/AB) = k x bc_r

  bc_r, [min_bc_retrace, max_bc_retrace] araliginda: standart 0.382-0.886
  (tum 4 aile icin ORTAK, Carney Bolum 3-6). k, aileye ozgu CD/BC orani
  araligi (asagida her preset'te kaynakli). Bilesik sinirlar:

    cd_min_ext = k_min x min_bc_retrace
    cd_max_ext = k_max x max_bc_retrace

  Bu, teorik olarak MUMKUN olan en genis `cd_r` araligidir (bc_r ve k
  BAGIMSIZ degiskenler gibi ele alinip her ikisinin de en ucundaki
  kombinasyon alinir) -- yani KORUNUMLU bir DIS SINIRDIR, belirli bir
  sinyalin GERCEK bc_r'siyle KOSULLANDIRILMIS bir CD/BC kontrolunun
  YERINI TUTMAZ. Sonuc: bu on-ayarlar bazi sinir-durum sinyallerini
  (dusuk bc_r + yuksek CD/BC ya da tam tersi kombinasyonlarda) YANLIS
  KABUL edebilir -- bilincli, belgelenmis bir yaklasiklik, `spec_abcd_
  mimari_kararlar.md`'deki "bilinen sinir, blocker degil" disipliniyle
  AYNI ruhta (bkz. o dosyanin Karar 3'u, yfinance intraday sinirlamasi).
  Kod tabaninda `cd_r`i BC-goreli olarak yeniden tanimlamak (dogru per-
  sinyal kontrolu icin) `abcd_pattern.py`ye dokunmayi gerektirir --
  KAPSAM DISI (gorev acikca "yeni detector YAZMA" diyor); ileride ayri
  bir faz olarak ele alinabilir.

## KRITIK ikinci not -- X noktasi / XD tamamlanma orani YOK

Standart 5-noktali XABCD harmonikleri (Gartley/Bat/Butterfly/Crab) bir X
capa noktasi tasir; D'nin XA bacagina gore tamamlanma orani (orn. Gartley
XD=0.786, Bat XD=0.886, Butterfly XD=1.27, Crab XD=1.618) formasyonun
AYIRT EDICI ikinci kontrolüdür. `abcd_pattern.detect()`in state machine'i
SADECE 4 nokta (A-B-C-D) tutar -- X yok, yani XD orani hic HESAPLANAMAZ
/KONTROL EDILEMEZ. Bu on-ayarlar SADECE BC-retracement + CD-extension
bantlarini ayirt eder; XD kontrolu OLMADIGI icin bu, literaturdeki tam
formasyon tanimindan BILINCLI, ACIKCA belgelenmis bir sadelestirmedir --
"Gartley" / "Bat" / "Butterfly" / "Crab" etiketleri burada "AB=CD'nin bu
BC/CD bant kombinasyonuyla filtrelenmis hali" anlamina gelir, TradingView/
literaturdeki XABCD cizim araclarinin urettigi formasyonlarla birebir
AYNI sinyal kumesi degildir.

Katman disiplini: bu modul `abcd_pattern.py` DISINDA hicbir seyi import
etmez, `src.fetchers.*`/`src.db.*` HICBIR modulu import ETMEZ (calculator.py/
scorer.py/technical.py ile AYNI ilke) -- SAF VERI.
"""

from __future__ import annotations

from src.analysis.abcd_pattern import Params

# BC retracement bandi -- Carney'nin 4 formasyonun TAMAMI icin ORTAK kabul
# ettigi standart bant (Harmonic Trading Vol. 1, Bolum 3-6 formasyon
# tablolari): BC, AB'nin 0.382-0.886 katsayisi arasinda geri cekilir.
_BC_MIN = 0.382
_BC_MAX = 0.886


def _cd_bounds(k_min: float, k_max: float) -> tuple[float, float]:
    """Standart CD/BC orani araligini ([k_min, k_max]) bu kod tabaninin
    CD/AB tanimina (`cd_r = |D-C|/|A-B|`) donusturur -- modul ust notundaki
    "KRITIK matematiksel not"a bakiniz. Bilesik sinir: cd_r = k * bc_r,
    bc_r in [_BC_MIN, _BC_MAX]."""
    return (round(k_min * _BC_MIN, 4), round(k_max * _BC_MAX, 4))


HARMONIC_PRESETS: dict[str, Params] = {
    # Klasik AB=CD -- CD, AB'nin ~1.0 kati (mevcut Pine-parity varsayilan,
    # DEGISTIRILMEDI). Referans/kontrol grubu olarak karsilastirma
    # tablosunda tutulur.
    "ABCD": Params(),
    # Gartley ("222 formasyonu", H.M. Gartley 1935; Carney'nin standart
    # Fibonacci kalibrasyonu, Harmonic Trading Vol. 1 Bolum 3): BC = AB'nin
    # 0.382-0.886'si, CD = BC'nin 1.272-1.618'i (XD=0.786 XA -- X noktasi
    # bu kod tabaninda kontrol EDILEMEZ, ust nota bkz.).
    "GARTLEY": Params(
        min_bc_retrace=_BC_MIN,
        max_bc_retrace=_BC_MAX,
        use_exact_cd=False,
        cd_min_ext=_cd_bounds(1.272, 1.618)[0],
        cd_max_ext=_cd_bounds(1.272, 1.618)[1],
    ),
    # Bat (Scott Carney, 1990'lar; Harmonic Trading Vol. 1 Bolum 4): BC =
    # AB'nin 0.382-0.886'si, CD = BC'nin 1.618-2.618'i (XD=0.886 XA --
    # kontrol EDILEMEZ, ust nota bkz.).
    "BAT": Params(
        min_bc_retrace=_BC_MIN,
        max_bc_retrace=_BC_MAX,
        use_exact_cd=False,
        cd_min_ext=_cd_bounds(1.618, 2.618)[0],
        cd_max_ext=_cd_bounds(1.618, 2.618)[1],
    ),
    # Butterfly (Bryce Gilmore'dan uyarlama, Carney formalizasyonu;
    # Harmonic Trading Vol. 1 Bolum 5): BC = AB'nin 0.382-0.886'si, CD =
    # BC'nin 1.618-2.24'u (XD=1.27 XA -- kontrol EDILEMEZ, ust nota bkz.).
    "BUTTERFLY": Params(
        min_bc_retrace=_BC_MIN,
        max_bc_retrace=_BC_MAX,
        use_exact_cd=False,
        cd_min_ext=_cd_bounds(1.618, 2.24)[0],
        cd_max_ext=_cd_bounds(1.618, 2.24)[1],
    ),
    # Crab (Scott Carney, 2000; Harmonic Trading Vol. 1 Bolum 6, en genis
    # uzatmali formasyon): BC = AB'nin 0.382-0.886'si, CD = BC'nin
    # 2.24-3.618'i (XD=1.618 XA -- kontrol EDILEMEZ, ust nota bkz.).
    "CRAB": Params(
        min_bc_retrace=_BC_MIN,
        max_bc_retrace=_BC_MAX,
        use_exact_cd=False,
        cd_min_ext=_cd_bounds(2.24, 3.618)[0],
        cd_max_ext=_cd_bounds(2.24, 3.618)[1],
    ),
}

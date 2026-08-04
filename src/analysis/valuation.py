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

Faz 16.6 (kullanıcı isteği, 2026-08-04 — "bu fiyata sadece F/K olarak değil
genel bakmak gerekiyor... ünlü finansçıların sistemlerini kullanalım"):
SADECE sektöre göreli F/K/PD-DD karşılaştırması YETERSİZ bulundu (hem
peer sayısı azken güvenilmez hem TEK bir yönteme dayanıyor). Araştırılıp
eklenen İKİ ek, KLASİK ve iyi belgelenmiş yöntem:

1. **Benjamin Graham "Savunmacı Yatırımcı" Ölçütü** ("The Intelligent
   Investor", 1949/1973 rev.) — Graham, F/K × PD/DD çarpımının 22,5'i
   AŞMAMASI gerektiğini savunur (klasik örnek: F/K 15 × PD/DD 1,5 = 22,5).
   Bu çarpım "Graham Çarpanı" olarak adlandırılır; ondan türeyen "Graham
   Sayısı" (`√(22,5 × EPS × DDPS)`) savunmacı bir yatırımcının ödemesi
   gereken TAVAN fiyattır. Kritik avantaj: SEKTÖR PEER'İ GEREKTİRMEZ --
   şirketin SADECE kendi F/K ve PD/DD'sinden hesaplanır (`current_price ×
   √(22,5 / (F/K × PD/DD))` -- EPS/DDPS'yi ayrı çıkarmaya GEREK YOK, çünkü
   `current_price = F/K × EPS = PD/DD × DDPS` özdeşliğinden matematiksel
   olarak eşdeğerdir). Bu yüzden peer sayısı 0 veya 1 olan şirketlerde bile
   (örn. THYAO'nun tek peer'i PGSUS) İKİNCİ, BAĞIMSIZ bir değerleme sinyali
   sağlar.
2. **Peter Lynch PEG Oranı** ("One Up On Wall Street", 1989) — F/K'nin
   kâr BÜYÜME oranına bölünmesiyle bulunur; Lynch'in klasik kuralı: PEG<1
   büyümeye göre ucuz, PEG=1 adil değerli, PEG>1 pahalı. Büyüme oranı
   olarak `calculator.Ratios.revenue_growth_yoy_pct` (scorer.py'nin
   "Büyüme" bileşeninde ZATEN kullanılan AYNI hasılat YoY büyümesi --
   yeni bir büyüme tanımı İCAT EDİLMEDİ) kullanılır.

Üç yöntem de (sektöre göre, Graham, PEG) BAĞIMSIZ sinyaller olarak AYRI
AYRI gösterilir (tek bir sayıya sıkıştırılıp "gerçek" bir hedef fiyatmış
gibi sunulmaz) -- `verdict`/`graham_verdict`/`peg_verdict` üçü de kartta
AYRI rozetler olarak görünür, kullanıcı üç farklı, tanınmış merceğin AYNI
FİKİRDE mi OLMADIĞI MI olduğunu görebilir (bu, TEK bir yöntemden daha
DÜRÜST bir sunumdur -- yöntemler çelişirse bu da anlamlı bir bilgidir).

Faz 16.7 (kullanıcı isteği, 2026-08-04 — "Damodaran'a göre de bir değerleme
ekleyelim, Graham'la birlikte görselde yer versin"):

4. **Aswath Damodaran "İstikrarlı Büyüme (Stable Growth) FCFE" Modeli**
   ("Investment Valuation", 3. baskı, Böl. 13-14) — Damodaran'ın TAM
   yöntemi çok-dönemli FCFF projeksiyonu + WACC + terminal değer
   gerektirir; bunun girdileri (capex, vergi gideri, işletme sermayesi
   değişimi, beta için endeks/kovaryans serisi) HİÇBİR fetcher'da
   (isyatirim/sec_edgar/kap_financials) YOK ve bunları UYDURMAK Kural
   3/4'e (emin olmadığın veri kalemini varsayımla eşleme / yetersiz veride
   uydurma yapma) AÇIKÇA aykırıdır (bkz. PROJE_HAFIZASI/09_DEGERLEME_YONTEMLERI.md
   için tam gerekçe). Bunun yerine Damodaran'ın KENDİ "tek aşamalı" (stable
   growth) FCFE modeli kullanılır -- SADECE zaten güvenilir şekilde
   hesapladığımız TTM Net Kâr + ROE + hasılat büyümesinden türetilir:

       reinvestment_rate = g / ROE   (Damodaran'ın "temel büyüme" özdeşliği:
                                       sürdürülebilir g = ROE × (1-dağıtım))
       FCFE = TTM_Net_Kâr × (1 - reinvestment_rate)
       Özkaynak Değeri = FCFE × (1+g) / (r - g)      (Gordon büyüme modeli)
       r (özkaynak maliyeti) = risksiz_faiz + özkaynak_risk_primi (CAPM,
         beta=1 -- piyasa-ortalaması risk VARSAYIMI: gerçek beta için
         gereken endeks/kovaryans serisi hiçbir fetcher'da YOK).

   `g`: güncel çeyreklik hasılat YoY büyümesi DOĞRUDAN kullanılmaz -- Gordon
   modeli SONSUZ ufuk varsayar, tek bir çeyreğin oynak büyüme rakamıyla
   sonsuza ekstrapolasyon yanıltıcı olur. Damodaran'ın KENDİ "istikrarlı
   büyüme" kısıtı (hiçbir şirket sonsuza kadar EKONOMİDEN hızlı büyüyemez)
   uygulanır: `g_kullanılan = min(hasılat_büyümesi, risksiz_faiz)`.

   `risksiz_faiz`/`özkaynak_risk_primi` CANLI ÇEKİLMEZ (böyle bir veri
   kaynağı YOK) -- Graham'ın 22,5 sabiti gibi AÇIKÇA belgelenmiş, ELLE
   PERİYODİK GÜNCELLENMESİ GEREKEN makro varsayımlardır (bkz.
   `_RISK_FREE_RATE_PCT`/`_EQUITY_RISK_PREMIUM_PCT`). ROE<=0, büyüme<=0
   veya `g >= ROE` (imkânsız/>%100 reinvestment) durumlarında SESSİZCE
   `None` kalır (K4) -- var olmayan bir "adil değer" UYDURULMAZ.

   Dördü de (sektöre göre, Graham, PEG, Damodaran) BAĞIMSIZ rozetler olarak
   yan yana gösterilir, yukarıdaki "üç yöntem" ilkesi DEĞİŞMEDEN dördüne de
   uygulanır.
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

# Benjamin Graham'in KENDI, 1949'dan beri KLASIK esigi -- "The Intelligent
# Investor"da savunmaci yatirimci icin onerdigi F/K x PD/DD tavani. Bu
# SABIT, tarihsel bir deger -- bizim tercihimiz DEGIL, Graham'in KENDI
# formulu (F/K<=15 VE PD/DD<=1.5 klasik ornegi 15*1.5=22.5 verir).
_GRAHAM_MULTIPLE_CEILING = Decimal("22.5")

# Peter Lynch'in KENDI PEG kurali: PEG<1 ucuz, PEG=1 adil, PEG>1 pahali.
# +-%10 tolerans -- sektor esigiyle AYNI ilke (sinirda kalan degerler
# gurultuyle "ucuz"/"pahali" arasinda SICRAMASIN diye kucuk bir bant).
_PEG_CHEAP_CEILING = Decimal("0.9")
_PEG_EXPENSIVE_FLOOR = Decimal("1.1")

# Damodaran modelinin r (ozkaynak maliyeti) ve g-tavani (istikrarli buyume
# kisiti) girdileri -- CANLI CEKILMEZ (hicbir fetcher risksiz faiz/ozkaynak
# risk primi saglamiyor), ACIKCA belgelenmis, ELLE PERIYODIK GUNCELLENMESI
# GEREKEN makro varsayimlardir (bkz. modul ust notu Faz 16.7 + PROJE_HAFIZASI/
# 09_DEGERLEME_YONTEMLERI.md). 2026-08 itibariyla yaklasik degerler: TR 10
# yillik gosterge tahvil faizi + Turkiye ulke risk primi (TRY), ABD 10 yillik
# hazine faizi + Damodaran'in kendi yayinladigi ABD ozkaynak risk primi (USD).
# BU SABITLER ZAMANLA (enflasyon/faiz rejimi degistiginde) GECERLILIGINI
# YITIRIR -- kullanicinin arada bir guncel gosterge tahvil faiziyle
# guncellemesi beklenir.
_RISK_FREE_RATE_PCT: dict[str, Decimal] = {"TRY": Decimal("32"), "USD": Decimal("4.3")}
_EQUITY_RISK_PREMIUM_PCT: dict[str, Decimal] = {"TRY": Decimal("8"), "USD": Decimal("4.6")}


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

    # Faz 16.6: Benjamin Graham "savunmacı yatırımcı" ölçütü -- SEKTÖR
    # PEER'İ GEREKTİRMEZ, SADECE şirketin kendi F/K + PD/DD'sinden hesaplanır.
    graham_multiple: Decimal | None  # F/K x PD/DD -- Graham'ın klasik eşiği 22,5
    graham_fair_value_price: Decimal | None
    graham_upside_pct: Decimal | None
    graham_verdict: str | None  # "Graham Ölçütüne Göre Ucuz" | "...Pahalı"

    # Faz 16.6: Peter Lynch PEG oranı (F/K / büyüme%) -- büyüme verisi
    # yoksa (veya negatifse) None kalır.
    peg_ratio: Decimal | None
    peg_verdict: str | None  # "Büyümeye Göre Ucuz (PEG)" | "Makul (PEG)" | "Pahalı (PEG)"

    # Faz 16.7: Aswath Damodaran "İstikrarlı Büyüme FCFE" modeli -- SEKTÖR
    # PEER'İ GEREKTİRMEZ, TTM Net Kâr + ROE + hasılat büyümesinden (+ elle
    # belgelenmiş risksiz faiz/özkaynak risk primi varsayımından) türetilir.
    damodaran_cost_of_equity_pct: Decimal | None  # r = risksiz faiz + özkaynak risk primi
    damodaran_growth_used_pct: Decimal | None  # g = min(hasılat büyümesi, risksiz faiz)
    damodaran_fair_value_price: Decimal | None
    damodaran_upside_pct: Decimal | None
    damodaran_verdict: str | None  # "Damodaran Modeline Göre Ucuz" | "...Pahalı"


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
    growth_rate_pct: Decimal | None = None,
    ttm_net_income: Decimal | None = None,
    roe_pct: Decimal | None = None,
    share_capital: Decimal | None = None,
    currency: str = "TRY",
) -> ValuationAssessment:
    """`own_pe`/`own_pb`: taranan hissenin GUNCEL F/K, PD/DD'si (`calculator.
    compute_valuation()` ciktisi). `peer_multiples`: AYNI sektor + AYNI
    financial_group'taki DIGER (zaten taranmis) sirketlerin GUNCEL carpanlari.
    `current_price`/`price_30d_ago`/`price_90d_ago`: fiyat gecmisinden (bkz.
    src.fetchers.price_history) cagiran tarafin sectigi kapanislar -- BURADA
    SADECE yuzde degisim/oranlar hesaplanir, veri CEKILMEZ. `growth_rate_pct`:
    PEG orani icin hasilat YoY buyume yuzdesi (`calculator.Ratios.
    revenue_growth_yoy_pct` -- scorer.py'nin "Buyume" bileseniyle AYNI kaynak);
    Damodaran modelindeki `g` icin de AYNI deger kullanilir (ayri bir buyume
    tanimi ICAT EDILMEDI). `ttm_net_income`/`roe_pct`/`share_capital`: SADECE
    Damodaran modeli icin -- sirasiyla `calculator.Ratios.ttm_net_income`,
    `calculator.Ratios.roe_annualized`, cagiran tarafin zaten sahip oldugu
    pay adedi (BIST'te `share_capital`, US_GAAP'te `shares_outstanding` --
    bkz. `calculator.ValuationMetrics.share_capital`). `currency`: "TRY" |
    "USD" -- Damodaran'in risksiz faiz/ozkaynak risk primi varsayimlarindan
    hangi setin kullanilacagini secer (bkz. `_RISK_FREE_RATE_PCT`).

    Peer'ler bos VEYA hicbirinde gecerli (pozitif) F/K, PD/DD yoksa
    sektor-goreli kisim `None` kalir (K4: yeterli veri yoksa uydurma
    yapilmaz); momentum VE Graham VE Damodaran olcutu bundan BAGIMSIZ calisir
    (fiyat gecmisi/own F-K-PD-DD/TTM net kar-ROE varsa sektor peer'i olmasa
    da hesaplanir)."""
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

    # --- Benjamin Graham "savunmacı yatırımcı" ölçütü (bkz. modül üst notu) ---
    # SEKTÖR PEER'İ GEREKTİRMEZ -- sadece own_pe/own_pb'den (ikisi de pozitif
    # olmalı: zarar eden veya özkaynağı eksi bir şirkette Graham Sayısı
    # TANIMSIZDIR, karekök negatif bir sayının içine düşerdi).
    graham_multiple: Decimal | None = None
    graham_fair_value_price: Decimal | None = None
    graham_upside_pct: Decimal | None = None
    graham_verdict: str | None = None
    if own_pe is not None and own_pe > 0 and own_pb is not None and own_pb > 0:
        graham_multiple = own_pe * own_pb
        graham_verdict = (
            "Graham Ölçütüne Göre Ucuz" if graham_multiple <= _GRAHAM_MULTIPLE_CEILING else "Graham Ölçütüne Göre Pahalı"
        )
        if current_price is not None:
            # current_price = own_pe * EPS = own_pb * DDPS oldugu icin
            # current_price * sqrt(22.5 / (own_pe*own_pb)) matematiksel
            # olarak sqrt(22.5 * EPS * DDPS) (klasik Graham Sayisi formulu)
            # ile AYNIDIR -- EPS/DDPS'yi AYRI cikarmaya GEREK YOK.
            graham_fair_value_price = current_price * (_GRAHAM_MULTIPLE_CEILING / graham_multiple).sqrt()
            graham_upside_pct = _pct_change(graham_fair_value_price, current_price)

    # --- Peter Lynch PEG orani (bkz. modul ust notu) ---
    peg_ratio: Decimal | None = None
    peg_verdict: str | None = None
    if own_pe is not None and own_pe > 0 and growth_rate_pct is not None and growth_rate_pct > 0:
        peg_ratio = own_pe / growth_rate_pct
        if peg_ratio < _PEG_CHEAP_CEILING:
            peg_verdict = "Büyümeye Göre Ucuz (PEG)"
        elif peg_ratio > _PEG_EXPENSIVE_FLOOR:
            peg_verdict = "Büyümeye Göre Pahalı (PEG)"
        else:
            peg_verdict = "Büyümeye Göre Makul (PEG)"

    # --- Aswath Damodaran "İstikrarlı Büyüme (Stable Growth) FCFE" modeli
    # (bkz. modul ust notu Faz 16.7) -- SEKTOR PEER'İ GEREKTİRMEZ. ROE<=0,
    # buyume<=0 veya g>=ROE (imkansiz/>%100 reinvestment orani) durumlarinda
    # K4 geregi SESSIZCE None kalir -- UYDURULMAZ.
    damodaran_cost_of_equity_pct: Decimal | None = None
    damodaran_growth_used_pct: Decimal | None = None
    damodaran_fair_value_price: Decimal | None = None
    damodaran_upside_pct: Decimal | None = None
    damodaran_verdict: str | None = None
    risk_free_pct = _RISK_FREE_RATE_PCT.get(currency)
    equity_risk_premium_pct = _EQUITY_RISK_PREMIUM_PCT.get(currency)
    if (
        risk_free_pct is not None
        and equity_risk_premium_pct is not None
        and ttm_net_income is not None
        and ttm_net_income > 0
        and roe_pct is not None
        and roe_pct > 0
        and growth_rate_pct is not None
        and growth_rate_pct > 0
        and share_capital is not None
        and share_capital > 0
    ):
        cost_of_equity_pct = risk_free_pct + equity_risk_premium_pct
        g_pct = min(growth_rate_pct, risk_free_pct)  # istikrarli buyume kisiti
        reinvestment_rate = g_pct / roe_pct
        if reinvestment_rate < 1 and cost_of_equity_pct > g_pct:
            fcfe = ttm_net_income * (1 - reinvestment_rate)
            equity_value = fcfe * (1 + g_pct / 100) / ((cost_of_equity_pct - g_pct) / 100)
            damodaran_cost_of_equity_pct = cost_of_equity_pct
            damodaran_growth_used_pct = g_pct
            damodaran_fair_value_price = equity_value / share_capital
            if current_price is not None and current_price > 0:
                damodaran_upside_pct = _pct_change(damodaran_fair_value_price, current_price)
                damodaran_verdict = (
                    "Damodaran Modeline Göre Ucuz"
                    if damodaran_fair_value_price >= current_price
                    else "Damodaran Modeline Göre Pahalı"
                )

    has_data = (
        bool(diffs)
        or price_change_1m_pct is not None
        or price_change_3m_pct is not None
        or graham_multiple is not None
        or peg_ratio is not None
        or damodaran_fair_value_price is not None
    )

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
        graham_multiple=graham_multiple,
        graham_fair_value_price=graham_fair_value_price,
        graham_upside_pct=graham_upside_pct,
        graham_verdict=graham_verdict,
        peg_ratio=peg_ratio,
        peg_verdict=peg_verdict,
        damodaran_cost_of_equity_pct=damodaran_cost_of_equity_pct,
        damodaran_growth_used_pct=damodaran_growth_used_pct,
        damodaran_fair_value_price=damodaran_fair_value_price,
        damodaran_upside_pct=damodaran_upside_pct,
        damodaran_verdict=damodaran_verdict,
    )

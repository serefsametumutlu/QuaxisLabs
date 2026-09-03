"""Türkçe etiket sözlükleri — `renderer.py`/`table.py`/`report.py` bunları
kullanır, kendi metin sabitlerini taşımaz (tek doğru kaynak burası)."""

from __future__ import annotations

STATE_TR: dict[str, str] = {
    "pending": "BEKLEMEDE",
    "active": "AKTİF",
    "confirmed": "TAMAMLANDI",
    "invalidated": "GEÇERSİZ",
    "completed": "TAMAM",
    "expired": "SÜRESİ DOLDU",
}

STYLE_TR: dict[str, str] = {
    "resistance": "Direnç",
    "support": "Destek",
    "resistance_zone": "Direnç Bölgesi",
    "support_zone": "Destek Bölgesi",
    "range_box": "Konsolidasyon",
    "poc": "POC",
    "value_area": "Değer Alanı",
    "fib_retracement": "Fib Geri Çekilme",
    "fib_extension": "Fib Uzatma",
    "bullish": "Boğa",
    "bearish": "Ayı",
    "y_holding": "Tutulan Dönem",
    "x_holding": "Tutulan Dönem",
    "golden_zone": "Altın Bölge",
    "golden_zone_alt": "Alt Bölge",
    "demand": "Talep",
    "supply": "Arz",
    "demand_broken": "Talep (Kırık)",
    "supply_broken": "Arz (Kırık)",
    "channel": "Kanal",
    "channel_current": "Güncel Kanal",
    "channel_frozen": "Dondurulmuş Kanal",
    "pattern_boundary": "Sınır/Boyun",
    "pattern_target": "Hedef",
    "pattern_pole": "Direk",
    # 2026-09-04: "Konsolidasyon" TEK kullanıcısı `flag_pennant.py` --
    # kullanıcı mockup'taki "BAYRAK" etiketiyle karşılaştırınca gerçek
    # sistemin jenerik ismini fark etti ("alakası yok" geri bildiriminin
    # bir parçası). Bayrak/flama ayrımı ÇALIŞMA ZAMANINDA belli olduğu
    # (Box'ın kendisi tek bir stil taşıyor, hangi şekil olduğunu bilmiyor)
    # için ikisini birden kapsayan tek bir etiket kullanılıyor.
    "pattern_consolidation": "Bayrak/Flama",
    "ma_8": "MA (Hızlı)",
    "ma_21": "MA (Orta-Hızlı)",
    "ma_55": "MA (Orta-Yavaş)",
    "ma_200": "MA (Yavaş)",
    "pattern_hologram": "Formasyon Alanı",
    # 2026-09-02: `trend.breakouts`in jenerik kırılım seviyeleri (Level) bu
    # iki stili kullanıyordu ama sözlükte karşılığı yoktu — grafikte çıplak
    # "broken_up"/"broken_down" metni olarak sızıyordu (gerçek ISCTR
    # verisiyle bulunan bir durum).
    "broken_up": "Kırılım (Yukarı)",
    "broken_down": "Kırılım (Aşağı)",
    "pending": "Beklemede",
}

DIRECTION_TR: dict[str, str] = {"long": "AL", "short": "SAT", "neutral": "NÖTR"}

INDICATOR_CATEGORY_TR: dict[str, str] = {
    "harmonics": "Harmonik Formasyon",
    "structure": "Fiyat Yapısı",
    "pair": "Pair (Rölatif Momentum)",
    "trend": "Trend",
    "patterns": "Klasik Formasyon",
    "momentum": "Momentum/Alfa Sıralaması",
}

# 2026-09-01: dashboard'un sinyal tablosu eskiden `İndikatör` sütununda ham
# katalog kimliğini (`structure.golden_zone`) gösteriyordu — kullanıcı bunu
# "Tarama Reçeteleri" mockup turunda AÇIKÇA reddetti ("tam net ismi
# yazmalı"), mockup'ta `INDICATOR_TR` sözlüğüyle çözüldü. Bu, o çözümün
# gerçek CATALOG'a (bkz. `tlab/indicators/bootstrap.py`) karşılık gelen
# birebir hâli — 8 harmonik ekolü, mockup'ın tek "Harmonik Formasyon"
# genellemesinin AKSİNE, AYRI AYRI adlandırılır (gerçek dashboard'da 8 satır
# yan yana görünebiliyor, ayırt edilebilir olmaları gerekiyor).
INDICATOR_DISPLAY_TR: dict[str, str] = {
    "harmonic.carney": "Gartley/Bat/Crab Taraması (Carney)",
    "harmonic.cypher": "Cypher Formasyonu (Oglesbee)",
    "harmonic.five_zero": "5-0 Formasyonu (Duddella)",
    "harmonic.gilmore": "Gartley/Butterfly Taraması (Gilmore)",
    "harmonic.navarro200": "200% Formasyonu (Navarro)",
    "harmonic.nenstar": "Gartley/Butterfly + EMA Teyidi (Kerkez-Nenstar)",
    "harmonic.pesavento": "Gartley/Butterfly Taraması (Pesavento)",
    "harmonic.three_drives": "Three Drives Formasyonu",
    "momentum.alpha_rank": "Alfa Sıralaması (Evren-Geneli)",
    "momentum.momentum_rank": "Momentum Sıralaması (Evren-Geneli)",
    "pair.relative_momentum": "Pair Trading — Rölatif Momentum",
    "pair.vol_harvest": "Pair Trading — Oynaklık Hasadı",
    "patterns.broadening": "Genişleyen Formasyon (Megafon)",
    "patterns.double_top_bottom": "Çift Tepe / Çift Dip",
    "patterns.flag_pennant": "Bayrak / Flama Formasyonu",
    "patterns.head_shoulders": "Omuz-Baş-Omuz / TOBO",
    "patterns.triangle": "Üçgen Formasyonu",
    "patterns.wedge": "Daralan Takoz Formasyonu",
    "structure.golden_zone": "Altın Bölge (Fibonacci 0.618–0.786)",
    "structure.price_structure": "Fiyat Yapısı — Destek/Direnç, Hacim Profili",
    "structure.supply_demand": "Arz/Talep Bölgeleri",
    "structure.swing_fib_abcd": "Swing Yapısı + Fibonacci AB=CD",
    "structure.report": "Birleşik Yapı Raporu",
    "trend.breakouts": "Çoklu Kırılım Taraması",
    "trend.ewmac": "EWMAC Trend Forecast",
    "trend.ma_systems": "Hareketli Ortalama Sistemi",
    "trend.weekly_channel": "Haftalık Regresyon Kanalı",
    "confluence": "Dönüş Haritası (Confluence)",
}


# 2026-09-02: kullanıcı web arayüzünde harmonik sinyallerin ekol adına göre
# (Carney/Pesavento/Gilmore...) değil, herkesin tanıdığı PATERN ŞEKLİNE göre
# (Gartley/Bat/Crab/Kelebek...) etiketlenmesini istedi — "carney pesavento
# diye ayırmak yerine abcd gartley crab butterfly bat gibi ayırsak daha
# güzel olmaz mı". Alttaki motor mimarisi ekol-bazlı KALIYOR (bkz. CLAUDE.md
# "Harmonik Formasyon Tarayıcı" — 8 ekol birbirinden bağımsız, "ekoller
# birbirini import etmez") ama her `Signal.payload["pattern_name"]` zaten
# ekolden BAĞIMSIZ, gerçek patern şeklini taşıyor (`TrackingConfig.
# pattern_name`, bkz. `schools/*.py::name=`) — bu sözlük SADECE o değeri
# okunabilir Türkçe'ye çeviren bir GÖRÜNTÜLEME katmanı, yeni bir hesap değil.
PATTERN_NAME_TR: dict[str, str] = {
    "gartley": "Gartley",
    "bat": "Bat (Yarasa)",
    "crab": "Crab (Yengeç)",
    "deep_crab": "Deep Crab (Derin Yengeç)",
    "butterfly": "Kelebek (Butterfly)",
    "shark": "Shark (Köpekbalığı)",
    "cypher": "Cypher",
    "nenstar": "Gartley + EMA Teyidi",
    "navarro200": "200% (Navarro)",
    "five_zero": "5-0 Formasyonu",
    "three_drives_1272": "Three Drives (1.272)",
    "three_drives_1618": "Three Drives (1.618)",
}


def tr_pattern_name(pattern_name: str) -> str:
    return PATTERN_NAME_TR.get(pattern_name, pattern_name)


def tr_indicator(indicator: str) -> str:
    return INDICATOR_DISPLAY_TR.get(indicator, indicator)


def tr_state(state: str) -> str:
    return STATE_TR.get(state, state.upper())


def tr_style(style: str) -> str:
    return STYLE_TR.get(style, style)


def tr_direction(direction: str) -> str:
    return DIRECTION_TR.get(direction, direction.upper())


# ============================================================
# OKUMA REHBERİ + AL SİNYALİ AÇIKLAMALARI (2026-09-01)
# ============================================================
# Gösterge türü başına STATİK metin (bir sinyal ÖRNEĞİ için değil — o
# göstergenin MEKANİĞİ için, "Grafik Stil Vitrini" mockup'ındaki
# SCENE_NOTES içeriğinin gerçek CATALOG anahtarlarına uyarlanmış hâli).
# `report_text.py`/`quant_report.py`'nin izlediği ilkeyle AYNI: bu metinler
# Plotly figürüne GÖMÜLMEZ, dashboard'da grafiğin yanında/altında ayrı bir
# metin bloğu olarak gösterilir ("karmaşıklık grafiğe değil yanına").
SignalReading = dict[str, str]  # anahtarlar: watch, measures, values, signal

_HARMONIC_READING: SignalReading = {
    "watch": (
        "X-A-B-C harflerini takip eden zikzak çizgiyi ve C'den sonra "
        'işaretlenen "Hedef Bölge (PRZ)" bandını izle.'
    ),
    "measures": (
        "X→A→B→C hareketlerinin birbirine oranı belirli standart sayılara "
        "(0.618, 0.786, 1.272 gibi) yakınsa, D noktasının nereye düşeceği "
        "matematiksel olarak tahmin edilebilir — PRZ bandı bu tahmindir."
    ),
    "values": (
        "Bandın İÇİNDE olmak = fiyat dönüş bölgesinde, henüz sinyal değil. "
        "Bandın (invalidasyon oranının) ÖTESİNE geçmek = formasyon "
        "bozuldu, artık geçersiz demektir."
    ),
    "signal": (
        "Şu 2 şart birden gerçekleştiğinde AL sinyali oluşur: (1) fiyat PRZ "
        "bandının İÇİNE girer, (2) o bantta en az 1 YEŞİL mumla (kapanış > "
        "açılış) tepki verilir — okulun onay politikasına göre bu birkaç "
        "bar sürebilir. Bant henüz hiç dokunulmadıysa durum AKTİF/BEKLEMEDE, "
        "henüz AL yoktur."
    ),
}

_PATTERNS_CLASSIC_HS: SignalReading = {
    "watch": (
        "Hologram (şeffaf) dolgunun üst sınırındaki Boyun Çizgisi'ni ve o "
        "çizginin kesildiği Kırılım noktasını izle."
    ),
    "measures": (
        "TOBO/OBO: fiyatın üç dip/tepe yaptığı, ortadaki uç noktanın (Baş) "
        "diğer ikisinden (Omuzlar) belirgin şekilde daha derin/yüksek "
        "olduğu bir dönüş formasyonu."
    ),
    "values": (
        "Baş ile boyun çizgisi arasındaki mesafe, kırılım noktasından "
        "yukarı (TOBO) veya aşağı (OBO) taşınarak ölçülü-hareket hedefini "
        "belirler."
    ),
    "signal": (
        "AL sinyali İKİ adımda değerlendirilir: (1) Kırılım — fiyat boyun "
        "çizgisini kapanışla keser. (2) Onay (opsiyonel ama güçlendirici) — "
        "birkaç bar sonra fiyat geri gelip çizgiye DOKUNUR ama ALTINA "
        "KAPANMAZ (retest tuttu). Hedef fiyata ulaşınca formasyon "
        "TAMAMLANDI sayılır."
    ),
}

_PATTERNS_FLAG: SignalReading = {
    "watch": (
        "Sert bir hareketin (Direk) ardından oluşan dar, hologramla "
        "işaretli konsolidasyon kanalını ve kanalın kırıldığı noktayı izle."
    ),
    "measures": (
        "Bir trend hareketinin (direk) kısa bir soluklanma (bayrak/flama) "
        "sonrası aynı yönde devam edip etmeyeceğini ölçer."
    ),
    "values": (
        "Kanal ne kadar dar ve kısa sürerse, devam ihtimali o kadar "
        "güçlü kabul edilir. Kanalın direğin ters yönünde kırılması "
        "formasyonu geçersiz kılar."
    ),
    "signal": (
        "AL sinyali, fiyat konsolidasyon kanalını direkle AYNI yönde "
        "kapanışla kırdığında oluşur. Hedef, direğin boyu kadar kırılım "
        "noktasından yukarı taşınarak hesaplanır."
    ),
}

_PATTERNS_WEDGE_TRIANGLE: SignalReading = {
    "watch": (
        "Daralan iki trend çizgisinin (üst ve alt sınır) birbirine "
        "yaklaştığı tepe noktasını (apex) ve fiyatın hangi yönde kırdığını "
        "izle."
    ),
    "measures": (
        "İki yakınsayan trend çizgisinin eğim oranını ölçer — takozda "
        "(wedge) her iki çizgi de aynı yöne eğik, üçgende (triangle) biri "
        "yatay/nötr olabilir."
    ),
    "values": (
        "Fiyat, apex'e yaklaştıkça sıkışır; kırılımın yönü ÖNCEDEN "
        "belirlenmez (özellikle simetrik üçgende), yalnızca kırılım anında "
        "netleşir."
    ),
    "signal": (
        "AL sinyali, fiyat üst sınır çizgisini kapanışla YUKARI kestiğinde "
        "oluşur. Apex'e çok yaklaşılmadan (formasyon süresinin çoğu "
        "geçmeden) oluşan erken kırılımlar daha az güvenilir kabul edilir."
    ),
}

_PATTERNS_DOUBLE: SignalReading = {
    "watch": (
        "Aynı seviyeye iki kez yaklaşıp geri dönen fiyatı ve aradaki "
        "boyun (dip/tepe) seviyesinin kırılıp kırılmadığını izle."
    ),
    "measures": (
        "Fiyatın aynı seviyede iki kez durup geri dönmesini (çift tepe = "
        "direnç, çift dip = destek) ölçer — bu seviyenin güçlü bir arz/"
        "talep duvarı olduğunun göstergesi."
    ),
    "values": (
        "İki tepe/dip arasındaki BOYUN seviyesi kilit noktadır: kırılana "
        "kadar formasyon yalnızca 'aday', kırıldıktan sonra geçerli "
        "sayılır."
    ),
    "signal": (
        "AL sinyali (çift dip için), fiyat iki dip arasındaki boyun "
        "seviyesini kapanışla YUKARI kestiğinde oluşur. Hedef, dip ile "
        "boyun arasındaki mesafenin boyun seviyesinden yukarı taşınmasıyla "
        "hesaplanır."
    ),
}

_PATTERNS_BROADENING: SignalReading = {
    "watch": (
        "Birbirinden UZAKLAŞAN (daralmayan) iki trend çizgisini ve "
        "fiyatın son olarak hangi sınırda olduğunu izle."
    ),
    "measures": (
        "Volatilitenin arttığı, üst ve alt sınırların birbirinden "
        "GENİŞLEDİĞİ bir formasyondur (takozun tersi) — kararsız/gergin "
        "bir piyasanın işareti."
    ),
    "values": (
        "Bu formasyon güvenilirliği düşük kabul edilir çünkü kırılım "
        "yönü klasik daralan formasyonlar kadar öngörülebilir değildir; "
        "temkinli yaklaşılmalıdır."
    ),
    "signal": (
        "AL sinyali, fiyat üst sınır çizgisini kapanışla kestiğinde "
        "değerlendirilir; ancak genişleyen yapı gereği yanlış kırılım "
        "riski diğer formasyonlara göre daha yüksektir."
    ),
}

_STRUCTURE_REPORT: SignalReading = {
    "watch": (
        "Hacim profilindeki en YOĞUN (POC) fiyat seviyesini ve destek/"
        "direnç kutularının çakıştığı bölgeleri izle."
    ),
    "measures": (
        "Fiyatın en çok işlem gördüğü seviyeleri (POC/VAH/VAL), trend "
        "çizgileriyle kesişen kırılma noktalarını ve swing yapısını "
        "(HH/HL/LH/LL) birlikte özetler."
    ),
    "values": (
        "Fiyat POC'un ÜSTÜNDEYSE görece pahalı, ALTINDAYSA görece ucuz "
        "sayılır. VAH/VAL dışına çıkmak genelde güçlü bir hareket "
        "işaretidir."
    ),
    "signal": (
        "İki ayrı AL senaryosu izlenir: (A) fiyat mavi destek bölgesine "
        "girip içinde yeşil bir mumla tepki verirse. (B) fiyat kırmızı "
        "direnç çizgisini kapanışla YUKARI keserse (kırılım)."
    ),
}

_STRUCTURE_PRICE: SignalReading = {
    "watch": (
        "Sağdaki hacim profili panelindeki en uzun çubuğun (POC) olduğu "
        "seviyeyi ve destek/direnç kutularını izle."
    ),
    "measures": (
        "Hangi FİYAT seviyesinde en çok işlem yapıldığını (POC/VAH/VAL) ve "
        "trend çizgisi kırılımlarını ölçer."
    ),
    "values": "POC'a yakın fiyat = denge; VAH üstü = pahalı, VAL altı = ucuz bölge olarak okunur.",
    "signal": (
        "AL sinyali, fiyat mavi destek bölgesine girip yeşil bir mumla "
        "tepki verdiğinde, veya kırmızı direnç çizgisini kapanışla yukarı "
        "kestiğinde değerlendirilir."
    ),
}

_STRUCTURE_SWING_FIB: SignalReading = {
    "watch": (
        "Sağdaki fib merdiveninde altın rengi (0.618/0.786) çizgileri ve "
        'yeşil kesikli "D (hedef)" çizgisini izle.'
    ),
    "measures": (
        "Son A→B→C swing hareketinin, C'den itibaren nereye kadar (D) "
        "uzayabileceğini AB=CD simetrisiyle tahmin eder."
    ),
    "values": (
        "Fiyat altın bölgeye (0.618–0.786) girerse tepki ihtimali "
        "istatistiksel olarak en yüksektir; D hedefine ulaşırsa formasyon "
        "tamamlanmış sayılır."
    ),
    "signal": (
        "Fiyat D hedef seviyesine yaklaşıp oradan yukarı dönen bir mum "
        "(uzun alt fitilli veya güçlü yeşil kapanış) oluşturduğunda AL "
        "değerlendirilir."
    ),
}

_STRUCTURE_GOLDEN_ZONE: SignalReading = {
    "watch": "Altın rengi bandın İÇİNDEKİ ilk tepki mumunu izle.",
    "measures": "Son yükselişin/düşüşün 0.618–0.786 Fibonacci geri çekilmesini ölçer.",
    "values": (
        "Bandın İÇİNDE kapanış = potansiyel destek. Bandın ALTINA (tamamen) "
        "kapanış = bölge geçersiz demektir."
    ),
    "signal": (
        "AL sinyali, fiyat altın banda girip önceki mumdan daha yüksek "
        "kapanan bir mumla yukarı döndüğünde oluşur (REAKSİYON işareti)."
    ),
}

_STRUCTURE_SUPPLY_DEMAND: SignalReading = {
    "watch": "Yeşil (talep) kutusuna değip geri dönen son mumu izle.",
    "measures": (
        "Fiyatın büyük bir hareket ÖNCESİ sıkışıp kaldığı dar "
        "konsolidasyon bölgesini (taban) işaretler."
    ),
    "values": (
        "Kutunun İÇİNDE kapanış = potansiyel giriş bölgesi. Kutunun "
        "ALTINA kapanış = bölge kırılmış (artık geçersiz) demektir."
    ),
    "signal": (
        "AL sinyali, fiyat talep kutusuna girip önceki mumdan yüksek "
        "kapanan bir mumla yukarı döndüğünde oluşur."
    ),
}

_TREND_BREAKOUTS: SignalReading = {
    "watch": (
        "Fiyatın hangi türde bir seviyeyi (trend çizgisi, aralık, swing, "
        "MA, Donchian, Bollinger, kanal) kestiğini izle."
    ),
    "measures": (
        "~20 farklı kırılım türünü tarar ve her biri için hacim/gövde/"
        "mesafeye dayalı bir kalite skoru üretir."
    ),
    "values": (
        "Yüksek kalite skoru = güçlü hacim + geniş gövde + net mesafe ile "
        "gerçekleşmiş bir kırılım demektir."
    ),
    "signal": (
        "AL sinyali, `confirm_bars` kadar ardışık bar boyunca kapanışın "
        "seviyenin YUKARISINDA kaldığı anda oluşur; kırılımdan sonra fiyat "
        "geri gelip seviyeyi test edip tutarsa (retest_hold) sinyal "
        "güçlenir, tutmazsa (false_break) geçersiz sayılır."
    ),
}

_TREND_WEEKLY_CHANNEL: SignalReading = {
    "watch": (
        "Güncel kanalın ALT sınırına değen mumları ve alttaki 'Kanal İçi "
        "Pozisyon' çizgisinin 0'a yaklaşmasını izle."
    ),
    "measures": (
        "Fiyatın haftalık regresyon kanalının neresinde olduğunu "
        "(0=alt bant, 1=üst bant) ölçer."
    ),
    "values": (
        "0'a yakın = kanal dibi (ucuz), 1'e yakın = kanal tepesi (pahalı); "
        "1'in üstüne kapanış = yukarı kırılım."
    ),
    "signal": (
        "Kanal İçi Pozisyon 0'a yakınken yukarı dönmeye başlarsa AL "
        "değerlendirilir; fiyat üst çizgiyi kapanışla keserse bu ayrı, "
        "momentum tabanlı bir AL sinyalidir."
    ),
}

_PAIR_RELATIVE_MOMENTUM: SignalReading = {
    "watch": "Z-Skoru çizgisinin üst (+2) veya alt (-2) sınıra DOKUNUP geri dönüşünü izle.",
    "measures": (
        "İki hissenin fiyat farkının kendi normal ortalamasından kaç "
        "standart sapma uzakta olduğunu ölçer."
    ),
    "values": (
        "Z-Skoru 0 = normal ilişki. +2 = Y, X'e göre aşırı pahalı. "
        "-2 = Y, X'e göre aşırı ucuz."
    ),
    "signal": (
        "AL sinyali, Z-Skoru ÖNCE ±2 sınırını geçip SONRA sınırın İÇİNE "
        "geri döndüğü anda oluşur (dönüş onaylı) — sınırı geçtiği an "
        "değil, geri döndüğü an."
    ),
}

_PAIR_VOL_HARVEST: SignalReading = {
    "watch": (
        "Hedef Ağırlık basamak çizgisinin ne zaman bir sonraki basamağa "
        "sıçradığını (rebalans noktalarını) izle."
    ),
    "measures": (
        "Z-Skoruna göre portföyün iki hisse arasındaki ağırlığını sürekli "
        "(0–1 arası) ayarlar, ikili AL/SAT değil."
    ),
    "values": (
        "Düz kalan bir ağırlık çizgisi = sistem 'duraklatıldı' "
        "(kointegrasyon bozuldu) demektir."
    ),
    "signal": (
        "Klasik anlamda tek bir AL anı yoktur — her rebalans noktası "
        "küçük bir işlemdir: ağırlık yukarı sıçrarsa Y'den biraz daha "
        "alınır, aşağı sıçrarsa X'e geçilir."
    ),
}

_MOMENTUM_ALPHA_RANK: SignalReading = {
    "watch": "α (alfa) çizgisinin ±2 anlamlılık bandının DIŞINA taştığı noktaları izle.",
    "measures": (
        "Hissenin endeksten arındırılmış (beta ile düzeltilmiş) fazladan "
        "getirisini ve bunun güvenilirliğini ölçer."
    ),
    "values": (
        "α bandın ÜSTÜNDE ve pozitifse endeksi kalıcı şekilde yeniyor "
        "demektir; β=1 civarı aynı riski taşıdığını gösterir."
    ),
    "signal": (
        "Bu bir sıralama aracıdır: rank_pct en iyi dilime (top_pct) "
        "girdiğinde `alpha_entry`, çıktığında `alpha_exit` sinyali üretir."
    ),
}

_MOMENTUM_MOMENTUM_RANK: SignalReading = {
    "watch": (
        "RS (Göreli Güç) çizgisinin yeni zirve yapıp yapmadığını ve ufuk "
        "bazlı momentum çubuklarının rengini izle."
    ),
    "measures": (
        "Hissenin piyasaya göre göreli gücünü ve farklı zaman "
        "ufuklarındaki momentum tutarlılığını ölçer."
    ),
    "values": (
        "RS yükseliyorsa hisse endeksten güçlü demektir; çubukların çoğu "
        "pozitifse momentum tüm ufuklarda tutarlıdır."
    ),
    "signal": (
        "`rs_breakout`: RS çizgisi trailing 252-bar zirvesini yeni geçtiğinde. "
        "`momentum_top_entry`: rank_pct en iyi dilime girdiğinde."
    ),
}

_TREND_EWMAC: SignalReading = {
    "watch": "Birleşik forecast çizgisinin sıfır çizgisini yukarı/aşağı kestiği anı izle.",
    "measures": (
        "Farklı hızlardaki hareketli ortalama farklarının ortalamasını "
        "alıp -20/+20 arasına ölçekler."
    ),
    "values": (
        "+20'e yakın = güçlü yükseliş trendi; -20'ye yakın = güçlü "
        "düşüş trendi; 0 civarı = trend yok."
    ),
    "signal": "`ewmac_bullish`: forecast sıfırdan yukarı geçer. `ewmac_bearish`: tam tersi.",
}

_TREND_MA_SYSTEMS: SignalReading = {
    "watch": (
        "MA çizgilerinin sıralanışını (hangisi en üstte) ve bant "
        "genişliği çizgisinin daralıp daralmadığını izle."
    ),
    "measures": (
        "Hareketli ortalamaların birbirine göre dizilimini (ribbon) ve "
        "daralıp genişlemesini (sıkışma/genişleme) ölçer."
    ),
    "values": (
        "Kısa vadeli MA en üstte, uzun vadeli en alttaysa 'boğa dizilimi'; "
        "bant daralması patlama öncesi sıkışmadır."
    ),
    "signal": (
        "`squeeze_expansion`: bant sıkışmadan çıktığında. `bull_stack_entry`: "
        "dizilim boğaya döndüğünde. `ma_cross_*_bull`: kısa MA uzun MA'yı "
        "yukarı kestiğinde."
    ),
}

_CONFLUENCE: SignalReading = {
    "watch": (
        'Fiyatın altında üst üste binen kutuların en KOYU/yoğun olduğu '
        'bandı ve "DİPTE OLASI: X%" rozetini izle.'
    ),
    "measures": (
        "Birden fazla göstergenin (golden zone, arz-talep, harmonik PRZ, "
        "kanal dibi) aynı fiyat bandında üst üste gelme sıklığını ölçer."
    ),
    "values": "Yüzde ve kaynak sayısı ne kadar yüksekse, o bant o kadar güçlü bir destek adayıdır.",
    "signal": (
        "AL sinyali, fiyat bu yoğun bant içine girip içinde bir yeşil "
        "dönüş mumu oluşturduğunda değerlendirilir — birden fazla "
        "yöntemin oybirliği aranır."
    ),
}

SIGNAL_READING_TR: dict[str, SignalReading] = {
    "harmonic.carney": _HARMONIC_READING,
    "harmonic.pesavento": _HARMONIC_READING,
    "harmonic.gilmore": _HARMONIC_READING,
    "harmonic.cypher": _HARMONIC_READING,
    "harmonic.nenstar": _HARMONIC_READING,
    "harmonic.navarro200": _HARMONIC_READING,
    "harmonic.five_zero": _HARMONIC_READING,
    "harmonic.three_drives": _HARMONIC_READING,
    "structure.report": _STRUCTURE_REPORT,
    "structure.price_structure": _STRUCTURE_PRICE,
    "structure.swing_fib_abcd": _STRUCTURE_SWING_FIB,
    "structure.golden_zone": _STRUCTURE_GOLDEN_ZONE,
    "structure.supply_demand": _STRUCTURE_SUPPLY_DEMAND,
    "trend.breakouts": _TREND_BREAKOUTS,
    "trend.weekly_channel": _TREND_WEEKLY_CHANNEL,
    "trend.ewmac": _TREND_EWMAC,
    "trend.ma_systems": _TREND_MA_SYSTEMS,
    "patterns.wedge": _PATTERNS_WEDGE_TRIANGLE,
    "patterns.triangle": _PATTERNS_WEDGE_TRIANGLE,
    "patterns.head_shoulders": _PATTERNS_CLASSIC_HS,
    "patterns.flag_pennant": _PATTERNS_FLAG,
    "patterns.double_top_bottom": _PATTERNS_DOUBLE,
    "patterns.broadening": _PATTERNS_BROADENING,
    "pair.relative_momentum": _PAIR_RELATIVE_MOMENTUM,
    "pair.vol_harvest": _PAIR_VOL_HARVEST,
    "momentum.alpha_rank": _MOMENTUM_ALPHA_RANK,
    "momentum.momentum_rank": _MOMENTUM_MOMENTUM_RANK,
    "confluence": _CONFLUENCE,
}


def signal_reading(indicator: str) -> SignalReading | None:
    """`indicator` (CATALOG anahtarı, ya da "structure.report"/"confluence")
    için okuma rehberi + AL sinyali metnini döndürür; bilinmeyen anahtar
    için `None` (çağıran taraf bloğu hiç göstermemeli)."""
    return SIGNAL_READING_TR.get(indicator)

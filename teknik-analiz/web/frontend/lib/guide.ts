// "Grafik Stil Vitrini" artifact'ındaki "Nasıl Okunur" (chart-note) +
// "AL sinyali ne zaman oluşur" (signal-box) bölümlerinin statik Türkçe
// karşılığı — LLM çağrısı YOK (bu bir referans rehberi, sembole özel yorum
// için `AiReportPanel` var). İndikatör KATEGORİSİNE göre gruplanmış
// (`bootstrap.py::CATALOG`'un `category` alanıyla aynı sözleşme).

export interface GuideEntry {
  whatItMeasures: string;
  whereToLook: string;
  buySignal: string;
}

export const GUIDE_BY_CATEGORY: Record<string, GuideEntry> = {
  harmonic: {
    whatItMeasures:
      "X-A-B-C-D beş noktalı bir fiyat geometrisi — her bacağın bir öncekine oranı (Fibonacci) belirli bir bant içindeyse bu bir 'harmonik formasyon' sayılır.",
    whereToLook:
      "Üçgenlerin birleştiği D noktası ve etrafındaki 'PRZ' (Potansiyel Dönüş Bölgesi) bandına bakın — fiyat oraya yaklaştıkça formasyon 'aktif', bandın içine girip tepki verirse 'onaylandı' sayılır.",
    buySignal:
      "Formasyon türü boğa yönlüyse (ör. Gartley/Bat/Crab) VE fiyat PRZ bandına girip yukarı tepki verirse — grafikte 'D: ... [TAMAMLANDI]' etiketiyle işaretlenir.",
  },
  structure: {
    whatItMeasures:
      "Fiyatın kendi geçmişine göre yapısı — swing (HH/HL/LH/LL) dizisi, destek/direnç bölgeleri, hacim profili (POC/VAH/VAL) ve trend çizgileri.",
    whereToLook:
      "Sağdaki hacim profili panelinde en kalın çubuk POC (en çok işlem gören fiyat); yeşil 'Destek' ve kırmızı 'Direnç' kutuları fiyatın sık sık tepki verdiği bölgeler.",
    buySignal:
      "Fiyat bir destek bölgesine/POC'a yaklaşıp tepki verirse, VEYA bir direnç bölgesini hacimle kırıp üstünde kapanırsa (grafikte 'Kırılım' etiketiyle işaretlenir).",
  },
  patterns: {
    whatItMeasures:
      "Klasik grafik formasyonları (omuz-baş-omuz, takoz, bayrak, çift tepe/dip, genişleyen üçgen) — fiyatın belirli bir geometrik sınırı kırmasıyla tetiklenir.",
    whereToLook:
      "Formasyonun sınır çizgilerine (boyun çizgisi/takoz kenarları) ve kırılım sonrası hedef seviyesine bakın — yalnızca ONAYLANMIŞ (confirmed/tamamlandı) formasyonlar gösterilir, denemeler elenir.",
    buySignal:
      "Boğa yönlü bir formasyon (ör. TOBO, yükselen takoz, boğa bayrağı) sınırını yukarı kırıp kapanış yaparsa — marker'da 'ONAY' rengiyle (accent) vurgulanır.",
  },
  pair: {
    whatItMeasures:
      "İki hissenin (Y/X) birbirine göre relatif fiyatı (spread) — Z-skoru bu spread'in kendi ortalamasından kaç standart sapma uzakta olduğunu ölçer.",
    whereToLook:
      "Alt paneldeki Z-skor çizgisine ve üst/alt eşik çizgilerine bakın — Z aşırı bir eşiği aşıp GERİ DÖNDÜĞÜNDE sinyal üretilir (eşiği aşan bar değil, dönüş barı).",
    buySignal:
      "Z-skoru alt eşiğin (ör. -2.0) altına inip yeniden içeri döndüğünde — o an ucuz kalan taraf (Y ya da X) 'AL' sinyali alır, sermaye o tarafa kaydırılır.",
  },
  trend: {
    whatItMeasures:
      "Trend yönü ve gücü — kırılım seviyeleri (kanal/Donchian/Bollinger), hareketli ortalama sistemleri veya EWMAC (üstel ağırlıklı momentum) ile ölçülür.",
    whereToLook:
      "Kanalın alt/üst sınırına, hareketli ortalamaların sıralanışına (fiyat üstlerinde mi altlarında mı) ya da EWMAC eğrisinin sıfır çizgisine göre konumuna bakın.",
    buySignal:
      "Fiyat bir direnç/kanal üstünü hacimle kırarsa, MA'lar yukarı sıralanırsa (bull_stack), veya EWMAC sıfırın üstüne geçerse — yön yukarı kabul edilir.",
  },
  momentum: {
    whatItMeasures:
      "Bir hissenin TÜM evrene (ör. BIST) göre göreli performansı — alpha (piyasa hareketinden bağımsız fazla getiri) veya momentum (12-1 gibi ufuk bazlı getiri sıralaması).",
    whereToLook:
      "Sıralama yüzdesine (rank_pct) bakın — en düşük yüzde en iyi performansı gösterir; α-t istatistiği ±2 bandının dışındaysa istatistiksel olarak anlamlı kabul edilir.",
    buySignal:
      "Sembol evrenin en iyi performans gösteren dilimine (ör. ilk %20) girerse VE trend/momentum skoru pozitifse — 'giriş' sinyali üretilir.",
  },
};

export const DEFAULT_GUIDE: GuideEntry = {
  whatItMeasures: "Bu gösterge, fiyat verisinden türetilmiş bir teknik analiz sinyali üretir.",
  whereToLook: "Grafikteki çizgi/kutu/işaretlere ve renk koduna (yeşil=boğa, kırmızı=ayı) bakın.",
  buySignal: "Sinyal metnindeki durum etiketine (ör. 'ONAY'/'TAMAMLANDI') bakın.",
};

export function guideFor(indicator: string): GuideEntry {
  const category = indicator.split(".")[0];
  return GUIDE_BY_CATEGORY[category] ?? DEFAULT_GUIDE;
}

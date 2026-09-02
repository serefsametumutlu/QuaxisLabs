"use client";

import { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api";

interface Props {
  symbol: string;
  tf: string;
  indicator: string;
  market: string;
  theme: string;
}

/** Kullanıcı isteği: grafik TradingView tarzı etkileşimli bir JS widget'ı
 * DEĞİL, Python'ın (`tlab/viz/renderer.py` — tlab'ın KENDİ, üçüncü parti
 * bir kütüphaneye bağımlı olmayan çizim motoru) ürettiği SABİT bir görsel
 * gibi gelmeli. Bu component yalnızca `/api/chart.png`'yi <img> olarak
 * gösterir — hiçbir çizim/declutter/etiketleme mantığı burada YOK, hepsi
 * zaten Python tarafında (aylar süren ayrı bir çalışmanın ürünü). */
export function ChartImage({ symbol, tf, indicator, market, theme }: Props) {
  const [loaded, setLoaded] = useState(false);
  const [failed, setFailed] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const qs = new URLSearchParams({ symbol, tf, indicator, market, theme }).toString();
  const src = `${API_BASE}/chart.png?${qs}`;

  // GERÇEK HATA (bulunup düzeltildi): `<a href={src} download>` — `src`
  // backend'de AYRI bir origin'de (localhost:8000) olduğu için tarayıcılar
  // `download` özniteliğini GÖRMEZDEN GELİR (yalnızca same-origin/blob:/
  // data: URL'lerde çalışır) — tıklayınca dosya inmek yerine görsel yeni
  // sekmede/pencerede AÇILIYORDU. Çözüm: görseli `fetch()` ile (bu, `<a
  // download>`in aksine cross-origin kısıtlamasına TAKILMAZ) byte olarak
  // indirip bir `blob:` URL'e çevirmek — blob: URL'ler HER ZAMAN same-origin
  // sayılır, `download` orada güvenilir çalışır.
  const downloadPng = async () => {
    setDownloading(true);
    try {
      const res = await fetch(src);
      const blob = await res.blob();
      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = `${symbol}_${indicator}_${tf}.png`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(blobUrl);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="relative w-full">
      {!loaded && !failed && (
        <div className="flex h-96 items-center justify-center font-mono text-sm text-text-3">
          Grafik oluşturuluyor…
        </div>
      )}
      {failed && (
        <div className="flex h-40 items-center justify-center rounded-md border border-danger/40 bg-danger/10 text-sm text-danger">
          Grafik üretilemedi (veri bulunamadı ya da bu göstergeyle uyumsuz bir sembol/zaman dilimi olabilir).
        </div>
      )}
      {/* eslint-disable-next-line @next/next/no-img-element -- sunucudan gelen dinamik PNG, next/image optimizasyonuna uygun değil */}
      <img
        key={src}
        src={src}
        alt={`${symbol} — ${indicator}`}
        className={`w-full rounded-md ${loaded ? "block" : "hidden"}`}
        onLoad={() => {
          setLoaded(true);
          setFailed(false);
        }}
        onError={() => {
          setFailed(true);
          setLoaded(false);
        }}
      />
      {loaded && (
        <button
          onClick={downloadPng}
          disabled={downloading}
          className="absolute right-1 top-1 rounded border border-border bg-surface-1/90 px-2 py-1 text-xs text-text-2 hover:border-accent hover:text-text-1 disabled:opacity-50"
        >
          {downloading ? "İndiriliyor…" : "PNG indir"}
        </button>
      )}
    </div>
  );
}

"use client";

import { useRef, useState } from "react";

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
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const qs = new URLSearchParams({ symbol, tf, indicator, market, theme }).toString();
  const src = `${API_BASE}/chart.png?${qs}`;

  // GERÇEK HATA (2026-09-03, kullanıcı geri bildirimiyle bulundu):
  // `<img key={src}>` src değişince DOM elemanını yeniden kurar, ama
  // `loaded`/`failed` bu component'in KENDİ state'i — src değiştiğinde
  // OTOMATİK sıfırlanmaz. Bir gösterge/sembol başarıyla yüklendikten
  // (loaded=true) SONRA dropdown'dan BAŞKA birine geçilince, yeni <img>
  // henüz hiçbir şey yüklememişken sarmalayıcı onu "block" gösteriyordu
  // (eski `loaded=true` hâlâ geçerliydi) — "Grafik oluşturuluyor…" mesajı
  // hiç görünmeden boş/eski bir görsel kalıyordu ("mumların görüntüsü
  // bozulmuş" şikayetinin muhtemel kaynağı). Düzeltme: React'ın "render
  // sırasında state ayarlama" deseni (useEffect DEĞİL — eslint
  // react-hooks/set-state-in-effect bunu reddediyor, ayrıca bir render
  // gecikmesi/flaş da eklerdi) — `prevSrc` ile karşılaştırılıp src
  // değiştiği ANDA, aynı render içinde senkron sıfırlanıyor.
  const [prevSrc, setPrevSrc] = useState(src);
  if (src !== prevSrc) {
    setPrevSrc(src);
    setLoaded(false);
    setFailed(false);
  }

  // GERÇEK HATA (2 tur bulunup düzeltildi):
  // (1) `<a href={src} download>` — `src` backend'de AYRI bir origin'de
  //     (localhost:8000) olduğu için tarayıcılar `download` özniteliğini
  //     GÖRMEZDEN GELİR — tıklayınca dosya inmek yerine görsel yeni
  //     sekmede açılıyordu.
  // (2) İlk düzeltme `fetch(src)` ile YENİDEN indiriyordu — ama bu, `<img>`
  //     ZATEN aynı görseli başarıyla yüklemişken GEREKSİZ ikinci bir ağ
  //     isteğiydi; `structure.report` gibi göstergeler saniyeler sürebildiği
  //     ve (geliştirme sırasında) backend arada yeniden başlayabildiği için
  //     bu ikinci istek "Failed to fetch" ile başarısız olabiliyordu.
  // Çözüm: ekranda ZATEN yüklü/görünür olan `<img>`'i bir `<canvas>`'a
  // çizip `toBlob()` ile PNG'ye çevirmek — hiçbir YENİ ağ isteği YOK,
  // backend'in o an ayakta olup olmaması tamamen İLGİSİZ. `<img
  // crossOrigin="anonymous">` (+ backend'in zaten gönderdiği CORS
  // başlığı) canvas'ın "kirlenmesini" (taint) önler.
  const downloadPng = () => {
    setDownloading(true);
    setDownloadError(null);
    try {
      const img = imgRef.current;
      if (!img || !img.complete || img.naturalWidth === 0) {
        throw new Error("Görsel henüz hazır değil");
      }
      const canvas = document.createElement("canvas");
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      const ctx = canvas.getContext("2d");
      if (!ctx) throw new Error("Canvas oluşturulamadı");
      ctx.drawImage(img, 0, 0);
      canvas.toBlob((blob) => {
        if (!blob) {
          setDownloadError("İndirilemedi — görsel dönüştürülemedi, tekrar deneyin.");
          setDownloading(false);
          return;
        }
        const blobUrl = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = blobUrl;
        a.download = `${symbol}_${indicator}_${tf}.png`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(blobUrl);
        setDownloading(false);
      }, "image/png");
    } catch {
      setDownloadError("İndirilemedi — tekrar deneyin.");
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
        ref={imgRef}
        key={src}
        src={src}
        alt={`${symbol} — ${indicator}`}
        crossOrigin="anonymous"
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
        <div className="absolute right-1 top-1 flex flex-col items-end gap-1">
          <button
            onClick={downloadPng}
            disabled={downloading}
            className="rounded border border-border bg-surface-1/90 px-2 py-1 text-xs text-text-2 hover:border-accent hover:text-text-1 disabled:opacity-50"
          >
            {downloading ? "İndiriliyor…" : "PNG indir"}
          </button>
          {downloadError && (
            <span className="rounded bg-danger/15 px-2 py-1 text-[11px] text-danger">{downloadError}</span>
          )}
        </div>
      )}
    </div>
  );
}

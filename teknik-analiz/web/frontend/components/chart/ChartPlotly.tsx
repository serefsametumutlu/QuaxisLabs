"use client";

import { useEffect, useRef, useState } from "react";
import Plotly from "plotly.js-finance-dist-min";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api";

interface Props {
  symbol: string;
  tf: string;
  indicator: string;
  market: string;
  theme: string;
}

type Status = "loading" | "ready" | "not_found" | "error";

/** `/api/chart.json`'dan (`tlab/chart` komposerinin ürettiği Plotly figürü)
 * çekip plotly.js-finance ile TARAYICIDA çizer. `ChartImage.tsx`'in sabit
 * PNG'sinden FARKLI: hover/crosshair/zaman-aralığı düğmeleri burada
 * GERÇEKTEN çalışır (`frame.py`'nin `hovermode="x unified"` + rangeselector
 * ayarları JS tarafında canlanır). Yalnızca `tlab/chart`'a bağlanmış
 * göstergeler için kullanılır (bkz. `chart_json.py::_SUPPORTED`) — diğerleri
 * ESKİSİ GİBİ `ChartImage`'ı (PNG) kullanmaya devam eder. */
export function ChartPlotly({ symbol, tf, indicator, market, theme }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const qs = new URLSearchParams({ symbol, tf, indicator, market, theme }).toString();
  const [status, setStatus] = useState<Status>("loading");
  const [errorMsg, setErrorMsg] = useState("");

  // `ChartImage.tsx`'in AYNI deseni: `qs` değişince eski durum RENDER
  // SIRASINDA (effect İÇİNDE DEĞİL) senkron sıfırlanır — react-hooks/
  // set-state-in-effect kuralı yalnızca effect GÖVDESİNDE senkron setState'i
  // yasaklıyor, callback (`.then`/`.catch`) içindeki setState'ler serbest.
  const [prevQs, setPrevQs] = useState(qs);
  if (qs !== prevQs) {
    setPrevQs(qs);
    setStatus("loading");
    setErrorMsg("");
  }

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_BASE}/chart.json?${qs}`)
      .then(async (res) => {
        if (!res.ok) {
          const body = await res.json().catch(() => null);
          const detail = typeof body?.detail === "string" ? body.detail : `HTTP ${res.status}`;
          const err = new Error(detail) as Error & { notFound?: boolean };
          err.notFound = res.status === 404;
          throw err;
        }
        return res.json();
      })
      .then((fig: { data: unknown[]; layout: Record<string, unknown> }) => {
        if (cancelled || !containerRef.current) return;
        // `frame.py::finish()` sabit width/height basar (1600x900) — burada
        // konteynerin genişliğine UYSUN diye `autosize`a çevriliyor
        // (`responsive:true` yalnızca layout'ta sabit boyut YOKSA çalışır).
        const layout: Record<string, unknown> = { ...fig.layout, autosize: true };
        delete layout.width;
        delete layout.height;
        return Plotly.react(containerRef.current, fig.data, layout, {
          // PNG indirme düğmesi: `ChartImage`(PNG) yerine `ChartPlotly`ye
          // geçilince modebar TAMAMEN kapatılmış ve kullanıcının kullandığı
          // "PNG olarak indir" düğmesi de onunla birlikte kaybolmuştu.
          // Yalnızca indirme düğmesi bırakılır -- geri kalan Plotly araçları
          // (zoom/pan/lasso) grafiğin kendi zaman düğmeleriyle çakışıyor.
          displayModeBar: true,
          displaylogo: false,
          modeBarButtonsToRemove: [
            "zoom2d", "pan2d", "select2d", "lasso2d", "zoomIn2d", "zoomOut2d",
            "autoScale2d", "resetScale2d", "toggleSpikelines",
            "hoverClosestCartesian", "hoverCompareCartesian",
          ],
          toImageButtonOptions: {
            format: "png",
            filename: `${symbol}_${indicator}_${tf}`,
            scale: 2,
          },
          responsive: true,
        });
      })
      .then(() => {
        if (!cancelled) setStatus("ready");
      })
      .catch((err: Error & { notFound?: boolean }) => {
        if (cancelled) return;
        setErrorMsg(err.message || "Grafik üretilemedi");
        setStatus(err.notFound ? "not_found" : "error");
      });
    return () => {
      cancelled = true;
    };
  }, [qs]);

  useEffect(() => {
    const el = containerRef.current;
    return () => {
      if (el) Plotly.purge(el);
    };
  }, []);

  return (
    <div className="relative w-full">
      {/* GERÇEK HATA (bu component yazılırken bulundu): konteyner
       * `display:none` (Tailwind `hidden`) iken `Plotly.react` çağrılırsa
       * `getBoundingClientRect()` genişliği 0 döner, Plotly sabit bir
       * varsayılana (700px) düşer ve GÖRÜNÜR olduktan SONRA bile o dar
       * genişlikte KALIR (resize event'i kaçırılmış olur). Düzeltme:
       * konteyner HER ZAMAN düzen akışında/görünür kalır (yalnızca
       * yükleniyor/hata durumunda ÜSTÜNE bindirilen bir katmanla
       * gizlenir) — Plotly ilk çizimde her zaman gerçek genişliği görür. */}
      {status === "loading" && (
        <div className="absolute inset-0 z-10 flex h-96 items-center justify-center font-mono text-sm text-text-3">
          Grafik oluşturuluyor…
        </div>
      )}
      {status === "not_found" && (
        <div className="absolute inset-0 z-10 flex h-40 items-center justify-center rounded-md border border-border bg-surface-1 text-sm text-text-3">
          {errorMsg || "Güncel/geçerli bir sinyal yok"}
        </div>
      )}
      {status === "error" && (
        <div className="absolute inset-0 z-10 flex h-40 items-center justify-center rounded-md border border-danger/40 bg-danger/10 text-sm text-danger">
          {errorMsg || "Grafik üretilemedi (veri bulunamadı ya da bu göstergeyle uyumsuz bir sembol/zaman dilimi olabilir)."}
        </div>
      )}
      <div
        ref={containerRef}
        className="w-full"
        style={{ height: 640, visibility: status === "ready" ? "visible" : "hidden" }}
      />
    </div>
  );
}

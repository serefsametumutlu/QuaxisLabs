"use client";

import { useState } from "react";
import { fetchReport, type QuantReportResponse } from "@/lib/api";

interface Props {
  symbol: string;
  tf: string;
  market: string;
}

/** `tlab/viz/quant_report.py::generate_quant_report()`'un (Gemini, aynı
 * anahtar `bilanco-radar`'dan okunuyor — bkz. `web/backend/routes/report.py`)
 * ürettiği doğal-dil raporu gösterir. Otomatik TETİKLENMEZ (API çağrısı
 * ücretli/hız sınırlı, ~30-40sn sürüyor) — kullanıcı butona basınca çalışır. */
export function AiReportPanel({ symbol, tf, market }: Props) {
  const [report, setReport] = useState<QuantReportResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = () => {
    setLoading(true);
    setError(null);
    fetchReport({ symbol, tf, market })
      .then(setReport)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  };

  return (
    <div className="rounded-lg border border-border bg-surface-1 p-4">
      <div className="mb-2 flex items-center gap-3">
        <span className="text-sm font-semibold text-text-1">Yapay Zeka Raporu</span>
        {report && (
          <span
            className={`rounded px-2 py-0.5 font-mono text-[10px] ${
              report.used_ai ? "bg-accent/15 text-accent" : "bg-warning/15 text-warning"
            }`}
          >
            {report.used_ai ? `Gemini · ${report.provider}` : "Deterministik özet (AI kullanılamadı)"}
          </span>
        )}
        <button
          onClick={generate}
          disabled={loading}
          className="ml-auto rounded-md bg-accent px-3 py-1 text-xs font-medium text-bg hover:opacity-90 disabled:opacity-50"
        >
          {loading ? "Oluşturuluyor… (~30sn)" : report ? "Yeniden Oluştur" : "Rapor Oluştur"}
        </button>
      </div>
      {error && <div className="text-sm text-danger">{error}</div>}
      {report?.note && !report.used_ai && (
        <div className="mb-2 text-xs text-warning">{report.note}</div>
      )}
      {report && (
        <p className="whitespace-pre-line text-sm leading-relaxed text-text-2">{report.text}</p>
      )}
      {!report && !loading && !error && (
        <p className="text-xs text-text-3">
          Bu sembol için POC/RSI/trend/hedef gibi zaten hesaplanmış olgulardan, Gemini ile
          samimi bir Türkçe özet üretir — hiçbir sayı uydurulmaz.
        </p>
      )}
    </div>
  );
}

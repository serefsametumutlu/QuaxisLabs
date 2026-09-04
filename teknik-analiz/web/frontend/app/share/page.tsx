"use client";

import { useState } from "react";
import { fetchShareText } from "@/lib/api";
import type { ShareTextResponse } from "@/lib/api";
import { Sidebar } from "@/components/layout/Sidebar";
import { useTheme } from "@/lib/useTheme";

const MARKETS = ["bist", "nasdaq"];

/** `web/backend/routes/share_text.py`'e ince bir arayüz — kullanıcı yalnızca
 * bir sembol adı girer, sistem o an sembolü çoklu-göstergeyle (yapı raporu,
 * harmonik, golden zone, arz-talep, çift tepe/dip) tarayıp X'te paylaşılabilir
 * TEK bir metin üretir. `AiReportPanel`'deki mevcut "yapay zeka rapor"tan
 * (bir göstergenin ZATEN açık olduğu grafiğe bağlı) BİLİNÇLİ OLARAK AYRI bir
 * sayfa — 2026-09-04 kullanıcı isteği: "ben hisse ismini vereyim ve yapılan
 * anlık taramalara göre analiz edip bana bu şekilde paylaşım metinleri
 * hazırlayacak yapay zeka rapor kısmından hariç olarak". */
export default function SharePage() {
  const [theme, setTheme] = useTheme();
  const [market, setMarket] = useState("bist");
  const [symbol, setSymbol] = useState("");
  const [report, setReport] = useState<ShareTextResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const generate = () => {
    const s = symbol.trim().toUpperCase();
    if (!s) return;
    setLoading(true);
    setError(null);
    setCopied(false);
    fetchShareText({ symbol: s, market })
      .then(setReport)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  };

  const copy = () => {
    if (!report) return;
    navigator.clipboard
      .writeText(report.text)
      .then(() => setCopied(true))
      .catch(() => {});
  };

  return (
    <div className="flex min-h-screen bg-bg text-text-1">
      <Sidebar theme={theme} onThemeChange={setTheme} />
      <div className="flex-1">
        <header className="flex flex-wrap items-end gap-4 border-b border-border px-6 py-4">
          <label className="flex flex-col gap-1 text-xs text-text-3">
            Piyasa
            <select
              value={market}
              onChange={(e) => setMarket(e.target.value)}
              className="rounded-md border border-border bg-surface-1 px-2.5 py-1.5 text-sm text-text-1 outline-none focus:border-accent"
            >
              {MARKETS.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs text-text-3">
            Sembol
            <input
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              onKeyDown={(e) => e.key === "Enter" && generate()}
              placeholder="ör. INTEM"
              className="w-40 rounded-md border border-border bg-surface-1 px-2.5 py-1.5 text-sm text-text-1 outline-none focus:border-accent"
            />
          </label>
          <button
            onClick={generate}
            disabled={loading || !symbol.trim()}
            className="rounded-md bg-accent px-3.5 py-1.5 text-sm font-medium text-bg hover:opacity-90 disabled:opacity-50"
          >
            {loading ? "Taranıyor… (~30sn)" : "Paylaşım Metni Oluştur"}
          </button>
        </header>

        <main className="flex flex-col gap-4 px-6 py-5">
          <p className="max-w-2xl text-xs text-text-3">
            Sembolü yapı raporu, harmonik (Carney), golden zone, arz-talep bölgeleri ve çift tepe/dip
            göstergeleri üzerinden 1D+4H tarar; Gemini ile bir quant&apos;ın kaleminden çıkmış gibi,
            X&apos;te doğrudan paylaşabileceğin tek bir metin üretir — hiçbir sayı uydurulmaz.
          </p>

          {error && (
            <div className="max-w-2xl rounded-md border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">
              {error}
            </div>
          )}

          {report && (
            <div className="max-w-2xl rounded-lg border border-border bg-surface-1 p-4">
              <div className="mb-3 flex items-center gap-3">
                <span
                  className={`rounded px-2 py-0.5 font-mono text-[10px] ${
                    report.used_ai ? "bg-accent/15 text-accent" : "bg-warning/15 text-warning"
                  }`}
                >
                  {report.used_ai ? `Gemini · ${report.provider}` : "Deterministik özet (AI kullanılamadı)"}
                </span>
                <button
                  onClick={copy}
                  className="ml-auto rounded-md border border-border px-3 py-1 text-xs font-medium text-text-2 hover:bg-surface-2"
                >
                  {copied ? "Kopyalandı ✓" : "Kopyala"}
                </button>
              </div>
              {report.note && !report.used_ai && (
                <div className="mb-2 text-xs text-warning">{report.note}</div>
              )}
              <p className="whitespace-pre-line text-sm leading-relaxed text-text-2">{report.text}</p>
            </div>
          )}

          {!report && !loading && !error && (
            <div className="max-w-2xl rounded-lg border border-dashed border-border px-4 py-6 text-sm text-text-3">
              Bir sembol yazıp &quot;Paylaşım Metni Oluştur&quot;a bas.
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

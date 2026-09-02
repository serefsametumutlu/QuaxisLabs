"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { fetchCatalog, fetchRuns, fetchSignals } from "@/lib/api";
import type { ScanRun, ScanSignal } from "@/lib/api";
import type { CatalogEntry } from "@/lib/types";
import { Sidebar } from "@/components/layout/Sidebar";
import { useTheme } from "@/lib/useTheme";

const MARKETS = ["bist", "nasdaq"];
const PAGE_SIZE = 50;

const STATE_COLOR: Record<string, string> = {
  confirmed: "text-accent",
  completed: "text-accent",
  active: "text-warning",
  pending: "text-text-3",
  invalidated: "text-danger",
  expired: "text-text-3",
};

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString("tr-TR", { dateStyle: "medium", timeStyle: "short" });
  } catch {
    return iso;
  }
}

/** Mevcut taramaları (`tlab eod`/`tlab scan`'in ZATEN ürettiği, `outputs/
 * results.db`'deki) listeler — YENİ bir tarama BAŞLATMAZ (bkz. `web/backend/
 * routes/scan.py` docstring'i: `run_eod()` dakikalarca sürebilen senkron
 * bir işlem, web isteği içinde tetiklemek kapsam dışı bırakıldı — kullanıcı
 * `tlab eod` komutunu kendi terminalinden çalıştırmalı). */
export default function ScanPage() {
  const router = useRouter();
  const [theme, setTheme] = useTheme();
  const [market, setMarket] = useState("bist");
  const [runs, setRuns] = useState<ScanRun[]>([]);
  const [runId, setRunId] = useState<string>("");
  const [tf, setTf] = useState("");
  const [indicator, setIndicator] = useState("");
  const [symbol, setSymbol] = useState("");
  const [allStates, setAllStates] = useState(false);
  const [offset, setOffset] = useState(0);
  const [catalog, setCatalog] = useState<CatalogEntry[]>([]);
  const [signals, setSignals] = useState<ScanSignal[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCatalog().then(setCatalog).catch(() => setCatalog([]));
  }, []);

  useEffect(() => {
    fetchRuns(market)
      .then((rs) => {
        setRuns(rs);
        setRunId(rs[0]?.run_id ?? "");
        setOffset(0);
      })
      .catch(() => setRuns([]));
  }, [market]);

  const load = useCallback(() => {
    if (!runId) return;
    setLoading(true);
    setError(null);
    fetchSignals({
      run_id: runId,
      tf: tf || undefined,
      indicator: indicator || undefined,
      symbol: symbol || undefined,
      all_states: allStates,
      limit: PAGE_SIZE,
      offset,
    })
      .then((res) => {
        setSignals(res.signals);
        setTotal(res.total);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [runId, tf, indicator, symbol, allStates, offset]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  const openChart = (s: ScanSignal) => {
    const qs = new URLSearchParams({
      symbol: s.symbol,
      tf: s.timeframe.toLowerCase(),
      indicator: s.indicator,
      market,
    });
    router.push(`/chart?${qs.toString()}`);
  };

  const selectedRun = runs.find((r) => r.run_id === runId);
  const page = Math.floor(offset / PAGE_SIZE) + 1;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));

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
            Tarama
            <select
              value={runId}
              onChange={(e) => {
                setRunId(e.target.value);
                setOffset(0);
              }}
              className="min-w-48 rounded-md border border-border bg-surface-1 px-2.5 py-1.5 text-sm text-text-1 outline-none focus:border-accent"
            >
              {runs.map((r) => (
                <option key={r.run_id} value={r.run_id}>
                  {r.run_id} ({r.universe_size} sembol)
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs text-text-3">
            Zaman Dilimi
            <select
              value={tf}
              onChange={(e) => {
                setTf(e.target.value);
                setOffset(0);
              }}
              className="rounded-md border border-border bg-surface-1 px-2.5 py-1.5 text-sm text-text-1 outline-none focus:border-accent"
            >
              <option value="">Tümü</option>
              {(selectedRun?.timeframes ?? []).map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs text-text-3">
            Gösterge
            <select
              value={indicator}
              onChange={(e) => {
                setIndicator(e.target.value);
                setOffset(0);
              }}
              className="min-w-48 rounded-md border border-border bg-surface-1 px-2.5 py-1.5 text-sm text-text-1 outline-none focus:border-accent"
            >
              <option value="">Tümü</option>
              {catalog.map((c) => (
                <option key={c.name} value={c.name}>
                  {c.name}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs text-text-3">
            Sembol
            <input
              value={symbol}
              onChange={(e) => {
                setSymbol(e.target.value.toUpperCase());
                setOffset(0);
              }}
              placeholder="ör. AKBNK"
              className="w-32 rounded-md border border-border bg-surface-1 px-2.5 py-1.5 text-sm text-text-1 outline-none focus:border-accent"
            />
          </label>
          <label className="flex items-center gap-2 pb-1.5 text-xs text-text-3">
            <input
              type="checkbox"
              checked={allStates}
              onChange={(e) => {
                setAllStates(e.target.checked);
                setOffset(0);
              }}
            />
            Tüm durumları göster
          </label>
        </header>

        <main className="flex flex-col gap-4 px-6 py-5">
          {selectedRun && (
            <div className="flex flex-wrap gap-4 text-xs text-text-3">
              <span>
                Durum: <span className="text-text-1">{selectedRun.status}</span>
              </span>
              <span>
                Bitiş: <span className="text-text-1">{formatDate(selectedRun.finished_at ?? selectedRun.started_at)}</span>
              </span>
              <span>
                Toplam eşleşme: <span className="text-text-1">{total.toLocaleString("tr-TR")}</span>
              </span>
            </div>
          )}
          {error && (
            <div className="rounded-md border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">
              {error}
            </div>
          )}
          {runs.length === 0 && !error && (
            <div className="rounded-md border border-border bg-surface-1 px-3 py-2 text-sm text-text-2">
              Bu piyasa için henüz bir tarama sonucu yok. Terminalden{" "}
              <code className="font-mono text-text-1">tlab eod --market {market}</code> çalıştırıp
              buraya geri dönebilirsin.
            </div>
          )}

          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="bg-surface-1 text-xs text-text-3">
                <tr>
                  <th className="px-3 py-2 font-medium">Sembol</th>
                  <th className="px-3 py-2 font-medium">TF</th>
                  <th className="px-3 py-2 font-medium">Gösterge</th>
                  <th className="px-3 py-2 font-medium">Durum</th>
                  <th className="px-3 py-2 font-medium">Yön</th>
                  <th className="px-3 py-2 font-medium">Skor</th>
                  <th className="px-3 py-2 font-medium">Tespit</th>
                </tr>
              </thead>
              <tbody>
                {signals.map((s, i) => (
                  <tr
                    key={`${s.symbol}-${s.timeframe}-${s.indicator}-${s.pattern_id}-${i}`}
                    onClick={() => openChart(s)}
                    className="cursor-pointer border-t border-border hover:bg-surface-2"
                  >
                    <td className="px-3 py-2 font-medium">{s.symbol}</td>
                    <td className="px-3 py-2 font-mono text-xs text-text-2">{s.timeframe}</td>
                    <td className="px-3 py-2 font-mono text-xs text-text-2">{s.indicator}</td>
                    <td className={`px-3 py-2 font-medium ${STATE_COLOR[s.state] ?? "text-text-2"}`}>
                      {s.state}
                    </td>
                    <td className="px-3 py-2">
                      {s.direction === "long" ? (
                        <span className="text-up">AL</span>
                      ) : s.direction === "short" ? (
                        <span className="text-down">SAT</span>
                      ) : (
                        <span className="text-text-3">{s.direction}</span>
                      )}
                    </td>
                    <td className="px-3 py-2 font-mono text-xs">{s.score.toFixed(2)}</td>
                    <td className="px-3 py-2 text-xs text-text-3">{formatDate(s.detected_at)}</td>
                  </tr>
                ))}
                {!loading && signals.length === 0 && runs.length > 0 && (
                  <tr>
                    <td colSpan={7} className="px-3 py-6 text-center text-sm text-text-3">
                      Bu filtrelerle eşleşen sinyal yok.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {loading && <div className="font-mono text-sm text-text-3">Yükleniyor…</div>}

          {total > PAGE_SIZE && (
            <div className="flex items-center gap-3 text-sm text-text-2">
              <button
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                className="rounded-md border border-border px-3 py-1 disabled:opacity-40"
              >
                Önceki
              </button>
              <span className="font-mono text-xs">
                Sayfa {page} / {pageCount}
              </span>
              <button
                disabled={offset + PAGE_SIZE >= total}
                onClick={() => setOffset(offset + PAGE_SIZE)}
                className="rounded-md border border-border px-3 py-1 disabled:opacity-40"
              >
                Sonraki
              </button>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

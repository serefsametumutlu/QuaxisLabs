"use client";

import { useEffect, useState, useCallback } from "react";
import { fetchCatalog, fetchChart, fetchUniverse } from "@/lib/api";
import type { CatalogEntry, ChartResponse } from "@/lib/types";
import { PriceChart } from "@/components/chart/PriceChart";
import { ChartGuide } from "@/components/chart/ChartGuide";
import { AiReportPanel } from "@/components/chart/AiReportPanel";
import { THEMES, THEME_KEYS, applyTheme } from "@/lib/themes";
import { Brand } from "@/components/layout/Brand";

const TIMEFRAMES = ["1h", "4h", "1d", "w1"];
const MARKETS = ["bist", "nasdaq"];

function Select({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: string[];
}) {
  return (
    <label className="flex flex-col gap-1 text-xs text-text-3">
      {label}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-md border border-border bg-surface-1 px-2.5 py-1.5 text-sm text-text-1 outline-none focus:border-accent"
      >
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </label>
  );
}

export default function ChartPage() {
  const [theme, setTheme] = useState<string>("dark");
  const [market, setMarket] = useState("bist");
  const [symbol, setSymbol] = useState("AKFIS");
  const [tf, setTf] = useState("4h");
  const [indicator, setIndicator] = useState("structure.swing_fib_abcd");
  const [catalog, setCatalog] = useState<CatalogEntry[]>([]);
  const [universe, setUniverse] = useState<string[]>([]);
  const [data, setData] = useState<ChartResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  useEffect(() => {
    fetchCatalog().then(setCatalog).catch(() => setCatalog([]));
  }, []);

  useEffect(() => {
    fetchUniverse(market).then(setUniverse).catch(() => setUniverse([]));
  }, [market]);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchChart({ symbol, tf, indicator, market })
      .then(setData)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [symbol, tf, indicator, market]);

  useEffect(() => {
    // Standart "effect veri çeker" deseni (React docs) — `load` zaten
    // loading/error/data state'ini kendi async akışında yönetiyor.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  const singleIndicators = catalog.filter((c) => !c.needs_context && !c.needs_universe);
  const indicatorOptions = ["structure.report", ...singleIndicators.map((c) => c.name)];

  return (
    <div className="min-h-screen bg-bg text-text-1">
      <header className="flex flex-wrap items-end gap-4 border-b border-border px-6 py-4">
        <Brand />
        <Select label="Piyasa" value={market} onChange={setMarket} options={MARKETS} />
        <label className="flex flex-col gap-1 text-xs text-text-3">
          Sembol
          <input
            list="symbol-list"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            className="rounded-md border border-border bg-surface-1 px-2.5 py-1.5 text-sm text-text-1 outline-none focus:border-accent"
          />
          <datalist id="symbol-list">
            {universe.map((s) => (
              <option key={s} value={s} />
            ))}
          </datalist>
        </label>
        <Select label="Zaman Dilimi" value={tf} onChange={setTf} options={TIMEFRAMES} />
        <label className="flex flex-col gap-1 text-xs text-text-3">
          Gösterge
          <select
            value={indicator}
            onChange={(e) => setIndicator(e.target.value)}
            className="min-w-56 rounded-md border border-border bg-surface-1 px-2.5 py-1.5 text-sm text-text-1 outline-none focus:border-accent"
          >
            {indicatorOptions.map((o) => (
              <option key={o} value={o}>
                {o}
              </option>
            ))}
          </select>
        </label>
        <button
          onClick={load}
          className="rounded-md bg-accent px-3.5 py-1.5 text-sm font-medium text-bg hover:opacity-90"
        >
          Yenile
        </button>
        <label className="ml-auto flex flex-col gap-1 text-xs text-text-3">
          Tasarım
          <select
            value={theme}
            onChange={(e) => setTheme(e.target.value)}
            className="rounded-md border border-border bg-surface-1 px-2.5 py-1.5 text-sm text-text-1 outline-none focus:border-accent"
          >
            {THEME_KEYS.map((k) => (
              <option key={k} value={k}>
                {THEMES[k].name}
              </option>
            ))}
          </select>
        </label>
      </header>

      <main className="flex flex-col gap-4 px-6 py-5">
        {loading && <div className="font-mono text-sm text-text-3">Yükleniyor…</div>}
        {error && (
          <div className="rounded-md border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">
            {error}
          </div>
        )}
        {data && !loading && !error && (
          <>
            <div className="rounded-lg border border-border bg-surface-1 p-3">
              <div className="mb-2 flex items-baseline gap-3 px-1">
                <span className="text-base font-semibold">{data.symbol}</span>
                <span className="font-mono text-xs text-text-3">
                  {data.result.indicator} · {data.tf.toUpperCase()}
                </span>
              </div>
              <PriceChart data={data} theme={theme} />
            </div>
            <ChartGuide indicator={data.result.indicator} />
            <AiReportPanel
              key={`${symbol}-${tf}-${market}-${indicator}`}
              symbol={symbol}
              tf={tf}
              market={market}
              indicator={indicator}
            />
          </>
        )}
      </main>
    </div>
  );
}

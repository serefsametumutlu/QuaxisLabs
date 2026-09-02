"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { fetchCatalog, fetchUniverse } from "@/lib/api";
import type { CatalogEntry } from "@/lib/types";
import { ChartImage } from "@/components/chart/ChartImage";
import { ChartGuide } from "@/components/chart/ChartGuide";
import { AiReportPanel } from "@/components/chart/AiReportPanel";
import { Sidebar } from "@/components/layout/Sidebar";
import { useTheme } from "@/lib/useTheme";

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
  return (
    <Suspense fallback={null}>
      <ChartPageInner />
    </Suspense>
  );
}

function ChartPageInner() {
  const [theme, setTheme] = useTheme();
  // `/scan` sayfasından bir sinyale tıklanınca buraya `?symbol=&tf=&indicator=&market=`
  // ile gelinir — URL parametreleri varsa varsayılanların YERİNE kullanılır.
  const searchParams = useSearchParams();
  const [market, setMarket] = useState(() => searchParams.get("market") ?? "bist");
  const [symbol, setSymbol] = useState(() => searchParams.get("symbol") ?? "AKFIS");
  const [tf, setTf] = useState(() => searchParams.get("tf") ?? "4h");
  const [indicator, setIndicator] = useState(
    () => searchParams.get("indicator") ?? "structure.swing_fib_abcd"
  );
  const [catalog, setCatalog] = useState<CatalogEntry[]>([]);
  const [universe, setUniverse] = useState<string[]>([]);
  // Grafik `<img>` olarak geliyor — aynı URL'e tekrar basmak tarayıcı
  // önbelleğinden dönebilir, "Yenile" butonu bu sayacı artırıp cache-bust eder.
  const [refreshTick, setRefreshTick] = useState(0);

  useEffect(() => {
    fetchCatalog().then(setCatalog).catch(() => setCatalog([]));
  }, []);

  useEffect(() => {
    fetchUniverse(market).then(setUniverse).catch(() => setUniverse([]));
  }, [market]);

  const singleIndicators = catalog.filter((c) => !c.needs_context && !c.needs_universe);
  const indicatorOptions = ["structure.report", ...singleIndicators.map((c) => c.name)];

  return (
    <div className="flex min-h-screen bg-bg text-text-1">
      <Sidebar theme={theme} onThemeChange={setTheme} />
      <div className="flex-1">
        <header className="flex flex-wrap items-end gap-4 border-b border-border px-6 py-4">
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
            onClick={() => setRefreshTick((t) => t + 1)}
            className="rounded-md bg-accent px-3.5 py-1.5 text-sm font-medium text-bg hover:opacity-90"
          >
            Yenile
          </button>
        </header>

        <main className="flex flex-col gap-4 px-6 py-5">
          <div className="rounded-lg border border-border bg-surface-1 p-3">
            <div className="mb-2 flex items-baseline gap-3 px-1">
              <span className="text-base font-semibold">{symbol}</span>
              <span className="font-mono text-xs text-text-3">
                {indicator} · {tf.toUpperCase()}
              </span>
            </div>
            <ChartImage
              key={refreshTick}
              symbol={symbol}
              tf={tf}
              indicator={indicator}
              market={market}
              theme={theme}
            />
          </div>
          <ChartGuide indicator={indicator} />
          <AiReportPanel
            key={`${symbol}-${tf}-${market}-${indicator}`}
            symbol={symbol}
            tf={tf}
            market={market}
            indicator={indicator}
          />
        </main>
      </div>
    </div>
  );
}
